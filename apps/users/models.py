from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class UserRole(models.TextChoices):
    SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
    COMPANY_MANAGER = 'COMPANY_MANAGER', 'Company Manager'
    HR_EMPLOYEE = 'HR_EMPLOYEE', 'HR Employee'
    EMPLOYEE = 'EMPLOYEE', 'Employee'


class CustomUser(AbstractUser):
    """
    Custom user model extending AbstractUser with role-based access control.
    Links users directly to companies for easier querying and data filtering.
    """
    role = models.CharField(
        max_length=20, 
        choices=UserRole.choices, 
        default=UserRole.EMPLOYEE,
        help_text="User's role within the system"
    )
    # Link a user directly to a company for easier querying
    company = models.ForeignKey(
        'companies.Company', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='employees',
        help_text="Company this user belongs to"
    )
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        help_text="User's contact phone number"
    )
    employee_id = models.CharField(
        max_length=50, 
        blank=True, 
        help_text="Company-specific employee identifier"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_customuser'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        # Ensure unique employee_id per company
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'employee_id'],
                name='unique_employee_id_per_company',
                condition=models.Q(employee_id__isnull=False) & ~models.Q(employee_id='')
            )
        ]
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_super_admin(self):
        return self.role == UserRole.SUPER_ADMIN
    
    @property
    def is_company_manager(self):
        return self.role == UserRole.COMPANY_MANAGER
    
    @property
    def is_hr_employee(self):
        return self.role == UserRole.HR_EMPLOYEE
    
    @property
    def can_manage_company(self):
        """Check if user can manage company-level operations"""
        return self.role in [UserRole.SUPER_ADMIN, UserRole.COMPANY_MANAGER]
    
    @property
    def can_manage_hr(self):
        """Check if user can manage HR operations"""
        return self.role in [UserRole.SUPER_ADMIN, UserRole.COMPANY_MANAGER, UserRole.HR_EMPLOYEE]


class UserProfile(models.Model):
    """
    Extended profile information for users.
    Separated from CustomUser to keep the user model lean.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    avatar = models.ImageField(
        upload_to='avatars/', 
        blank=True, 
        null=True,
        help_text="User's profile picture"
    )
    bio = models.TextField(
        blank=True, 
        help_text="Short biography or description"
    )
    date_of_birth = models.DateField(
        blank=True, 
        null=True,
        help_text="User's date of birth"
    )
    address = models.TextField(
        blank=True, 
        help_text="User's address"
    )
    emergency_contact_name = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Emergency contact person's name"
    )
    emergency_contact_phone = models.CharField(
        max_length=20, 
        blank=True,
        help_text="Emergency contact phone number"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_userprofile'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.username}'s Profile"


class UserInvitation(models.Model):
    """
    Model to handle user invitations to join companies.
    Allows company managers to invite users before they register.
    """
    class InvitationStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        EXPIRED = 'EXPIRED', 'Expired'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    email = models.EmailField(help_text="Email address of the invitee")
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations'
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.EMPLOYEE,
        help_text="Role to assign to the invited user"
    )
    status = models.CharField(
        max_length=10,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING
    )
    invitation_token = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique token for invitation verification"
    )
    expires_at = models.DateTimeField(
        help_text="When this invitation expires"
    )
    accepted_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the invitation was accepted"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_userinvitation'
        verbose_name = 'User Invitation'
        verbose_name_plural = 'User Invitations'
        # Prevent duplicate pending invitations for same email/company
        constraints = [
            models.UniqueConstraint(
                fields=['email', 'company'],
                name='unique_pending_invitation',
                condition=models.Q(status='PENDING')
            )
        ]
    
    def __str__(self):
        return f"Invitation to {self.email} for {self.company.name}"
    
    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def mark_as_accepted(self):
        from django.utils import timezone
        self.status = self.InvitationStatus.ACCEPTED
        self.accepted_at = timezone.now()
        self.save()
