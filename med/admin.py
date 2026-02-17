from django.contrib import admin
from .models import Doctor, Appointment, LabTest, EmailLog
# Register your models here.

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    """Custom admin view for the Doctor model."""
    list_display = ('name', 'expert', 'location', 'rating', 'user')
    search_fields = ('name', 'expert', 'location')
    list_filter = ('location', 'expert', 'gender')
    # Use raw_id_fields for better performance with thousands of users
    raw_id_fields = ('user',)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Custom admin view for the Appointment model."""
    list_display = ('patient_name', 'doctor', 'appointment_date', 'appointment_time', 'status', 'booked_by', 'created_at')
    list_filter = ('status', 'appointment_date', 'doctor', 'created_at')
    search_fields = ('patient_name', 'doctor__name', 'disease')
    date_hierarchy = 'appointment_date'
    ordering = ('-appointment_date', '-appointment_time')
    raw_id_fields = ('doctor', 'booked_by')

@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    """Custom admin view for the LabTest model."""
    list_display = ('test_type', 'location', 'booked_by', 'status', 'created_at')
    list_filter = ('status', 'location', 'test_type', 'created_at')
    search_fields = ('test_type', 'location', 'booked_by__username')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    raw_id_fields = ('booked_by',)

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    """Custom admin view for the EmailLog model."""
    list_display = ('recipient', 'subject', 'status', 'sent_at')
    list_filter = ('status', 'sent_at')
    search_fields = ('recipient', 'subject')
    readonly_fields = ('recipient', 'subject', 'body', 'status', 'sent_at', 'error_message')