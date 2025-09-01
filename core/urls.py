from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .views import DoctorPasswordChangeView



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

    path("password_reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
