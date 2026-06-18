from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import CompanyProfile
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample companies with users'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=5, help='Number of companies to create')
        parser.add_argument('--password', type=str, default='password123', help='Default password for users')

    @transaction.atomic
    def handle(self, *args, **options):
        count = options['count']
        password = options['password']
        
        company_types = ['hotel', 'apartman', 'restoran', 'kafic', 'apres_ski', 
                        'aktivnost', 'ski_skola', 'organizator', 'servis_iznajmljivanje', 'prevoz']
        
        for i in range(1, count + 1):
            email = f'company{i}@example.com'
            
            # Create user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': f'company{i}',
                    'role': User.Role.COMPANY,
                    'email_confirmed': True,
                    'is_approved': True,
                    'is_active': True
                }
            )
            
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f'Created user: {email}')
            
            # Create company profile
            company_type = company_types[(i - 1) % len(company_types)]
            company_name = f'Sample {company_type.capitalize()} {i}'
            
            company, created = CompanyProfile.objects.get_or_create(
                user=user,
                defaults={
                    'type': company_type,
                    'company_name': company_name,
                    'address': f'Sample Address {i}, Test City',
                    'pib': f'12345678{i:03d}',
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created company: {company_name}'))
            else:
                self.stdout.write(f'Company {company_name} already exists')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} companies'))