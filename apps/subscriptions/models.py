from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class SubscriptionPlan(models.Model):
    """
    Subscription plans that can be configured from admin panel.
    Supports Free, Professional, and Enterprise tiers.
    """
    PLAN_TYPES = [
        ('FREE', 'Free'),
        ('PROFESSIONAL', 'Professional'),
        ('ENTERPRISE', 'Enterprise'),
    ]
    
    BILLING_CYCLES = [
        ('MONTHLY', 'Monthly'),
        ('YEARLY', 'Yearly'),
        ('LIFETIME', 'Lifetime'),
    ]
    
    name = models.CharField(max_length=100, help_text="Plan name (e.g., 'Professional Plan')")
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    description = models.TextField(help_text="Plan description and features")
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Price in USD (0.00 for free plan)"
    )
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLES, default='MONTHLY')
    
    # Feature limits
    max_employees = models.PositiveIntegerField(
        default=10,
        help_text="Maximum number of employees (0 = unlimited)"
    )
    max_branches = models.PositiveIntegerField(
        default=1,
        help_text="Maximum number of branches (0 = unlimited)"
    )
    max_attendance_groups = models.PositiveIntegerField(
        default=5,
        help_text="Maximum attendance groups (0 = unlimited)"
    )
    
    # Features
    has_advanced_reporting = models.BooleanField(default=False)
    has_api_access = models.BooleanField(default=False)
    has_custom_branding = models.BooleanField(default=False)
    has_priority_support = models.BooleanField(default=False)
    has_data_export = models.BooleanField(default=True)
    
    # Admin settings
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Show as recommended plan")
    sort_order = models.PositiveIntegerField(default=0, help_text="Display order")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['sort_order', 'price']
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'
    
    def __str__(self):
        return f"{self.name} - ${self.price}/{self.billing_cycle.lower()}"
    
    @property
    def is_free(self):
        return self.plan_type == 'FREE'
    
    @property
    def is_enterprise(self):
        return self.plan_type == 'ENTERPRISE'
    
    def get_feature_list(self):
        """Get list of features for this plan"""
        features = []
        
        if self.max_employees == 0:
            features.append("Unlimited employees")
        else:
            features.append(f"Up to {self.max_employees} employees")
            
        if self.max_branches == 0:
            features.append("Unlimited branches")
        else:
            features.append(f"Up to {self.max_branches} branches")
            
        if self.max_attendance_groups == 0:
            features.append("Unlimited attendance groups")
        else:
            features.append(f"Up to {self.max_attendance_groups} attendance groups")
        
        if self.has_advanced_reporting:
            features.append("Advanced reporting & analytics")
        if self.has_api_access:
            features.append("API access")
        if self.has_custom_branding:
            features.append("Custom branding")
        if self.has_priority_support:
            features.append("Priority support")
        if self.has_data_export:
            features.append("Data export")
            
        return features


class CompanySubscription(models.Model):
    """
    Company's current subscription to a plan.
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
        ('PENDING', 'Pending Payment'),
        ('TRIAL', 'Trial'),
    ]
    
    company = models.OneToOneField(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Subscription dates
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    trial_end_date = models.DateTimeField(null=True, blank=True)
    
    # Payment info
    auto_renew = models.BooleanField(default=True)
    next_billing_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Company Subscription'
        verbose_name_plural = 'Company Subscriptions'
    
    def __str__(self):
        return f"{self.company.name} - {self.plan.name} ({self.status})"
    
    @property
    def is_active(self):
        return self.status == 'ACTIVE' and (not self.end_date or self.end_date > timezone.now())
    
    @property
    def is_trial(self):
        return self.status == 'TRIAL' and self.trial_end_date and self.trial_end_date > timezone.now()
    
    @property
    def days_remaining(self):
        if self.end_date:
            delta = self.end_date - timezone.now()
            return max(0, delta.days)
        return None


class PaymentMethod(models.Model):
    """
    Flexible payment methods that can be configured from admin.
    """
    PAYMENT_TYPES = [
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CREDIT_CARD', 'Credit Card'),
        ('PAYPAL', 'PayPal'),
        ('CRYPTO', 'Cryptocurrency'),
        ('CHECK', 'Check'),
        ('CASH', 'Cash'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=100, help_text="Payment method name")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    description = models.TextField(blank=True, help_text="Instructions for this payment method")
    is_active = models.BooleanField(default=True)
    requires_approval = models.BooleanField(
        default=True, 
        help_text="Whether payments need manual approval"
    )
    
    # Configuration fields (JSON-like storage for flexibility)
    config_fields = models.JSONField(
        default=dict,
        blank=True,
        help_text="Configuration for required fields (e.g., account number, routing number)"
    )
    
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'
    
    def __str__(self):
        return self.name


class Payment(models.Model):
    """
    Payment records for subscriptions.
    Accepts any payment method without validation.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    subscription = models.ForeignKey(
        CompanySubscription,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT
    )
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Payment details (flexible JSON storage)
    payment_details = models.JSONField(
        default=dict,
        help_text="Payment details like account numbers, transaction IDs, etc."
    )
    
    # Admin fields
    admin_notes = models.TextField(blank=True, help_text="Internal notes for admins")
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_payments'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Reference fields
    reference_number = models.CharField(max_length=100, blank=True)
    external_transaction_id = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
    
    def __str__(self):
        return f"Payment #{self.id} - {self.subscription.company.name} - ${self.amount}"
    
    def approve(self, admin_user=None):
        """Approve this payment and activate subscription"""
        self.status = 'APPROVED'
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.save()
        
        # Activate or extend subscription
        subscription = self.subscription
        if subscription.status in ['PENDING', 'EXPIRED']:
            subscription.status = 'ACTIVE'
            subscription.save()
    
    def reject(self, admin_user=None, reason=""):
        """Reject this payment"""
        self.status = 'REJECTED'
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        if reason:
            self.admin_notes = reason
        self.save()
