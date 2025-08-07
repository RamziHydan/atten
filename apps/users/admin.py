from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser, UserProfile, UserInvitation


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Custom admin interface for CustomUser model.
    Extends Django's built-in UserAdmin with our custom fields.
    """
    list_display = (
        'username', 'email', 'first_name', 'last_name', 
        'role', 'company', 'employee_id', 'is_active', 'date_joined'
    )
    list_filter = (
        'role', 'company', 'is_active', 'is_staff', 'is_superuser', 'date_joined'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name', 'employee_id')
    ordering = ('-date_joined',)
    
    # Add our custom fields to the user form
    fieldsets = UserAdmin.fieldsets + (
        ('Company Information', {
            'fields': ('role', 'company', 'employee_id', 'phone_number')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        """Optimize queries by selecting related company"""
        return super().get_queryset(request).select_related('company')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for UserProfile model.
    """
    list_display = (
        'user', 'get_user_email', 'get_user_company', 
        'date_of_birth', 'emergency_contact_name', 'created_at'
    )
    list_filter = ('user__company', 'created_at')
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'emergency_contact_name', 'emergency_contact_phone'
    )
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'avatar', 'bio')
        }),
        ('Personal Details', {
            'fields': ('date_of_birth', 'address')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'
    get_user_email.admin_order_field = 'user__email'
    
    def get_user_company(self, obj):
        return obj.user.company.name if obj.user.company else 'No Company'
    get_user_company.short_description = 'Company'
    get_user_company.admin_order_field = 'user__company__name'
    
    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related('user', 'user__company')


@admin.register(UserInvitation)
class UserInvitationAdmin(admin.ModelAdmin):
    """
    Admin interface for UserInvitation model.
    """
    list_display = (
        'email', 'company', 'role', 'status', 
        'invited_by', 'expires_at', 'created_at'
    )
    list_filter = ('status', 'role', 'company', 'created_at', 'expires_at')
    search_fields = ('email', 'company__name', 'invited_by__username')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Invitation Details', {
            'fields': ('email', 'company', 'invited_by', 'role')
        }),
        ('Status & Timing', {
            'fields': ('status', 'expires_at', 'accepted_at')
        }),
        ('Security', {
            'fields': ('invitation_token',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('invitation_token', 'accepted_at', 'created_at', 'updated_at')
    
    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related('company', 'invited_by')
    
    def has_add_permission(self, request):
        """Only allow adding invitations through the application logic"""
        return False
