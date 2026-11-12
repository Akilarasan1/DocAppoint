# DocAppoint — Fixes & UI Improvements

Oct 19, 2026

## Summary

DocAppoint now has 5 security holes closed, 15 bugs fixed, a redesigned UI across every page, and 33 automated tests that all pass. Nothing has been committed yet; all changes are in the working tree on branch `hospital_v2`.

| Area | Changes | Main files |
| --- | --- | --- |
| Security | 5 fixes | `settings.py`, `views.py`, `urls.py` |
| Bugs (crashes and wrong behaviour) | 15 fixes | `views.py`, `forms.py`, `models.py`, migration `0009` |
| Project hygiene | `.gitignore`, `requirements.txt`, `.env.example`, README setup | repo root |
| UI | New design system, 24 templates rebuilt, 3 new pages | `style.css`, `templates/` |
| Tests | 0 → 33 tests | `core/tests.py` |

The most urgent item for you: the Gmail password that was in `settings.py` is still in git history. Change that password now (see Security fixes).

## Security fixes

All five issues from the review are fixed, and tests cover each one.

| # | Problem | Fix | Where |
| --- | --- | --- | --- |
| 1 | Gmail password and `SECRET_KEY` hard-coded in settings and committed to git | All secrets now come from environment variables or a local `.env` file (git-ignored). The app refuses to start with `DJANGO_DEBUG=False` and the dev key. `ALLOWED_HOSTS` is no longer empty. | `hospital_project/settings.py` lines 20–38 and 136–145; new `.env.example` |
| 2 | Any logged-in user could approve or reject any appointment | New `update_appointment_status` view only finds appointments where `doctor = request.user.doctor`; anyone else gets a 404. Already-handled appointments can't be changed again. | `core/views.py` line 430 |
| 3 | Approve/Reject were plain GET links (no CSRF protection, triggerable by prefetch) | View is `@require_POST`; buttons are now small forms with `{% csrf_token %}`; Reject asks for confirmation. | `core/views.py` line 428; `templates/core/partials/appointment_actions.html` |
| 4 | Open redirect through `?next=` on Create Department | New `safe_next_url()` helper only allows URLs on this site. Also used by login. | `core/views.py` line 54 |
| 5 | Logout worked over GET (any page could log users out) | Logout is POST-only; the navbar uses a small form button. | `core/views.py` line 152; `templates/base.html` |

Password rules were also raised from "at least 4 characters" to Django's standard four validators: minimum 8 characters, not too similar to the username, not a common password, not all numbers (`settings.py` line 102). Existing passwords keep working; the rules apply when a password is set or changed.

**Action for you:** the old Gmail password is still readable in earlier commits. Changing the code does not remove it from history, so change that password (or create a Gmail App Password) and put the new one only in `.env`.

## Bug fixes

Nine of these were crashes (500 errors) that users would have hit; six were wrong behaviour. Several were found during the fix work, beyond the original review.

| # | Bug | What users saw | Fix | Where |
| --- | --- | --- | --- | --- |
| 1 | `guest_success` URL didn't exist | Guest booking saved, then crashed | Added the route and view | `urls.py` line 20; `views.py` line 376 |
| 2 | Home page linked to a missing `doctor_detail` URL | Home page crashed once any doctor was "featured" | Added a real doctor profile page | `urls.py` line 16; new `doctor_detail.html` |
| 3 | `forms.py` imported Django's built-in `User`, overriding the custom user | "Add doctor" always crashed | Uses `get_user_model()` everywhere | `forms.py` line 12 |
| 4 | `clean_patient` tried to create a `Patient` from a name only | Logged-in booking crashed | Patient now comes from the logged-in user | `forms.py` line 128 |
| 5 | Logged-in doctor/admin could open the booking form | Crash on submit | Friendly message and redirect | `views.py` line 323 |
| 6 | Doctor dashboard/profile used `.get()` with no role check | 500 error for non-doctors | New `doctor_required` / `patient_required` decorators | `views.py` line 36 |
| 7 | Password reset email used a URL name that doesn't exist | "Forgot password" crashed | Custom email template pointing at the right URL | `urls.py` line 48; `password_reset_email.txt` |
| 8 | Reset confirmation redirected to a missing URL | Crash right after choosing a new password | `success_url` set correctly | `urls.py` line 64 |
| 9 | Patient profile POST without the button name | Crash (`UnboundLocalError`) | Simplified the view | `views.py` line 477 |
| 10 | "Invalid credentials" shown on every visit to the login page | Confusing error before typing anything | Removed; real errors only after a failed login | `views.py` line 136 |
| 11 | Doctors created on the admin page never got `role='doctor'` | Doctor navbar links missing | Role set on creation; migration backfills existing doctors | `forms.py` line 94; migration `0009` |
| 12 | Signup saved gender as `M`/`F`; the model expects `Male`/`Female` | Wrong values in the database | Form uses the model's choices; migration converts old rows | `forms.py` line 143; migration `0009` |
| 13 | `role` defaulted to the string `'None'` | Invalid value on staff accounts | Blank default; migration cleans old rows | `models.py` line 23 |
| 14 | `is_admin` checked for a field that doesn't exist | Only superusers could add doctors | Any active staff user can | `views.py` line 29 |
| 15 | Symptom matching never matched your departments ("cardio" vs "Cardiology") and always picked the first doctor | No doctor ever assigned | Patients can pick a department; tolerant name matching; picks the least-busy doctor who works that day and hour; no double-booking | `views.py` lines 269–320 |

