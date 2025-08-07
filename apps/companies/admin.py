from django.contrib import admin
from django.utils.html import format_html
from .models import Company, Branch, Department, DepartmentMembership


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """
    Admin interface for Company model.
    """
    list_display = (
        'name', 'owner', 'subscription_plan', 'employee_count_display',
        'max_employees', 'is_active', 'created_at'
    )
    list_filter = ('subscription_plan', 'is_active', 'created_at')
    search_fields = ('name', 'owner__username', 'owner__email', 'email')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'owner', 'description', 'logo')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone_number', 'website', 'address')
        }),
        ('Subscription & Limits', {
            'fields': ('subscription_plan', 'max_employees', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def employee_count_display(self, obj):
        count = obj.employee_count
        max_count = obj.max_employees
        if count >= max_count:
            color = 'red'
        elif count >= max_count * 0.8:
            color = 'orange'
        else:
            color = 'green'
        return format_html(
            '<span style="color: {};">{}/{}</span>',
            color, count, max_count
        )
    employee_count_display.short_description = 'Employees'
    
    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related('owner')


class DepartmentInline(admin.TabularInline):
    """
    Inline admin for departments within branches.
    """
    model = Department
    extra = 0
    fields = ('name', 'code', 'head', 'is_active')
    readonly_fields = ('active_employee_count',)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    """
    Admin interface for Branch model.
    """
    list_display = (
        'name', 'company', 'code', 'manager', 
        'employee_count_display', 'has_coordinates', 'is_active'
    )
    list_filter = ('company', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'company__name', 'manager__username')
    ordering = ('company', 'name')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'company', 'code', 'manager')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone_number', 'address')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude'),
            'description': 'Geographic coordinates for location-based features'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    inlines = [DepartmentInline]
    
    def employee_count_display(self, obj):
        count = obj.employee_count
        return format_html('<strong>{}</strong>', count)
    employee_count_display.short_description = 'Employees'
    
    def has_coordinates(self, obj):
        return obj.has_coordinates
    has_coordinates.boolean = True
    has_coordinates.short_description = 'GPS Coordinates'
    
    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related('company', 'manager')


class DepartmentMembershipInline(admin.TabularInline):
    """
    Inline admin for department memberships.
    """
    model = DepartmentMembership
    extra = 0
    fields = ('employee', 'position', 'is_active', 'joined_at')
    readonly_fields = ('joined_at',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """
    Admin interface for Department model.
    """
    list_display = (
        'name', 'branch', 'get_company', 'code', 'head',
        'active_employee_count', 'is_active'
    )
    list_filter = ('branch__company', 'branch', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'branch__name', 'branch__company__name', 'head__username')
    ordering = ('branch__company', 'branch', 'name')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'branch', 'code', 'head')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    inlines = [DepartmentMembershipInline]
    
    def get_company(self, obj):
        return obj.company.name
    get_company.short_description = 'Company'
    get_company.admin_order_field = 'branch__company__name'
    
    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related(
            'branch', 'branch__company', 'head'
        )


@admin.register(DepartmentMembership)
class DepartmentMembershipAdmin(admin.ModelAdmin):
    """
    Admin interface for DepartmentMembership model.
    """
    list_display = (
        'employee', 'department', 'get_company', 'position',
        'is_active', 'joined_at', 'left_at'
    )
    list_filter = (
        'department__branch__company', 'department__branch', 
        'department', 'is_active', 'joined_at'
    )
    search_fields = (
        'employee__username', 'employee__first_name', 'employee__last_name',
        'department__name', 'position'
    )
    ordering = ('-joined_at',)
    
    fieldsets = (
        ('Membership Details', {
            'fields': ('employee', 'department', 'position')
        }),
        ('Status & Timing', {
            'fields': ('is_active', 'joined_at', 'left_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('joined_at', 'left_at', 'created_at', 'updated_at')
    
    def get_company(self, obj):
        return obj.department.company.name
    get_company.short_description = 'Company'
    get_company.admin_order_field = 'department__branch__company__name'
    
    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related(
            'employee', 'department', 'department__branch', 'department__branch__company'
        )
