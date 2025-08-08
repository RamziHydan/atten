# Django Attendance Platform - PythonAnywhere Deployment Guide

This guide will help you deploy the Django Attendance Platform to PythonAnywhere.

## Prerequisites

1. PythonAnywhere account (free or paid)
2. Git repository with your code
3. Basic knowledge of Django deployment

## Step-by-Step Deployment

### 1. Upload Your Code

**Option A: Using Git (Recommended)**
```bash
# In PythonAnywhere console
git clone https://github.com/yourusername/attendance-platform.git
cd attendance-platform
```

**Option B: Upload files directly**
- Use PythonAnywhere's file manager to upload your project files

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
mkvirtualenv --python=/usr/bin/python3.10 attendance-env

# Activate virtual environment
workon attendance-env

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file or set environment variables in PythonAnywhere:

```bash
# In PythonAnywhere console or .env file
export SECRET_KEY='your-super-secret-key-here-generate-a-new-one'
export DEBUG=False
export ALLOWED_HOSTS='yourusername.pythonanywhere.com'

# Optional: Database configuration (if using MySQL/PostgreSQL)
# export DB_ENGINE='django.db.backends.mysql'
# export DB_NAME='yourusername$attendance'
# export DB_USER='yourusername'
# export DB_PASSWORD='your-db-password'
# export DB_HOST='yourusername.mysql.pythonanywhere-services.com'
```

### 4. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Seed test data (optional)
python manage.py seed_all --clear-all
```

### 5. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 6. Configure Web App in PythonAnywhere

1. Go to PythonAnywhere Dashboard → Web
2. Click "Add a new web app"
3. Choose "Manual configuration" → Python 3.10
4. Set the following configurations:

**Source code:** `/home/yourusername/attendance-platform`
**Working directory:** `/home/yourusername/attendance-platform`

### 7. Configure WSGI File

Edit `/var/www/yourusername_pythonanywhere_com_wsgi.py`:

```python
import os
import sys

# Add your project directory to sys.path
path = '/home/yourusername/attendance-platform'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variables
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
os.environ.setdefault('SECRET_KEY', 'your-secret-key-here')
os.environ.setdefault('DEBUG', 'False')
os.environ.setdefault('ALLOWED_HOSTS', 'yourusername.pythonanywhere.com')

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 8. Configure Static Files

In PythonAnywhere Web tab, set:
- **Static files URL:** `/static/`
- **Static files directory:** `/home/yourusername/attendance-platform/staticfiles/`

### 9. Configure Media Files (if needed)

- **Media files URL:** `/media/`
- **Media files directory:** `/home/yourusername/attendance-platform/mediafiles/`

### 10. Reload Web App

Click "Reload" button in PythonAnywhere Web tab.

## Test Accounts

The platform comes with pre-seeded test accounts:

- **Super Admin:** `superadmin / admin123`
- **Company Owner 1:** `owner1 / owner123` (TechCorp Solutions)
- **Company Owner 2:** `owner2 / owner123` (Global Innovations Inc)
- **HR Manager 1:** `hr1_1 / hr123` (TechCorp - Main Branch)
- **HR Manager 2:** `hr2_1 / hr123` (Global Innovations - Main Branch)
- **Employee 1:** `emp1_1 / emp123` (TechCorp Employee)
- **Employee 2:** `emp2_1 / emp123` (Global Innovations Employee)

## Troubleshooting

### Common Issues

1. **Static files not loading:**
   - Run `python manage.py collectstatic --noinput`
   - Check static files configuration in Web tab

2. **Database errors:**
   - Ensure migrations are run: `python manage.py migrate`
   - Check database configuration in settings

3. **Import errors:**
   - Verify virtual environment is activated
   - Check all dependencies are installed

4. **Permission errors:**
   - Ensure proper file permissions
   - Check working directory configuration

### Logs

Check error logs in PythonAnywhere:
- Web tab → Log files
- Console for command-line errors

## Security Checklist

- [ ] Set DEBUG=False in production
- [ ] Use strong SECRET_KEY
- [ ] Configure ALLOWED_HOSTS properly
- [ ] Set up HTTPS (if using custom domain)
- [ ] Review CSRF_TRUSTED_ORIGINS
- [ ] Enable security middleware settings

## Performance Optimization

1. **Database:**
   - Consider upgrading to MySQL/PostgreSQL for better performance
   - Add database indexes for frequently queried fields

2. **Static Files:**
   - WhiteNoise is configured for static file serving
   - Consider CDN for large-scale deployments

3. **Caching:**
   - Add Redis/Memcached for session and cache storage
   - Enable Django's caching framework

## Maintenance

### Regular Tasks

1. **Database Backups:**
   ```bash
   python manage.py dumpdata > backup_$(date +%Y%m%d).json
   ```

2. **Update Dependencies:**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

3. **Monitor Logs:**
   - Check error logs regularly
   - Monitor application performance

### Updating Code

```bash
# Pull latest changes
git pull origin main

# Install any new dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Reload web app in PythonAnywhere dashboard
```

## Support

For issues specific to this attendance platform, check:
1. Django documentation
2. PythonAnywhere help pages
3. Project documentation

## Features Available

- Multi-tenant SaaS architecture
- Role-based access control (Super Admin, Company Owner, HR Manager, Employee)
- Attendance tracking with geolocation
- Comprehensive reporting with filtering
- Employee management
- Branch and department management
- Attendance groups and periods
- Real-time dashboard
- Mobile-responsive design
- Test data seeding for quick setup
