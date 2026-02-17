from django.shortcuts import render, redirect
from .models import Doctor, Appointment, LabTest, EmailLog
from django.urls import reverse
from django.db.models import Count
from urllib.parse import urlencode
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.db import transaction
from .email_utils import send_confirmation_email_async, send_reschedule_email_async, send_lab_test_email_async, send_appointment_cancellation_email_async, send_lab_test_cancellation_email_async, send_doctor_confirmation_email_async
from .filters import AppointmentFilter, UserFilter, PatientAppointmentFilter, LabTestFilter
from .decorators import group_required, superuser_required
from django.http import JsonResponse
from django.contrib.auth.models import User, Group

# Create your views here.
def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

@login_required
@group_required('Doctors')
def doctor_dashboard(request):
    try:
        doctor = request.user.doctor_profile
    except Doctor.DoesNotExist:
        messages.error(request, "Your doctor profile could not be found.")
        return redirect('home')

    # --- Year Filter ---
    all_years = Appointment.objects.filter(doctor=doctor).dates('appointment_date', 'year', order='DESC')
    available_years = [d.year for d in all_years]

    # Determine the default year. Use the most recent year with appointments,
    # or the current year if there are no appointments at all.
    default_year = available_years[0] if available_years else datetime.today().year

    try:
        # Use the year from the request, but fall back to our calculated default.
        selected_year = int(request.GET.get('year', default_year))
    except (ValueError, TypeError):
        selected_year = default_year

    # --- Data Aggregation for the selected year ---
    appointments = Appointment.objects.filter(doctor=doctor, appointment_date__year=selected_year)

    # 1. Key Metrics
    total_bookings = appointments.count()
    status_counts = appointments.values('status').annotate(count=Count('id'))
    
    status_data = {item['status']: item['count'] for item in status_counts}
    completed_count = status_data.get('Completed', 0)
    confirmed_count = status_data.get('Confirmed', 0)

    # 2. Monthly Bookings for Bar Chart
    monthly_counts = {i: 0 for i in range(1, 13)}
    for appt in appointments.values('appointment_date__month').annotate(count=Count('id')):
        monthly_counts[appt['appointment_date__month']] = appt['count']

    # 3. Status Distribution for Pie Chart
    pie_chart_labels = list(status_data.keys())
    pie_chart_data = list(status_data.values())
    status_color_map = {
        'Pending': '#ffc107',   # Bootstrap Warning
        'Confirmed': '#198754', # Bootstrap Success
        'Cancelled': '#dc3545', # Bootstrap Danger
        'Completed': '#0dcaf0', # Bootstrap Info
    }
    pie_chart_colors = [status_color_map.get(status, '#6c757d') for status in pie_chart_labels] # Default to secondary

    context = {
        'doctor': doctor,
        'selected_year': selected_year,
        'available_years': available_years,
        'total_bookings': total_bookings,
        'completed_count': completed_count,
        'confirmed_count': confirmed_count,
        'monthly_bookings_data': list(monthly_counts.values()),
        'pie_chart_labels': pie_chart_labels,
        'pie_chart_data': pie_chart_data,
        'pie_chart_colors': pie_chart_colors,
    }

    return render(request, 'doctor_dashboard.html', context)

@superuser_required
def admin_dashboard(request):
    # Use prefetch_related and select_related for better performance
    user_list = User.objects.prefetch_related('groups').select_related('profile').all().order_by('username')
    user_filter = UserFilter(request.GET, queryset=user_list)

    paginator = Paginator(user_filter.qs, 15)  # Show 15 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Preserve other GET parameters during pagination
    get_params = request.GET.copy()
    if 'page' in get_params:
        del get_params['page']

    context = {
        'filter': user_filter,
        'page_obj': page_obj,
        'query_params': get_params.urlencode(),
    }
    return render(request, 'admin_dashboard.html', context)

