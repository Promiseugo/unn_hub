# UNN Exchange & Services Hub — Complete Setup Guide

## Prerequisites
- Python 3.11 installed
- VS Code installed
- Git installed

---

## Step 1 — Create Your Virtual Environment

Open VS Code, open the terminal (`Ctrl+``), then run:

```bash
# Navigate to where you keep your projects
cd ~/Projects   # or wherever you prefer

# Create the project folder
mkdir unn_hub && cd unn_hub

# Create virtual environment
python3.11 -m venv .venv

# Activate it
# On Mac/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# You should see (.venv) in your terminal prompt
```

---

## Step 2 — Copy the Scaffold Into Your Folder

Copy all files from this scaffold into your `unn_hub/` folder.
Your structure should look like this:

```
unn_hub/
├── .venv/               ← created by you above
├── apps/
├── config/
├── templates/
├── static/
├── requirements/
├── manage.py
├── .env.example
└── .gitignore
```

---

## Step 3 — Install Dependencies

```bash
# Make sure your venv is activated first
pip install -r requirements/development.txt
```

Expected output: Django, Pillow, crispy-forms etc. all install cleanly.

---

## Step 4 — Set Up Your Environment File

```bash
# Copy the example env file
cp .env.example .env
```

Open `.env` in VS Code and set a real secret key.
Generate one with:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Paste the output as your `DJANGO_SECRET_KEY` value. Your `.env` should look like:

```
DJANGO_SECRET_KEY=your-generated-key-here
DJANGO_SETTINGS_MODULE=config.settings.development
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## Step 5 — Select Python Interpreter in VS Code

Press `Ctrl+Shift+P` → type "Python: Select Interpreter"
→ Choose the one that shows `.venv` in the path.

This ensures VS Code uses your virtual environment for IntelliSense and linting.

---

## Step 6 — CRITICAL: Verify AUTH_USER_MODEL Before Any Migration

Open `config/settings/base.py` and confirm this line exists:

```python
AUTH_USER_MODEL = 'accounts.User'
```

**This must be set before you run your first migration.**
If you change this after migrating, you must drop the database and start over.

---

## Step 7 — Run Your First Migrations

```bash
# This creates the SQLite database and all tables
python manage.py makemigrations
python manage.py migrate
```

Expected: You see 20–30 "Applying..." lines ending with "OK".

If you see errors:
- `ModuleNotFoundError` → check your venv is activated
- `django.core.exceptions.ImproperlyConfigured` → check your `.env` file

---

## Step 8 — Create a Superuser

```bash
python manage.py createsuperuser
```

Enter your email, username, and password when prompted.
This account lets you access Django Admin at `/admin/`.

---

## Step 9 — Run the Development Server

```bash
python manage.py runserver
```

Open your browser:
- `http://127.0.0.1:8000/` → Marketplace home
- `http://127.0.0.1:8000/admin/` → Django Admin
- `http://127.0.0.1:8000/accounts/register/` → Registration

---

## Step 10 — Seed Initial Categories (via Admin)

Log into Admin → add Marketplace Categories:
- Electronics
- Books & Study Materials
- Clothing
- Food & Groceries
- Room & Accommodation ← replaces Rentals app
- Part-time Jobs ← replaces Jobs app
- Other

Add Service Categories:
- Tutoring
- Repairs & Tech
- Delivery
- Laundry
- Graphic Design
- Photography

---

## Step 11 — Initialize Git

```bash
git init
git add .
git commit -m "Initial project scaffold — UNN Exchange & Services Hub"
```

---

## Common Commands Reference

```bash
# Run server
python manage.py runserver

# Make and apply migrations after model changes
python manage.py makemigrations
python manage.py migrate

# Django shell (test queries)
python manage.py shell

# Collect static files (production only)
python manage.py collectstatic

# Run tests
python manage.py test apps/

# Check for deployment issues
python manage.py check --deploy
```

---

## Environment Variables Reference

| Variable | Development | Production |
|---|---|---|
| `DJANGO_SECRET_KEY` | Any random string | Long random string, kept secret |
| `DJANGO_SETTINGS_MODULE` | `config.settings.development` | `config.settings.production` |
| `DEBUG` | `True` | `False` |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | `yourdomain.com` |
| `DB_NAME` | (not needed, uses SQLite) | `unn_hub_db` |
| `USE_S3` | `False` | `True` (when ready) |

---

## What Each App Does

| App | Responsibility |
|---|---|
| `core` | Abstract base models shared by all apps |
| `accounts` | Custom User, Profile, register/login/logout |
| `marketplace` | Buy/sell listings with images and categories |
| `services` | Service offers (tutoring, repairs, rentals, jobs) |
| `messaging` | Private threads and messages between users |
| `reviews` | Generic star ratings for users, listings, services |

---

## Week-by-Week Build Order

```
Week 1 → accounts (User, Profile, register, login)
Week 2 → marketplace (Listing CRUD, images, categories)
Week 3 → services (ServiceOffer CRUD)
Week 4 → messaging (Thread, inbox, replies)
Week 5 → reviews (Review form, star display, profile ratings)
Week 6 → hardening (permissions, validation, deploy)
```
