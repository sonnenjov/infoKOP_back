# smestaj/serializers.py

from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from .models import Smestaj, SmestajReservation
from decimal import Decimal


class SmestajSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.company_name', read_only=True)
    company_slug = serializers.CharField(source='company.slug', read_only=True)
    image_url = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Smestaj
        fields = [
            'id', 'company', 'company_name', 'company_slug',
            'naziv', 'slug', 'opis', 'tip', 'season',
            'cena_po_nocenju', 'udaljenost_od_staza', 'kapacitet',
            'image', 'image_url',
            'ima_spa', 'ima_bazen', 'ski_in_ski_out', 'ima_restoran', 'ima_parking', 'ima_wifi',
            'tags', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_tags(self, obj):
        """Returns a list of amenity tag strings for easy frontend rendering."""
        tags = []
        if obj.ski_in_ski_out:
            tags.append('ski-in')
        if obj.ima_spa:
            tags.append('spa')
        if obj.ima_bazen:
            tags.append('bazen')
        if obj.ima_restoran:
            tags.append('restoran')
        if obj.ima_parking:
            tags.append('parking')
        if obj.ima_wifi:
            tags.append('wifi')
        return tags


class SmestajCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Smestaj
        fields = [
            'naziv', 'opis', 'tip', 'season',
            'cena_po_nocenju', 'udaljenost_od_staza', 'kapacitet',
            'image', 'ima_spa', 'ima_bazen', 'ski_in_ski_out',
            'ima_restoran', 'ima_parking', 'ima_wifi', 'is_active',
        ]

    def validate_cena_po_nocenju(self, value):
        if value <= 0:
            raise serializers.ValidationError('Cena mora biti veća od 0.')
        return value

    def create(self, validated_data):
        request = self.context['request']
        validated_data['company'] = request.user.company_profile
        return super().create(validated_data)


class SmestajReservationSerializer(serializers.ModelSerializer):
    smestaj_naziv = serializers.CharField(source='smestaj.naziv', read_only=True)
    smestaj_image = serializers.SerializerMethodField()
    company_name = serializers.CharField(source='smestaj.company.company_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    total_guests = serializers.SerializerMethodField()
    nights = serializers.SerializerMethodField()

    class Meta:
        model = SmestajReservation
        fields = [
            'id', 'smestaj', 'smestaj_naziv', 'smestaj_image', 'company_name',
            'user', 'user_email',
            'check_in', 'check_out', 'nights',
            'broj_odraslih', 'broj_dece', 'total_guests',
            'status', 'napomena', 'total_price', 'created_at',
        ]
        read_only_fields = ['id', 'user', 'total_price', 'created_at']

    def get_smestaj_image(self, obj):
        if obj.smestaj.image:
            return obj.smestaj.image.url
        return None
    
    def get_total_guests(self, obj):
        return obj.broj_odraslih + obj.broj_dece
    
    def get_nights(self, obj):
        return (obj.check_out - obj.check_in).days

    def validate(self, data):
        check_in = data.get('check_in') or getattr(self.instance, 'check_in', None)
        check_out = data.get('check_out') or getattr(self.instance, 'check_out', None)
        if check_in and check_out and check_out <= check_in:
            raise serializers.ValidationError({'check_out': 'Datum odjave mora biti posle datuma prijave.'})

        smestaj = data.get('smestaj') or getattr(self.instance, 'smestaj', None)
        odrasli = data.get('broj_odraslih', getattr(self.instance, 'broj_odraslih', 1))
        deca = data.get('broj_dece', getattr(self.instance, 'broj_dece', 0))
        if smestaj and (odrasli + deca) > smestaj.kapacitet:
            raise serializers.ValidationError({
                'broj_odraslih': f'Maksimalan kapacitet smeštaja je {smestaj.kapacitet} osoba.'
            })
        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        # Calculate total price
        validated_data['total_price'] = validated_data['smestaj'].cena_po_nocenju * (
            validated_data['check_out'] - validated_data['check_in']
        ).days
        return super().create(validated_data)


class SmestajReservationStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmestajReservation
        fields = ['status']


class SmestajPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100