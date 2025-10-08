from django import forms
from .models import Appointment
from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.models import User
from .models import Doctor, Patient,CustomUser
from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Patient
from django import forms
from django import forms
from django.utils import timezone

User = get_user_model()

# core/forms.py
from .models import Appointment


from django import forms
from django.contrib.auth.models import User
from .models import Doctor, Department

class DoctorCreationForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    class Meta:
        model = Doctor
        fields = [
            'username',  'password',  'name',
            'email','phone','department','specialization','available_days','available_time','is_featured']

    def save(self, commit=True):
        # First create the User object
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        email = self.cleaned_data['email']

        user = User.objects.create_user(username=username, password=password, email=email)
        doctor = super().save(commit=False)
        doctor.user = user
        if commit:
            doctor.save()
        return doctor


class GuestAppointmentForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=True)
    symptoms = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Describe your symptoms...'}),
        label="Your Symptoms"
    )
    appointment_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )
    appointment_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        required=True
    )

    def clean(self):
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get("appointment_date")
        appointment_time = cleaned_data.get("appointment_time")

        if appointment_date and appointment_time:
            combined_dt = timezone.make_aware(
                timezone.datetime.combine(appointment_date, appointment_time)
            )
            if combined_dt < timezone.now():
                raise forms.ValidationError("Appointment time cannot be in the past.")
            cleaned_data["appointment_datetime"] = combined_dt
        return cleaned_data


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
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "doctor"
        if commit:
            user.save()
        return user       
            
            

class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialization', 'email', 'department')
    search_fields = ('name', 'specialization', 'email')


class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']  # only editable fields

# Form for Patient model (extra info)
class PatientExtraForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['name', 'age', 'gender', 'phone', 'address']