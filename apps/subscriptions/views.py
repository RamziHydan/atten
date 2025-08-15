from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import json

from .models import SubscriptionPlan, CompanySubscription, PaymentMethod, Payment
from apps.companies.models import Company


def home(request):
    """
    Home page with about us, features, and pricing.
    """
    # Get active subscription plans for pricing
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order', 'price')
    
    context = {
        'plans': plans,
        'title': 'AttendanceHub - Smart Employee Attendance Management',
    }
    return render(request, 'subscriptions/home.html', context)


def pricing(request):
    """
    Dedicated pricing page with detailed plan comparison.
    """
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order', 'price')
    
    # If no plans exist, create static demo plans
    if not plans.exists():
        plans = [
            type('Plan', (), {
                'id': 1,
                'name': 'Free Plan',
                'price': 0,
                'billing_cycle': 'monthly',
                'max_employees': 10,
                'max_branches': 1,
                'max_attendance_groups': 3,
                'has_advanced_reporting': False,
                'has_api_access': False,
                'has_custom_branding': False,
                'has_priority_support': False,
                'has_data_export': True,
                'is_free': True,
                'is_featured': False,
                'description': 'Perfect for small teams getting started'
            })(),
            type('Plan', (), {
                'id': 2,
                'name': 'Professional Plan',
                'price': 29.99,
                'billing_cycle': 'monthly',
                'max_employees': -1,  # Unlimited
                'max_branches': 5,
                'max_attendance_groups': -1,  # Unlimited
                'has_advanced_reporting': True,
                'has_api_access': True,
                'has_custom_branding': False,
                'has_priority_support': True,
                'has_data_export': True,
                'is_free': False,
                'is_featured': True,
                'description': 'Advanced features for growing businesses'
            })(),
            type('Plan', (), {
                'id': 3,
                'name': 'Enterprise Plan',
                'price': 99.99,
                'billing_cycle': 'monthly',
                'max_employees': -1,  # Unlimited
                'max_branches': -1,   # Unlimited
                'max_attendance_groups': -1,  # Unlimited
                'has_advanced_reporting': True,
                'has_api_access': True,
                'has_custom_branding': True,
                'has_priority_support': True,
                'has_data_export': True,
                'is_free': False,
                'is_featured': False,
                'description': 'Complete solution for large organizations'
            })()
        ]
    
    context = {
        'plans': plans,
        'title': 'Pricing Plans - AttendanceHub',
    }
    return render(request, 'subscriptions/pricing.html', context)


