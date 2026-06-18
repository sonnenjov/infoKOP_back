# dogadjaji/serializers.py

from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from .models import Dogadjaj, DogadjajReservation
from decimal import Decimal


class DogadjajSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.company_name', read_only=True)
    company_slug = serializers.CharField(source='company.slug', read_only=True)
    image_url = serializers.SerializerMethodField()
    je_besplatan = serializers.SerializerMethodField()

    class Meta:
        model = Dogadjaj
        fields = [
            'id', 'company', 'company_name', 'company_slug',
            'naziv', 'slug', 'opis', 'kategorija', 'season',
            'datum_pocetka', 'datum_zavrsetka', 'vreme',
            'lokacija', 'cena', 'je_besplatan', 'max_kapacitet',
            'image', 'image_url', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_je_besplatan(self, obj):
        return obj.cena is None or obj.cena == 0


class DogadjajCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dogadjaj
        fields = [
            'naziv', 'opis', 'kategorija', 'season',
            'datum_pocetka', 'datum_zavrsetka', 'vreme',
            'lokacija', 'cena', 'max_kapacitet', 'image', 'is_active',
        ]

    def validate_cena(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError('Cena ne može biti negativna.')
        return value

    def validate(self, data):
        pocetak = data.get('datum_pocetka')
        kraj = data.get('datum_zavrsetka')
        if pocetak and kraj and kraj < pocetak:
            raise serializers.ValidationError({
                'datum_zavrsetka': 'Datum završetka mora biti isti ili posle datuma početka.'
            })
        return data

    def create(self, validated_data):
        request = self.context['request']
        validated_data['company'] = request.user.company_profile
        return super().create(validated_data)


class DogadjajReservationSerializer(serializers.ModelSerializer):
    dogadjaj_naziv = serializers.CharField(source='dogadjaj.naziv', read_only=True)
    dogadjaj_image = serializers.SerializerMethodField()
    dogadjaj_date = serializers.DateField(source='dogadjaj.datum_pocetka', read_only=True)
    dogadjaj_price = serializers.DecimalField(
        source='dogadjaj.cena',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    company_name = serializers.CharField(source='dogadjaj.company.company_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = DogadjajReservation
        fields = [
            'id', 'dogadjaj', 'dogadjaj_naziv', 'dogadjaj_image', 'dogadjaj_date', 'dogadjaj_price',
            'company_name',
            'user', 'user_email',
            'broj_karata', 'status', 'napomena', 'total_price', 'created_at',
        ]
        read_only_fields = ['id', 'user', 'total_price', 'created_at']

    def get_dogadjaj_image(self, obj):
        if obj.dogadjaj.image:
            return obj.dogadjaj.image.url
        return None

    def validate(self, data):
        dogadjaj = data.get('dogadjaj') or getattr(self.instance, 'dogadjaj', None)
        karte = data.get('broj_karata', getattr(self.instance, 'broj_karata', 1))

        if dogadjaj and dogadjaj.max_kapacitet is not None:
            ukupno_rezervisano = (
                DogadjajReservation.objects
                .filter(dogadjaj=dogadjaj, status__in=['pending', 'confirmed'])
                .exclude(pk=getattr(self.instance, 'pk', None))
                .values_list('broj_karata', flat=True)
            )
            zauzeto = sum(ukupno_rezervisano)
            if zauzeto + karte > dogadjaj.max_kapacitet:
                slobodno = dogadjaj.max_kapacitet - zauzeto
                raise serializers.ValidationError({
                    'broj_karata': f'Dostupno je samo {slobodno} karata za ovaj dogadjaj.'
                })
        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        # Calculate total price
        dogadjaj = validated_data['dogadjaj']
        broj_karata = validated_data['broj_karata']
        if dogadjaj.cena:
            validated_data['total_price'] = dogadjaj.cena * broj_karata
        else:
            validated_data['total_price'] = Decimal('0')
        return super().create(validated_data)


class DogadjajReservationStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DogadjajReservation
        fields = ['status']


class DogadjajPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100