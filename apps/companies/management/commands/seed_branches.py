from django.core.management.base import BaseCommand
from django.db import transaction
from apps.companies.models import Company, Branch
from faker import Faker

fake = Faker()

class Command(BaseCommand):
    help = 'Seed branches: 2 branches per company (4 total branches)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing branches before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing branches...'))
            Branch.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing branches cleared.'))

        # Check if we have the required companies
        companies = Company.objects.all().order_by('id')
        if companies.count() < 2:
            self.stdout.write(
                self.style.ERROR(
                    'Not enough companies found. Please run seed_companies first.'
                )
            )
            return

        with transaction.atomic():
            branches = self.create_branches(companies)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(branches)} branches:\n' +
                '\n'.join([f'  - {branch.name} ({branch.company.name})' 
                          for branch in branches])
            )
        )

    def create_branches(self, companies):
        """Create 2 branches per company (4 total branches)"""
        branches = []
        
        # Branch data for each company
        branch_templates = [
            # TechCorp Solutions branches
            [
                {
                    'name': 'TechCorp Headquarters',
                    'code': 'TC-HQ',
                    'address': '123 Tech Street, Silicon Valley, CA 94000',
                    'phone_number': '+15550111',
                    'email': 'hq@techcorp.com',
                    'latitude': 37.4419,
                    'longitude': -122.1430,
                    'radius': 150
                },
                {
                    'name': 'TechCorp R&D Center',
                    'code': 'TC-RD',
                    'address': '789 Innovation Drive, Silicon Valley, CA 94001',
                    'phone_number': '+15550112',
                    'email': 'rd@techcorp.com',
                    'latitude': 37.4519,
                    'longitude': -122.1530,
                    'radius': 200
                }
            ],
            # InnovateLab Inc branches
            [
                {
                    'name': 'InnovateLab Main Office',
                    'code': 'IL-MAIN',
                    'address': '456 Innovation Blvd, Austin, TX 78701',
                    'phone_number': '+15550221',
                    'email': 'main@innovatelab.com',
                    'latitude': 30.2672,
                    'longitude': -97.7431,
                    'radius': 100
                },
                {
                    'name': 'InnovateLab Lab Facility',
                    'code': 'IL-LAB',
                    'address': '321 Research Park, Austin, TX 78702',
                    'phone_number': '+15550222',
                    'email': 'lab@innovatelab.com',
                    'latitude': 30.2772,
                    'longitude': -97.7531,
                    'radius': 120
                }
            ]
        ]
        
        for company_idx, company in enumerate(companies):
            company_branches = branch_templates[company_idx]
            
            for branch_data in company_branches:
                branch = Branch.objects.create(
                    name=branch_data['name'],
                    company=company,
                    code=branch_data['code'],
                    address=branch_data['address'],
                    phone_number=branch_data['phone_number'],
                    email=branch_data['email'],
                    latitude=branch_data['latitude'],
                    longitude=branch_data['longitude'],
                    radius=branch_data['radius']
                )
                
                branches.append(branch)
                self.stdout.write(f'Created Branch: {branch.name} ({company.name})')
        
        return branches

    def get_branch_summary(self):
        """Display summary of created branches"""
        branches = Branch.objects.all()
        return {
            'total_branches': branches.count(),
            'branches_by_company': {
                company.name: [
                    {
                        'name': branch.name,
                        'address': branch.address,
                        'phone': branch.phone_number
                    }
                    for branch in company.branches.all()
                ]
                for company in Company.objects.all()
            }
        }