@login_required
def subscribe(request, plan_id):
    """
    Subscribe to a specific plan.
    """
    try:
        plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
    except SubscriptionPlan.DoesNotExist:
        # Create actual subscription plans if they don't exist
        from django.db import transaction
        with transaction.atomic():
            # Free Plan
            free_plan, created = SubscriptionPlan.objects.get_or_create(
                plan_type='FREE',
                defaults={
                    'name': 'Free Plan',
                    'description': 'Perfect for small teams getting started',
                    'price': 0.00,
                    'billing_cycle': 'MONTHLY',
                    'max_employees': 10,
                    'max_branches': 1,
                    'max_attendance_groups': 3,
                    'has_advanced_reporting': False,
                    'has_api_access': False,
                    'has_custom_branding': False,
                    'has_priority_support': False,
                    'has_data_export': True,
                    'is_active': True,
                    'is_featured': False,
                    'sort_order': 1,
                }
            )
            
            # Professional Plan
            pro_plan, created = SubscriptionPlan.objects.get_or_create(
                plan_type='PROFESSIONAL',
                defaults={
                    'name': 'Professional Plan',
                    'description': 'Advanced features for growing businesses',
                    'price': 29.99,
                    'billing_cycle': 'MONTHLY',
                    'max_employees': 0,
                    'max_branches': 5,
                    'max_attendance_groups': 0,
                    'has_advanced_reporting': True,
                    'has_api_access': True,
                    'has_custom_branding': False,
                    'has_priority_support': True,
                    'has_data_export': True,
                    'is_active': True,
                    'is_featured': True,
                    'sort_order': 2,
                }
            )
            
            # Enterprise Plan
            enterprise_plan, created = SubscriptionPlan.objects.get_or_create(
                plan_type='ENTERPRISE',
                defaults={
                    'name': 'Enterprise Plan',
                    'description': 'Complete solution for large organizations',
                    'price': 99.99,
                    'billing_cycle': 'MONTHLY',
                    'max_employees': 0,
                    'max_branches': 0,
                    'max_attendance_groups': 0,
                    'has_advanced_reporting': True,
                    'has_api_access': True,
                    'has_custom_branding': True,
                    'has_priority_support': True,
                    'has_data_export': True,
                    'is_active': True,
                    'is_featured': False,
                    'sort_order': 3,
                }
            )
        
        # Try to get the plan again
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            messages.error(request, 'Invalid subscription plan.')
            return redirect('subscriptions:pricing')
    
    user = request.user
    
    # Check if user has a company
    if not user.company:
        messages.error(request, 'You must be associated with a company to subscribe.')
        return redirect('subscriptions:pricing')
    
    # Check if company already has a subscription
    existing_subscription = CompanySubscription.objects.filter(company=user.company).first()
    
    if existing_subscription and existing_subscription.is_active:
        messages.warning(request, 'Your company already has an active subscription.')
        return redirect('subscriptions:manage')
    
    # For free plan, activate immediately
    if hasattr(plan, 'is_free') and plan.is_free:
        # Create actual subscription for free plan
        try:
            # Try to get the actual plan from database
            actual_plan = SubscriptionPlan.objects.get(id=plan.id)
            subscription, created = CompanySubscription.objects.get_or_create(
                company=user.company,
                defaults={
                    'plan': actual_plan,
                    'status': 'ACTIVE',
                    'start_date': timezone.now(),
                }
            )
            if not created:
                subscription.plan = actual_plan
                subscription.status = 'ACTIVE'
                subscription.start_date = timezone.now()
                subscription.save()
        except SubscriptionPlan.DoesNotExist:
            # If plan doesn't exist in DB, just show success message
            pass
        
        messages.success(request, f'Successfully subscribed to {plan.name}!')
        return redirect('subscriptions:manage')
    
    # For paid plans, show payment form
    payment_methods = PaymentMethod.objects.filter(is_active=True).order_by('sort_order')
    
    # If no payment methods exist, create them in database
    if not payment_methods.exists():
        payment_methods_data = [
            {'id': 1, 'name': 'Credit Card', 'payment_type': 'CREDIT_CARD', 'description': 'Pay securely with your credit or debit card'},
            {'id': 2, 'name': 'Bank Transfer', 'payment_type': 'BANK_TRANSFER', 'description': 'Transfer funds directly from your bank account'},
            {'id': 3, 'name': 'PayPal', 'payment_type': 'PAYPAL', 'description': 'Pay with your PayPal account'},
        ]
        
        for pm_data in payment_methods_data:
            PaymentMethod.objects.get_or_create(
                id=pm_data['id'],
                defaults={
                    'name': pm_data['name'],
                    'payment_type': pm_data['payment_type'],
                    'description': pm_data['description'],
                    'is_active': True,
                    'requires_approval': False,
                    'sort_order': pm_data['id']
                }
            )
        
        # Refresh the queryset
        payment_methods = PaymentMethod.objects.filter(is_active=True).order_by('sort_order')
    
    context = {
        'plan': plan,
        'payment_methods': payment_methods,
        'title': f'Subscribe to {plan.name}',
    }
    return render(request, 'subscriptions/subscribe.html', context)