@login_required
@group_required('Patients')
def lab_test(request): 
    if request.method == 'POST':
        location = request.POST.get('location')
        test_type = request.POST.get('type_test')

        if not location or not test_type:
            messages.error(request, 'Please select both a location and a lab test.')
            return render(request, 'lab_test.html')

        # Create and save the LabTest record
        new_lab_test = LabTest.objects.create(
            test_type=test_type,
            location=location,
            booked_by=request.user
        )
        
        # Send confirmation email asynchronously
        send_lab_test_email_async(new_lab_test.id, request.user.id)
        
        # Instead of a message and redirect, render a dedicated confirmation page.
        return render(request, 'lab_test_booked.html')
    return render(request, 'lab_test.html')

@login_required
@group_required('Patients')
def doctor_details(request):
    # Check if the user has come from the booking page by checking for session data
    if 'patient_details' not in request.session:
        messages.error(request, 'Please fill out the appointment form to find doctors.')
        return redirect('book_appointment')

    # Get filter criteria from URL query parameters
    disease = request.GET.get('disease')
    location = request.GET.get('location')

    # Validate that both disease and location are present
    if not disease or not location:
        messages.error(request, 'Please select both a disease/symptom and a location to find doctors.')
        return redirect('book_appointment')

    # Start with all doctors
    docs_query = Doctor.objects.all()

    # Apply filters if they exist
    if disease not in ('Other'):
        # Assuming 'expert' field in Doctors model stores expertise related to diseases
        docs_query = docs_query.filter(expert__icontains=disease)

    if location not in ('Other'):
        docs_query = docs_query.filter(location__icontains=location)

    # Order the results for consistent pagination
    docs_query = docs_query.order_by('name')

    paginator = Paginator(docs_query, 10)  # Show 10 doctors per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'searched_disease': disease,
        'searched_location': location,
    }
    return render(request, 'doctor_details.html', context)

def _generate_time_slots(start_time, end_time, interval_minutes=30):
    """Helper function to generate time slots as (start, end) tuples."""
    slots = []
    if not start_time or not end_time:
        return slots
        
    start_datetime = datetime.combine(datetime.today(), start_time)
    end_datetime = datetime.combine(datetime.today(), end_time)
    
    current_start = start_datetime
    while current_start < end_datetime:
        current_end = current_start + timedelta(minutes=interval_minutes)
        # Ensure the slot doesn't go past the doctor's end time
        if current_end > end_datetime:
            break
        slots.append((current_start.time(), current_end.time()))
        current_start = current_end
        
    return slots

