from django import forms
from .models import Appointment
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Doctor, Patient,CustomUser
from django.contrib import admin

class AppointmentForm(forms.ModelForm):
    patient = forms.CharField(label="Patient Name")

    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'appointment_datetime', 'description']
        widgets = {
            'appointment_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean_patient(self):
        patient_name = self.cleaned_data['patient']
        patient, created = Patient.objects.get_or_create(name=patient_name)
        return patient

        
# class PatientSignUpForm(UserCreationForm):
#     age = forms.IntegerField()
#     gender = forms.ChoiceField(choices=[('Male', 'Male'), ('Female', 'Female')])
#     phone = forms.CharField(max_length=15)
#     address = forms.CharField(widget=forms.Textarea)

#     class Meta:
#         model = User
#         fields = ['username', 'password1', 'password2', 'email', 'age', 'gender', 'phone', 'address']

class PatientSignUpForm(UserCreationForm):
    age = forms.IntegerField()
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')])
    phone = forms.CharField(max_length=15)
    address = forms.CharField(widget=forms.Textarea)

    class Meta(UserCreationForm.Meta):
        model = CustomUser   # your custom user model
        fields = ['username', 'password1', 'password2', 'email', 'age', 'gender', 'phone', 'address']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'patient'   
        if commit:
            user.save()
        return user



class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['name', 'specialization', 'email']

class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialization', 'email', 'department')
    search_fields = ('name', 'specialization', 'email')