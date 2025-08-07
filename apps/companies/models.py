from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator


class Company(models.Model):
    """
    Main company model for multi-tenant SaaS platform.
    Each company is a separate tenant with its own data isolation.
    """
    name = models.CharField(
        max_length=255,
        help_text="Company name"
    )
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='owned_company',
        help_text="Company owner/primary administrator"
    )
    description = models.TextField(
        blank=True,
        help_text="Company description or about information"
    )
    website = models.URLField(
        blank=True,
        help_text="Company website URL"
    )
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        help_text="Company contact phone number"
    )
    email = models.EmailField(
        blank=True,
        help_text="Company contact email"
    )
    address = models.TextField(
        blank=True,
        help_text="Company headquarters address"
    )
    logo = models.ImageField(
        upload_to='company_logos/',
        blank=True,
        null=True,
        help_text="Company logo image"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this company account is active"
    )
    subscription_plan = models.CharField(
        max_length=50,
        default='basic',
        help_text="Current subscription plan"
    )
    max_employees = models.PositiveIntegerField(
        default=50,
        help_text="Maximum number of employees allowed"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'companies_company'
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def employee_count(self):
        """Get current number of employees in this company"""
        return self.employees.count()
    
    @property
    def can_add_employee(self):
        """Check if company can add more employees based on subscription"""
        return self.employee_count < self.max_employees
    
    def get_branches_count(self):
        """Get total number of branches for this company"""
        return self.branches.count()
    
    def get_departments_count(self):
        """Get total number of departments across all branches"""
        return sum(branch.departments.count() for branch in self.branches.all())


class Branch(models.Model):
    """
    Branch model representing physical locations of a company.
    Each branch can have multiple departments and attendance groups.
    """
    name = models.CharField(
        max_length=255,
        help_text="Branch name or identifier"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='branches',
        help_text="Company this branch belongs to"
    )
    code = models.CharField(
        max_length=20,
        help_text="Unique branch code within the company"
    )
    address = models.TextField(
        help_text="Branch physical address"
    )
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        help_text="Branch contact phone number"
    )
    email = models.EmailField(
        blank=True,
        help_text="Branch contact email"
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_branches',
        help_text="Branch manager"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this branch is active"
    )
    # Geographic coordinates for location-based features
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Branch latitude coordinate"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Branch longitude coordinate"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'companies_branch'
        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'
        ordering = ['company', 'name']
        # Ensure unique branch codes within each company
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'code'],
                name='unique_branch_code_per_company'
            )
        ]
    
    def __str__(self):
        return f"{self.company.name} - {self.name}"
    
    @property
    def employee_count(self):
        """Get number of employees in this branch's departments"""
        return sum(dept.employees.count() for dept in self.departments.all())
    
    @property
    def has_coordinates(self):
        """Check if branch has geographic coordinates set"""
        return self.latitude is not None and self.longitude is not None


class Department(models.Model):
    """
    Department model representing organizational units within branches.
    Employees are assigned to departments for better organization.
    """
    name = models.CharField(
        max_length=255,
        help_text="Department name"
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='departments',
        help_text="Branch this department belongs to"
    )
    code = models.CharField(
        max_length=20,
        help_text="Unique department code within the branch"
    )
    description = models.TextField(
        blank=True,
        help_text="Department description or responsibilities"
    )
    head = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments',
        help_text="Department head/manager"
    )
    # Many-to-many relationship with employees
    employees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='DepartmentMembership',
        related_name='departments',
        blank=True,
        help_text="Employees in this department"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this department is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'companies_department'
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        ordering = ['branch', 'name']
        # Ensure unique department codes within each branch
        constraints = [
            models.UniqueConstraint(
                fields=['branch', 'code'],
                name='unique_department_code_per_branch'
            )
        ]
    
    def __str__(self):
        return f"{self.branch.company.name} - {self.branch.name} - {self.name}"
    
    @property
    def company(self):
        """Get the company this department belongs to"""
        return self.branch.company
    
    @property
    def active_employee_count(self):
        """Get number of active employees in this department"""
        return self.departmentmembership_set.filter(
            is_active=True,
            employee__is_active=True
        ).count()


class DepartmentMembership(models.Model):
    """
    Through model for Department-Employee many-to-many relationship.
    Allows tracking of employee roles within departments and membership history.
    """
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="Employee in the department"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        help_text="Department the employee belongs to"
    )
    position = models.CharField(
        max_length=100,
        blank=True,
        help_text="Employee's position/role in this department"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this membership is currently active"
    )
    joined_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the employee joined this department"
    )
    left_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the employee left this department"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'companies_departmentmembership'
        verbose_name = 'Department Membership'
        verbose_name_plural = 'Department Memberships'
        # Ensure one active membership per employee per department
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'department'],
                name='unique_active_membership',
                condition=models.Q(is_active=True)
            )
        ]
    
    def __str__(self):
        return f"{self.employee.username} in {self.department.name}"
    
    def deactivate(self):
        """Deactivate this membership and set left_at timestamp"""
        from django.utils import timezone
        self.is_active = False
        self.left_at = timezone.now()
        self.save()
