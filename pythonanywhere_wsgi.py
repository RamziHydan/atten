"""
WSGI configuration for Django Attendance Platform on PythonAnywhere.

Copy this content to your PythonAnywhere WSGI file:
/var/www/yourusername_pythonanywhere_com_wsgi.py

Replace 'yourusername' with your actual PythonAnywhere username.
"""

import os
import sys

# Add your project directory to the Python path
# Replace 'yourusername' with your actual PythonAnywhere username
project_home = '/home/yourusername/attendance-platform'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set the Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'

# Set production environment variables
# IMPORTANT: Replace these with your actual values
os.environ.setdefault('SECRET_KEY', 'your-super-secret-key-here-generate-a-new-one')
os.environ.setdefault('DEBUG', 'False')
os.environ.setdefault('ALLOWED_HOSTS', 'yourusername.pythonanywhere.com')

# Optional: Database configuration (if using MySQL/PostgreSQL)
# os.environ.setdefault('DB_ENGINE', 'django.db.backends.mysql')
# os.environ.setdefault('DB_NAME', 'yourusername$attendance')
# os.environ.setdefault('DB_USER', 'yourusername')
# os.environ.setdefault('DB_PASSWORD', 'your-database-password')
# os.environ.setdefault('DB_HOST', 'yourusername.mysql.pythonanywhere-services.com')

# Optional: Additional CSRF trusted origins
# os.environ.setdefault('CSRF_TRUSTED_ORIGINS', 'https://yourdomain.com,https://www.yourdomain.com')

# Import Django's WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
