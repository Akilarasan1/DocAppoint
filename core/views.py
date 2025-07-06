from django.shortcuts import render
from .models import Appointment, Doctor, Patient
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import AppointmentForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import redirect,get_object_or_404
from .forms import PatientSignUpForm
from .models import Patient
from django.contrib.auth.decorators import login_required



def home(request):
    return render(request, 'core/home.html')

    # core/templates/core/home.html


@login_required
def book_appointment(request):
    patient = Patient.objects.get(user=request.user)
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = patient  # set logged-in patient automatically
            appointment.save()
            return redirect('patient_dashboard')
    else:
        form = AppointmentForm()

    return render(request, 'core/book_appointment.html', {'form': form})

# @login_required
# def book_appointment(request):
#     patient = get_object_or_404(Patient, user=request.user)

#     if request.method == 'POST':
#         form = AppointmentForm(request.POST)
#         if form.is_valid():
#             appointment = form.save(commit=False)
#             appointment.patient = patient
#             appointment.save()
#             return redirect('patient_dashboard')
#     else:
#         form = AppointmentForm()

#     return render(request, 'core/book_appointment.html', {'form': form})



def register(request):
    if request.method == 'POST':
        form = PatientSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            Patient.objects.create(
                user=user,
                name=user.username,
                email=user.email
            )
            login(request, user)
            return redirect('home')
    else:
        form = PatientSignUpForm()
    return render(request, 'core/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            try:
                if hasattr(user, 'patient'):
                    return redirect('patient_dashboard')
                elif hasattr(user, 'doctor'):
                    return redirect('doctor_dashboard')
                else:
                    return redirect('home')
            except ObjectDoesNotExist:
                return redirect('home')

    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('home')


@login_required
def patient_dashboard(request):
    patient = Patient.objects.get(user=request.user)
    appointments = Appointment.objects.filter(patient=patient)
    return render(request, 'core/patient_dashboard.html', {
        'patient': patient,
        'appointments': appointments
    })

@login_required
def doctor_dashboard(request):
    doctor = Doctor.objects.get(user=request.user)
    appointments = Appointment.objects.filter(doctor=doctor)
    return render(request, 'core/doctor_dashboard.html', {
        'doctor': doctor,
        'appointments': appointments
    })
