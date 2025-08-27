from django.shortcuts import render,redirect
from .models import Appointment, Doctor, Patient, Department
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
from django.contrib import messages
from django.http import HttpResponseForbidden

from .forms import DoctorProfileForm

from django.contrib.auth import get_user_model

User = get_user_model()
def custom_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        role = request.POST['role']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.role == role:  # ✅ Match role
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, "Role mismatch! Please login with correct role.")
        else:
            messages.error(request, "Invalid credentials.")
    return render(request, 'login.html')




def dashboard_redirect(request):
    if hasattr(request.user, 'patient'):
        return redirect('patient_dashboard')
    elif hasattr(request.user, 'doctor'):
        return redirect('doctor_dashboard')
    else:
        return redirect('home')


def doctors_list(request):
    doctors = Doctor.objects.all()
    return render(request, 'core/doctors_list.html', {'doctors': doctors})

def homepage(request):
    departments = Department.objects.all()[:6]  # Limit to 6 for neatness
    doctors = Doctor.objects.filter(is_featured=True)[:4]  # You can add a boolean field for featured doctors
    return render(request, 'core/home.html', {
        'departments': departments,
        'doctors': doctors
    })
def patient_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if hasattr(user, 'patient'):
                login(request, user)
                return redirect('patient_dashboard')
            else:
                messages.error(request, "This login is for patients only.")
                return redirect('patient_login')
    else:
        form = AuthenticationForm()
    return render(request, 'core/patient_login.html', {'form': form})


def departments(request):
    return render(request, 'core/departments_list.html')

def doctors(request):
    return render(request, 'core/doctors.html')
# def departments_detail(request, department_id):
#     department = get_object_or_404(Department, pk=department_id)
#     return render(request, "core/departments_detail.html", {'department': department})


def departments_list(request):
    departments = Department.objects.all()
    return render(request, 'core/departments_list.html', {'departments': departments})

def departments_detail(request, pk):
    department = get_object_or_404(Department, pk=pk)
    return render(request, 'core/departments_detail.html', {'department': department})

def doctor_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if hasattr(user, 'doctor'):
                login(request, user)
                return redirect('doctor_dashboard')
            else:
                messages.error(request, "This login is for doctors only.")
                return redirect('doctor_login')
    else:
        form = AuthenticationForm()
    return render(request, 'core/doctor_login.html', {'form': form})



def home(request):
    return render(request, 'core/home.html')

    # core/templates/core/home.html

@login_required
def book_appointment(request):
    # 1️⃣ Decide which patient to use
    if hasattr(request.user, 'patient'):
        # Logged-in user is a patient
        patient = request.user.patient
    else:
        # Logged-in user is NOT a patient — must select a patient in form
        if request.method == 'POST':
            patient_id = request.POST.get('patient_id')
            try:
                patient = Patient.objects.get(id=patient_id)
            except Patient.DoesNotExist:
                messages.error(request, "Invalid patient selected.")
                return redirect('home')
        else:
            patient = None  # No patient yet for GET requests

    # 2️⃣ Process form
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid() and patient:
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
            return redirect('patient_dashboard' if hasattr(request.user, 'patient') else 'home')
    else:
        form = AppointmentForm()

    # 3️⃣ Pass patient info for template rendering
    return render(request, 'core/book_appointment.html', {
        'form': form,
        'is_patient': hasattr(request.user, 'patient')
    })


def register(request):
    if request.method == 'POST':
        form = PatientSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            age = form.cleaned_data.get('age')
            gender = form.cleaned_data.get('gender')
            phone = form.cleaned_data.get('phone')
            address = form.cleaned_data.get('address')
            role = form.POST.get("role")


            Patient.objects.create(
                user=user,
                name=user.username,
                email=user.email,
                age=age,
                gender=gender,
                phone=phone,
                address=address,
                role = role
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
    
    if not hasattr(request.user, 'patient'):
        return HttpResponseForbidden("Access denied. You are not a patient.")
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
