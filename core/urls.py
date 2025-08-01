from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/approve/<int:appointment_id>/', views.approve_appointment, name='approve_appointment'),
    path('doctor/reject/<int:appointment_id>/', views.reject_appointment, name='reject_appointment'),
    path("admin-dashboard/", views.admin_dashboard,name = "admin_dashboard"),
    path('doctor/profile/', views.doctor_profile, name='doctor_profile'),
    ]


