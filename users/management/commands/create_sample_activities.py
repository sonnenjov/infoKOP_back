import random
from django.core.management.base import BaseCommand
from aktivnosti.models import Activity
from users.models import CompanyProfile

class Command(BaseCommand):
    help = 'Create sample activities for testing'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=20, help='Number of activities to create')
        parser.add_argument('--clear', action='store_true', help='Clear existing activities first')

    def handle(self, *args, **options):
        count = options['count']
        clear = options.get('clear', False)

        if clear:
            Activity.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared existing activities'))

        companies = CompanyProfile.objects.all()
        if not companies:
            self.stdout.write(self.style.ERROR('No companies found. Please create companies first.'))
            return

        seasons = ['summer', 'winter', 'all_year']
        titles = [
            'Ski Lessons', 'Snowboarding', 'Hiking Tour', 'Mountain Biking',
            'Yoga Session', 'Paragliding', 'Rock Climbing', 'Ice Skating',
            'Snowmobile Ride', 'Photography Tour', 'Wine Tasting',
            'Nordic Skiing', 'Snowshoeing', 'Aurora Viewing',
            'Sunset Hike', 'Wildlife Spotting', 'Fishing Trip',
            'Kayaking', 'Horse Riding', 'Zip Line'
        ]
        locations = [
            'Kopaonik Ski Resort', 'Mountain Trail', 'Wellness Pavilion',
            'Sports Center', 'Adventure Park', 'Nature Reserve',
            'Lake View', 'Forest Trail', 'Mountain Peak', 'Valley'
        ]

        created_count = 0
        for i in range(count):
            company = random.choice(companies)
            title = random.choice(titles) + f' {i+1}'
            
            Activity.objects.create(
                company=company,
                title=title,
                description=f'Exciting {title.lower()} experience organized by {company.company_name}',
                season=random.choice(seasons),
                price=random.choice([10, 15, 20, 25, 30, 35, 40, 45, 50]),
                duration_minutes=random.choice([30, 45, 60, 90, 120, 150, 180]),
                max_capacity=random.choice([1, 2, 4, 6, 8, 10, 12, 15, 20]),
                location=random.choice(locations),
                is_active=True
            )
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Created {created_count} sample activities!'))