from django.urls import path
from . import views

urlpatterns= [
    path('new-account/', views.NewAccountView.as_view(), name='new_account'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout, name='logout'),
    path('book/', views.book, name='book'),
    path('api/check-username/', views.check_username, name='api_check_username'),
    path('api/check-email/', views.check_email, name='api_check_email'),
]