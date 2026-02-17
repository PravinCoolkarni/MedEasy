import django_filters
from django import forms
from django.contrib.auth.models import User, Group
from .models import Appointment, LabTest

class AppointmentFilter(django_filters.FilterSet):
    patient_name = django_filters.CharFilter(
        lookup_expr='icontains',
        label='',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Patient Name'})
    )
    disease = django_filters.CharFilter(
        lookup_expr='icontains',
        label='',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Symptom'})
    )
    appointment_date = django_filters.DateFilter(
        label='',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'text',  # Start as text to show the placeholder
            'placeholder': 'Date',
            'onfocus': "(this.type='date')",
            'onblur': "if(!this.value) this.type='text'"
        })
    )
    status = django_filters.ChoiceFilter(
        choices=Appointment.STATUS_CHOICES,
        label='',
        empty_label='Status',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Appointment
        fields = ['patient_name', 'disease', 'appointment_date', 'status']

class PatientAppointmentFilter(django_filters.FilterSet):
    doctor__name = django_filters.CharFilter(
        lookup_expr='icontains',
        label='',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Doctor Name'})
    )
    disease = django_filters.CharFilter(
        lookup_expr='icontains',
        label='',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Symptom'})
    )
    status = django_filters.ChoiceFilter(
        choices=Appointment.STATUS_CHOICES,
        label='',
        empty_label='All Statuses',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Appointment
        fields = ['doctor__name', 'disease', 'status']

class LabTestFilter(django_filters.FilterSet):
    test_type = django_filters.CharFilter(
        lookup_expr='icontains',
        label='',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Test Type'})
    )
    location = django_filters.CharFilter(
        lookup_expr='icontains',
        label='',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'})
    )
    status = django_filters.ChoiceFilter(
        choices=LabTest.STATUS_CHOICES,
        label='',
        empty_label='All Statuses',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = LabTest
        fields = ['test_type', 'location', 'status']

class UserFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(
        lookup_expr='icontains', 
        label="",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    email = django_filters.CharFilter(
        lookup_expr='icontains', 
        label="",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    groups = django_filters.ModelChoiceFilter(
        queryset=Group.objects.all(),
        label="",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="All Groups"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'groups']