# SaaS Attendance Platform

A multi-tenant Django-based attendance management system with location-based check-ins, role-based access control, and comprehensive company hierarchy management.

## Features

### 🏢 Multi-Tenant Architecture
- **Company Management**: Complete company hierarchy with branches and departments
- **User Roles**: Super Admin, Company Manager, HR Employee, and Employee roles
- **Data Isolation**: Each company's data is completely isolated from others
- **Subscription Management**: Built-in subscription plans and employee limits

### 👥 User Management
- **Custom User Model**: Extended Django user with role-based permissions
- **User Profiles**: Extended profile information with emergency contacts
- **User Invitations**: Email-based invitation system for new employees
- **Role-Based Access**: Granular permissions based on user roles

### 📍 Location-Based Attendance
- **Attendance Groups**: Define check-in locations with radius validation
- **Geographic Validation**: Haversine formula for distance calculation
- **Flexible Schedules**: Multiple periods/shifts per attendance group
- **Grace Periods**: Configurable late check-in and early check-out allowances

### 📊 Comprehensive Tracking
- **Check-In/Check-Out**: Detailed attendance records with location validation
- **Daily Summaries**: Automated daily attendance summaries
- **Status Tracking**: On-time, late, early, and invalid location status
- **Audit Trail**: Complete history of all attendance activities

## Project Structure

```
attendance_saas/
├── apps/
│   ├── companies/      # Company hierarchy management
│   │   ├── models.py   # Company, Branch, Department, DepartmentMembership
│   │   ├── admin.py    # Admin interfaces with optimized queries
│   │   └── apps.py     # App configuration
│   ├── users/          # User management and authentication
│   │   ├── models.py   # CustomUser, UserProfile, UserInvitation
│   │   ├── admin.py    # User admin with role-based filtering
│   │   └── apps.py     # App configuration
│   └── attendance/     # Core attendance functionality
│       ├── models.py   # AttendanceGroup, Period, CheckIn, AttendanceSummary
│       ├── admin.py    # Location-aware admin interfaces
│       └── apps.py     # App configuration
├── core/
│   ├── settings.py     # Django settings with logging and security
│   ├── urls.py         # URL configuration
│   └── wsgi.py         # WSGI configuration
├── static/             # Static files directory
├── logs/               # Application logs
├── requirements.txt    # Python dependencies
├── .gitignore         # Git ignore rules
└── manage.py          # Django management script
```

## Models Overview

### Users App
- **CustomUser**: Extended user model with roles and company association
- **UserProfile**: Additional profile information and emergency contacts
- **UserInvitation**: Email-based invitation system with token validation

### Companies App
- **Company**: Multi-tenant company model with subscription management
- **Branch**: Physical locations with geographic coordinates
- **Department**: Organizational units within branches
- **DepartmentMembership**: Employee-department relationships with history

### Attendance App
- **AttendanceGroup**: Location-based attendance zones with radius validation
- **Period**: Work schedules/shifts with weekday and time configuration
- **CheckIn**: Individual attendance records with location validation
- **AttendanceSummary**: Daily attendance summaries for quick reporting

## Key Features Implemented

### 🔐 Security & Permissions
- Role-based access control with property methods for permission checking
- Data filtering at the queryset level to ensure tenant isolation
- Unique constraints to prevent data inconsistencies
- Audit trails with created_at and updated_at timestamps

### 📱 Location Services
- Haversine formula for accurate distance calculations
- Configurable radius validation for check-in locations
- Support for multiple attendance groups per company
- Distance tracking and validation status

### 🎯 Performance Optimizations
- Optimized database queries with select_related and prefetch_related
- Database indexes on frequently queried fields
- Efficient admin interfaces with custom querysets
- Proper foreign key relationships to minimize N+1 queries

### 🛠 Admin Interface
- Comprehensive admin interfaces for all models
- Custom display methods with color-coded status indicators
- Inline editing for related models
- Advanced filtering and search capabilities

## Installation & Setup

1. **Clone the repository**
   ```bash
   cd c:\Users\Haidan\Desktop\attendance\atten
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start development server**
   ```bash
   python manage.py runserver
   ```

7. **Access admin interface**
   - Navigate to `http://127.0.0.1:8000/admin/`
   - Login with your superuser credentials

## Configuration Notes

### GeoDjango Support
Currently using latitude/longitude fields for location storage. To enable full GeoDjango support:

1. Install GDAL library for your operating system
2. Uncomment GeoDjango settings in `settings.py`
3. Update attendance models to use `PointField`
4. Run new migrations

### Database Configuration
- Development: SQLite (current setup)
- Production: PostgreSQL with PostGIS recommended for GeoDjango

### Environment Variables
For production deployment, use environment variables for:
- `SECRET_KEY`
- Database credentials
- Email configuration
- Static/media file storage

## Development Guidelines

### Model Design
- All models include `created_at` and `updated_at` timestamps
- Proper foreign key relationships with appropriate `on_delete` behavior
- Unique constraints to maintain data integrity
- Descriptive help text for all fields

### Admin Interfaces
- Optimized querysets with `select_related` and `prefetch_related`
- Custom display methods for better user experience
- Proper filtering and search functionality
- Inline editing for related models

### Security Best Practices
- Role-based access control at the view level
- Data filtering at the queryset level
- CSRF protection enabled
- Proper validation on all user inputs

## Future Enhancements

### Planned Features
- RESTful API with Django REST Framework
- Real-time notifications with WebSockets
- Mobile app integration
- Advanced reporting and analytics
- Bulk operations for HR management
- Integration with payroll systems

### Technical Improvements
- Full GeoDjango implementation with PostGIS
- Celery for background task processing
- Redis for caching and session storage
- Docker containerization
- CI/CD pipeline setup

## Contributing

This project follows Django best practices and the development guidelines specified in the project documentation. All contributions should maintain the established patterns for:

- Model design and relationships
- Admin interface optimization
- Security and permissions
- Code organization and documentation

## License

This project is developed as a comprehensive SaaS attendance management solution following enterprise-grade development practices.
