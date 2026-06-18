import csv
import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import CompanyProfile
from smestaj.models import Smestaj

User = get_user_model()

class Command(BaseCommand):
    help = 'Bulk import accommodations from CSV or JSON file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to CSV or JSON file')
        parser.add_argument('--format', type=str, default='csv', choices=['csv', 'json'], 
                           help='File format (csv or json)')
        parser.add_argument('--company-id', type=int, help='Company ID to assign all accommodations to')
        parser.add_argument('--company-email', type=str, help='Company email to assign all accommodations to')

    def handle(self, *args, **options):
        file_path = options['file_path']
        file_format = options['format']
        company_id = options.get('company_id')
        company_email = options.get('company_email')
        
        company = None
        if company_id:
            try:
                company = CompanyProfile.objects.get(id=company_id)
                self.stdout.write(self.style.SUCCESS(f'Using company: {company.company_name} (ID: {company.id})'))
            except CompanyProfile.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Company with ID {company_id} not found'))
                return
        elif company_email:
            try:
                user = User.objects.get(email=company_email)
                company = CompanyProfile.objects.get(user=user)
                self.stdout.write(self.style.SUCCESS(f'Using company: {company.company_name} (Email: {company_email})'))
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with email {company_email} not found'))
                return
            except CompanyProfile.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Company profile for {company_email} not found'))
                return
        else:
            self.stdout.write(self.style.ERROR('Please provide --company-id or --company-email'))
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                if file_format == 'csv':
                    reader = csv.DictReader(file)
                    data = list(reader)
                else:
                    data = json.load(file)
                    if isinstance(data, dict) and 'results' in data:
                        data = data['results']
                    elif isinstance(data, dict):
                        data = [data]
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading file: {e}'))
            return

        created_count = 0
        updated_count = 0
        error_count = 0

        for item in data:
            try:
                naziv = item.get('naziv') or item.get('name') or item.get('title')
                if not naziv:
                    self.stdout.write(self.style.WARNING(f'Skipping item without name: {item}'))
                    error_count += 1
                    continue

                existing = Smestaj.objects.filter(naziv=naziv, company=company).first()
                
                defaults = {
                    'opis': item.get('opis') or item.get('description') or '',
                    'tip': item.get('tip') or item.get('type') or 'hotel',
                    'season': item.get('season') or 'all_year',
                    'cena_po_nocenju': float(item.get('cena_po_nocenju') or item.get('price_per_night') or 0),
                    'udaljenost_od_staza': int(item.get('udaljenost_od_staza') or item.get('distance_from_slopes') or 0),
                    'kapacitet': int(item.get('kapacitet') or item.get('capacity') or 1),
                    'ima_spa': self.str_to_bool(item.get('ima_spa') or item.get('has_spa') or False),
                    'ima_bazen': self.str_to_bool(item.get('ima_bazen') or item.get('has_pool') or False),
                    'ski_in_ski_out': self.str_to_bool(item.get('ski_in_ski_out') or False),
                    'ima_restoran': self.str_to_bool(item.get('ima_restoran') or item.get('has_restaurant') or False),
                    'ima_parking': self.str_to_bool(item.get('ima_parking') or item.get('has_parking') or False),
                    'ima_wifi': self.str_to_bool(item.get('ima_wifi') or item.get('has_wifi') or True),
                    'is_active': self.str_to_bool(item.get('is_active', True)),
                }

                if existing:
                    for key, value in defaults.items():
                        setattr(existing, key, value)
                    existing.save()
                    updated_count += 1
                    self.stdout.write(f'Updated: {naziv}')
                else:
                    smestaj = Smestaj.objects.create(
                        company=company,
                        naziv=naziv,
                        **defaults
                    )
                    created_count += 1
                    self.stdout.write(f'Created: {naziv}')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error importing {item.get("naziv", "unknown")}: {e}'))
                error_count += 1

        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS(f'Import complete!'))
        self.stdout.write(self.style.SUCCESS(f'Created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'Updated: {updated_count}'))
        self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))
        self.stdout.write(self.style.SUCCESS('='*50))

    def str_to_bool(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'y', 'on']
        return bool(value)