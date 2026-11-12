from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Appointment, Department, Doctor, GuestAppointment, Patient
from .views import detect_department, find_available_doctor

User = get_user_model()
PASSWORD = "Str0ng-pass-123"


def next_weekday_at(hour, weekday=0):
    """Timezone-aware datetime for the next given weekday (0 = Monday) at `hour`:00."""
    today = timezone.localdate()
    days_ahead = (weekday - today.weekday()) % 7 or 7
    return timezone.make_aware(datetime.combine(today + timedelta(days=days_ahead), time(hour, 0)))


class BaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cardio = Department.objects.create(name="Cardiology", description="Heart care")
        cls.general = Department.objects.create(name="General Medicine", description="General care")

        cls.doctor_user = User.objects.create_user("drheart", password=PASSWORD, role="doctor")
        cls.doctor = Doctor.objects.create(
            user=cls.doctor_user, name="Heart", email="heart@example.com", phone="1",
            department=cls.cardio, specialization="Cardiologist",
            available_days=["Mon", "Tue", "Wed", "Thu", "Fri"], start_time=time(9), end_time=time(17),
        )
        cls.other_doctor_user = User.objects.create_user("drother", password=PASSWORD, role="doctor")
        cls.other_doctor = Doctor.objects.create(
            user=cls.other_doctor_user, name="Other", email="other@example.com", phone="2",
            department=cls.general, specialization="GP",
        )

        cls.patient_user = User.objects.create_user("pat", password=PASSWORD, email="pat@example.com", role="patient")
        cls.patient = Patient.objects.create(
            user=cls.patient_user, name="Pat", age=30, gender="Male",
            email="pat@example.com", phone="3", address="Street",
        )
        cls.admin_user = User.objects.create_user("boss", password=PASSWORD, is_staff=True)

        cls.slot = next_weekday_at(10)
        cls.appointment = Appointment.objects.create(
            patient=cls.patient, doctor=cls.doctor, appointment_datetime=cls.slot, description="chest pain",
        )


class AppointmentPermissionTests(BaseTestCase):
    def url(self, action="approve", kind="patient", pk=None):
        return reverse("update_appointment_status", args=[kind, pk or self.appointment.pk, action])

    def test_get_request_cannot_change_status(self):
        self.client.force_login(self.doctor_user)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 405)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, "Pending")

    def test_patient_cannot_approve(self):
        self.client.force_login(self.patient_user)
        self.client.post(self.url())
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, "Pending")

    def test_other_doctor_cannot_approve(self):
        self.client.force_login(self.other_doctor_user)
        response = self.client.post(self.url())
        self.assertEqual(response.status_code, 404)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, "Pending")

    def test_assigned_doctor_can_approve_and_patient_is_emailed(self):
        self.client.force_login(self.doctor_user)
        response = self.client.post(self.url())
        self.assertRedirects(response, reverse("doctor_dashboard"))
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, "Approved")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["pat@example.com"])

    def test_already_handled_appointment_is_not_changed_again(self):
        self.appointment.status = "Rejected"
        self.appointment.save()
        self.client.force_login(self.doctor_user)
        self.client.post(self.url("approve"))
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, "Rejected")

    def test_doctor_can_reject_own_guest_appointment(self):
        guest = GuestAppointment.objects.create(
            name="Guest", email="g@example.com", phone="4", symptoms="chest pain",
            department="Cardiology", doctor=self.doctor, appointment_datetime=self.slot,
        )
        self.client.force_login(self.doctor_user)
        self.client.post(self.url("reject", "guest", guest.pk))
        guest.refresh_from_db()
        self.assertEqual(guest.status, "Rejected")
        self.assertEqual(mail.outbox[0].to, ["g@example.com"])


