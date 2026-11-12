Project Title: DocAppoint

Project Description:
This project is a web-based hospital management system that allows patients to book appointments with doctors online. The system is designed to streamline the appointment process, making it more convenient for both patients and hospital staff.

Key Features:
User Registration & Login: Patients can sign up and log in securely.

Doctor Listings: Patients can view available doctors and their specialties.

Appointment Booking: Registered users can select a doctor and schedule an appointment.

Doctor Dashboard: Doctors can view and manage their scheduled appointments.

Admin Panel: Hospital administrators can manage departments, doctors, and monitor appointments.

Responsive Design: Optimized for both desktop and mobile users.

Getting Started:

    python -m venv .venv
    .venv\Scripts\activate          (Windows)   or   source .venv/bin/activate
    pip install -r requirements.txt
    copy .env.example .env          (then set DJANGO_SECRET_KEY and, optionally, email settings)
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver

Open http://127.0.0.1:8000/. Log in as the superuser to reach the admin dashboard,
where you can add departments and doctors.

Running Tests:

    python manage.py test core
