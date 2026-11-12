from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from .forms import StyledPasswordResetForm, StyledSetPasswordForm


urlpatterns = [
    # Public pages
    path('', views.homepage, name='home'),
    path('departments/', views.departments_list, name='departments_list'),
    path('departments/<int:pk>/', views.departments_detail, name='departments_detail'),
    path('doctors/', views.doctors, name='doctors'),
    path('doctors/<int:pk>/', views.doctor_detail, name='doctor_detail'),

    # Booking
    path('book/', views.book_appointment, name='book_appointment'),
    path('book/success/', views.guest_success, name='guest_success'),

    # Auth
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('change-password/', views.change_password, name='change_password'),

    # Dashboards
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('patient/profile/', views.patient_profile, name='patient_profile'),
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/profile/', views.doctor_profile, name='doctor_profile'),
    path('doctor/change-password/', views.DoctorPasswordChangeView.as_view(), name='doctor_change_password'),
    path('doctor/appointments/<str:kind>/<int:pk>/<str:action>/', views.update_appointment_status,
         name='update_appointment_status'),

    # Hospital admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('add-doctor/', views.add_doctor, name='add_doctor'),
    path('create-department/', views.manage_department, name='create_department'),

    # Password reset (by email)
    path("password_reset/",
         auth_views.PasswordResetView.as_view(
             template_name="core/doctor_password_reset.html",
             form_class=StyledPasswordResetForm,
             email_template_name="core/password_reset_email.txt",
             subject_template_name="core/password_reset_subject.txt",
             success_url=reverse_lazy("doctor_password_reset_done"),
         ),
         name="doctor_password_reset"),

    path("doctor/password_reset/done/",
         auth_views.PasswordResetDoneView.as_view(
             template_name="core/doctor_password_reset_done.html"
         ),
         name="doctor_password_reset_done"),

    path("doctor/reset/<uidb64>/<token>/",
         auth_views.PasswordResetConfirmView.as_view(
             template_name="core/doctor_password_reset_confirm.html",
             form_class=StyledSetPasswordForm,
             success_url=reverse_lazy("doctor_password_reset_complete"),
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
