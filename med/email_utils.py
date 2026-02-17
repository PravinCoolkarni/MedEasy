import threading
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Appointment, User, EmailLog, LabTest

def send_confirmation_email_async(appointment_id, user_id):
    """
    Sends the appointment confirmation email in a background thread to avoid
    blocking the user's request.
    """
    def send_email():
        """The actual email sending logic."""
        try:
            # Fetch fresh objects from the DB for this thread
            appointment = Appointment.objects.select_related('doctor', 'booked_by').get(pk=appointment_id)
            user = User.objects.get(pk=user_id)
            doctor = appointment.doctor
        except (Appointment.DoesNotExist, User.DoesNotExist):
            # Log if the core objects are gone, which is unlikely but possible
            EmailLog.objects.create(
                recipient="unknown", subject="Appointment Confirmation Failed",
                body=f"Could not find Appointment or User for IDs {appointment_id}, {user_id}",
                status='Failed', error_message="Object Does Not Exist"
            )
            return

        email_subject = f"Your Appointment Request with Dr. {doctor.name}"
        try:
            email_body_html = render_to_string('emails/appointment_confirmation.html', {
                'appointment': appointment,
                'doctor': doctor,
                'user': user,
            })
            send_mail(
                subject=email_subject, message='', from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email], html_message=email_body_html, fail_silently=False,
            )
            EmailLog.objects.create(recipient=user.email, subject=email_subject, body=email_body_html, status='Sent')
        except Exception as e:
            # Log any exception that occurs during email rendering or sending
            EmailLog.objects.create(
                recipient=user.email, subject=email_subject,
                body=f"Failed to render or send email. Error: {e}", status='Failed', error_message=str(e)
            )

    # Start the email sending process in a new thread
    email_thread = threading.Thread(target=send_email)
    email_thread.start()

def send_reschedule_email_async(appointment_id, user_id):
    """
    Sends the appointment reschedule confirmation email in a background thread.
    """
    def send_email():
        """The actual email sending logic."""
        try:
            appointment = Appointment.objects.select_related('doctor', 'booked_by').get(pk=appointment_id)
            user = User.objects.get(pk=user_id)
            doctor = appointment.doctor
        except (Appointment.DoesNotExist, User.DoesNotExist):
            EmailLog.objects.create(
                recipient="unknown", subject="Reschedule Confirmation Failed",
                body=f"Could not find Appointment or User for IDs {appointment_id}, {user_id}",
                status='Failed', error_message="Object Does Not Exist"
            )
            return

        email_subject = f"Your Appointment with Dr. {doctor.name} has been Rescheduled"
        try:
            email_body_html = render_to_string('emails/reschedule_confirmation.html', {
                'appointment': appointment, 'doctor': doctor, 'user': user,
            })
            send_mail(
                subject=email_subject, message='', from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email], html_message=email_body_html, fail_silently=False,
            )
            EmailLog.objects.create(recipient=user.email, subject=email_subject, body=email_body_html, status='Sent')
        except Exception as e:
            EmailLog.objects.create(
                recipient=user.email, subject=email_subject,
                body=f"Failed to render or send reschedule email. Error: {e}", status='Failed', error_message=str(e)
            )

    email_thread = threading.Thread(target=send_email)
    email_thread.start()

def send_lab_test_email_async(lab_test_id, user_id):
    """
    Sends the lab test confirmation email in a background thread.
    """
    def send_email():
        """The actual email sending logic."""
        try:
            lab_test = LabTest.objects.get(pk=lab_test_id)
            user = User.objects.get(pk=user_id)
        except (LabTest.DoesNotExist, User.DoesNotExist):
            EmailLog.objects.create(
                recipient="unknown", subject="Lab Test Confirmation Failed",
                body=f"Could not find LabTest or User for IDs {lab_test_id}, {user_id}",
                status='Failed', error_message="Object Does Not Exist"
            )
            return

        email_subject = f"Your Lab Test Request for a {lab_test.test_type}"
        try:
            email_body_html = render_to_string('emails/lab_test_confirmation.html', {
                'lab_test': lab_test, 'user': user,
            })
            send_mail(
                subject=email_subject, message='', from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email], html_message=email_body_html, fail_silently=False,
            )
            EmailLog.objects.create(recipient=user.email, subject=email_subject, body=email_body_html, status='Sent')
        except Exception as e:
            EmailLog.objects.create(
                recipient=user.email, subject=email_subject,
                body=f"Failed to render or send lab test email. Error: {e}", status='Failed', error_message=str(e)
            )

    email_thread = threading.Thread(target=send_email)
    email_thread.start()

