import logging
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import PasswordChangeView
from django.core.mail import send_mail
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import (
    AppointmentForm, DepartmentForm, DoctorCreationForm, DoctorProfileForm,
    GuestAppointmentForm, PatientExtraForm, PatientProfileForm, PatientSignUpForm, StyledPasswordChangeForm,
)
from .models import Appointment, Department, Doctor, GuestAppointment, Patient

logger = logging.getLogger(__name__)


## ----------------## ACCESS HELPERS

def is_admin(user):
    return user.is_active and user.is_staff


admin_required = user_passes_test(is_admin, login_url='login')


def role_required(profile_attr):
    """Allow only logged-in users that have the given profile (``patient`` or ``doctor``)."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not hasattr(request.user, profile_attr):
                messages.error(request, f"That page is only available to {profile_attr}s.")
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


patient_required = role_required('patient')
doctor_required = role_required('doctor')


def safe_next_url(request, default):
    """Return ?next= only when it points at this site, to prevent open redirects."""
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return next_url
    return default


## ----------------## ADMIN

@admin_required
def manage_department(request):
    if request.method == "POST":
        form = DepartmentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Department created successfully!")
            return redirect(safe_next_url(request, 'admin_dashboard'))
    else:
        form = DepartmentForm()
    return render(request, 'core/create_department.html', {'form': form})


@admin_required
def add_doctor(request):
    if request.method == "POST":
        form = DoctorCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Doctor account created successfully!")
            return redirect("admin_dashboard")
        messages.error(request, "Please fix the errors below.")
    else:
        form = DoctorCreationForm()

    return render(request, "core/add_doctor.html", {"form": form})


@admin_required
def admin_dashboard(request):
    status_counts = Appointment.objects.aggregate(
        total=Count('id'),
        approved=Count('id', filter=Q(status='Approved')),
        rejected=Count('id', filter=Q(status='Rejected')),
        pending=Count('id', filter=Q(status='Pending')),
    )
    context = {
        "total_patients": Patient.objects.count(),
        "total_doctors": Doctor.objects.count(),
        "total_departments": Department.objects.count(),
        "total_appointments": status_counts['total'],
        "approved": status_counts['approved'],
        "rejected": status_counts['rejected'],
        "pending": status_counts['pending'],
        "guest_pending": GuestAppointment.objects.filter(status='Pending').count(),
        "recent_appointments": Appointment.objects.select_related('patient', 'doctor')
                                                  .order_by('-id')[:5],
        "recent_guest_appointments": GuestAppointment.objects.select_related('doctor').order_by('-id')[:5],
    }
    return render(request, "core/admin_dashboard.html", context)


## ----------------## AUTH

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = PatientSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account is ready.")
            return redirect('patient_dashboard')
    else:
        form = PatientSignUpForm()
    return render(request, 'core/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect(safe_next_url(request, 'dashboard'))
    else:
        form = AuthenticationForm(request)
    return render(request, 'core/login.html', {'form': form, 'next': request.GET.get('next', '')})


@require_POST
def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


def dashboard_redirect(request):
    """Send each user to the dashboard that matches their role."""
    if not request.user.is_authenticated:
        return redirect('login')
    if is_admin(request.user):
        return redirect('admin_dashboard')
    if hasattr(request.user, 'doctor'):
        return redirect('doctor_dashboard')
    if hasattr(request.user, 'patient'):
        return redirect('patient_dashboard')
    return redirect('home')


@login_required
def change_password(request):
    if request.method == "POST":
        form = StyledPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # keeps user logged in
            messages.success(request, "Your password has been changed.")
            return redirect("dashboard")
    else:
        form = StyledPasswordChangeForm(request.user)

    return render(request, "core/change_password.html", {"form": form})


class DoctorPasswordChangeView(PasswordChangeView):
    template_name = 'core/change_password.html'
    form_class = StyledPasswordChangeForm
    success_url = reverse_lazy('doctor_dashboard')

    def form_valid(self, form):
        messages.success(self.request, "Your password has been changed successfully.")
        return super().form_valid(form)


## ----------------## PUBLIC PAGES

def homepage(request):
    departments = Department.objects.all()[:6]
    doctors = Doctor.objects.filter(is_featured=True).select_related('department')[:4]
    return render(request, 'core/home.html', {
        'departments': departments,
        'doctors': doctors,
        'department_count': Department.objects.count(),
        'doctor_count': Doctor.objects.count(),
    })


def doctors(request):
    doctor_list = Doctor.objects.select_related('department').order_by('department__name', 'name')
    selected = request.GET.get('department', '')
    if selected.isdigit():
        doctor_list = doctor_list.filter(department_id=selected)
    return render(request, 'core/doctors.html', {
        'doctors': doctor_list,
        'departments': Department.objects.order_by('name'),
        'selected_department': selected,
    })


def doctor_detail(request, pk):
    doctor = get_object_or_404(Doctor.objects.select_related('department'), pk=pk)
    return render(request, 'core/doctor_detail.html', {'doctor': doctor})


def departments_list(request):
    departments = Department.objects.annotate(doctor_count=Count('doctor')).order_by('name')
    return render(request, 'core/departments_list.html', {'departments': departments})


def departments_detail(request, pk):
    department = get_object_or_404(Department, pk=pk)
    return render(request, 'core/departments_detail.html', {
        'department': department,
        'doctors': department.doctor_set.order_by('name'),
    })


## ----------------## BOOKING

SYMPTOM_DEPARTMENT_MAP = {
    "fever": "General Medicine",
    "cough": "General Medicine",
    "cold": "General Medicine",
    "headache": "General Medicine",
    "fracture": "Orthopedics",
    "back pain": "Orthopedics",
    "joint pain": "Orthopedics",
    "chest pain": "Cardiology",
    "palpitation": "Cardiology",
    "skin rash": "Dermatology",
    "itching": "Dermatology",
    "acne": "Dermatology",
}


def detect_department(symptoms):
    """
    Detect department based on symptom keywords.
    """
    symptoms = symptoms.lower()
    for key, department in SYMPTOM_DEPARTMENT_MAP.items():
        if key in symptoms:
            return department
    return "General Medicine"  # fallback


def resolve_department(form_data, symptoms):
    """
    Use the department the patient picked, otherwise detect one from the symptoms.
    Matching is tolerant of short names in the database ("Cardio" matches "Cardiology").
    Returns (Department or None, display name).
    """
    if form_data.get("department"):
        return form_data["department"], form_data["department"].name

    detected = detect_department(symptoms)
    department = Department.objects.filter(name__iexact=detected).first()
    if department is None:
        prefix = detected.lower()[:5]
        department = next((d for d in Department.objects.all() if d.name.lower()[:5] == prefix), None)
    return department, (department.name if department else detected)


ACTIVE_STATUSES = ['Pending', 'Approved']


def find_available_doctor(department, when):
    """
    Pick the least-busy doctor in the department who works on that weekday and hour
    and has no other active booking at exactly that time. Returns None if nobody fits.
    """
    if department is None:
        return None

    local_when = timezone.localtime(when)
    weekday = local_when.strftime('%a')  # "Mon", "Tue", ...
    slot_time = local_when.time()

    busy_doctors = (Appointment.objects.filter(appointment_datetime=when, status__in=ACTIVE_STATUSES)
                    .values('doctor_id'))
    busy_guest_doctors = (GuestAppointment.objects.filter(appointment_datetime=when, status__in=ACTIVE_STATUSES,
                                                          doctor__isnull=False)
                          .values('doctor_id'))
    candidates = (
        Doctor.objects.filter(department=department)
        .exclude(id__in=busy_doctors)
        .exclude(id__in=busy_guest_doctors)
        .annotate(load=Count('appointment', filter=Q(appointment__status__in=ACTIVE_STATUSES), distinct=True)
                  + Count('guestappointment', filter=Q(guestappointment__status__in=ACTIVE_STATUSES), distinct=True))
        .order_by('load', 'id')
    )
    for doctor in candidates:
        days = doctor.available_day_codes
        works_that_day = not days or weekday in days
        in_hours = doctor.start_time <= slot_time and (doctor.end_time is None or slot_time < doctor.end_time)
        if works_that_day and in_hours:
            return doctor
    return None


def book_appointment(request):
    if request.user.is_authenticated:
        patient = getattr(request.user, 'patient', None)
        if patient is None:
            messages.warning(request, "Only patient accounts can book appointments. Log out to book as a guest.")
            return redirect('dashboard')

        form = AppointmentForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            when = form.cleaned_data["appointment_datetime"]
            dept_obj, department = resolve_department(form.cleaned_data, form.cleaned_data["description"])
            doctor = find_available_doctor(dept_obj, when)

            if doctor:
                appointment = form.save(commit=False)
                appointment.patient = patient
                appointment.doctor = doctor
                appointment.appointment_datetime = when
                appointment.save()
                messages.success(request, f"Appointment requested with Dr. {doctor.name} ({department}). "
                                          f"You'll get an email once it is approved.")
                return redirect("patient_dashboard")
            messages.error(request, f"No {department} doctor is available at that time. "
                                    f"Please try a different date or time.")

    else:
        # Guest booking
        form = GuestAppointmentForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            cleaned = form.cleaned_data
            dept_obj, department = resolve_department(cleaned, cleaned["symptoms"])
            doctor = find_available_doctor(dept_obj, cleaned["appointment_datetime"])
            guest = GuestAppointment.objects.create(
                name=cleaned["name"],
                email=cleaned["email"],
                phone=cleaned["phone"],
                symptoms=cleaned["symptoms"],
                department=department,
                doctor=doctor,  # can be None if no doctor available
                appointment_datetime=cleaned["appointment_datetime"],
            )

            if doctor:
                messages.success(request, f"Your request was sent to Dr. {doctor.name} ({department}). "
                                          f"We'll email {guest.email} once it is confirmed.")
            else:
                messages.warning(request, f"Your request was received, but no {department} doctor is free at "
                                          f"that time. Our staff will contact you to arrange a slot.")
            return redirect("guest_success")

    return render(request, "core/book_appointment.html", {"form": form})


def guest_success(request):
    return render(request, "core/guest_success.html")


## ----------------## DASHBOARDS

@patient_required
def patient_dashboard(request):
    patient = request.user.patient
    appointments = (Appointment.objects.filter(patient=patient)
                    .select_related('doctor', 'doctor__department')
                    .order_by('-appointment_datetime'))
    now = timezone.now()
    return render(request, 'core/patient_dashboard.html', {
        'patient': patient,
        'appointments': appointments,
        'upcoming_count': appointments.filter(appointment_datetime__gte=now).exclude(status='Rejected').count(),
        'pending_count': appointments.filter(status='Pending').count(),
    })


@doctor_required
def doctor_dashboard(request):
    doctor = request.user.doctor
    appointments = (Appointment.objects.filter(doctor=doctor)
                    .select_related('patient').order_by('appointment_datetime'))
    guest_appointments = GuestAppointment.objects.filter(doctor=doctor).order_by('appointment_datetime')
    return render(request, 'core/doctor_dashboard.html', {
        'doctor': doctor,
        'appointments': appointments,
        'guest_appointments': guest_appointments,
        'pending_count': (appointments.filter(status='Pending').count()
                          + guest_appointments.filter(status='Pending').count()),
    })


def _notify(subject, name, email, doctor, when, approved):
    if approved:
        body = (f"Dear {name},\n\nYour appointment with Dr. {doctor.name} on "
                f"{timezone.localtime(when):%d %b %Y at %I:%M %p} has been APPROVED.\n\nThank you!")
    else:
        body = (f"Dear {name},\n\nWe regret to inform you that your appointment with Dr. {doctor.name} on "
                f"{timezone.localtime(when):%d %b %Y at %I:%M %p} has been REJECTED.\n\n"
                f"Please try booking another slot.\n\nThank you!")
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [email])
        return True
    except Exception:
        logger.exception("Could not send appointment email to %s", email)
        return False


@require_POST
@doctor_required
def update_appointment_status(request, kind, pk, action):
    """Approve or reject an appointment that belongs to the logged-in doctor."""
    if action not in ('approve', 'reject') or kind not in ('patient', 'guest'):
        messages.error(request, "Unknown action.")
        return redirect('doctor_dashboard')

    doctor = request.user.doctor
    if kind == 'patient':
        appointment = get_object_or_404(Appointment.objects.select_related('patient'), pk=pk, doctor=doctor)
        name, email = appointment.patient.name, appointment.patient.email
    else:
        appointment = get_object_or_404(GuestAppointment, pk=pk, doctor=doctor)
        name, email = appointment.name, appointment.email

    if appointment.status != 'Pending':
        messages.info(request, "That appointment was already handled.")
        return redirect('doctor_dashboard')

    approved = action == 'approve'
    appointment.status = 'Approved' if approved else 'Rejected'
    appointment.save(update_fields=['status'])

    subject = 'Appointment Approved' if approved else 'Appointment Rejected'
    if _notify(subject, name, email, doctor, appointment.appointment_datetime, approved):
        messages.success(request, f"Appointment {appointment.status.lower()} and {name} was notified by email.")
    else:
        messages.warning(request, f"Appointment {appointment.status.lower()}, but the email to {name} could not be sent.")
    return redirect('doctor_dashboard')


## ----------------## PROFILES

@doctor_required
def doctor_profile(request):
    doctor = request.user.doctor
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('doctor_dashboard')
    else:
        form = DoctorProfileForm(instance=doctor)
    return render(request, 'core/doctor_profile.html', {'form': form, 'doctor': doctor})


@patient_required
def patient_profile(request):
    user = request.user
    patient = user.patient

    if request.method == 'POST':
        profile_form = PatientProfileForm(request.POST, instance=user)
        extra_form = PatientExtraForm(request.POST, instance=patient)
        if profile_form.is_valid() and extra_form.is_valid():
            profile_form.save()
            extra_form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('patient_profile')
    else:
        profile_form = PatientProfileForm(instance=user)
        extra_form = PatientExtraForm(instance=patient)

    return render(request, 'core/patient_profile.html', {
        'profile_form': profile_form,
        'extra_form': extra_form,
    })
