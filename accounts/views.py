from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth, Group
from django.contrib import messages
from .models import Profile
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.decorators import login_required
from med.decorators import superuser_required
from django.views import View
from django.db import transaction
from django.http import JsonResponse
import json

# Create your views here.
@login_required
def logout(request):
    """
    Logs the user out and clears the session.
    This also handles the edge case where an impersonating admin logs out directly
    instead of using the 'Stop Impersonation' feature.
    """
    was_impersonating = 'impersonator_id' in request.session

    auth.logout(request)

    if was_impersonating:
        messages.warning(request, "You have been logged out from an impersonation session. Please log in again.")
    else:
        messages.success(request, "You have been successfully logged out.")
    return redirect('home')

@login_required
def book(request):
    return render(request, 'book.html')

class LoginView(View):
    def dispatch(self, request, *args, **kwargs):
        # This check now runs before the view's POST handling, solving the CSRF issue.
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return redirect('login')

        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            messages.success(request, f'Welcome to MedEasy, {user.first_name or user.username}!')

            # Check for a 'next' parameter in the POST data from the hidden input
            next_page = request.POST.get('next')
            # Security check to ensure the redirect is to a safe, local URL
            if next_page and url_has_allowed_host_and_scheme(url=next_page, allowed_hosts={request.get_host()}):
                return redirect(next_page)
            # Fallback to a default page if 'next' is not present or is invalid
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
            return redirect('login')

class NewAccountView(View):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, 'new_account.html')

    def post(self, request):
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        age = request.POST.get('age', '').strip()
        gender = request.POST.get('gender')
        mobile = request.POST.get('mobile', '').strip()
        password = request.POST.get('password1', '')

        if not all([first_name, last_name, username, email, age, gender, mobile, password]):
            messages.error(request, 'All fields are required.')
            return redirect('new_account')

        if len(username) < 3:
            messages.error(request, 'Username must be at least 3 characters long.')
            return redirect('new_account')

        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('new_account')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username is already taken. Please choose another one.')
            return redirect('new_account')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return redirect('new_account')
        else:
            try:
                with transaction.atomic():
                    user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name, email=email, password=password)
                    
                    # Get or create the 'Patients' group and add the user to it
                    patients_group, _ = Group.objects.get_or_create(name='Patients')
                    user.groups.add(patients_group)

                    # Create and save the profile
                    Profile.objects.create(user=user, age=age, gender=gender, mobile=mobile)
                
                messages.success(request, 'Your account has been created successfully. Please log in.')
                return redirect('login')
            except Exception as e:
                messages.error(request, f'An error occurred during account creation: {e}')
                return redirect('new_account')
            

def check_username(request):
    # If a user tries to access this URL directly with a GET request,
    # redirect them to the homepage.
    if request.method == 'GET':
        return redirect('home')

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            # Use case-insensitive check for better user experience
            if User.objects.filter(username__iexact=username).exists():
                return JsonResponse({'is_taken': True})
            else:
                return JsonResponse({'is_taken': False})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

def check_email(request):
    if request.method == 'GET':
        return redirect('home')

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            if User.objects.filter(email__iexact=email).exists():
                return JsonResponse({'is_taken': True})
            else:
                return JsonResponse({'is_taken': False})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        

@superuser_required
def impersonate_user(request, user_id):
    impersonator_id = request.user.id  # Store the admin's ID before it's lost.
    try:
        user_to_impersonate = User.objects.get(pk=user_id)

        # For security, prevent a superuser from impersonating another superuser.
        if user_to_impersonate.is_superuser:
            messages.error(request, "For security reasons, you cannot impersonate another superuser.")
            return redirect('admin_dashboard')

        # Login as the new user. This flushes the old session.
        auth.login(request, user_to_impersonate, backend='django.contrib.auth.backends.ModelBackend')
        
        # Now, in the new session, store the original admin's ID.
        request.session['impersonator_id'] = impersonator_id

        messages.info(request, f"You are now impersonating {user_to_impersonate.username}.")
        return redirect('home')
    except User.DoesNotExist:
        messages.error(request, "User to impersonate not found.")
        return redirect('admin_dashboard')

@login_required
def stop_impersonation(request):
    impersonator_id = request.session.get('impersonator_id')
    if not impersonator_id:
        return redirect('home')

    try:
        impersonator = User.objects.get(pk=impersonator_id)
        # First, log out the current (impersonated) user.
        # This will call request.session.flush() and clear the session completely.
        auth.logout(request)

        # Now, log the original admin user back in.
        # This will create a new, clean session for the admin.
        auth.login(request, impersonator, backend='django.contrib.auth.backends.ModelBackend')

        messages.success(request, "You have stopped impersonating and returned to your admin account.")
        return redirect('admin_dashboard')
    except User.DoesNotExist:
        # If the original admin user was deleted, we should just log out.
        auth.logout(request)
        messages.error(request, "Your original admin account could not be found. You have been logged out for security.")
        return redirect('login')