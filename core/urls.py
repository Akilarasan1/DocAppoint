from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .views import DoctorPasswordChangeView
from django.urls import reverse_lazy


urlpatterns = [
    path('', views.homepage, name='home'),
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

    path("doctors/", views.doctors, name='doctors'),
    path('departments/', views.departments_list, name='departments_list'),
    path('departments/<int:pk>/', views.departments_detail, name='departments_detail'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),

    path("patient/profile/", views.patient_profile, name="patient_profile"),
    path("profile/", views.patient_profile, name="patient_profile"),
    path("change-password/", views.change_password, name="change_password"),



    path("doctor/change-password/", DoctorPasswordChangeView.as_view(), name="doctor_change_password"),
    
    # path("password_reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    # path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    # path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    # path("reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),

    path("password_reset/", 
         auth_views.PasswordResetView.as_view(
             template_name="core/doctor_password_reset.html", success_url=reverse_lazy("doctor_password_reset_done") 
         ), 
         name="doctor_password_reset"),

    path("doctor/password_reset/done/", 
         auth_views.PasswordResetDoneView.as_view(
             template_name="core/doctor_password_reset_done.html"
         ), 
         name="doctor_password_reset_done"),

    path("doctor/reset/<uidb64>/<token>/", 
         auth_views.PasswordResetConfirmView.as_view(
             template_name="core/doctor_password_reset_confirm.html"
         ), 
         name="doctor_password_reset_confirm"),

    path("doctor/reset/done/", 
         auth_views.PasswordResetCompleteView.as_view(
             template_name="core/doctor_password_reset_complete.html"
         ), 
         name="doctor_password_reset_complete"),
  


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
