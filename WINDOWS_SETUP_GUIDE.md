# UNN Exchange & Services Hub — Windows PowerShell Setup Guide

> This guide is written specifically for **Windows + VS Code + PowerShell**.
> Every command here is tested for PowerShell. Do not use Git Bash or CMD — stick to PowerShell.

---

## Before You Start — Fix PowerShell Execution Policy

PowerShell on Windows blocks scripts (including venv activation) by default.
You must fix this **once** before anything else works.

Open PowerShell **as Administrator** (right-click → Run as Administrator) and run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Type `Y` and press Enter when prompted. You only need to do this once.
Close the Administrator PowerShell. Now open VS Code normally.

---

## Step 1 — Verify Python is Installed

Open VS Code. Open the terminal with `` Ctrl+` ``.
Make sure the terminal says **PowerShell** in the top-right dropdown (not CMD or bash).

```powershell
python --version
```

Expected output: `Python 3.11.x`

If you see `Python was not found` — Python is not on your PATH.
Fix: Reinstall Python from https://python.org and tick **"Add Python to PATH"** during install.

If you see `3.9` or `3.10` instead of `3.11`:

```powershell
# Check all installed Python versions
py -0

# Use the launcher to target 3.11 specifically
py -3.11 --version
```

---

## Step 2 — Navigate to Your Projects Folder and Create the Project

```powershell
# Go to your preferred location (change this path to wherever you keep projects)
cd C:\Users\YourName\Documents\Projects

# If the Projects folder doesn't exist yet, create it first:
mkdir Projects
cd Projects

# Create the project folder and enter it
mkdir unn_hub
cd unn_hub
```

---

## Step 3 — Create and Activate the Virtual Environment

```powershell
# Create the virtual environment (use py -3.11 if python gives you wrong version)
python -m venv .venv

# Activate it — this is the Windows PowerShell command (NOT source .venv/bin/activate)
.venv\Scripts\Activate.ps1
```

After activation, your terminal prompt changes to show `(.venv)` at the start:

```
(.venv) PS C:\Users\YourName\Documents\Projects\unn_hub>
```

**If activation fails with a permissions error**, go back to Step 0 and fix the execution policy.

> IMPORTANT: You must activate the venv every time you open a new terminal.
> If you ever see `ModuleNotFoundError: No module named 'django'` — your venv is not activated.

---

## Step 4 — Extract the Scaffold Into This Folder

Unzip `unn_hub_scaffold.zip` into your `unn_hub\` folder.

After extracting, verify the structure looks correct:

```powershell
# List the top-level contents
dir
```

You should see these folders and files:

```
Mode    Name
----    ----
d----   apps
d----   config
d----   media
d----   requirements
d----   static
d----   templates
-a---   .env
-a---   .env.example
-a---   .gitignore
-a---   manage.py
-a---   SETUP_GUIDE.md
```

If you see everything inside a nested `unn_hub\unn_hub\` folder, you extracted one level too deep.
Move the contents up one level so `manage.py` is directly inside your working folder.

---

## Step 5 — Tell VS Code to Use Your Virtual Environment

Press `Ctrl+Shift+P` → type: `Python: Select Interpreter` → press Enter

Choose the option that shows `.venv` in the path, something like:
`.venv\Scripts\python.exe`

This makes VS Code IntelliSense, linting, and the integrated terminal all use your venv.

After selecting, **close and reopen the terminal** inside VS Code (`` Ctrl+` `` to close, then reopen).
Check the venv is still active — you should still see `(.venv)` in the prompt.
If not, run `.venv\Scripts\Activate.ps1` again.

---

## Step 6 — Install All Dependencies

```powershell
pip install -r requirements\development.txt
```

Note the **backslash** — PowerShell uses `\` not `/` for paths.

This installs: Django, Pillow, crispy-forms, django-filter, debug-toolbar, whitenoise, python-decouple.

Expected: Several lines of `Downloading...` and `Installing...` ending with `Successfully installed`.

If you see `pip is not recognized` — your venv is not activated. Run `.venv\Scripts\Activate.ps1`.

---

## Step 7 — Set Up Your .env File

The `.env` file stores secret config values and must never be committed to Git.
The scaffold already created a `.env` file with a placeholder key. Let's replace it with a real one.

**First, generate a real secret key:**

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

This prints a long random string like:
`django-insecure-abc123xyz...`

**Now open `.env` in VS Code:**

```powershell
code .env
```

Replace the contents with your real values:

```
DJANGO_SECRET_KEY=paste-your-generated-key-here
DJANGO_SETTINGS_MODULE=config.settings.development
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

Save the file (`Ctrl+S`). Keep `.env` open — you'll need it later if errors appear.

---

## Step 8 — Verify AUTH_USER_MODEL (Critical — Do Not Skip)

Open `config\settings\base.py` in VS Code:

```powershell
code config\settings\base.py
```

Find this line (it should be around line 30):

```python
AUTH_USER_MODEL = 'accounts.User'
```

**This must exist before you run any migrations.**
If it's missing, add it now before proceeding.

---

## Step 9 — Run Migrations

```powershell
# First, generate migration files for all apps
python manage.py makemigrations

# Then apply them to create the database
python manage.py migrate
```

**Expected output for `makemigrations`:**
```
Migrations for 'accounts':
  apps\accounts\migrations\0001_initial.py
Migrations for 'marketplace':
  apps\marketplace\migrations\0001_initial.py
... (one block per app)
```

