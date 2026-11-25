# Quick Summary

Students register, sign in, submit a course override, and check its status. Staff can approve or deny requests. This is a coursework demonstration, not an official VCU service.

## First-time setup on Windows

Install Python 3.11 or newer with pip and make sure the `python` command is available in PowerShell. Python 3.13 was used for testing; it is not required. Check your version with:

```powershell
python --version
```

Extract the project ZIP, then open a PowerShell terminal inside the extracted `course-override` folder (the folder containing `main.py` and `requirements.txt`).

Create your own environment and install the project's packages:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The first command creates a new `.venv` folder on your computer. The second installs the required packages into it. The commands below use that environment directly, so activation is not needed.

Create the database tables by applying the included migrations:

```powershell
.\.venv\Scripts\python.exe -m flask --app main db upgrade
```

## Start the app

After completing setup, run this from the project folder:

```powershell
.\.venv\Scripts\python.exe -m flask --app main run
```

Open http://127.0.0.1:5000 and create an account. No email setup or `.env` file is needed to run the app. SQLite stores requests in `instance/overrides.db`. A local session secret is generated automatically. No accounts or passwords are included.

For later runs, use the same start command. You only need to create the environment and install dependencies once per project setup. Stop the server with **Ctrl+C**.

If using VS Code, select your newly created environment after completing setup: run **Python: Select Interpreter**, choose **Enter interpreter path**, and select `.venv/Scripts/python.exe` inside the project.

To create a staff reviewer, run this command and answer the prompts:

```powershell
.\.venv\Scripts\python.exe -m flask --app main create-staff
```

Sign in with that account to review requests. Students see only their own requests. Public registration always creates a student account.

## Optional email

Email uses one Flask-Mail function in `website/notifications.py`. With no mail server configured, it simply returns. Requests still save normally, with no email logs or extra development notices.

To enable submission and decision emails, copy `.env.example` to `.env` and fill in these three settings:

```dotenv
MAIL_SERVER=smtp.your-provider.com
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-provider-app-password
```

Restart the app. It uses port 587 with TLS and sends from `MAIL_USERNAME` to the student's account email. Use an SMTP provider that supports these settings. If delivery fails, the request stays saved and a warning appears. Real email delivery requires working provider credentials; automated tests capture messages without sending them.

## Features

| Feature                                                                   | Where to find it                                                           |
| ------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Required student name, ID, course name and number; optional justification | `website/forms.py`                                                         |
| Server validation and submission confirmation                             | `website/forms.py`, `website/views.py`                                     |
| Custom 404 and 500 pages                                                  | `website/__init__.py`, `templates/error.html`                              |
| Shared Jinja2 base template and flash messages                            | `templates/base.html`                                                      |
| Responsive Bootstrap styling                                              | Bootstrap-Flask (`flask_bootstrap.Bootstrap5`); daisyUI buttons and badges |
| Application factory and Blueprints                                        | `website/__init__.py`, `auth.py`, `views.py`                               |
| Authentication and authorization                                          | Flask-Login, password hashes, ownership and staff checks, CSRF             |
| Email capability                                                          | `website/notifications.py`                                                 |
| Database migrations                                                       | `migrations/`, Flask-Migrate and SQLite                                    |
| Tests                                                                     | `tests/`                                                                   |

Student IDs use `V` followed by eight digits, for example `V01234567`. Course numbers use a subject and three digits, for example `CMSC 301`. These validation rules can be changed in `forms.py`.

## Tests and migrations

```powershell
.\.venv\Scripts\python.exe -m pytest -q
# After changing models, generate and inspect a migration:
.\.venv\Scripts\python.exe -m flask --app main db migrate -m "Describe change"
.\.venv\Scripts\python.exe -m flask --app main db upgrade
```

Tests use temporary databases and cover validation, login, student/staff permissions, email being optional, notification failures, CSRF, and error pages. `requirements-lock.txt` records the tested dependency versions.

Bootstrap assets are served locally. daisyUI/Tailwind styling requires internet access. Browser visual verification was unavailable in this environment.