@login_required
@group_required('Patients')
def create_appointment(request, doctor_id):
    patient_details = request.session.get('patient_details')
    if not patient_details:
        messages.error(request, 'Your session has expired. Please fill out the appointment form again.')
        return redirect('book_appointment')

    try:
        doctor = Doctor.objects.get(pk=doctor_id)
    except Doctor.DoesNotExist:
        messages.error(request, 'The selected doctor could not be found.')
        return redirect('home')

    # Determine the date for which to show slots. Default to today.
    date_str = request.GET.get('date', datetime.today().strftime('%Y-%m-%d'))
    try:
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        appointment_date = datetime.today().date()

    # Get already booked time slots for the selected date for this doctor
    booked_slots = list(Appointment.objects.filter(
        doctor=doctor,
        appointment_date=appointment_date,
        appointment_time__isnull=False,
    ).exclude(status='Cancelled').values_list('appointment_time', flat=True))

    if request.method == 'POST':
        # The date is submitted along with the time
        appointment_date_str = request.POST.get('appointment_date')
        selected_time_str = request.POST.get('appointment_time')
        if not appointment_date_str or not selected_time_str:
            messages.error(request, 'Please select both a date and an available time slot.')

            # Re-build context for re-rendering the page with the error message
            try:
                # Use the date from the failed POST if available, otherwise today
                appointment_date_for_rerender = datetime.strptime(appointment_date_str, '%Y-%m-%d').date() if appointment_date_str else datetime.today().date()
            except (ValueError, TypeError):
                appointment_date_for_rerender = datetime.today().date()

            # Recalculate booked slots for the date that was being submitted
            booked_slots_for_rerender = list(Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date_for_rerender,
                appointment_time__isnull=False
            ).exclude(status='Cancelled').values_list('appointment_time', flat=True))

            time_slots = _generate_time_slots(doctor.from_time, doctor.to_time)
            context = {
                'doctor': doctor, 'time_slots': time_slots,
                'booked_slots': booked_slots_for_rerender, 'appointment_date': appointment_date_for_rerender
            }
            return render(request, 'create_appointment.html', context)

        # Server-side validation to prevent booking an already taken slot
        try:
            appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, 'An invalid date was provided.')
            return redirect('home')

        # Re-fetch booked slots for the submitted date to prevent race conditions.
        booked_slots_for_post_date = list(Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time__isnull=False
        ).exclude(status='Cancelled').values_list('appointment_time', flat=True))

        selected_time_obj = datetime.strptime(selected_time_str, '%H:%M').time()
        if selected_time_obj in booked_slots_for_post_date:
            messages.error(request, 'This time slot was just booked by someone else. Please select a different time.')
            time_slots = _generate_time_slots(doctor.from_time, doctor.to_time)
            context = {'doctor': doctor, 'time_slots': time_slots, 'booked_slots': booked_slots_for_post_date, 'appointment_date': appointment_date}
            return render(request, 'create_appointment.html', context)

        rescheduling_id = request.session.get('rescheduling_appointment_id')

        with transaction.atomic():
            if rescheduling_id:
                try:
                    # This is a reschedule: update the existing appointment
                    appointment_to_update = Appointment.objects.get(pk=rescheduling_id, booked_by=request.user)
                    
                    appointment_to_update.appointment_date = appointment_date
                    appointment_to_update.appointment_time = selected_time_obj
                    # Reset status to 'Pending' so doctor must re-confirm the new time
                    appointment_to_update.status = 'Pending'
                    appointment_to_update.save(update_fields=['appointment_date', 'appointment_time', 'status'])
                    
                    # Send reschedule confirmation email asynchronously
                    send_reschedule_email_async(appointment_to_update.id, request.user.id)
                    messages.success(request, f'Your appointment with {doctor.name} has been successfully rescheduled.')

                except Appointment.DoesNotExist:
                    messages.error(request, 'The appointment you were trying to reschedule could not be found.')
                    # Clean up session just in case and redirect
                    if 'rescheduling_appointment_id' in request.session:
                        del request.session['rescheduling_appointment_id']
                    return redirect('patient_appointments')
            else:
                # This is a new booking: create a new appointment
                new_appointment = Appointment.objects.create(
                    doctor=doctor,
                    patient_name=patient_details['patient_name'],
                    patient_age=patient_details['age'],
                    patient_mobile=patient_details['mobile'],
                    booked_by=request.user,
                    disease=request.session.get('searched_disease', 'Not specified'),
                    appointment_time=selected_time_obj,
                    appointment_date=appointment_date,
                )
                
                # Send confirmation email asynchronously without blocking the user's request.
                send_confirmation_email_async(new_appointment.id, request.user.id)
                messages.success(request, f'Your appointment request with {doctor.name} has been successfully submitted.')

        # Clean up the session data after booking/rescheduling
        for key in ['patient_details', 'searched_disease', 'searched_location', 'rescheduling_appointment_id']:
            if key in request.session:
                del request.session[key]

        # Redirect based on whether it was a reschedule or a new booking
        if rescheduling_id:
            return redirect('patient_appointments')
        else:
            return render(request, 'book.html')

    # Handle GET request
    else:
        time_slots = _generate_time_slots(doctor.from_time, doctor.to_time)
        context = {
            'doctor': doctor,
            'time_slots': time_slots,
            'booked_slots': booked_slots,
            'appointment_date': appointment_date,
        }
        return render(request, 'create_appointment.html', context)

@login_required
@group_required('Doctors')
def doctor_appointment_list(request):
    """Displays a filterable list of all appointments for a doctor."""
    try:
        doctor = request.user.doctor_profile

        # Check if any filter parameters are present and have a non-empty value.
        filter_fields = ['patient_name', 'disease', 'appointment_date', 'status']
        is_filtered = any(request.GET.get(field) for field in filter_fields)

        if is_filtered:
            # If filters are applied, search through all appointments, showing the most recent first.
            base_queryset = Appointment.objects.filter(doctor=doctor).order_by('-appointment_date', '-appointment_time')
        else:
            # If no filters are applied, default to showing today's and future appointments, upcoming first.
            today = datetime.today().date()
            base_queryset = Appointment.objects.filter(
                doctor=doctor,
                appointment_date__gte=today
            ).order_by('appointment_date', 'appointment_time')

        # Apply the filter using data from the request's GET parameters
        appointment_filter = AppointmentFilter(request.GET, queryset=base_queryset)

        context = {
            'filter': appointment_filter,
        }
        return render(request, 'doctor_appointment_list.html', context)
    except Doctor.DoesNotExist:
        messages.error(request, "Your doctor profile could not be found.")
        return redirect('home')

