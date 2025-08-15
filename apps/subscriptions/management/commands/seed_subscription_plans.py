from django.core.management.base import BaseCommand
from django.db import transaction
from apps.subscriptions.models import SubscriptionPlan, PaymentMethod


class Command(BaseCommand):
    help = 'Seed subscription plans and payment methods'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing subscription plans and payment methods before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing subscription plans and payment methods...'))
            SubscriptionPlan.objects.all().delete()
            PaymentMethod.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

        with transaction.atomic():
            # Create subscription plans
            plans = self.create_subscription_plans()
            
            # Create payment methods
            payment_methods = self.create_payment_methods()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created:\n'
                f'  - {len(plans)} subscription plans\n'
                f'  - {len(payment_methods)} payment methods'
            )
        )

    def create_subscription_plans(self):
        """Create the three main subscription plans"""
        plans = []

        # Free Plan
        free_plan = SubscriptionPlan.objects.create(
            name='Free Plan',
            plan_type='FREE',
            description='Perfect for small teams getting started with attendance tracking. Includes basic features to manage up to 10 employees.',
            price=0.00,
            billing_cycle='MONTHLY',
            max_employees=10,
            max_branches=1,
            max_attendance_groups=3,
            has_advanced_reporting=False,
            has_api_access=False,
            has_custom_branding=False,
            has_priority_support=False,
            has_data_export=True,
            is_active=True,
            is_featured=False,
            sort_order=1
        )
        plans.append(free_plan)
        self.stdout.write(f'Created plan: {free_plan.name}')

        # Professional Plan
        professional_plan = SubscriptionPlan.objects.create(
            name='Professional Plan',
            plan_type='PROFESSIONAL',
            description='Ideal for growing businesses. Advanced reporting, unlimited employees, and priority support to scale your attendance management.',
            price=29.99,
            billing_cycle='MONTHLY',
            max_employees=0,  # Unlimited
            max_branches=5,
            max_attendance_groups=0,  # Unlimited
            has_advanced_reporting=True,
            has_api_access=True,
            has_custom_branding=False,
            has_priority_support=True,
            has_data_export=True,
            is_active=True,
            is_featured=True,  # Most popular
            sort_order=2
        )
        plans.append(professional_plan)
        self.stdout.write(f'Created plan: {professional_plan.name}')

        # Enterprise Plan
        enterprise_plan = SubscriptionPlan.objects.create(
            name='Enterprise Plan',
            plan_type='ENTERPRISE',
            description='Complete solution for large organizations. Custom features, dedicated support, unlimited everything, and white-label branding.',
            price=0.00,  # Custom pricing
            billing_cycle='YEARLY',
            max_employees=0,  # Unlimited
            max_branches=0,  # Unlimited
            max_attendance_groups=0,  # Unlimited
            has_advanced_reporting=True,
            has_api_access=True,
            has_custom_branding=True,
            has_priority_support=True,
            has_data_export=True,
            is_active=True,
            is_featured=False,
            sort_order=3
        )
        plans.append(enterprise_plan)
        self.stdout.write(f'Created plan: {enterprise_plan.name}')

        return plans

    def create_payment_methods(self):
        """Create flexible payment methods"""
        payment_methods = []

        # Credit Card
        credit_card = PaymentMethod.objects.create(
            name='Credit Card',
            payment_type='CREDIT_CARD',
            description='Pay securely with your credit or debit card. Instant processing and automatic billing.',
            is_active=True,
            requires_approval=False,  # Instant processing
            config_fields={
                'required_fields': ['card_number', 'expiry', 'cvv', 'cardholder_name'],
                'validation': 'basic'
            },
            sort_order=1
        )
        payment_methods.append(credit_card)
        self.stdout.write(f'Created payment method: {credit_card.name}')

        # Bank Transfer
        bank_transfer = PaymentMethod.objects.create(
            name='Bank Transfer',
            payment_type='BANK_TRANSFER',
            description='Transfer funds directly from your bank account. Please allow 2-3 business days for processing.',
            is_active=True,
            requires_approval=True,  # Manual verification
            config_fields={
                'required_fields': ['bank_name', 'account_number', 'routing_number', 'account_holder'],
                'instructions': 'Please provide your bank details. We will verify the payment manually.'
            },
            sort_order=2
        )
        payment_methods.append(bank_transfer)
        self.stdout.write(f'Created payment method: {bank_transfer.name}')

        # PayPal
        paypal = PaymentMethod.objects.create(
            name='PayPal',
            payment_type='PAYPAL',
            description='Pay with your PayPal account. Quick and secure payment processing.',
            is_active=True,
            requires_approval=False,
            config_fields={
                'required_fields': ['paypal_email'],
                'redirect_url': 'https://paypal.com'
            },
            sort_order=3
        )
        payment_methods.append(paypal)
        self.stdout.write(f'Created payment method: {paypal.name}')

        # Cryptocurrency
        crypto = PaymentMethod.objects.create(
            name='Cryptocurrency',
            payment_type='CRYPTO',
            description='Pay with Bitcoin, Ethereum, or USDT. Provide transaction ID after payment.',
            is_active=True,
            requires_approval=True,  # Manual verification
            config_fields={
                'required_fields': ['crypto_type', 'wallet_address', 'transaction_id'],
                'supported_currencies': ['BTC', 'ETH', 'USDT']
            },
            sort_order=4
        )
        payment_methods.append(crypto)
        self.stdout.write(f'Created payment method: {crypto.name}')

        # Check/Money Order
        check = PaymentMethod.objects.create(
            name='Check / Money Order',
            payment_type='CHECK',
            description='Mail a check or money order. Please include your company name and subscription details.',
            is_active=True,
            requires_approval=True,
            config_fields={
                'required_fields': ['check_number', 'amount', 'date'],
                'mailing_address': '123 Business St, Suite 100, City, State 12345'
            },
            sort_order=5
        )
        payment_methods.append(check)
        self.stdout.write(f'Created payment method: {check.name}')

        # Other/Custom
        other = PaymentMethod.objects.create(
            name='Other Payment Method',
            payment_type='OTHER',
            description='Have a different payment method in mind? Contact us and we\'ll work with you.',
            is_active=True,
            requires_approval=True,
            config_fields={
                'required_fields': ['payment_details'],
                'contact_info': 'support@7hader.com'
            },
            sort_order=6
        )
        payment_methods.append(other)
        self.stdout.write(f'Created payment method: {other.name}')

        return payment_methods
