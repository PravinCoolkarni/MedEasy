from django.core.management.base import BaseCommand
from django.utils import timezone
from med.models import Appointment
from datetime import datetime

class Command(BaseCommand):
    """
    A Django management command to automatically update the status of past appointments.
    This command finds all 'Confirmed' appointments where the appointment end time
    has passed and updates their status to 'Completed'.
    """
    help = 'Updates the status of past confirmed appointments to "Completed".'

    def handle(self, *args, **options):
        now = timezone.now()
        self.stdout.write(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Checking for appointments to mark as completed...")

        # Get all confirmed appointments on or before the current date to check them.
        appointments_to_check = Appointment.objects.filter(
            status='Confirmed',
            appointment_date__lte=now.date()
        )

        updated_count = 0
        for appointment in appointments_to_check:
            # Combine the appointment's date and its end time to get a full datetime object.
            appointment_end_datetime = timezone.make_aware(datetime.combine(appointment.appointment_date, appointment.appointment_end_time))
            if appointment_end_datetime < now:
                appointment.status = 'Completed'
                appointment.save(update_fields=['status'])
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} appointment(s) to "Completed".'))