@login_required
@group_required('Patients')
def book_appointment(request):
    if request.method == 'POST':
        # Store patient details in the session to carry them to the next step
        request.session['patient_details'] = {
            'patient_name': request.POST.get('patient_name'),
            'age': request.POST.get('age'),
            'mobile': request.POST.get('mobile'),
        }

        # Get filtering criteria for finding doctors and build query string
        disease = request.POST.get('disease', '')
        location = request.POST.get('location', '')
        # Store search criteria in session for the final booking step
        request.session['searched_disease'] = disease
        request.session['searched_location'] = location
        query_string = urlencode({'disease': disease, 'location': location})
        
        # Redirect to the doctor details page with search criteria
        return redirect(f"{reverse('doctor_details')}?{query_string}")

    # For GET requests, clear any previous patient details from the session.
    # This ensures a fresh start for each booking attempt.
    if 'patient_details' in request.session:
        del request.session['patient_details']

    return render(request, 'book_appointment.html')

@login_required
@group_required('Doctors')
def update_appointment_status(request, appointment_id, status):
    """
    Updates the status of an appointment to 'Confirmed' or 'Cancelled'.
    Ensures the appointment belongs to the logged-in doctor.
    """
    try:
        # Security check: ensure the appointment belongs to the logged-in doctor
        appointment = Appointment.objects.get(pk=appointment_id, doctor=request.user.doctor_profile)
    except (Appointment.DoesNotExist, Doctor.DoesNotExist):
        messages.error(request, "Appointment not found or you don't have permission to modify it.")
        return redirect('doctor_appointment_list')

    # Validate the status against the available choices in the model
    valid_statuses = [s[0] for s in Appointment.STATUS_CHOICES]
    if status not in valid_statuses:
        messages.error(request, "Invalid status update.")
        return redirect('doctor_appointment_list')

    appointment.status = status
    appointment.save()

    # Notify the patient when the doctor confirms or cancels the appointment.
    if status == 'Confirmed':
        send_doctor_confirmation_email_async(appointment.id, appointment.booked_by.id)
    elif status == 'Cancelled':
        send_appointment_cancellation_email_async(appointment.id, appointment.booked_by.id)

    messages.success(request, f"The appointment has been successfully marked as {status.lower()}.")
    return redirect('doctor_appointment_list')

@login_required
@group_required('Patients')
def patient_appointments(request):
    # Determine active tab from GET parameter, default to 'appointments'
    active_tab = request.GET.get('tab', 'appointments')

    # Base querysets for the logged-in user
    appointment_qs = Appointment.objects.filter(
        booked_by=request.user
    ).order_by('-appointment_date', '-appointment_time')

    lab_test_qs = LabTest.objects.filter(
        booked_by=request.user
    ).order_by('-created_at')

    # Initialize filters with querysets
    appointment_filter = PatientAppointmentFilter(request.GET, queryset=appointment_qs, prefix='appt')
    lab_test_filter = LabTestFilter(request.GET, queryset=lab_test_qs, prefix='lab')

    context = {
        'appointment_filter': appointment_filter,
        'lab_test_filter': lab_test_filter,
        'active_tab': active_tab,
    }
    return render(request, 'patient_appointments.html', context)

