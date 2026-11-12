from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.templatetags.static import static
from datetime import time


class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='images/', default='default_department.png')

    def __str__(self):
        return self.name

    @property
    def image_url(self):
        # The default image ships with the app's static files, not with uploaded media
        if not self.image or self.image.name == 'default_department.png':
            return static('images/default_department.png')
        return self.image.url

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
    )
    # Empty for admin/staff accounts
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, blank=True, default='')

class Doctor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    specialization = models.CharField(max_length=100)
    is_featured = models.BooleanField(default=False)

    # Replace CharFields with proper day/time fields
    DAYS_OF_WEEK = [
        ('Mon', 'Monday'),
        ('Tue', 'Tuesday'),
        ('Wed', 'Wednesday'),
        ('Thu', 'Thursday'),
        ('Fri', 'Friday'),
        ('Sat', 'Saturday'),
        ('Sun', 'Sunday'),
    ]
    available_days = models.JSONField(default=list)  # can store multiple days, e.g. ["Mon","Wed","Fri"]

    start_time = models.TimeField(default=time(9, 0))
    end_time = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"Dr. {self.name} ({self.department.name if self.department else 'No Department'})"

    @property
    def initials(self):
        return "".join(part[0] for part in self.name.split()[:2]).upper() or "DR"

    @property
    def available_day_codes(self):
        """Valid day codes from available_days; old rows may hold a number or a plain string."""
        days = self.available_days
        if isinstance(days, str):
            days = [d.strip() for d in days.split(',')]
        if not isinstance(days, (list, tuple)):
            return []
        valid = dict(self.DAYS_OF_WEEK)
        return [d for d in days if d in valid]

    def get_available_days_display(self):
        labels = dict(self.DAYS_OF_WEEK)
        return ", ".join(labels[day] for day in self.available_day_codes) or "Every day"





class Patient(models.Model):
    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female')]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=100, blank=True)
    age = models.PositiveBigIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()

    def __str__(self):
        return self.name
        
    
class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    patient = models.ForeignKey("Patient", on_delete=models.CASCADE)
    doctor = models.ForeignKey("Doctor", on_delete=models.CASCADE)
    appointment_datetime = models.DateTimeField(null=True, blank=True)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"{self.patient.name} with Dr. {self.doctor.name} on {self.appointment_datetime}"


class GuestAppointment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    symptoms = models.TextField()
    department = models.CharField(max_length=100)
    doctor = models.ForeignKey("Doctor", on_delete=models.SET_NULL, null=True, blank=True)
    appointment_datetime = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"Guest: {self.name} on {self.appointment_datetime.strftime('%Y-%m-%d %H:%M')}"

