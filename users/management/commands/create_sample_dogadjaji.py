from datetime import datetime, timedelta
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from dogadjaji.models import Dogadjaj
from users.models import CompanyProfile

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample dogadjaji for testing'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=20, help='Number of events to create')
        parser.add_argument('--clear', action='store_true', help='Clear existing events first')

    def handle(self, *args, **options):
        count = options['count']
        clear = options['clear']

        if clear:
            Dogadjaj.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared existing dogadjaji'))

        companies = CompanyProfile.objects.select_related('user').all()
        
        if not companies:
            self.stdout.write(self.style.ERROR('No companies found. Please create companies first.'))
            return

        categories = ['koncerti', 'takmicenja', 'festivali', 'edukacija']
        seasons = ['summer', 'winter', 'all_year']
        event_names = [
            'Winter Music Festival', 'Ski Competition', 'New Year Celebration',
            'Wine Tasting', 'Summer Festival', 'Jazz Concert', 'Ski School Opening',
            'Christmas Market', 'Mountain Bike Race', 'Yoga Session',
            'Food Festival', 'Art Exhibition', 'Dance Party', 'Tech Conference',
            'Film Screening', 'Book Fair', 'Sports Tournament', 'Cooking Class',
            'Wine Tasting', 'Photography Workshop'
        ]

        created_count = 0

        for i in range(count):
            company = random.choice(companies)
            name = random.choice(event_names) + f' {i+1}'
            
            start_date = datetime.now().date() + timedelta(days=random.randint(30, 180))
            end_date = start_date + timedelta(days=random.randint(1, 3))
            
            # Random time between 8:00 and 22:00
            hour = random.randint(8, 22)
            minute = random.choice([0, 15, 30, 45])
            time_str = f'{hour:02d}:{minute:02d}'
            
            # Random price (0 = free)
            price = random.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 50])
            max_capacity = random.choice([None, 50, 100, 200, 500, 1000])

            dogadjaj = Dogadjaj.objects.create(
                company=company,
                naziv=name,
                opis=f'Exciting event organized by {company.company_name}',
                kategorija=random.choice(categories),
                season=random.choice(seasons),
                datum_pocetka=start_date,
                datum_zavrsetka=end_date,
                vreme=time_str,
                lokacija=random.choice(['Kopaonik', 'Ski Center', 'Mountain Resort', 'Town Square']),
                cena=price if price > 0 else None,
                max_kapacitet=max_capacity,
                is_active=True
            )
            
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'Created: {dogadjaj.naziv}'))

        self.stdout.write(self.style.SUCCESS(f'\n✅ Created {created_count} sample dogadjaji!'))