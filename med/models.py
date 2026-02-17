from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import time, datetime, timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.utils import timezone

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='doctor_profile')
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]

    name = models.CharField(max_length=100)
    expert = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    gender= models.CharField(max_length=10, choices=GENDER_CHOICES, default='Male')
    rating= models.DecimalField(max_digits=2, decimal_places=1, validators=[MinValueValidator(0), MaxValueValidator(5)], default=Decimal('0.0'))
    description = models.TextField(help_text="A brief description or biography of the doctor.", default='No description provided.')
    from_time = models.TimeField(help_text="Available from time in 24hr format.", default=time(9, 0))
    to_time = models.TimeField(help_text="Available until time in 24hr format.", default=time(17, 0))

    def __str__(self):
        return self.name

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
    ]
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    patient_name = models.CharField(max_length=100)
    patient_age = models.PositiveIntegerField()
    patient_mobile = models.CharField(max_length=15)
    booked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='booked_appointments')
    disease = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    appointment_date = models.DateField(default=timezone.now)
    appointment_time = models.TimeField(default=time(0, 0))

    @property
    def appointment_end_time(self):
        if self.appointment_time:
            # Assuming a fixed 30-minute slot duration based on the booking page logic
            start_datetime = datetime.combine(datetime.min, self.appointment_time)
            end_datetime = start_datetime + timedelta(minutes=30)
            return end_datetime.time()
        return None

    def __str__(self):
        return f"Appointment for {self.patient_name} with {self.doctor.name}"

class LabTest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    test_type = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    booked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lab_tests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lab test for {self.booked_by.username} - {self.test_type}"

class EmailLog(models.Model):
    """Model to log all outgoing emails."""
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=[('Sent', 'Sent'), ('Failed', 'Failed')])
    sent_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(blank=True, null=True, help_text="Error message if sending failed.")

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"Email to {self.recipient} - {self.subject} [{self.status}]"