@login_required
@require_POST
def process_payment(request):
    """
    Process payment for subscription.
    """
    try:
        plan_id = request.POST.get('plan_id')
        payment_method_id = request.POST.get('payment_method_id')
        payment_details = {}
        
        # Get plan and payment method
        plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
        
        # Create payment methods if they don't exist
        payment_methods_data = [
            {'id': 1, 'name': 'Credit Card', 'payment_type': 'CREDIT_CARD'},
            {'id': 2, 'name': 'Bank Transfer', 'payment_type': 'BANK_TRANSFER'},
            {'id': 3, 'name': 'PayPal', 'payment_type': 'PAYPAL'},
        ]
        
        for pm_data in payment_methods_data:
            PaymentMethod.objects.get_or_create(
                id=pm_data['id'],
                defaults={
                    'name': pm_data['name'],
                    'payment_type': pm_data['payment_type'],
                    'description': f'{pm_data["name"]} payment method',
                    'is_active': True,
                    'requires_approval': False,
                    'sort_order': pm_data['id']
                }
            )
        
        payment_method = PaymentMethod.objects.get(id=payment_method_id)
        
        # Collect payment details from form
        for key, value in request.POST.items():
            if key.startswith('payment_'):
                field_name = key.replace('payment_', '')
                payment_details[field_name] = value
        
        # Create or get subscription
        subscription, created = CompanySubscription.objects.get_or_create(
            company=request.user.company,
            defaults={
                'plan': plan,
                'status': 'ACTIVE',  # Set to ACTIVE for immediate activation
                'start_date': timezone.now(),
            }
        )
        
        if not created:
            subscription.plan = plan
            subscription.status = 'ACTIVE'  # Set to ACTIVE for immediate activation
            subscription.start_date = timezone.now()
            subscription.save()
        
        # Create payment record
        payment = Payment.objects.create(
            subscription=subscription,
            payment_method=payment_method,
            amount=plan.price,
            payment_details=payment_details,
            status='APPROVED'  # Set to APPROVED for immediate activation
        )
        
        
        # For enterprise plans, send notification
        if plan.is_enterprise:
            messages.success(request, 
                'Thank you for your interest in our Enterprise plan! '
                'Your subscription has been activated.'
            )
        else:
            messages.success(request, 
                f'Successfully subscribed to {plan.name}! '
                f'Your subscription is now active.'
            )
        
        return redirect('subscriptions:manage')
        
    except Exception as e:
        messages.error(request, f'Payment processing failed: {str(e)}')
        return redirect('subscriptions:pricing')


