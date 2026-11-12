from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Department, Doctor, Patient, Appointment, GuestAppointment

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email")

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("username", "email", "is_active", "is_staff")

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ["username", "email", "role", "is_staff", "is_active"]

    fieldsets = (
        (None, {"fields": ("username", "email", "password", "role")}),  # added role here
        ("Permissions", {"fields": ("is_staff", "is_superuser", "is_active", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2", "role", "is_staff", "is_active"),  # added role here
        }),
    )


class DoctorAdmin(admin.ModelAdmin):
    list_display = ("name", "specialization", "department", "email", "is_featured")
    list_filter = ("department", "is_featured")
    search_fields = ("name", "specialization", "email")


class PatientAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "age", "gender")
    search_fields = ("name", "email", "phone")


class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "appointment_datetime", "status")
    list_filter = ("status", "doctor__department")
    search_fields = ("patient__name", "doctor__name")


class GuestAppointmentAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "department", "doctor", "appointment_datetime", "status")
    list_filter = ("status", "department")
    search_fields = ("name", "email", "phone")


# Register
admin.site.register(User, CustomUserAdmin)
admin.site.register(Department)
admin.site.register(Patient, PatientAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(GuestAppointment, GuestAppointmentAdmin)
admin.site.register(Doctor, DoctorAdmin)
