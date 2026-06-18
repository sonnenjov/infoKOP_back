import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from dogadjaji.models import Dogadjaj
from users.models import CompanyProfile

User = get_user_model()

class Command(BaseCommand):
    help = 'Import dogadjaji (events) from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')
        parser.add_argument('--clear', action='store_true', help='Clear existing dogadjaji before import')
        parser.add_argument('--dry-run', action='store_true', help='Preview import without saving')

    @transaction.atomic
    def handle(self, *args, **options):
        csv_file = options['csv_file']
        clear = options.get('clear', False)
        dry_run = options.get('dry_run', False)

        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f'File {csv_file} does not exist'))
            return

        if clear:
            count = Dogadjaj.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f'Cleared {count} existing dogadjaji'))

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No data will be saved'))

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            created_count = 0
            updated_count = 0
            error_count = 0

            for row_num, row in enumerate(reader, start=2):
                try:
                    # Get company by email or name
                    company = None
                    company_email = row.get('company_email', '').strip()
                    company_name = row.get('company_name', '').strip()

                    if company_email:
                        try:
                            user = User.objects.get(email=company_email)
                            company = CompanyProfile.objects.filter(user=user).first()
                            if not company:
                                self.stdout.write(self.style.WARNING(f'Row {row_num}: No company profile for user {company_email}'))
                        except User.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'Row {row_num}: User {company_email} not found'))
                    elif company_name:
                        company = CompanyProfile.objects.filter(company_name__icontains=company_name).first()
                        if not company:
                            self.stdout.write(self.style.WARNING(f'Row {row_num}: Company {company_name} not found'))

                    if not company:
                        self.stdout.write(self.style.WARNING(f'Row {row_num}: Skipping - Company not found'))
                        error_count += 1
                        continue

                    # Parse data
                    naziv = row.get('naziv', '').strip()
                    if not naziv:
                        self.stdout.write(self.style.WARNING(f'Row {row_num}: Skipping - No name provided'))
                        error_count += 1
                        continue

                    # Parse dates
                    datum_pocetka = None
                    if row.get('datum_pocetka'):
                        try:
                            datum_pocetka = datetime.strptime(row['datum_pocetka'].strip(), '%Y-%m-%d').date()
                        except ValueError:
                            self.stdout.write(self.style.WARNING(f'Row {row_num}: Invalid datum_pocetka format, use YYYY-MM-DD'))
                            error_count += 1
                            continue

                    datum_zavrsetka = None
                    if row.get('datum_zavrsetka'):
                        try:
                            datum_zavrsetka = datetime.strptime(row['datum_zavrsetka'].strip(), '%Y-%m-%d').date()
                        except ValueError:
                            self.stdout.write(self.style.WARNING(f'Row {row_num}: Invalid datum_zavrsetka format, use YYYY-MM-DD'))

                    # Parse time
                    vreme = None
                    if row.get('vreme'):
                        try:
                            vreme = datetime.strptime(row['vreme'].strip(), '%H:%M').time()
                        except ValueError:
                            self.stdout.write(self.style.WARNING(f'Row {row_num}: Invalid vreme format, use HH:MM'))

                    # Parse price
                    cena = None
                    if row.get('cena') and row['cena'].strip():
                        try:
                            cena = float(row['cena'].strip())
                        except ValueError:
                            self.stdout.write(self.style.WARNING(f'Row {row_num}: Invalid cena format'))

                    # Parse max capacity
                    max_kapacitet = None
                    if row.get('max_kapacitet') and row['max_kapacitet'].strip():
                        try:
                            max_kapacitet = int(row['max_kapacitet'].strip())
                        except ValueError:
                            self.stdout.write(self.style.WARNING(f'Row {row_num}: Invalid max_kapacitet format'))

                    # Parse categories
                    kategorija = row.get('kategorija', 'koncerti').strip().lower()
                    if kategorija not in ['koncerti', 'takmicenja', 'festivali', 'edukacija']:
                        kategorija = 'koncerti'
                        self.stdout.write(self.style.WARNING(f'Row {row_num}: Invalid kategorija, defaulting to koncerti'))

                    season = row.get('season', 'all_year').strip().lower()
                    if season not in ['summer', 'winter', 'all_year']:
                        season = 'all_year'

                    is_active = row.get('is_active', 'True').strip().lower() in ['true', '1', 'yes']

                    # Create or update
                    defaults = {
                        'opis': row.get('opis', '').strip(),
                        'kategorija': kategorija,
                        'season': season,
                        'datum_pocetka': datum_pocetka,
                        'datum_zavrsetka': datum_zavrsetka,
                        'vreme': vreme,
                        'lokacija': row.get('lokacija', '').strip(),
                        'cena': cena,
                        'max_kapacitet': max_kapacitet,
                        'is_active': is_active,
                    }

                    if dry_run:
                        self.stdout.write(f'Row {row_num}: Would create/update: {naziv}')
                        continue

                    dogadjaj, created = Dogadjaj.objects.update_or_create(
                        naziv=naziv,
                        company=company,
                        defaults=defaults
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(f'Row {row_num}: Created: {dogadjaj.naziv}'))
                    else:
                        updated_count += 1
                        self.stdout.write(f'Row {row_num}: Updated: {dogadjaj.naziv}')

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Row {row_num}: Error: {str(e)}'))
                    error_count += 1

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                f'\n✅ Import completed! Created: {created_count}, Updated: {updated_count}, Errors: {error_count}'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'\n✅ DRY RUN completed! Would create/update: {created_count + updated_count}, Errors: {error_count}'
            ))