@login_required
@group_required('Patients')
def reschedule_appointment(request, appointment_id):
    try:
        # Security check: ensure the appointment belongs to the logged-in patient
        appointment = Appointment.objects.get(pk=appointment_id, booked_by=request.user)
    except Appointment.DoesNotExist:
        messages.error(request, "Appointment not found or you don't have permission to modify it.")
        return redirect('patient_appointments')

    # Patients should only be able to reschedule appointments that are pending or confirmed
    if appointment.status not in ['Pending', 'Confirmed']:
        messages.error(request, f"You cannot reschedule an appointment with '{appointment.status}' status.")
        return redirect('patient_appointments')

    # Store patient details from the existing appointment into the session
    request.session['patient_details'] = {
        'patient_name': appointment.patient_name,
        'age': appointment.patient_age,
        'mobile': appointment.patient_mobile,
    }
    request.session['searched_disease'] = appointment.disease
    request.session['rescheduling_appointment_id'] = appointment.id

    messages.info(request, f"Please select a new date and time to reschedule your appointment with {appointment.doctor.name}.")
    return redirect('create_appointment', doctor_id=appointment.doctor.id)

@login_required
@group_required('Patients')
def cancel_appointment_patient(request, appointment_id):
    try:
        appointment = Appointment.objects.get(pk=appointment_id, booked_by=request.user)
    except Appointment.DoesNotExist:
        messages.error(request, "Appointment not found or you don't have permission to modify it.")
        return redirect('patient_appointments')

    appointment.status = 'Cancelled'
    appointment.save(update_fields=['status'])

    # Send cancellation confirmation email
    send_appointment_cancellation_email_async(appointment.id, request.user.id)

    messages.success(request, "Your appointment has been successfully cancelled.")
    return redirect('patient_appointments')

@login_required
@group_required('Patients')
def cancel_lab_test(request, test_id):
    try:
        lab_test = LabTest.objects.get(pk=test_id, booked_by=request.user)
    except LabTest.DoesNotExist:
        messages.error(request, "Lab test request not found or you don't have permission to modify it.")
        return redirect('patient_appointments')

    # Allow cancellation only for pending or scheduled tests
    if lab_test.status not in ['Pending', 'Scheduled']:
        messages.error(request, f"You cannot cancel a lab test with '{lab_test.status}' status.")
        return redirect('patient_appointments')

    lab_test.status = 'Cancelled'
    lab_test.save(update_fields=['status'])

    # Send cancellation confirmation email
    send_lab_test_cancellation_email_async(lab_test.id, request.user.id)

    messages.success(request, "Your lab test request has been successfully cancelled.")
    return redirect(f"{reverse('patient_appointments')}?tab=lab-tests")


# API views for Appointment Booking
@login_required
@group_required('Patients')
def get_locations(request):
    term = request.GET.get('term', '').strip().lower()
    # Using distinct locations from the Doctor model
    locations_query = Doctor.objects.values_list('location', flat=True).distinct()
    
    if term:
        locations = [loc for loc in locations_query if term in loc.lower()]
    else:
        locations = list(locations_query)
    
    results = [{'id': loc, 'text': loc} for loc in locations]
    return JsonResponse({'results': results})

@login_required
@group_required('Patients')
def search_diseases(request):
    term = request.GET.get('term', '').strip().lower()
    # In a real app, this would come from a Disease model
    diseases = [
        "Fever", "Cold", "Cough", "Headache", "Stomach Pain", 
        "Diabetes", "Hypertension", "Heart Problem", "Skin Rash", "Allergy", "Other"
    ]
    
    if term:
        results = [{'id': d, 'text': d} for d in diseases if term in d.lower()]
    else:
        results = [{'id': d, 'text': d} for d in diseases]
        
    return JsonResponse({'results': results})

# API views for Lab Test Booking
@login_required
@group_required('Patients')
def get_lab_locations(request):
    term = request.GET.get('term', '').strip().lower()
    locations = ["Aurangabad", "Beed", "Latur", "Osmanabad", "Solapur"]
    
    if term:
        results = [{'id': loc, 'text': loc} for loc in locations if term in loc.lower()]
    else:
        results = [{'id': loc, 'text': loc} for loc in locations]
        
    return JsonResponse({'results': results})

@login_required
@group_required('Patients')
def search_lab_tests(request):
    term = request.GET.get('term', '').strip().lower()
    tests = ["Blood Test", "Urine Test", "RTPCR Test", "HIV Test", "DNA Test"]
    
    if term:
        results = [{'id': test, 'text': test} for test in tests if term in test.lower()]
    else:
        results = [{'id': test, 'text': test} for test in tests]
        
    return JsonResponse({'results': results})