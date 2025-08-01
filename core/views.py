from django.shortcuts import render
from .models import Appointment, Doctor, Patient
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import AppointmentForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from .forms import PatientSignUpForm
# from .models import Patient
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.contrib.admin.views.decorators import staff_member_required

from .forms import DoctorProfileForm

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
            appointment.patient = patient
            appointment.save()

            send_mail(
                'Appointment Request Received',
                f'Dear {patient.name},\n\nYour appointment request with Dr. {appointment.doctor.name} on {appointment.appointment_date} at {appointment.appointment_time} has been received and is pending approval.\n\nThank you!',
                'akshospital@gmail.com',
                [patient.email],
                fail_silently=False,
            )

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
            age = form.cleaned_data.get('age')
            gender = form.cleaned_data.get('gender')
            phone = form.cleaned_data.get('phone')
            address = form.cleaned_data.get('address')

            Patient.objects.create(
                user=user,
                name=user.username,
                email=user.email,
                age=age,
                gender=gender,
                phone=phone,
                address=address
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



@login_required
def approve_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.status = 'Approved'
    appointment.save()

    send_mail(
        'Appointment Approved',
        f'Dear {appointment.patient.name},\n\nYour appointment with Dr. {appointment.doctor.name} on {appointment.appointment_date} at {appointment.appointment_time} has been APPROVED.\n\nThank you!',
        'hospital@example.com',
        [appointment.patient.email],
        fail_silently=False,
    )

    return redirect('doctor_dashboard')

@login_required
def reject_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.status = 'Rejected'
    appointment.save()

    send_mail(
        'Appointment Rejected',
        f'Dear {appointment.patient.name},\n\nWe regret to inform you that your appointment with Dr. {appointment.doctor.name} on {appointment.appointment_date} at {appointment.appointment_time} has been REJECTED.\n\nPlease try booking another slot.\n\nThank you!',
        'hospital@example.com',
        [appointment.patient.email],
        fail_silently=False,
    )

    return redirect('doctor_dashboard')

@staff_member_required
def admin_dashboard(request):
    total_patients = Patient.objects.count()
    total_doctors = Patient.objects.count()
    total_appointment = Appointment.objects.count()
    approved = Appointment.objects.filter(status = "Approved").count()
    rejected = Appointment.objects.filter(status = "Rejected").count()
    pending = Appointment.objects.filter(status = "Pending").count()

    context = {
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "total_appointments": total_appointment,
        "approved": approved,
        "rejected": rejected,
        "pending":pending,
    }

    return render(request, "core/admin_dashboard.html", context)


@login_required
def doctor_profile(request):
    if not hasattr(request.user, 'doctor'):
        return redirect('login')  # Just in case

    doctor = request.user.doctor

    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            return redirect('doctor_profile')
    else:
        form = DoctorProfileForm(instance=doctor)

    return render(request, 'core/doctor_profile.html', {'form': form})