class BookingTests(BaseTestCase):
    def booking_data(self, **extra):
        when = timezone.localtime(next_weekday_at(11, weekday=1))
        data = {"appointment_date": when.date().isoformat(), "appointment_time": "11:00", "department": ""}
        data.update(extra)
        return data

    def test_guest_booking_redirects_to_success_page(self):
        data = self.booking_data(name="Guest", email="g@example.com", phone="5", symptoms="I have chest pain")
        response = self.client.post(reverse("book_appointment"), data, follow=True)
        self.assertRedirects(response, reverse("guest_success"))
        guest = GuestAppointment.objects.get()
        self.assertEqual(guest.doctor, self.doctor)
        self.assertEqual(guest.department, "Cardiology")

    def test_guest_booking_in_the_past_is_rejected(self):
        data = self.booking_data(name="Guest", email="g@example.com", phone="5", symptoms="fever",
                                 appointment_date="2000-01-01")
        response = self.client.post(reverse("book_appointment"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(GuestAppointment.objects.exists())

    def test_patient_booking_assigns_doctor(self):
        self.client.force_login(self.patient_user)
        response = self.client.post(reverse("book_appointment"), self.booking_data(description="chest pain again"))
        self.assertRedirects(response, reverse("patient_dashboard"))
        self.assertEqual(Appointment.objects.filter(patient=self.patient).count(), 2)

    def test_patient_can_pick_department(self):
        self.client.force_login(self.patient_user)
        self.client.post(reverse("book_appointment"),
                         self.booking_data(description="something vague", department=self.general.pk))
        latest = Appointment.objects.latest("id")
        self.assertEqual(latest.doctor, self.other_doctor)

    def test_doctor_account_cannot_book(self):
        self.client.force_login(self.doctor_user)
        response = self.client.post(reverse("book_appointment"), self.booking_data(description="chest pain"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Appointment.objects.count(), 1)


class DoctorMatchingTests(BaseTestCase):
    def test_detect_department(self):
        self.assertEqual(detect_department("Bad CHEST PAIN since morning"), "Cardiology")
        self.assertEqual(detect_department("no idea"), "General Medicine")

    def test_double_booking_is_avoided(self):
        self.assertIsNone(find_available_doctor(self.cardio, self.slot))

    def test_outside_working_hours(self):
        self.assertIsNone(find_available_doctor(self.cardio, next_weekday_at(20)))

    def test_not_on_working_day(self):
        self.assertIsNone(find_available_doctor(self.cardio, next_weekday_at(10, weekday=6)))

    def test_free_slot(self):
        self.assertEqual(find_available_doctor(self.cardio, next_weekday_at(14)), self.doctor)

    def test_legacy_available_days_value_does_not_crash(self):
        # Old rows stored a number here before available_days became a JSON list
        self.doctor.available_days = 7
        self.doctor.save()
        self.assertEqual(self.doctor.get_available_days_display(), "Every day")
        self.assertEqual(find_available_doctor(self.cardio, next_weekday_at(14)), self.doctor)
        self.assertEqual(self.client.get(reverse("doctors")).status_code, 200)

    def test_short_department_names_still_match(self):
        from .views import resolve_department
        self.cardio.name = "cardio"
        self.cardio.save()
        department, name = resolve_department({}, "chest pain")
        self.assertEqual(department, self.cardio)


class AccessTests(BaseTestCase):
    def test_public_pages_render(self):
        for name, args in [("home", []), ("departments_list", []), ("departments_detail", [self.cardio.pk]),
                           ("doctors", []), ("doctor_detail", [self.doctor.pk]), ("book_appointment", []),
                           ("login", []), ("register", []), ("guest_success", []), ("doctor_password_reset", [])]:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200)

    def test_homepage_with_featured_doctor(self):
        self.doctor.is_featured = True
        self.doctor.save()
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("doctor_detail", args=[self.doctor.pk]))

    def test_doctors_filter_ignores_garbage(self):
        self.assertEqual(self.client.get(reverse("doctors") + "?department=abc").status_code, 200)

    def test_login_page_has_no_error_on_first_visit(self):
        response = self.client.get(reverse("login"))
        self.assertNotContains(response, "Incorrect username")
        self.assertNotContains(response, "Invalid credentials")

    def test_login_redirects_by_role(self):
        for user, target in [("pat", "patient_dashboard"), ("drheart", "doctor_dashboard"), ("boss", "admin_dashboard")]:
            with self.subTest(user=user):
                self.client.logout()
                response = self.client.post(reverse("login"), {"username": user, "password": PASSWORD}, follow=True)
                self.assertRedirects(response, reverse(target))

    def test_login_ignores_external_next(self):
        response = self.client.post(reverse("login"), {"username": "pat", "password": PASSWORD,
                                                       "next": "https://evil.example.com/"})
        self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)

    def test_create_department_ignores_external_next(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(reverse("create_department") + "?next=https://evil.example.com/",
                                    {"name": "Neurology", "description": "Brain"})
        self.assertRedirects(response, reverse("admin_dashboard"))

    def test_logout_requires_post(self):
        self.client.force_login(self.patient_user)
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.client.post(reverse("logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_role_pages_reject_wrong_role(self):
        self.client.force_login(self.patient_user)
        self.assertRedirects(self.client.get(reverse("doctor_dashboard")), reverse("home"))
        self.assertRedirects(self.client.get(reverse("doctor_profile")), reverse("home"))
        self.client.force_login(self.doctor_user)
        self.assertRedirects(self.client.get(reverse("patient_dashboard")), reverse("home"))

    def test_dashboards_render_for_their_role(self):
        for user, name in [(self.patient_user, "patient_dashboard"), (self.doctor_user, "doctor_dashboard"),
                           (self.admin_user, "admin_dashboard"), (self.patient_user, "patient_profile"),
                           (self.doctor_user, "doctor_profile"), (self.patient_user, "change_password"),
                           (self.doctor_user, "doctor_change_password")]:
            with self.subTest(name=name):
                self.client.force_login(user)
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_admin_pages_need_staff(self):
        self.client.force_login(self.patient_user)
        for name in ("admin_dashboard", "add_doctor", "create_department"):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 302)


class AccountTests(BaseTestCase):
    def test_register_creates_patient_with_valid_gender(self):
        response = self.client.post(reverse("register"), {
            "username": "newbie", "email": "new@example.com",
            "password1": PASSWORD, "password2": PASSWORD,
            "age": 25, "gender": "Female", "phone": "6", "address": "Road",
        })
        self.assertRedirects(response, reverse("patient_dashboard"))
        patient = Patient.objects.get(user__username="newbie")
        self.assertEqual(patient.gender, "Female")
        self.assertEqual(patient.user.role, "patient")

    def test_admin_can_add_doctor_with_role(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(reverse("add_doctor"), {
            "username": "drnew", "password": PASSWORD, "name": "New", "email": "new@example.com",
            "phone": "7", "department": self.cardio.pk, "specialization": "Cardiologist",
            "available_days": ["Mon", "Tue"], "start_time": "09:00", "end_time": "17:00",
        })
        self.assertRedirects(response, reverse("admin_dashboard"))
        user = User.objects.get(username="drnew")
        self.assertEqual(user.role, "doctor")
        self.assertTrue(hasattr(user, "doctor"))

    def test_patient_profile_update(self):
        self.client.force_login(self.patient_user)
        response = self.client.post(reverse("patient_profile"), {
            "username": "pat", "email": "pat2@example.com",
            "name": "Pat Two", "age": 31, "gender": "Male", "phone": "3", "address": "Street",
        })
        self.assertRedirects(response, reverse("patient_profile"))
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.name, "Pat Two")

    def test_password_reset_email_is_sent(self):
        self.doctor_user.email = "heart@example.com"
        self.doctor_user.save()
        response = self.client.post(reverse("doctor_password_reset"), {"email": "heart@example.com"})
        self.assertRedirects(response, reverse("doctor_password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/doctor/reset/", mail.outbox[0].body)
