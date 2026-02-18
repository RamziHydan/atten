from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.subscriptions.models import SubscriptionPlan, PaymentMethod
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create subscription plans and payment methods with static data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing subscription data...')
            SubscriptionPlan.objects.all().delete()
            PaymentMethod.objects.all().delete()

        # Create subscription plans
        self.stdout.write('Creating subscription plans...')
        
        # Free Plan
        free_plan, created = SubscriptionPlan.objects.get_or_create(
            plan_type='FREE',
            defaults={
                'name': 'Free Plan',
                'description': 'Perfect for small teams getting started with attendance tracking',
                'price': Decimal('0.00'),
                'billing_cycle': 'MONTHLY',
                'max_employees': 10,
                'max_branches': 1,
                'max_attendance_groups': 2,
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
        if created:
            self.stdout.write(f'✓ Created {free_plan.name}')

        # Professional Plan
        pro_plan, created = SubscriptionPlan.objects.get_or_create(
            plan_type='PROFESSIONAL',
            defaults={
                'name': 'Professional Plan',
                'description': 'Advanced features for growing businesses',
                'price': Decimal('29.99'),
                'billing_cycle': 'MONTHLY',
                'max_employees': 100,
                'max_branches': 5,
                'max_attendance_groups': 10,
                'has_advanced_reporting': True,
                'has_api_access': True,
                'has_custom_branding': False,
                'has_priority_support': False,
                'has_data_export': True,
                'is_active': True,
                'is_featured': True,
                'sort_order': 2,
            }
        )
        if created:
            self.stdout.write(f'✓ Created {pro_plan.name}')

        # Enterprise Plan
        enterprise_plan, created = SubscriptionPlan.objects.get_or_create(
            plan_type='ENTERPRISE',
            defaults={
                'name': 'Enterprise Plan',
                'description': 'Complete solution for large organizations',
                'price': Decimal('99.99'),
                'billing_cycle': 'MONTHLY',
                'max_employees': 0,  # Unlimited
                'max_branches': 0,   # Unlimited
                'max_attendance_groups': 0,  # Unlimited
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
        if created:
            self.stdout.write(f'✓ Created {enterprise_plan.name}')

        # Create payment methods
        self.stdout.write('Creating payment methods...')
        
        # Bank Transfer
        bank_transfer, created = PaymentMethod.objects.get_or_create(
            payment_type='BANK_TRANSFER',
            defaults={
                'name': 'Bank Transfer',
                'description': 'Transfer payment directly to our bank account',
                'is_active': True,
                'requires_approval': True,
                'config_fields': {
                    'account_holder': {'label': 'Account Holder Name', 'required': True},
                    'bank_name': {'label': 'Bank Name', 'required': True},
                    'reference': {'label': 'Transfer Reference', 'required': True}
                },
                'sort_order': 1,
            }
        )
        if created:
            self.stdout.write(f'✓ Created {bank_transfer.name}')

        # Credit Card
        credit_card, created = PaymentMethod.objects.get_or_create(
            payment_type='CREDIT_CARD',
            defaults={
                'name': 'Credit Card',
                'description': 'Pay securely with your credit or debit card',
                'is_active': True,
                'requires_approval': False,
                'config_fields': {
                    'card_number': {'label': 'Card Number', 'required': True},
                    'expiry': {'label': 'Expiry Date (MM/YY)', 'required': True},
                    'cvv': {'label': 'CVV', 'required': True},
                    'cardholder_name': {'label': 'Cardholder Name', 'required': True}
                },
                'sort_order': 2,
            }
        )
        if created:
            self.stdout.write(f'✓ Created {credit_card.name}')

        # PayPal
        paypal, created = PaymentMethod.objects.get_or_create(
            payment_type='PAYPAL',
            defaults={
                'name': 'PayPal',
                'description': 'Pay with your PayPal account',
                'is_active': True,
                'requires_approval': False,
                'config_fields': {
                    'paypal_email': {'label': 'PayPal Email', 'required': True},
                    'transaction_id': {'label': 'Transaction ID', 'required': False}
                },
                'sort_order': 3,
            }
        )
        if created:
            self.stdout.write(f'✓ Created {paypal.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully created subscription data!\n'
                f'Plans: {SubscriptionPlan.objects.count()}\n'
                f'Payment Methods: {PaymentMethod.objects.count()}'
            )
        )
