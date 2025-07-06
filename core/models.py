from django.db import models
from django.contrib.auth.models import User



class Department(models.Model):
    name = models.CharField(max_length = 100)
    description = models.TextField(blank = True)

    def __str__(self):
        return self.name
    

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,null=True, blank=True)
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    available_days = models.CharField(max_length=100)
    available_time = models.CharField(max_length=50)

    def __str__(self):
        return f"Dr. {self.name} ({self.department.name})"

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,null=True, blank=True)
    name = models.CharField(max_length=100)
    age = models.PositiveBigIntegerField()
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')])
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()

    def __str__(self):
        return self.name
    
class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete = models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    description = models.TextField(blank = True)
    status = models.CharField(max_length = 20, choices = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Cancelled', 'Cancelled'),
    ], default = 'Pending')

    def __str__(self):
        return f"{self.patient.name} with Dr. {self.doctor.name } on \
            {self.appointment_date}"
    
