from django.contrib import admin
# from django.contrib.gis.admin import GISModelAdmin  # Temporarily disabled
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    AttendanceGroup, AttendanceGroupMembership, Period, 
    CheckIn, AttendanceSummary
)


class AttendanceGroupMembershipInline(admin.TabularInline):
    """
    Inline admin for attendance group memberships.
    """
    model = AttendanceGroupMembership
    extra = 0
    fields = ('employee', 'is_active', 'assigned_at')
    readonly_fields = ('assigned_at',)


class PeriodInline(admin.TabularInline):
    """
    Inline admin for periods within attendance groups.
    """
    model = Period
    extra = 0
    fields = ('name', 'start_time', 'end_time', 'weekdays', 'is_active')


@admin.register(AttendanceGroup)
class AttendanceGroupAdmin(admin.ModelAdmin):  # Using regular ModelAdmin temporarily
    """
    Admin interface for AttendanceGroup model.
    Uses GISModelAdmin for map-based location editing.
    """
    list_display = (
        'name', 'company', 'branch', 'radius', 
        'active_employee_count', 'is_active'
    )
    list_filter = ('company', 'branch', 'is_active', 'created_at')
    search_fields = ('name', 'company__name', 'branch__name')
    ordering = ('company', 'name')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'company', 'branch', 'description')
        }),
        ('Location Settings', {
            'fields': ('latitude', 'longitude', 'radius'),
            'description': 'Set the geographic location and check-in radius'
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
    inlines = [PeriodInline, AttendanceGroupMembershipInline]
    
    # GIS settings - temporarily disabled
    # default_zoom = 16
    # default_lat = 40.7128  # New York City
    # default_lon = -74.0060
    
    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related('company', 'branch')


@admin.register(AttendanceGroupMembership)
class AttendanceGroupMembershipAdmin(admin.ModelAdmin):
    """
    Admin interface for AttendanceGroupMembership model.
    """
    list_display = (
        'employee', 'attendance_group', 'get_company', 
        'is_active', 'assigned_at', 'removed_at'
    )
    list_filter = (
        'attendance_group__company', 'attendance_group', 
        'is_active', 'assigned_at'
    )
    search_fields = (
        'employee__username', 'employee__first_name', 'employee__last_name',
        'attendance_group__name'
    )
    ordering = ('-assigned_at',)
    
    fieldsets = (
        ('Membership Details', {
            'fields': ('employee', 'attendance_group')
        }),
        ('Status & Timing', {
            'fields': ('is_active', 'assigned_at', 'removed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('assigned_at', 'removed_at', 'created_at', 'updated_at')
    
    def get_company(self, obj):
        return obj.attendance_group.company.name
    get_company.short_description = 'Company'
    get_company.admin_order_field = 'attendance_group__company__name'
    
    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related(
            'employee', 'attendance_group', 'attendance_group__company'
        )


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    """
    Admin interface for Period model.
    """
    list_display = (
        'name', 'group', 'get_company', 'start_time', 'end_time',
        'weekday_names_display', 'is_active'
    )
    list_filter = ('group__company', 'group', 'is_active', 'created_at')
    search_fields = ('name', 'group__name', 'group__company__name')
    ordering = ('group', 'start_time')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'group')
        }),
        ('Schedule', {
            'fields': ('start_time', 'end_time', 'weekdays'),
            'description': 'Weekdays format: 1=Monday, 2=Tuesday, etc. Use comma-separated values like "1,2,3,4,5" for Mon-Fri'
        }),
        ('Grace Periods', {
            'fields': ('late_checkin_grace_minutes', 'early_checkout_grace_minutes')
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
    
    def get_company(self, obj):
        return obj.group.company.name
    get_company.short_description = 'Company'
    get_company.admin_order_field = 'group__company__name'
    
    def weekday_names_display(self, obj):
        return ', '.join(obj.weekday_names)
    weekday_names_display.short_description = 'Weekdays'
    
    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related(
            'group', 'group__company'
        )


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):  # Using regular ModelAdmin temporarily
    """
    Admin interface for CheckIn model.
    Uses GISModelAdmin for map-based location viewing.
    """
    list_display = (
        'employee', 'attendance_group', 'type', 'status',
        'timestamp', 'distance_display', 'is_valid'
    )
    list_filter = (
        'attendance_group__company', 'attendance_group', 'type', 
        'status', 'timestamp'
    )
    search_fields = (
        'employee__username', 'employee__first_name', 'employee__last_name',
        'attendance_group__name'
    )
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('Check-in Details', {
            'fields': ('employee', 'attendance_group', 'period', 'type')
        }),
        ('Location & Validation', {
            'fields': ('latitude', 'longitude', 'distance_from_location', 'status')
        }),
        ('Additional Information', {
            'fields': ('notes', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('timestamp', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = (
        'distance_from_location', 'timestamp', 'created_at', 'updated_at'
    )
    
    # GIS settings - temporarily disabled
    # default_zoom = 18
    
    def distance_display(self, obj):
        if obj.distance_from_location is not None:
            distance = round(obj.distance_from_location, 1)
            if distance <= obj.attendance_group.radius:
                color = 'green'
            else:
                color = 'red'
            return format_html(
                '<span style="color: {};">{} m</span>',
                color, distance
            )
        return '-'
    distance_display.short_description = 'Distance'
    
    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related(
            'employee', 'attendance_group', 'attendance_group__company', 'period'
        )


@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(admin.ModelAdmin):
    """
    Admin interface for AttendanceSummary model.
    """
    list_display = (
        'employee', 'attendance_group', 'date', 'total_hours',
        'total_checkins', 'is_present', 'is_late'
    )
    list_filter = (
        'attendance_group__company', 'attendance_group', 
        'date', 'is_present', 'is_late'
    )
    search_fields = (
        'employee__username', 'employee__first_name', 'employee__last_name',
        'attendance_group__name'
    )
    ordering = ('-date', 'employee')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Summary Details', {
            'fields': ('employee', 'attendance_group', 'date')
        }),
        ('Check-in Records', {
            'fields': ('first_checkin', 'last_checkout', 'total_checkins')
        }),
        ('Summary Statistics', {
            'fields': ('total_hours', 'is_present', 'is_late')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related(
            'employee', 'attendance_group', 'attendance_group__company',
            'first_checkin', 'last_checkout'
        )
