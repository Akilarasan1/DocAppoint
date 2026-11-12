from datetime import datetime

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm, UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone

from .models import Appointment, Department, Doctor, Patient

User = get_user_model()


class BootstrapFormMixin:
    """Adds Bootstrap 5 CSS classes to every widget so templates stay clean."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple, forms.RadioSelect)):
                css = 'form-check-input'
            elif isinstance(widget, forms.Select):
                css = 'form-select'
            else:
                css = 'form-control'
            widget.attrs['class'] = f"{widget.attrs.get('class', '')} {css}".strip()


class AppointmentSlotMixin(forms.Form):
    """Optional department + date/time inputs combined into one timezone-aware datetime in the future."""

    department = forms.ModelChoiceField(
        queryset=Department.objects.order_by('name'),
        required=False,
        empty_label="Not sure — match me by my symptoms",
    )
    appointment_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Preferred date")
    appointment_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), label="Preferred time")

    def clean(self):
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get("appointment_date")
        appointment_time = cleaned_data.get("appointment_time")

        if appointment_date and appointment_time:
            combined_dt = timezone.make_aware(datetime.combine(appointment_date, appointment_time))
            if combined_dt < timezone.now():
                raise forms.ValidationError("Appointment time cannot be in the past.")
            cleaned_data["appointment_datetime"] = combined_dt
        return cleaned_data


class DepartmentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description', 'image']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}


class DoctorCreationForm(BootstrapFormMixin, forms.ModelForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    available_days = forms.MultipleChoiceField(
        choices=Doctor.DAYS_OF_WEEK,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Doctor
        fields = [
            'username', 'password', 'name', 'email', 'phone',
            'department', 'specialization', 'available_days',
            'start_time', 'end_time', 'is_featured'
        ]
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_password(self):
        password = self.cleaned_data['password']
        validate_password(password)
        return password

    @transaction.atomic
    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            email=self.cleaned_data['email'],
            role='doctor',
        )
        doctor = super().save(commit=False)
        doctor.user = user
        doctor.available_days = self.cleaned_data['available_days']
        if commit:
            doctor.save()
        return doctor


class DoctorProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['name', 'specialization', 'email', 'phone']


class GuestAppointmentForm(BootstrapFormMixin, AppointmentSlotMixin):
    name = forms.CharField(max_length=100, label="Full name")
    email = forms.EmailField()
    phone = forms.CharField(max_length=15)
    symptoms = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'e.g. fever and cough for 3 days'}),
        label="Your symptoms",
        help_text="We use this to match you with the right department.",
    )

    field_order = ['name', 'email', 'phone', 'symptoms', 'department', 'appointment_date', 'appointment_time']


class AppointmentForm(BootstrapFormMixin, AppointmentSlotMixin, forms.ModelForm):
    """Booking form for a logged-in patient; the patient and doctor are set by the view."""

    class Meta:
        model = Appointment
        fields = ['description']
        labels = {'description': "Your symptoms"}
        help_texts = {'description': "We use this to match you with the right department."}
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'e.g. fever and cough for 3 days'}),
        }

    field_order = ['description', 'department', 'appointment_date', 'appointment_time']


class PatientSignUpForm(BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField()
    age = forms.IntegerField(min_value=0, max_value=130)
    gender = forms.ChoiceField(choices=Patient.GENDER_CHOICES)
    phone = forms.CharField(max_length=15)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'age', 'gender', 'phone', 'address']

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'patient'
        if commit:
            user.save()
            Patient.objects.create(
                user=user,
                name=user.username,
                email=user.email,
                age=self.cleaned_data['age'],
                gender=self.cleaned_data['gender'],
                phone=self.cleaned_data['phone'],
                address=self.cleaned_data['address'],
            )
        return user


# Form for the login account fields of a patient
class PatientProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']


# Form for Patient model (extra info)
class PatientExtraForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['name', 'age', 'gender', 'phone', 'address']
        widgets = {'address': forms.Textarea(attrs={'rows': 2})}


# Django's built-in password forms with Bootstrap styling
class StyledPasswordChangeForm(BootstrapFormMixin, PasswordChangeForm):
    pass


class StyledPasswordResetForm(BootstrapFormMixin, PasswordResetForm):
    pass


class StyledSetPasswordForm(BootstrapFormMixin, SetPasswordForm):
    pass
