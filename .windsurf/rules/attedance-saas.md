---
trigger: always_on
---

# SaaS Attendance Platform: Django Development Rules

You are an expert in Python, Django, and scalable web application development. These rules are tailored for the development of our multi-tenant **SaaS Attendance Platform**, ensuring a robust, maintainable, and secure codebase.

---

## Key Principles

* **Write clear, technical responses** with precise Django examples.
* **Use Django's built-in features** wherever possible. For this project, this means heavily relying on `django.contrib.auth` for our user roles, `django.contrib.gis` (GeoDjango) for location services, and the ORM for all data access.
* **Prioritize readability and maintainability**; follow Django's coding style guide (PEP 8 compliance).
* **Use descriptive names**; for example, `get_employees_for_department` is better than `get_data`.
* **Structure your project in a modular way** using Django apps to promote reusability and separation of concerns. This is critical for our SaaS platform.

---

## 1. Project & App Structure

A logical app structure is the foundation of a maintainable project. We will follow a clear, modular layout.

```plaintext
attendance_saas/
├── apps/
│   ├── companies/      # Models: Company, Branch, Department
│   ├── users/          # CustomUser model, Profiles, Roles, Invitations
│   ├── attendance/     # Models: AttendanceGroup, Period, CheckIn
│   └── core/           # Shared utilities, base models, custom middleware
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── manage.py

companies: Manages the multi-tenant hierarchy. All data related to companies, their branches, and departments lives here.

users: Handles all user-related logic. We will have a CustomUser model to include a role field.

attendance: Contains the core business logic for attendance, including groups, schedules (periods), and the actual check-in/out records.

core: A place for cross-app utilities, such as a BaseModel with created_at and updated_at fields.

2. Models & ORM (The Data Layer)
This is the most critical part of our application. Business logic should reside in models whenever possible.

Key Models
Custom User & Roles: We'll extend AbstractUser to add roles.

# apps/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class UserRole(models.TextChoices):
    SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
    COMPANY_MANAGER = 'COMPANY_MANAGER', 'Company Manager'
    HR_EMPLOYEE = 'HR_EMPLOYEE', 'HR Employee'
    EMPLOYEE = 'EMPLOYEE', 'Employee'

class CustomUser(AbstractUser):
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.EMPLOYEE)
    # Link a user directly to a company for easier querying
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, null=True, blank=True)

Company Hierarchy: A clear relational structure.

# apps/companies/models.py
from django.db import models
from config import settings # Assuming settings.AUTH_USER_MODEL

class Company(models.Model):
    name = models.CharField(max_length=255)
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='owned_company')
    # ... other company details

class Branch(models.Model):
    name = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches')
    # ... other branch details

class Department(models.Model):
    name = models.CharField(max_length=255)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='departments')

Attendance & Location: Use GeoDjango for efficient location-based queries.

# apps/attendance/models.py
from django.contrib.gis.db import models as gis_models
from django.db import models

class AttendanceGroup(models.Model):
    name = models.CharField(max_length=100)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    # Store location using GeoDjango for powerful spatial queries
    location = gis_models.PointField()
    # Radius in meters for valid check-ins
    radius = models.PositiveIntegerField(default=100)

class Period(models.Model):
    # e.g., "Morning Shift", "Evening Shift"
    name = models.CharField(max_length=100)
    group = models.ForeignKey(AttendanceGroup, on_delete=models.CASCADE, related_name='periods')
    start_time = models.TimeField()
    end_time = models.TimeField()
    # Use a simple field for weekdays, e.g., store as "1,2,3,4,5" for Mon-Fri
    weekdays = models.CharField(max_length=15)

class CheckIn(models.Model):
    class CheckInType(models.TextChoices):
        CHECK_IN = 'IN', 'Check-In'
        CHECK_OUT = 'OUT', 'Check-Out'

    employee = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    location = gis_models.PointField()
    type = models.CharField(max_length=3, choices=CheckInType.choices)


3. Permissions & Authorization
Permissions are role-based and must be strictly enforced at the view and data level.

Strategy
View-Level Access: Use custom decorators or mixins to check user.role before allowing access to a view.

Object-Level Access (Data Filtering): Never show data that doesn't belong to the user's scope. The primary method is to override get_queryset() in Class-Based Views.

Example: get_queryset for a Company Manager
A Company Manager should only see branches belonging to their company.

# apps/companies/views.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from .models import Branch

class BranchListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Branch
    template_name = 'companies/branch_list.html'

    def test_func(self):
        # Only allow Company Managers to access this view
        return self.request.user.role == 'COMPANY_MANAGER'

    def get_queryset(self):
        """
        This is the crucial part. It filters the data based on the logged-in user.
        A manager will only see branches associated with their company.
        """
        user = self.request.user
        # Filter the default queryset (Branch.objects.all())
        return Branch.objects.filter(company=user.company)


4. Views & Templates (The Frontend Layer)
Views: Keep views thin. Their job is to handle web requests/responses and delegate business logic to models or services.

Templates: Use Tailwind CSS for styling. Data from the view's context should be used to dynamically render content.

Mapping: Use Leaflet.js and OpenStreetMap on the frontend. Pass coordinates from the view context to the template to initialize the map.

Example: Check-in Page Template

{% comment %} This assumes you have included Leaflet CSS/JS {% endcomment %}
<div id="map" class="h-64 w-full"></div>

<script>
    // Get the group's location from the Django context
    const groupLat = {{ group.location.y }}; // GeoDjango PointField y-coordinate is latitude
    const groupLon = {{ group.location.x }}; // GeoDjango PointField x-coordinate is longitude
    const radius = {{ group.radius }};

    // Initialize Leaflet map
    const map = L.map('map').setView([groupLat, groupLon], 16);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="[https://www.openstreetmap.org/copyright](https://www.openstreetmap.org/copyright)">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Show the attendance zone
    L.circle([groupLat, groupLon], {
        color: 'blue',
        fillColor: '#3498db',
        fillOpacity: 0.4,
        radius: radius
    }).addTo(map).bindPopup("Valid check-in area.");
</script>

5. Performance Optimization
For a SaaS platform, performance is a feature.

Database Queries:

Use select_related for foreign key relationships (one-to-one, many-to-one).

Example: CheckIn.objects.select_related('employee__company').get(id=1)

Use prefetch_related for many-to-many or reverse foreign key relationships.

Example: Company.objects.prefetch_related('branches__departments').get(id=1)

GeoDjango: Use spatial indexes on PointField columns in PostgreSQL. This makes distance-based lookups (e.g., "Is this employee within 100m of the office?") incredibly fast.

# Example: Find all groups within 5km of a user's current location
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

user_location = Point(longitude, latitude, srid=4326)
nearby_groups = AttendanceGroup.objects.filter(location__distance_lte=(user_location, D(km=5)))


Asynchronous Tasks: Use Celery with Redis for tasks that shouldn't block the user, such as sending end-of-day attendance summary emails or generating large reports.

6. Dependencies & Key Conventions
Core Dependencies
django

psycopg2-binary: For PostgreSQL, which is required for GeoDjango.

gunicorn: For production deployment.

djangorestframework: For building APIs if needed.

django-leaflet: Simplifies integrating Leaflet maps.

Key Conventions
Convention Over Configuration: Stick to Django's way of doing things. Don't reinvent the wheel.

Security First: Use Django's built-in CSRF protection, parameterize all queries (the ORM does this by default), and escape all user-generated content in templates.

Test Everything: Write unit and integration tests for models, business logic, and view permissions. Use pytest-django.

Environment Variables: Never hardcode secrets like SECRET_KEY or database passwords. Use a .env file and a library like django-environ.