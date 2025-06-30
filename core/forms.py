from django import forms
from .models import Appointment
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'appointment_date', 'appointment_time', 'description']


class PatientSignUpForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