**Expected output for `migrate`:**
```
Operations to perform:
  Apply all migrations: accounts, admin, auth, contenttypes, marketplace, messaging, reviews, services, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying accounts.0001_initial... OK
  ... (20-30 lines all ending in OK)
```

### Common migration errors and exact fixes:

**Error: `No module named 'apps.accounts'`**
Your terminal is in the wrong folder. Run:
```powershell
# Check where you are
pwd
# You must be in the folder that contains manage.py
# If you're not, cd to it:
cd C:\Users\YourName\Documents\Projects\unn_hub
```

**Error: `ModuleNotFoundError: No module named 'django'`**
Your venv is not activated. Run:
```powershell
.venv\Scripts\Activate.ps1
```

**Error: `decouple.UndefinedValueError: DJANGO_SECRET_KEY not found`**
Your `.env` file is missing or has the wrong format. Open it and check:
- No spaces around the `=` sign: `KEY=value` not `KEY = value`
- No quotes around values: `KEY=abc` not `KEY="abc"`
- The file is named `.env` not `.env.txt` (Windows sometimes adds `.txt`)

Check the actual filename:
```powershell
dir -Force | Where-Object { $_.Name -like ".env*" }
```
If it shows `.env.txt`, rename it:
```powershell
Rename-Item .env.txt .env
```

**Error: `django.db.utils.OperationalError: table already exists`**
You ran `migrate` before `makemigrations` completed, or ran it twice. Reset:
```powershell
# Delete the SQLite database
Remove-Item db.sqlite3

# Delete all migration files EXCEPT __init__.py
Get-ChildItem -Path apps -Recurse -Filter "*.py" |
  Where-Object { $_.DirectoryName -like "*migrations*" -and $_.Name -ne "__init__.py" } |
  Remove-Item

# Start fresh
python manage.py makemigrations
python manage.py migrate
```

---

## Step 10 — Create a Superuser

```powershell
python manage.py createsuperuser
```

You'll be prompted:
```
Email address: your@email.com
Username: admin
Password: (type password, nothing shows — that's normal)
Password (again): (retype)
Superuser created successfully.
```

This account gives you access to Django Admin. Your Profile is auto-created by the signal.

---

## Step 11 — Run the Development Server

```powershell
python manage.py runserver
```

Expected output:
```
Django version 5.0.6, using settings 'config.settings.development'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

Open your browser and visit:

| URL | What you'll see |
|-----|----------------|
| `http://127.0.0.1:8000/` | Marketplace home (empty listings) |
| `http://127.0.0.1:8000/admin/` | Django Admin login |
| `http://127.0.0.1:8000/accounts/register/` | Registration page |
| `http://127.0.0.1:8000/accounts/login/` | Login page |

To stop the server: press `Ctrl+C` in the terminal.

---

## Step 12 — Seed Categories via Django Admin

Log into `http://127.0.0.1:8000/admin/` with your superuser.

**Add Marketplace Categories** (Admin → Marketplace → Categories → Add):

| Name | Slug |
|------|------|
| Electronics | electronics |
| Books & Study Materials | books-study |
| Clothing | clothing |
| Food & Groceries | food-groceries |
| Room & Accommodation | room-accommodation |
| Part-time Jobs | part-time-jobs |
| Other | other |

**Add Service Categories** (Admin → Services → Service categories → Add):

| Name | Slug |
|------|------|
| Tutoring | tutoring |
| Repairs & Tech | repairs-tech |
| Delivery | delivery |
| Laundry | laundry |
| Graphic Design | graphic-design |
| Photography | photography |

---

## Step 13 — Initialize Git

```powershell
git init
git add .
git commit -m "Initial project scaffold — UNN Exchange & Services Hub"
```

---

## Daily Workflow in PowerShell

Every time you open VS Code to work on this project:

```powershell
# 1. Open terminal (Ctrl+`)
# 2. Navigate to project folder
cd C:\Users\YourName\Documents\Projects\unn_hub

# 3. Activate venv (ALWAYS do this first)
.venv\Scripts\Activate.ps1

# 4. Start the server
python manage.py runserver
```

---

## PowerShell vs Linux/Mac Command Differences

The scaffold's original guide used Linux commands. Here are the Windows equivalents:

| Linux/Mac | PowerShell (Windows) | What it does |
|-----------|---------------------|--------------|
| `source .venv/bin/activate` | `.venv\Scripts\Activate.ps1` | Activate venv |
| `cp .env.example .env` | `Copy-Item .env.example .env` | Copy a file |
| `rm db.sqlite3` | `Remove-Item db.sqlite3` | Delete a file |
| `python3` | `python` | Run Python |
| `ls` | `dir` | List files |
| `pwd` | `pwd` or `cd` with no args | Show current path |
| `touch file.py` | `New-Item file.py` | Create empty file |
| Forward slashes in paths `/` | Backslashes `\` | Path separator |

---

## Complete Commands Reference (PowerShell versions)

```powershell
# Activate venv (run this every session)
.venv\Scripts\Activate.ps1

# Run development server
python manage.py runserver

# After changing any models.py file
python manage.py makemigrations
python manage.py migrate

# Open interactive Django shell
python manage.py shell

# Collect static files (before deploying)
python manage.py collectstatic

# Run all tests
python manage.py test apps\

# Check for production issues
python manage.py check --deploy

# Install a new package and save it
pip install package-name
pip freeze > requirements\base.txt
```
