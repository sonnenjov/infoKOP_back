import csv
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from aktivnosti.models import Activity
from users.models import CompanyProfile

User = get_user_model()

class Command(BaseCommand):
    help = 'Import activities from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')
        parser.add_argument('--clear', action='store_true', help='Clear existing activities before import')
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
            count = Activity.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f'Cleared {count} existing activities'))

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No data will be saved'))

        created_count = 0
        updated_count = 0
        error_count = 0
        errors = []

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Print available columns for debugging
            self.stdout.write(self.style.NOTICE(f'Available columns: {", ".join(reader.fieldnames)}'))
            
            # Required columns
            required_fields = ['title', 'price']
            missing_fields = [f for f in required_fields if f not in reader.fieldnames]
            if missing_fields:
                self.stdout.write(self.style.ERROR(f'Missing required columns: {", ".join(missing_fields)}'))
                return

            for row_num, row in enumerate(reader, start=2):
                try:
                    # Skip empty rows
                    if not any(row.values()):
                        continue

                    # Get company
                    company = None
                    company_email = row.get('company_email', '').strip()
                    company_name = row.get('company_name', '').strip()

                    if company_email:
                        try:
                            user = User.objects.get(email=company_email)
                            company = CompanyProfile.objects.filter(user=user).first()
                            if not company:
                                self.stdout.write(self.style.WARNING(f'Row {row_num}: No company profile for email: {company_email}'))
                        except User.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'Row {row_num}: User not found: {company_email}'))
                    elif company_name:
                        company = CompanyProfile.objects.filter(company_name__icontains=company_name).first()
                        if not company:
                            self.stdout.write(self.style.WARNING(f'Row {row_num}: Company not found: {company_name}'))

                    if not company:
                        error_count += 1
                        errors.append(f'Row {row_num}: Company not found (email: {company_email}, name: {company_name})')
                        continue

                    # Parse required fields
                    title = row.get('title', '').strip()
                    if not title:
                        error_count += 1
                        errors.append(f'Row {row_num}: Missing title')
                        continue

                    # Parse price
                    try:
                        price_str = row.get('price', '0').strip()
                        price = float(price_str) if price_str else 0.0
                        if price <= 0:
                            self.stdout.write(self.style.WARNING(f'Row {row_num}: Price should be > 0, got: {price}'))
                    except ValueError:
                        error_count += 1
                        errors.append(f'Row {row_num}: Invalid price format: {row.get("price")}')
                        continue

                    # Parse optional fields
                    description = row.get('description', '').strip()

                    duration_minutes = None
                    duration_str = row.get('duration_minutes', '').strip()
                    if duration_str:
                        try:
                            duration_minutes = int(duration_str)
                        except ValueError:
                            self.stdout.write(self.style.WARNING(f'Row {row_num}: Invalid duration_minutes: {duration_str}, using None'))

                    max_capacity = 1
                    capacity_str = row.get('max_capacity', '1').strip()
                    if capacity_str:
                        try:
                            max_capacity = int(capacity_str)
                            if max_capacity < 1:
                                self.stdout.write(self.style.WARNING(f'Row {row_num}: max_capacity should be >= 1, got: {max_capacity}, using 1'))
                                max_capacity = 1
                        except ValueError:
                            self.stdout.write(self.style.WARNING(f'Row {row_num}: Invalid max_capacity: {capacity_str}, using 1'))

                    season = row.get('season', 'all_year').strip().lower()
                    if season not in ['summer', 'winter', 'all_year']:
                        self.stdout.write(self.style.WARNING(f'Row {row_num}: Invalid season: {season}, defaulting to all_year'))
                        season = 'all_year'

                    location = row.get('location', '').strip()

                    is_active = row.get('is_active', 'True').strip().lower() in ['true', '1', 'yes', 't']

                    # Prepare data for Activity model
                    activity_data = {
                        'company': company,
                        'title': title,
                        'description': description,
                        'season': season,
                        'price': price,
                        'duration_minutes': duration_minutes,
                        'max_capacity': max_capacity,
                        'location': location,
                        'is_active': is_active,
                    }

                    if dry_run:
                        self.stdout.write(f'Row {row_num}: Would create/update: {title} (Company: {company.company_name}, Price: {price}€)')
                        created_count += 1
                        continue

                    # Create or update activity
                    try:
                        # Check if activity exists with same title and company
                        activity, created = Activity.objects.get_or_create(
                            title=title,
                            company=company,
                            defaults=activity_data
                        )
                        
                        if not created:
                            # Update existing activity
                            for key, value in activity_data.items():
                                if key != 'company':  # Don't change company
                                    setattr(activity, key, value)
                            activity.save()
                            updated_count += 1
                            self.stdout.write(f'🔄 Row {row_num}: Updated: {activity.title}')
                        else:
                            created_count += 1
                            self.stdout.write(self.style.SUCCESS(f'✅ Row {row_num}: Created: {activity.title}'))
                            
                    except Exception as e:
                        error_count += 1
                        errors.append(f'Row {row_num}: Database error: {str(e)}')
                        self.stdout.write(self.style.ERROR(f'Row {row_num}: Error: {str(e)}'))

                except Exception as e:
                    error_count += 1
                    errors.append(f'Row {row_num}: Unexpected error: {str(e)}')
                    self.stdout.write(self.style.ERROR(f'Row {row_num}: Unexpected error: {str(e)}'))

        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.NOTICE('📊 IMPORT SUMMARY'))
        self.stdout.write('='*60)
        self.stdout.write(f'✅ Created: {created_count}')
        self.stdout.write(f'🔄 Updated: {updated_count}')
        self.stdout.write(f'❌ Errors: {error_count}')
        
        if errors:
            self.stdout.write('\n' + self.style.WARNING('⚠️ ERROR DETAILS:'))
            for error in errors[:10]:
                self.stdout.write(f'  • {error}')
            if len(errors) > 10:
                self.stdout.write(f'  ... and {len(errors) - 10} more errors')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️ DRY RUN completed - No data was saved'))

        self.stdout.write('='*60)