from django.contrib import admin

from .models import Department, Doctor, Patient, Appointment, CustomUser

admin.site.register(Department)
admin.site.register(Doctor)
admin.site.register(Patient)
admin.site.register(Appointment)
admin.site.register(CustomUser)
