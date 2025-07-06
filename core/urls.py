from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.patient_dashboard, name='patient_dashboard'),
    # ,path('book/', views.book_appointment, name='book_appointment'),
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),



]

