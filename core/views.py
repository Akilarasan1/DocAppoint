from django.shortcuts import render
from .models import Appointment, Doctor, Patient
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import AppointmentForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import redirect
from .forms import PatientSignUpForm
from .models import Patient
from django.contrib.auth.decorators import login_required



def home(request):
    return render(request, 'core/home.html')

    # core/templates/core/home.html

@login_required
def book_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('home'))
    else:
        form = AppointmentForm()

    return render(request, 'core/book_appointment.html', {'form': form})



def register(request):
    if request.method == 'POST':
        form = PatientSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create a Patient linked to this user
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
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('home')

