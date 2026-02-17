from django.urls import path
from django.shortcuts import redirect
from . import views
from accounts import views as account_views

urlpatterns= [
    path('',views.home,name='home'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('home/', lambda request: redirect('home', permanent=True)),
    path('about/',views.about,name='about'),
    path('book-appointment/', views.book_appointment, name='book_appointment'),
    path('doctor-details/', views.doctor_details, name='doctor_details'),
    path('create-appointment/<int:doctor_id>/', views.create_appointment, name='create_appointment'),
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/appointments/', views.doctor_appointment_list, name='doctor_appointment_list'),
    path('my-appointments/', views.patient_appointments, name='patient_appointments'),
    path('my-appointments/<int:appointment_id>/cancel/', views.cancel_appointment_patient, name='cancel_appointment_patient'),
    path('my-appointments/<int:appointment_id>/reschedule/', views.reschedule_appointment, name='reschedule_appointment'),
    path('my-lab-tests/<int:test_id>/cancel/', views.cancel_lab_test, name='cancel_lab_test'),
    path('admin/impersonate/<int:user_id>/', account_views.impersonate_user, name='impersonate_user'),
    path('admin/stop-impersonating/', account_views.stop_impersonation, name='stop_impersonation'),
    path('appointment/<int:appointment_id>/update/<str:status>/', views.update_appointment_status, name='update_appointment_status'),
    path('lab-test/', views.lab_test, name='lab_test'),
    # API URLs
    path('api/locations/', views.get_locations, name='api_get_locations'),
    path('api/search-diseases/', views.search_diseases, name='api_search_diseases'),
    path('api/lab-locations/', views.get_lab_locations, name='api_get_lab_locations'),
    path('api/search-lab-tests/', views.search_lab_tests, name='api_search_lab_tests'),
]