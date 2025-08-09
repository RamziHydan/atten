# 🚀 Django SaaS Attendance Platform - Complete Setup Guide for Beginners

This guide will walk you through setting up the Django SaaS Attendance Platform on your local machine, step by step. No prior Django experience required!

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Steps](#installation-steps)
3. [Running the Project](#running-the-project)
4. [Loading Test Data](#loading-test-data)
5. [Exploring the Platform](#exploring-the-platform)
6. [Troubleshooting](#troubleshooting)
7. [Next Steps](#next-steps)

---

## 🔧 Prerequisites

Before we start, make sure you have these installed on your computer:

### 1. **Python 3.10 or Higher**
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **macOS**: Use Homebrew: `brew install python3` or download from python.org
- **Linux**: `sudo apt install python3 python3-pip` (Ubuntu/Debian)

**Verify installation:**
```bash
python --version
# Should show: Python 3.10.x or higher
```

### 2. **Git** (for cloning the repository)
- **Windows**: Download from [git-scm.com](https://git-scm.com/)
- **macOS**: `brew install git` or use Xcode Command Line Tools
- **Linux**: `sudo apt install git`

**Verify installation:**
```bash
git --version
# Should show: git version 2.x.x
```

### 3. **Code Editor** (Optional but recommended)
- [Visual Studio Code](https://code.visualstudio.com/) (Free, highly recommended)
- [PyCharm Community](https://www.jetbrains.com/pycharm/) (Free)
- Any text editor you prefer

---

## 📥 Installation Steps

### Step 1: Clone the Repository

Open your terminal/command prompt and run:

```bash
# Clone the project
git clone <repository-url>
cd atten

# Or if you downloaded as ZIP, extract and navigate to the folder
cd path/to/extracted/atten
```

### Step 2: Create a Virtual Environment

A virtual environment keeps your project dependencies separate from other Python projects.

**Windows:**
```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# You should see (venv) at the beginning of your command prompt
```

**macOS/Linux:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# You should see (venv) at the beginning of your terminal prompt
```

### Step 3: Install Dependencies

With your virtual environment activated, install all required packages:

```bash
# Install all project dependencies
pip install -r requirements.txt

# This will install:
# - Django (web framework)
# - Pillow (image processing)
# - Faker (test data generation)
# - And other required packages
```

**Wait for installation to complete** (this may take a few minutes).

### Step 4: Set Up the Database

Django uses a database to store all your data. We'll use SQLite (included with Python):

```bash
# Create database tables
python manage.py migrate

# You should see output like:
# Applying contenttypes.0001_initial... OK
# Applying auth.0001_initial... OK
# ... (more migration messages)
```

### Step 5: Create a Superuser (Optional)

Create an admin account to access the Django admin interface:

```bash
python manage.py createsuperuser

# Follow the prompts:
# Username: admin (or your preferred username)
# Email: your-email@example.com
# Password: (choose a secure password)
# Password (again): (confirm password)
```

---

## 🏃‍♂️ Running the Project

### Start the Development Server

```bash
# Start the Django development server
python manage.py runserver

# You should see:
# Watching for file changes with StatReloader
# Performing system checks...
# System check identified no issues (0 silenced).
# Starting development server at http://127.0.0.1:8000/
```

### Access the Application

Open your web browser and go to:
- **Main Application**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Admin Interface**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

**🎉 Congratulations!** Your Django application is now running!

---

## 📊 Loading Test Data

The platform includes a comprehensive test data seeder that creates a complete multi-company environment with realistic data.

### Load Complete Test Environment

```bash
# Stop the server first (Ctrl+C in the terminal)
# Then run the seeder:
python manage.py seed_all --clear-all

# This creates:
# - 2 complete companies (TechCorp Solutions, Global Innovations Inc)
# - 4 branches with geographic coordinates
# - 8 departments with HR manager assignments
# - 8 attendance groups with realistic locations
# - 16 work periods with schedules
# - 27 users across all roles
# - 1 month of realistic attendance data
```

### Start the Server Again

```bash
python manage.py runserver
```

---

## 🎯 Exploring the Platform

### Test Accounts Available

After running the seeder, you can log in with these accounts:

| Role | Username | Password | What You Can Do |
|------|----------|----------|-----------------|
| **Super Admin** | `superadmin` | `admin123` | Access everything, manage all companies |
| **Company Owner** | `owner1` | `owner123` | Manage TechCorp Solutions company |
| **Company Owner** | `owner2` | `owner123` | Manage Global Innovations Inc company |
| **HR Manager** | `hr1_1` | `hr123` | Manage TechCorp Main Branch employees |
| **HR Manager** | `hr2_1` | `hr123` | Manage Global Innovations Main Branch |
| **Employee** | `emp1_1` | `emp123` | Check-in/out at TechCorp locations |
| **Employee** | `emp2_1` | `emp123` | Check-in/out at Global Innovations locations |

### What Each Role Sees

**🔑 Super Admin (`superadmin / admin123`)**
- Complete system overview
- All companies and their data
- System-wide reports and analytics
- User management across all companies

**🏢 Company Owner (`owner1 / owner123`)**
- Company dashboard with statistics
- Branch and department management
- Employee management company-wide
- Company-specific reports
- Attendance group management

**👥 HR Manager (`hr1_1 / hr123`)**
- Branch-specific dashboard
- Employee management within their branch
- Department management
- Branch attendance reports
- Attendance group management for their branch

**👤 Employee (`emp1_1 / emp123`)**
- Mobile-first check-in/out interface
- Personal attendance history
- Simple, clean interface focused on attendance

### Key Features to Explore

1. **Dashboard**: Real-time statistics and recent activity
2. **Employee Management**: Add, edit, assign employees to departments
3. **Attendance Groups**: Create check-in locations with geofencing
4. **Reports**: Comprehensive attendance analytics with filtering
5. **Check-in/out**: Location-based attendance tracking
6. **Company Hierarchy**: Multi-tenant company → branch → department structure

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. **"Command not found" errors**
```bash
# Make sure your virtual environment is activated
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

#### 2. **"No module named 'django'" error**
```bash
# Install dependencies again
pip install -r requirements.txt
```

#### 3. **Database errors**
```bash
# Reset the database
rm db.sqlite3  # Delete the database file
python manage.py migrate  # Recreate it
python manage.py seed_all --clear-all  # Reload test data
```

#### 4. **Port already in use**
```bash
# Use a different port
python manage.py runserver 8001

# Then access: http://127.0.0.1:8001/
```

#### 5. **Static files not loading**
```bash
# Collect static files
python manage.py collectstatic --noinput
```

### Getting Help

If you encounter issues:

1. **Check the terminal output** for error messages
2. **Ensure your virtual environment is activated** (you should see `(venv)` in your prompt)
3. **Make sure all dependencies are installed**: `pip list` should show Django, Pillow, Faker, etc.
4. **Try restarting the server**: Stop with Ctrl+C, then `python manage.py runserver`

---

## 🎓 Next Steps

### Learning More

1. **Explore the Code Structure**:
   ```
   atten/
   ├── apps/
   │   ├── users/          # User management
   │   ├── companies/      # Company hierarchy
   │   ├── attendance/     # Attendance tracking
   │   └── dashboard/      # Dashboard views
   ├── templates/          # HTML templates
   ├── static/            # CSS, JavaScript, images
   └── core/              # Django settings
   ```

2. **Django Documentation**: [docs.djangoproject.com](https://docs.djangoproject.com/)
3. **Python Tutorial**: [python.org/tutorial](https://docs.python.org/3/tutorial/)

### Customizing the Platform

1. **Add New Features**: Modify the code in the `apps/` directory
2. **Change Styling**: Edit CSS in `static/` directory
3. **Modify Templates**: Update HTML in `templates/` directory
4. **Add New Models**: Create database models in `models.py` files

### Development Workflow

```bash
# 1. Make changes to your code
# 2. If you changed models, create migrations:
python manage.py makemigrations

# 3. Apply migrations:
python manage.py migrate

# 4. Test your changes:
python manage.py runserver

# 5. Create new test data if needed:
python manage.py seed_all --clear-all
```

---

## 🎉 You're All Set!

You now have a fully functional Django SaaS Attendance Platform running locally with:

- ✅ **Multi-tenant architecture** with 2 complete companies
- ✅ **Role-based access control** with 4 different user types
- ✅ **27 test accounts** for comprehensive testing
- ✅ **Realistic attendance data** for reports and analytics
- ✅ **Mobile-responsive design** for all device types
- ✅ **Interactive maps** for location-based check-ins
- ✅ **Comprehensive reporting** with filtering and export

### Quick Reference Commands

```bash
# Start the server
python manage.py runserver

# Reset and reload test data
python manage.py seed_all --clear-all

# Create database migrations (after model changes)
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Access Django shell for debugging
python manage.py shell

# Run tests
python manage.py test
```

**Happy coding!** 🚀

---

**Need help?** Check the main [README.md](README.md) for more detailed information about the platform's features and architecture.
