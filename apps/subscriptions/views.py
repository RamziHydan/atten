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
    plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
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
    if plan.is_free:
        subscription, created = CompanySubscription.objects.get_or_create(
            company=user.company,
            defaults={
                'plan': plan,
                'status': 'ACTIVE',
                'start_date': timezone.now(),
            }
        )
        if not created:
            subscription.plan = plan
            subscription.status = 'ACTIVE'
            subscription.start_date = timezone.now()
            subscription.save()
        
        messages.success(request, f'Successfully subscribed to {plan.name}!')
        return redirect('dashboard:dashboard')
    
    # For paid plans, show payment form
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
        payment_method = get_object_or_404(PaymentMethod, id=payment_method_id, is_active=True)
        
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
                'status': 'PENDING',
                'start_date': timezone.now(),
            }
        )
        
        if not created:
            subscription.plan = plan
            subscription.status = 'PENDING'
            subscription.save()
        
        # Create payment record
        payment = Payment.objects.create(
            subscription=subscription,
            payment_method=payment_method,
            amount=plan.price,
            payment_details=payment_details,
            status='PENDING'
        )
        
        # For enterprise plans, send notification
        if plan.is_enterprise:
            messages.success(request, 
                'Thank you for your interest in our Enterprise plan! '
                'Our team will contact you shortly to discuss your requirements.'
            )
        else:
            messages.success(request, 
                f'Payment submitted successfully! Your subscription will be activated '
                f'once payment is verified. Reference: #{payment.id}'
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
    
    context = {
        'subscription': subscription,
        'payments': payments,
        'available_plans': available_plans,
        'title': 'Manage Subscription',
    }
    return render(request, 'subscriptions/manage.html', context)


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