Also fixed along the way:

- **Doctors never saw guest bookings.** The doctor dashboard now has a "Guest requests" table with Approve and Reject buttons.
- **Duplicate views and URLs removed.** `patient_profile` was defined twice, and `/dashboard/` was registered twice, so the role-based redirect could never be reached.
- **Default department image was a broken link.** It pointed at `/media/`; it now falls back to the copy in `static/` (`models.py` line 17).
- **One existing doctor stored `available_days` as the number 7.** This crashed the new doctor list during testing on a copy of your data, so the model now tolerates old formats (`models.py` line 63).
- **A failed email no longer causes a 500 error.** The status still changes, and the doctor sees a warning.

## Project cleanup

The code itself is tidy now. A few file removals still need you to run them, because I wasn't permitted to delete files.

**Done:**

- **`.gitignore` added.** It ignores `__pycache__/`, `.env`, `db.sqlite3`, `media/`, virtual environments and editor files.
- **`requirements.txt` added.** It pins Django `>=5.1,<6.0`, matching the version your migrations were made with, plus Pillow for image uploads.
- **`.env.example` added.** It lists every setting the app reads, with a one-line command to generate a secret key.
- **README now has setup and test steps.**
- **`views.py` and `forms.py` were rewritten cleanly.** About 25 duplicate imports, debug `print` calls and five unused views (`home`, `doctors_list`, `departments`, `doctor_login`, `patient_login`) are gone. Views are grouped by area: admin, auth, public, booking, dashboards, profiles.
- **Migration `0009_role_blank_and_gender_fix` added.** Before changing the `role` column, it cleans existing data: NULL/`'None'` roles, missing doctor roles, and `M`/`F` genders. It was tested on a copy of your database; your real `db.sqlite3` was not touched.
- **The admin site shows more.** Guest appointments are registered, and the doctor, patient and appointment lists have columns, filters and search.

**Still to do (run in the project folder):**

```
git rm -r hospital_project/hospital_project hospital_project/manage.py
git rm core/templates/core/doctor_login.html core/templates/core/patient_login.html core/templates/core/doctors_list.html core/templates/core/doctor_password_change.html
git rm -r --cached db.sqlite3 core/__pycache__ core/migrations/__pycache__ hospital_project/__pycache__
```

- **Line 1 removes a leftover scaffold.** It's from a second `startproject` run: admin-only URLs, no `core` app, and its own unused secret key.
- **Line 2 removes templates nothing uses anymore.**
- **Line 3 stops git tracking compiled files and the database.** `--cached` keeps the files on your disk.

## UI improvements

Every page now shares one layout and one stylesheet, so the site looks and behaves the same everywhere. Before, 7 pages were bare HTML with no navbar, and styles were scattered inline. All pages return 200 in tests, but I haven't looked at them in a browser, so please click through once.

**Design system** (`core/static/css/style.css`, which was empty before)

- Inter font, a calm blue/teal palette, soft cards with rounded corners, and consistent buttons.
- Coloured status pills (Pending amber, Approved green, Rejected red) used on every table.
- Stat cards, modern tables and "empty state" messages shared by all dashboards.
- Only Bootstrap 5.3 and Bootstrap Icons are loaded now; Font Awesome was dropped.

**Layout** (`templates/base.html`)

