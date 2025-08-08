import os
import sys

# Add your project's main directory to the Python path
path = '/home/ramzihaidan537/atten'
if path not in sys.path:
    sys.path.insert(0, path)

# Point to your project's settings file
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'

# Import the WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()