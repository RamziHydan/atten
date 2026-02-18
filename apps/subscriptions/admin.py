from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import SubscriptionPlan, CompanySubscription, PaymentMethod, Payment


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'plan_type', 'price', 'billing_cycle', 
        'max_employees', 'max_branches', 'is_active', 'is_featured'
    ]
    list_filter = ['plan_type', 'billing_cycle', 'is_active', 'is_featured']
    search_fields = ['name', 'description']
    ordering = ['sort_order', 'price']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'plan_type', 'description', 'price', 'billing_cycle')
        }),
        ('Limits', {
            'fields': ('max_employees', 'max_branches', 'max_attendance_groups')
        }),
        ('Features', {
            'fields': (
                'has_advanced_reporting', 'has_api_access', 'has_custom_branding',
                'has_priority_support', 'has_data_export'
            )
        }),
        ('Display Settings', {
            'fields': ('is_active', 'is_featured', 'sort_order')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('subscriptions')


@admin.register(CompanySubscription)
class CompanySubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'company', 'plan', 'status', 'start_date', 'end_date', 
        'days_remaining_display', 'auto_renew'
    ]
    list_filter = ['status', 'plan', 'auto_renew', 'start_date']
    search_fields = ['company__name', 'plan__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Subscription Details', {
            'fields': ('company', 'plan', 'status')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'trial_end_date', 'next_billing_date')
        }),
        ('Settings', {
            'fields': ('auto_renew',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def days_remaining_display(self, obj):
        days = obj.days_remaining
        if days is None:
            return "No expiry"
        elif days <= 0:
            return format_html('<span style="color: red;">Expired</span>')
        elif days <= 7:
            return format_html('<span style="color: orange;">{} days</span>', days)
        else:
            return f"{days} days"
    days_remaining_display.short_description = "Days Remaining"


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'payment_type', 'is_active', 'requires_approval', 'sort_order']
    list_filter = ['payment_type', 'is_active', 'requires_approval']
    search_fields = ['name', 'description']
    ordering = ['sort_order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'payment_type', 'description')
        }),
        ('Configuration', {
            'fields': ('config_fields', 'requires_approval')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'sort_order')
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'subscription_company', 'amount', 'payment_method', 
        'status', 'created_at', 'processed_by'
    ]
    list_filter = ['status', 'payment_method', 'created_at', 'processed_by']
    search_fields = [
        'subscription__company__name', 'reference_number', 
        'external_transaction_id', 'admin_notes'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('subscription', 'payment_method', 'amount', 'currency', 'status')
        }),
        ('Payment Details', {
            'fields': ('payment_details', 'reference_number', 'external_transaction_id')
        }),
        ('Admin Processing', {
            'fields': ('admin_notes', 'processed_by', 'processed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_payments', 'reject_payments']
    
    def subscription_company(self, obj):
        return obj.subscription.company.name
    subscription_company.short_description = "Company"
    
    def approve_payments(self, request, queryset):
        count = 0
        for payment in queryset.filter(status='PENDING'):
            payment.approve(admin_user=request.user)
            count += 1
        self.message_user(request, f"Approved {count} payments.")
    approve_payments.short_description = "Approve selected payments"
    
    def reject_payments(self, request, queryset):
        count = 0
        for payment in queryset.filter(status='PENDING'):
            payment.reject(admin_user=request.user, reason="Rejected by admin")
            count += 1
        self.message_user(request, f"Rejected {count} payments.")
    reject_payments.short_description = "Reject selected payments"