- A frosted white navbar highlights the current page and has a user menu (profile, change password, Django admin for staff, log out). A "Book appointment" button is always visible.
- Success, warning and error messages appear as dismissible toasts on every page; success toasts hide after 5 seconds. Before, most pages never showed them.
- A real footer with links and emergency information.

**Pages**

| Page | What changed |
| --- | --- |
| Home | Hero with live counts of departments and doctors, a 3-step "How booking works" strip, department cards with images, featured doctors with initials avatars |
| Book appointment | One form for guests and patients; optional department picker ("Not sure — match me by my symptoms"); separate date and time fields that block past dates; "What happens next" and emergency side panels |
| Login | One login for everyone; the role dropdown is gone and users go to the right dashboard automatically. Adds show/hide password, "Forgot password?" and "Book as a guest" |
| Register | Two-column form with inline errors and password rules shown under the field |
| Patient dashboard | Total, upcoming and awaiting-approval stats; appointments table with status pills; empty state with a "Book your first appointment" button |
| Doctor dashboard | Pending-requests banner; separate tables for patient and guest bookings; POST Approve and Reject buttons |
| Admin dashboard | 8 stat cards, plus the latest patient and guest bookings with links into Django admin |
| Doctors (new) | Real list with a department filter, working days and hours. It was a "List of doctors will go here" placeholder |
| Doctor profile (new) | Public page with schedule and a "Book appointment" button |
| Departments | Image cards with doctor counts; the detail page lists that department's doctors |
| Profiles, password change and reset | One shared form layout (`partials/form_page.html`) with clear headings and back links |

**Reusable pieces** in `templates/core/partials/`: `form_fields.html` renders any form with labels, required markers, help text and errors. There are also `status_badge.html`, `appointment_actions.html` and `form_page.html`.

## How to run and verify

Three commands get you running. The migration must be applied before you start the server.

1. Install dependencies and create your `.env`:

   ```
   pip install -r requirements.txt
   copy .env.example .env
   ```

   Set `DJANGO_SECRET_KEY` in `.env`. Email prints to the terminal unless you fill in the SMTP lines.
2. Apply the new migration, then start the server:

   ```
   python manage.py migrate
   python manage.py runserver
   ```
3. Run the tests: `python manage.py test core` should report `Ran 33 tests ... OK`.

**What the tests cover:**

- **Security:** wrong doctor, patient, GET request and external `next` URLs are all blocked.
- **Booking:** guest, patient, chosen department, past date, double-booking, working hours and days.
- **Logins:** every role lands on the right dashboard.
- **Accounts:** signup, add doctor, profile edit and the password reset email.
- **Pages:** every public page, dashboard and profile renders.

**Things that behave differently now:**

- **Patient dashboard URL** is `/patient/dashboard/`. `/dashboard/` sends each user to the dashboard that matches their role.
- **Login form** no longer has a role dropdown.
- **Logout** is a button in the user menu (POST), not a link.
- **Staff accounts** reach the admin dashboard; previously only superusers could add doctors.
- **The emergency number 108** appears in the footer and on the booking page. Change it in `base.html` and `book_appointment.html` if your region differs.

**Data notes from your current database:**

- **The account `ajay` has the doctor role but no doctor profile.** It now gets a friendly redirect instead of a crash. Create its profile in Django admin, or remove the role.
- **Department names are short** (`cardio`, `dermatalogist`, `neurology`). Matching now tolerates this, but renaming them to `Cardiology`, `Dermatology` and `Neurology` gives cleaner pages and more reliable symptom matching.
- **There is no General Medicine department.** That is the fallback for symptoms that don't match anything, so add one to avoid "no doctor available" messages.

## Recommended next steps

These were left out on purpose. Each is a bigger design change, worth deciding on before building.

1. **Merge `Appointment` and `GuestAppointment`** into one model with an optional `patient`. This would remove the duplicate tables in the doctor and admin dashboards. It needs a data migration.
2. **Let patients cancel or reschedule** a pending appointment from their dashboard.
3. **Use real time slots** (e.g. 15-minute blocks inside each doctor's hours) instead of any free-typed time, and show doctors' free slots when booking.
4. **Drop the duplicated `email` fields** on `Doctor` and `Patient` and use `User.email`, so they can't drift apart.
5. **Prepare for deployment:** PostgreSQL, `collectstatic` with WhiteNoise, HTTPS settings (`SECURE_SSL_REDIRECT`, secure cookies) and a real SMTP provider.
