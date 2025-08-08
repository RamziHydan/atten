from django.core.management.base import BaseCommand
from django.db import transaction
from apps.companies.models import Company, Branch
from apps.attendance.models import AttendanceGroup
from faker import Faker
import random

fake = Faker()

class Command(BaseCommand):
    help = 'Seed attendance groups: 2 groups per branch (8 total groups)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing attendance groups before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing attendance groups...'))
            AttendanceGroup.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing attendance groups cleared.'))

        # Check if we have the required branches
        branches = Branch.objects.all().order_by('company_id', 'id')
        if branches.count() < 4:
            self.stdout.write(
                self.style.ERROR(
                    'Not enough branches found. Please run seed_branches first.'
                )
            )
            return

        with transaction.atomic():
            groups = self.create_attendance_groups(branches)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(groups)} attendance groups:\n' +
                '\n'.join([f'  - {group.name} ({group.company.name} - {group.branch.name})' 
                          for group in groups])
            )
        )

    def create_attendance_groups(self, branches):
        """Create 2 attendance groups per branch (8 total groups)"""
        groups = []
        
        # Group templates for each branch
        group_templates = [
            # TechCorp Headquarters groups
            [
                {
                    'name': 'Main Office Floor 1',
                    'description': 'Ground floor office space for general staff',
                    'latitude_offset': 0.0001,
                    'longitude_offset': 0.0001,
                    'radius': 120
                },
                {
                    'name': 'Executive Floor',
                    'description': 'Executive offices and meeting rooms',
                    'latitude_offset': -0.0001,
                    'longitude_offset': 0.0001,
                    'radius': 80
                }
            ],
            # TechCorp R&D Center groups
            [
                {
                    'name': 'Development Lab A',
                    'description': 'Primary development laboratory',
                    'latitude_offset': 0.0002,
                    'longitude_offset': 0.0002,
                    'radius': 150
                },
                {
                    'name': 'Testing Facility',
                    'description': 'Product testing and quality assurance area',
                    'latitude_offset': -0.0002,
                    'longitude_offset': 0.0002,
                    'radius': 100
                }
            ],
            # InnovateLab Main Office groups
            [
                {
                    'name': 'Open Workspace',
                    'description': 'Collaborative open office environment',
                    'latitude_offset': 0.0001,
                    'longitude_offset': -0.0001,
                    'radius': 110
                },
                {
                    'name': 'Conference Center',
                    'description': 'Meeting rooms and presentation areas',
                    'latitude_offset': -0.0001,
                    'longitude_offset': -0.0001,
                    'radius': 90
                }
            ],
            # InnovateLab Lab Facility groups
            [
                {
                    'name': 'Research Lab',
                    'description': 'Advanced research laboratory',
                    'latitude_offset': 0.0003,
                    'longitude_offset': -0.0003,
                    'radius': 130
                },
                {
                    'name': 'Clean Room',
                    'description': 'Controlled environment laboratory',
                    'latitude_offset': -0.0003,
                    'longitude_offset': -0.0003,
                    'radius': 70
                }
            ]
        ]
        
        for branch_idx, branch in enumerate(branches):
            branch_groups = group_templates[branch_idx]
            
            for group_data in branch_groups:
                # Calculate group location based on branch location with small offset
                group_lat = float(branch.latitude) + group_data['latitude_offset']
                group_lon = float(branch.longitude) + group_data['longitude_offset']
                
                group = AttendanceGroup.objects.create(
                    name=group_data['name'],
                    company=branch.company,
                    branch=branch,
                    description=group_data['description'],
                    latitude=group_lat,
                    longitude=group_lon,
                    radius=group_data['radius']
                )
                
                groups.append(group)
                self.stdout.write(
                    f'Created Attendance Group: {group.name} '
                    f'({branch.company.name} - {branch.name}) '
                    f'at ({group_lat:.6f}, {group_lon:.6f}) with {group_data["radius"]}m radius'
                )
        
        return groups

    def get_group_summary(self):
        """Display summary of created attendance groups"""
        groups = AttendanceGroup.objects.all()
        return {
            'total_groups': groups.count(),
            'groups_by_company': {
                company.name: {
                    branch.name: [
                        {
                            'name': group.name,
                            'description': group.description,
                            'location': f"({group.latitude}, {group.longitude})",
                            'radius': group.radius
                        }
                        for group in branch.attendance_groups.all()
                    ]
                    for branch in company.branches.all()
                }
                for company in Company.objects.all()
            }
        }
