from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

def group_required(*group_names):
    """
    Decorator for views that checks that the logged-in user is a member of
    at least one of the specified groups.
    Assumes the user is already authenticated (e.g., used with @login_required).
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # The check for `is_superuser` is removed to enforce strict application roles.
            # Superusers must belong to the required group to access the view.
            if request.user.groups.filter(name__in=group_names).exists():
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "You don't have permission to access this page.")
                # If the user is a doctor trying to access a non-doctor page, redirect to their dashboard.
                if request.user.groups.filter(name='Doctors').exists():
                    return redirect('doctor_dashboard')
                return redirect('home')
        return _wrapped_view
    return decorator

def superuser_required(view_func):
    """
    Decorator for views that checks that the user is a logged-in superuser.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "You do not have permission to access this page.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return login_required(_wrapped_view)