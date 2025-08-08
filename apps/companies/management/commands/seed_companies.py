from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.companies.models import Company
from faker import Faker

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Seed companies: 2 companies with their respective owners'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing companies before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing companies...'))
            Company.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing companies cleared.'))

        # Check if we have the required owners
        owners = User.objects.filter(role='COMPANY_MANAGER').order_by('id')
        if owners.count() < 2:
            self.stdout.write(
                self.style.ERROR(
                    'Not enough company owners found. Please run seed_users first.'
                )
            )
            return

        with transaction.atomic():
            companies = self.create_companies(owners)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(companies)} companies:\n' +
                '\n'.join([f'  - {company.name} (Owner: {company.owner.get_full_name()})' 
                          for company in companies])
            )
        )

    def create_companies(self, owners):
        """Create 2 companies with their respective owners"""
        companies = []
        
        company_data = [
            {
                'name': 'TechCorp Solutions',
                'description': 'Leading technology solutions provider specializing in enterprise software development and digital transformation.',
                'website': 'https://techcorp.com',
                'phone_number': '+15550101',
                'email': 'contact@techcorp.com',
                'address': '123 Tech Street, Silicon Valley, CA 94000',
                'subscription_plan': 'premium',
                'max_employees': 100,
                'default_radius': 150
            },
            {
                'name': 'InnovateLab Inc',
                'description': 'Innovation-driven company focused on research and development of cutting-edge products and services.',
                'website': 'https://innovatelab.com',
                'phone_number': '+15550202',
                'email': 'hello@innovatelab.com',
                'address': '456 Innovation Blvd, Austin, TX 78701',
                'subscription_plan': 'basic',
                'max_employees': 50,
                'default_radius': 100
            }
        ]
        
        for i, data in enumerate(company_data):
            company = Company.objects.create(
                name=data['name'],
                description=data['description'],
                website=data['website'],
                phone_number=data['phone_number'],
                email=data['email'],
                address=data['address'],
                subscription_plan=data['subscription_plan'],
                max_employees=data['max_employees'],
                default_radius=data['default_radius'],
                owner=owners[i]
            )
            
            # Update the owner's company field
            owner = owners[i]
            owner.company = company
            owner.save()
            
            companies.append(company)
            self.stdout.write(f'Created Company: {company.name} (Owner: {owner.get_full_name()})')
        
        return companies

    def get_company_summary(self):
        """Display summary of created companies"""
        companies = Company.objects.all()
        return {
            'total_companies': companies.count(),
            'companies': [
                {
                    'name': company.name,
                    'owner': company.owner.get_full_name(),
                    'industry': company.industry
                }
                for company in companies
            ]
        }