def send_appointment_cancellation_email_async(appointment_id, user_id):
    """
    Sends the appointment cancellation confirmation email in a background thread.
    """
    def send_email():
        """The actual email sending logic."""
        try:
            appointment = Appointment.objects.select_related('doctor', 'booked_by').get(pk=appointment_id)
            user = User.objects.get(pk=user_id)
            doctor = appointment.doctor
        except (Appointment.DoesNotExist, User.DoesNotExist):
            EmailLog.objects.create(
                recipient="unknown", subject="Cancellation Confirmation Failed",
                body=f"Could not find Appointment or User for IDs {appointment_id}, {user_id}",
                status='Failed', error_message="Object Does Not Exist"
            )
            return

        email_subject = f"Your Appointment with Dr. {doctor.name} has been Cancelled"
        try:
            email_body_html = render_to_string('emails/appointment_cancellation.html', {
                'appointment': appointment, 'doctor': doctor, 'user': user,
            })
            send_mail(
                subject=email_subject, message='', from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email], html_message=email_body_html, fail_silently=False,
            )
            EmailLog.objects.create(recipient=user.email, subject=email_subject, body=email_body_html, status='Sent')
        except Exception as e:
            EmailLog.objects.create(
                recipient=user.email, subject=email_subject,
                body=f"Failed to render or send cancellation email. Error: {e}", status='Failed', error_message=str(e)
            )

    email_thread = threading.Thread(target=send_email)
    email_thread.start()

def send_lab_test_cancellation_email_async(lab_test_id, user_id):
    """
    Sends the lab test cancellation confirmation email in a background thread.
    """
    def send_email():
        """The actual email sending logic."""
        try:
            lab_test = LabTest.objects.get(pk=lab_test_id)
            user = User.objects.get(pk=user_id)
        except (LabTest.DoesNotExist, User.DoesNotExist):
            EmailLog.objects.create(
                recipient="unknown", subject="Lab Test Cancellation Failed",
                body=f"Could not find LabTest or User for IDs {lab_test_id}, {user_id}",
                status='Failed', error_message="Object Does Not Exist"
            )
            return

        email_subject = f"Your Lab Test Request for a {lab_test.test_type} has been Cancelled"
        try:
            email_body_html = render_to_string('emails/lab_test_cancellation.html', {
                'lab_test': lab_test, 'user': user,
            })
            send_mail(
                subject=email_subject, message='', from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email], html_message=email_body_html, fail_silently=False,
            )
            EmailLog.objects.create(recipient=user.email, subject=email_subject, body=email_body_html, status='Sent')
        except Exception as e:
            EmailLog.objects.create(
                recipient=user.email, subject=email_subject,
                body=f"Failed to render or send lab test cancellation email. Error: {e}", status='Failed', error_message=str(e)
            )

    email_thread = threading.Thread(target=send_email)
    email_thread.start()

def send_doctor_confirmation_email_async(appointment_id, user_id):
    """
    Sends an email to the patient when a doctor confirms their appointment.
    """
    def send_email():
        """The actual email sending logic."""
        try:
            appointment = Appointment.objects.select_related('doctor', 'booked_by').get(pk=appointment_id)
            user = User.objects.get(pk=user_id)
            doctor = appointment.doctor
        except (Appointment.DoesNotExist, User.DoesNotExist):
            EmailLog.objects.create(
                recipient="unknown", subject="Doctor Confirmation Email Failed",
                body=f"Could not find Appointment or User for IDs {appointment_id}, {user_id}",
                status='Failed', error_message="Object Does Not Exist"
            )
            return

        email_subject = f"Your Appointment with Dr. {doctor.name} is Confirmed!"
        try:
            email_body_html = render_to_string('emails/doctor_confirmation.html', {
                'appointment': appointment, 'doctor': doctor, 'user': user,
            })
            send_mail(
                subject=email_subject, message='', from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email], html_message=email_body_html, fail_silently=False,
            )
            EmailLog.objects.create(recipient=user.email, subject=email_subject, body=email_body_html, status='Sent')
        except Exception as e:
            EmailLog.objects.create(
                recipient=user.email, subject=email_subject,
                body=f"Failed to render or send doctor confirmation email. Error: {e}", status='Failed', error_message=str(e)
            )

    email_thread = threading.Thread(target=send_email)
    email_thread.start()