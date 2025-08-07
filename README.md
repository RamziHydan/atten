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
- **Employee Assignment**: Assign employees to attendance groups and departments
- **Branch-Level Management**: HR managers restricted to their assigned branch

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

## Role-Based Access Control

The SaaS Attendance Platform implements a comprehensive role-based access control system with four distinct user roles, each with specific privileges and restrictions.

### 🔐 User Roles & Privileges

#### **Super Admin**
- **System-Wide Access**: Complete access to all companies, branches, and data
- **Company Management**: Create, edit, delete any company
- **User Management**: Manage all users across all companies
- **Attendance Groups**: Create, edit, delete attendance groups in any company
- **Employee Assignment**: Assign any employee to any attendance group
- **Reports & Analytics**: Access to system-wide reports and analytics
- **System Settings**: Configure global system settings and features

#### **Company Manager**
- **Company Scope**: Access limited to their own company and all its branches
- **Branch Management**: Create, edit, delete branches within their company
- **Department Management**: Manage all departments across all company branches
- **HR Manager Assignment**: Assign HR managers to specific branches
- **Employee Management**: Manage all employees within their company
- **Attendance Groups**: Create, edit, delete attendance groups within their company
- **Employee Assignment**: Assign any company employee to attendance groups
- **Work Periods**: Manage work schedules and periods for all company groups
- **Company Reports**: Access to company-wide attendance reports

#### **HR Employee (HR Manager)**
- **Branch Scope**: Access limited to their assigned branch only
- **Department Management**: Manage departments within their assigned branch
- **Employee Management**: 
  - View and manage employees in departments within their branch
  - Add new employees (restricted to their branch departments)
  - Edit employee information for branch employees
- **Attendance Groups**: 
  - Create, edit attendance groups within their assigned branch
  - Cannot access groups from other branches
- **Employee Assignment**: Assign branch employees to attendance groups
- **Work Periods**: Manage work schedules for groups in their branch
- **Branch Reports**: Access to branch-specific attendance reports

#### **Employee**
- **Personal Access**: Limited to their own attendance and profile data
- **Check-In/Check-Out**: Record attendance at assigned attendance groups
- **Attendance History**: View their own attendance records and summaries
- **Profile Management**: Update their own profile information
- **Schedule Viewing**: View their assigned work periods and schedules
- **No Administrative Access**: Cannot manage other users or system settings

### 🛡️ Security & Data Isolation

#### **Multi-Tenant Security**
- **Company Isolation**: Each company's data is completely isolated
- **Branch-Level Restrictions**: HR managers cannot access other branches
- **Department Filtering**: Users only see employees in their scope
- **Attendance Group Access**: Location-based restrictions by role

#### **Permission Enforcement**
- **View-Level Security**: All views check user permissions before displaying data
- **Object-Level Filtering**: Database queries filtered by user's access scope
- **Form Validation**: Server-side validation prevents unauthorized actions
- **API Security**: All API endpoints respect role-based restrictions

### 📋 Access Control Matrix

| Feature | Super Admin | Company Manager | HR Manager | Employee |
|---------|-------------|-----------------|------------|-----------|
| **Company Management** | ✅ All | ✅ Own Company | ❌ | ❌ |
| **Branch Management** | ✅ All | ✅ Company Branches | ❌ | ❌ |
| **Department Management** | ✅ All | ✅ Company Depts | ✅ Branch Depts | ❌ |
| **Employee Management** | ✅ All | ✅ Company Employees | ✅ Branch Employees | ✅ Own Profile |
| **Attendance Groups** | ✅ All | ✅ Company Groups | ✅ Branch Groups | ❌ |
| **Employee Assignment** | ✅ All | ✅ Company Scope | ✅ Branch Scope | ❌ |
| **Work Periods** | ✅ All | ✅ Company Periods | ✅ Branch Periods | ❌ |
| **Check-In/Out** | ✅ All | ✅ All | ✅ All | ✅ Own Only |
| **Reports** | ✅ System-Wide | ✅ Company Reports | ✅ Branch Reports | ✅ Personal Only |
| **User Invitations** | ✅ All | ✅ Company Users | ✅ Branch Users | ❌ |

### 🔧 Implementation Details

#### **Role Assignment**
- **Super Admin**: Assigned during system setup or by existing Super Admin
- **Company Manager**: Assigned when creating a company or by Super Admin
- **HR Manager**: Assigned by Company Manager with specific branch assignment
- **Employee**: Default role for new users, assigned to departments by managers

#### **Branch Assignment for HR Managers**
- HR Managers must be assigned to a specific branch
- This assignment determines their access scope
- Cannot be changed without Company Manager or Super Admin privileges
- All their actions are restricted to their assigned branch

#### **Data Filtering**
- **get_accessible_employees()**: Helper function filters employees by user's role
- **Branch-level queries**: HR managers see only their branch data
- **Company-level queries**: Company managers see all company data
- **System-level queries**: Super admins see all data

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
