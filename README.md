# 🏢 SaaS Attendance Platform

A comprehensive multi-tenant Django-based attendance management system with location-based check-ins, role-based access control, geofencing, comprehensive reporting, and enterprise-grade features.

## 🚀 Live Demo
**Production URL**: [https://ramzihaidan537.pythonanywhere.com/](https://ramzihaidan537.pythonanywhere.com/)

### 🔐 Test Accounts
Use the **"Demo Accounts"** button on the login page to access pre-configured test accounts:
- **Super Admin**: `superadmin / admin123` - Full system access
- **Company Owners**: `owner1 / owner123`, `owner2 / owner123` - Company management
- **HR Managers**: `hr1_1 / hr123`, `hr2_1 / hr123` - Branch-level management
- **Employees**: `emp1_1 / emp123`, `emp2_1 / emp123` - Check-in/out only

## ✨ Key Features

### 🏢 Multi-Tenant SaaS Architecture
- **Complete Company Hierarchy**: Companies → Branches → Departments → Employees
- **Role-Based Access Control**: Super Admin, Company Owner, HR Manager, Employee
- **Data Isolation**: Strict tenant separation with branch-level restrictions
- **Scalable Design**: Support for unlimited companies and employees

### 👥 Advanced User Management
- **Custom User Model**: Extended Django user with role field and company assignment
- **Branch-Level HR Management**: HR managers restricted to their assigned branch
- **Employee-Department Assignment**: Flexible department membership with position tracking
- **User Authentication**: Custom login with role-based redirects

### 📍 Geofencing & Location Services
- **Interactive Maps**: Leaflet.js integration with OpenStreetMap
- **Attendance Groups**: Define check-in zones with customizable radius
- **Real-Time Location Validation**: GPS-based check-in/out with distance calculation
- **Multiple Locations**: Support for multiple attendance groups per branch

### 📊 Comprehensive Reporting & Analytics
- **Real-Time Dashboard**: Dynamic statistics and recent activity
- **Advanced Filtering**: Filter reports by date range, department, employee
- **Export Capabilities**: CSV export and print functionality
- **Attendance Trends**: Daily, weekly, monthly attendance patterns
- **Performance Metrics**: Employee attendance summaries and statistics

### 📱 Mobile-First Design
- **Responsive UI**: Tailwind CSS with mobile-optimized interfaces
- **Employee Mobile App**: Dedicated check-in/out interface for employees
- **Touch-Friendly**: Large buttons and intuitive navigation
- **Offline Support**: Graceful handling of connectivity issues

### 🔧 Enterprise Features
- **Work Periods & Schedules**: Flexible shift management with grace periods
- **Bulk Operations**: Mass employee management and assignments
- **Audit Trail**: Complete history of all system activities
- **Security**: Production-ready settings with HTTPS and CSRF protection

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

## 🚀 Quick Start - Local Development

### Prerequisites
- Python 3.10+ (recommended)
- Git
- Virtual environment tool

### 1. Clone & Setup
```bash
# Clone the repository
git clone <repository-url>
cd atten

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Database Setup
```bash
# Run migrations
python manage.py migrate

# Create superuser (optional - seeder includes test accounts)
python manage.py createsuperuser
```

### 4. 🎯 Load Complete Test Data (Recommended)
```bash
# Load comprehensive test data with 2 companies, branches, departments, and users
python manage.py seed_all --clear-all
```

**This creates:**
- 2 complete company structures (TechCorp Solutions, Global Innovations Inc)
- 4 branches with geographic coordinates
- 8 departments with HR manager assignments
- 8 attendance groups with realistic locations
- 16 work periods with schedules
- 27 users across all roles with proper assignments
- 1 month of realistic attendance data for testing reports

### 5. Start Development Server
```bash
python manage.py runserver
```

### 6. Access the Platform
- **Main Application**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Admin Interface**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

### 🔐 Test Accounts (After Running Seeder)

| Role | Username | Password | Access Level |
|------|----------|----------|--------------|
| **Super Admin** | `superadmin` | `admin123` | Full system access |
| **Company Owner** | `owner1` | `owner123` | TechCorp Solutions |
| **Company Owner** | `owner2` | `owner123` | Global Innovations Inc |
| **HR Manager** | `hr1_1` | `hr123` | TechCorp Main Branch |
| **HR Manager** | `hr2_1` | `hr123` | Global Innovations Main |
| **Employee** | `emp1_1` | `emp123` | TechCorp Employee |
| **Employee** | `emp2_1` | `emp123` | Global Innovations Employee |

### 🎨 What You'll See

**After login, different roles see different interfaces:**

- **Employees**: Mobile-first check-in/out interface with map
- **HR Managers**: Branch management dashboard with employee oversight
- **Company Owners**: Full company management with reporting
- **Super Admin**: System-wide access to all companies and features

### 📊 Testing Reports
The seeder includes 1 month of realistic attendance data, so you can immediately test:
- Daily attendance trends
- Employee performance reports
- Department-wise analytics
- Export and filtering features

## 🔧 Configuration & Deployment

### Environment Variables
Create a `.env` file (use `.env.example` as template):

```bash
# Security
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,localhost,127.0.0.1

# Database (optional - defaults to SQLite)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=attendance_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# CSRF Protection
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
```

### 🌐 Production Deployment (PythonAnywhere)

The project is production-ready with:
- ✅ **Environment-based configuration**
- ✅ **WhiteNoise for static files**
- ✅ **Console-only logging**
- ✅ **Security middleware**
- ✅ **WSGI configuration**

**Quick Deploy Steps:**
1. Upload code to PythonAnywhere
2. Create virtual environment and install requirements
3. Copy `pythonanywhere_wsgi.py` content to WSGI file
4. Run migrations and collect static files
5. Configure static files mapping
6. Reload web app

**Detailed deployment guide**: See `DEPLOYMENT.md` and `PRODUCTION_CHECKLIST.md`

### 📍 Location Services
- **Current**: Latitude/longitude fields with Haversine distance calculation
- **Future**: Full GeoDjango support with PostGIS for advanced spatial queries
- **Maps**: Leaflet.js with OpenStreetMap (no API keys required)

### 🗄️ Database Support
- **Development**: SQLite (included)
- **Production**: PostgreSQL recommended
- **Scaling**: Supports multiple database backends

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

## 📈 Recent Updates & Enhancements

### ✅ Latest Features (v2.0)
- **Comprehensive Reporting System**: Real-time analytics with filtering and export
- **Mobile-First Employee Interface**: Dedicated check-in/out UI for employees
- **Interactive Maps**: Leaflet.js integration with attendance zone visualization
- **Advanced User Management**: Branch-level HR restrictions and bulk operations
- **Production Deployment**: Full PythonAnywhere deployment with security hardening
- **Test Data Seeder**: Complete multi-company test environment with realistic data
- **Login Demo Modal**: Easy access to test accounts for demonstrations

### 🔄 Recent Fixes
- **AUTH_USER_MODEL Configuration**: Fixed custom user model integration
- **Console-Only Logging**: Resolved production logging issues
- **Role-Based Redirects**: Proper user routing based on roles
- **Static Files**: WhiteNoise integration for production
- **Security Headers**: HTTPS and CSRF protection

### 🚀 Future Enhancements

#### Planned Features
- **RESTful API**: Django REST Framework integration
- **Real-Time Updates**: WebSocket notifications for live attendance
- **Mobile Apps**: Native iOS/Android applications
- **Advanced Analytics**: Machine learning insights and predictions
- **Payroll Integration**: Automated timesheet generation
- **Multi-Language**: Internationalization support

#### Technical Roadmap
- **GeoDjango**: Full PostGIS integration for advanced spatial queries
- **Microservices**: Celery + Redis for background processing
- **Containerization**: Docker and Kubernetes deployment
- **CI/CD Pipeline**: Automated testing and deployment
- **Performance**: Caching and query optimization
- **Monitoring**: Application performance monitoring (APM)

## 🛠️ Development Commands

### Seeder Commands
```bash
# Complete system reset and seed
python manage.py seed_all --clear-all

# Individual seeders
python manage.py seed_users --clear
python manage.py seed_companies --clear
python manage.py seed_branches --clear
python manage.py seed_departments --clear
python manage.py seed_groups --clear
python manage.py seed_periods --clear
python manage.py seed_assignments --clear
python manage.py seed_checkins --clear
```

### Development Tools
```bash
# Run tests
python manage.py test

# Check deployment readiness
python manage.py check --deploy

# Collect static files
python manage.py collectstatic --noinput

# Database shell
python manage.py dbshell

# Django shell
python manage.py shell
```

### 📁 Project Structure
```
atten/
├── apps/
│   ├── core/           # Base models and utilities
│   ├── users/          # User management and authentication
│   ├── companies/      # Company hierarchy (Company, Branch, Department)
│   ├── attendance/     # Attendance groups, periods, check-ins
│   └── dashboard/      # Dashboard views and analytics
├── templates/          # HTML templates
├── static/            # CSS, JS, images
├── core/              # Django settings and configuration
├── requirements.txt   # Python dependencies
├── DEPLOYMENT.md      # Deployment guide
├── PRODUCTION_CHECKLIST.md  # Production checklist
└── pythonanywhere_wsgi.py   # WSGI configuration
```

## 🤝 Contributing

This project follows Django best practices and enterprise development standards:

### Development Guidelines
- **Code Style**: PEP 8 compliance with descriptive naming
- **Model Design**: Proper relationships with audit trails
- **Security**: Role-based access control and data validation
- **Performance**: Optimized queries with select_related/prefetch_related
- **Testing**: Comprehensive test coverage for all features

### Pull Request Process
1. Fork the repository
2. Create a feature branch
3. Run tests and ensure code quality
4. Submit pull request with detailed description

## 📄 License

This project is developed as a comprehensive SaaS attendance management solution following enterprise-grade development practices.

---

**Built with Django 5.2.5 | Tailwind CSS | Leaflet.js | Production-Ready**