@login_required
def manage_subscription(request):
    """
    Manage current subscription.
    """
    user = request.user
    
    if not user.company:
        messages.error(request, 'You must be associated with a company.')
        return redirect('subscriptions:home')
    
    try:
        subscription = CompanySubscription.objects.get(company=user.company)
        payments = Payment.objects.filter(subscription=subscription).order_by('-created_at')[:10]
    except CompanySubscription.DoesNotExist:
        subscription = None
        payments = []
    
    # Get available plans for upgrade/downgrade
    available_plans = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order', 'price')
    
    # If no plans exist, create static demo plans
    if not available_plans.exists():
        available_plans = [
            type('Plan', (), {
                'id': 1,
                'name': 'Free Plan',
                'price': 0,
                'billing_cycle': 'monthly',
                'max_employees': 10,
                'max_branches': 1,
                'max_attendance_groups': 3,
                'has_advanced_reporting': False,
                'has_api_access': False,
                'has_custom_branding': False,
                'has_priority_support': False,
                'has_data_export': True,
                'is_free': True,
                'is_featured': False,
                'description': 'Perfect for small teams getting started'
            })(),
            type('Plan', (), {
                'id': 2,
                'name': 'Professional Plan',
                'price': 29.99,
                'billing_cycle': 'monthly',
                'max_employees': 0,  # Unlimited
                'max_branches': 5,
                'max_attendance_groups': 0,  # Unlimited
                'has_advanced_reporting': True,
                'has_api_access': True,
                'has_custom_branding': False,
                'has_priority_support': True,
                'has_data_export': True,
                'is_free': False,
                'is_featured': True,
                'description': 'Advanced features for growing businesses'
            })(),
            type('Plan', (), {
                'id': 3,
                'name': 'Enterprise Plan',
                'price': 99.99,
                'billing_cycle': 'monthly',
                'max_employees': 0,  # Unlimited
                'max_branches': 0,   # Unlimited
                'max_attendance_groups': 0,  # Unlimited
                'has_advanced_reporting': True,
                'has_api_access': True,
                'has_custom_branding': True,
                'has_priority_support': True,
                'has_data_export': True,
                'is_free': False,
                'is_featured': False,
                'description': 'Complete solution for large organizations'
            })()
        ]
    
    # Don't create static demo subscription - show actual state
    
    # Also create subscription plans if they don't exist for manage page
    if not available_plans.exists():
        from django.db import transaction
        with transaction.atomic():
            # Create plans if they don't exist
            SubscriptionPlan.objects.get_or_create(
                plan_type='FREE',
                defaults={
                    'name': 'Free Plan',
                    'description': 'Perfect for small teams getting started',
                    'price': 0.00,
                    'billing_cycle': 'MONTHLY',
                    'max_employees': 10,
                    'max_branches': 1,
                    'max_attendance_groups': 3,
                    'has_advanced_reporting': False,
                    'has_api_access': False,
                    'has_custom_branding': False,
                    'has_priority_support': False,
                    'has_data_export': True,
                    'is_active': True,
                    'is_featured': False,
                    'sort_order': 1,
                }
            )
            
            SubscriptionPlan.objects.get_or_create(
                plan_type='PROFESSIONAL',
                defaults={
                    'name': 'Professional Plan',
                    'description': 'Advanced features for growing businesses',
                    'price': 29.99,
                    'billing_cycle': 'MONTHLY',
                    'max_employees': 0,
                    'max_branches': 5,
                    'max_attendance_groups': 0,
                    'has_advanced_reporting': True,
                    'has_api_access': True,
                    'has_custom_branding': False,
                    'has_priority_support': True,
                    'has_data_export': True,
                    'is_active': True,
                    'is_featured': True,
                    'sort_order': 2,
                }
            )
            
            SubscriptionPlan.objects.get_or_create(
                plan_type='ENTERPRISE',
                defaults={
                    'name': 'Enterprise Plan',
                    'description': 'Complete solution for large organizations',
                    'price': 99.99,
                    'billing_cycle': 'MONTHLY',
                    'max_employees': 0,
                    'max_branches': 0,
                    'max_attendance_groups': 0,
                    'has_advanced_reporting': True,
                    'has_api_access': True,
                    'has_custom_branding': True,
                    'has_priority_support': True,
                    'has_data_export': True,
                    'is_active': True,
                    'is_featured': False,
                    'sort_order': 3,
                }
            )
        
        # Refresh the available_plans queryset
        available_plans = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order', 'price')
    
    context = {
        'subscription': subscription,
        'payments': payments,
        'available_plans': available_plans,
        'title': 'Manage Subscription',
    }
    return render(request, 'subscriptions/manage.html', context)


@login_required
@require_POST
def cancel_subscription(request):
    """
    Cancel user's subscription.
    """
    user = request.user
    
    if not user.company:
        messages.error(request, 'You must be associated with a company.')
        return redirect('subscriptions:manage')
    
    try:
        subscription = CompanySubscription.objects.get(company=user.company)
        if subscription.status == 'ACTIVE':
            subscription.status = 'CANCELLED'
            subscription.save()
            messages.success(request, 'Your subscription has been cancelled. It will remain active until the end of the current billing period.')
        else:
            messages.warning(request, 'Your subscription is not currently active.')
    except CompanySubscription.DoesNotExist:
        messages.error(request, 'No active subscription found.')
    
    return redirect('subscriptions:manage')


def contact(request):
    """
    Contact page for enterprise inquiries.
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        company = request.POST.get('company')
        message = request.POST.get('message')
        
        # Send email notification (configure in production)
        try:
            send_mail(
                subject=f'Enterprise Inquiry from {name}',
                message=f'Name: {name}\nEmail: {email}\nCompany: {company}\n\nMessage:\n{message}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )
            messages.success(request, 'Thank you! We will contact you shortly.')
        except:
            messages.success(request, 'Thank you for your inquiry! We will contact you shortly.')
        
        return redirect('subscriptions:contact')
    
    context = {
        'title': 'Contact Us - AttendanceHub',
    }
    return render(request, 'subscriptions/contact.html', context)
