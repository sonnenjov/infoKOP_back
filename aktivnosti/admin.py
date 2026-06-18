from django.contrib import admin
from django import forms
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.management import call_command
from django.http import HttpResponse
from django.template.response import TemplateResponse
from .models import Activity, Reservation
import csv

class ActivityAdminForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = '__all__'

class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Upload CSV file with columns: title, company_email, description, season, price, duration_minutes, max_capacity, location, is_active',
        widget=forms.FileInput(attrs={'accept': '.csv'})
    )
    clear_existing = forms.BooleanField(
        required=False,
        label='Clear existing activities before import',
        initial=False,
        help_text='Delete all existing activities before importing new ones'
    )

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'season', 'price', 'max_capacity', 'is_active', 'created_at']
    list_filter = ['season', 'is_active', 'company']
    search_fields = ['title', 'description', 'location']
    readonly_fields = ['slug', 'created_at']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import/', self.admin_site.admin_view(self.import_view), name='activity-import'),
            path('export-sample/', self.admin_site.admin_view(self.export_sample), name='activity-export-sample'),
            path('generate-sample/', self.admin_site.admin_view(self.generate_sample), name='activity-generate-sample'),
        ]
        return custom_urls + urls

    def import_view(self, request):
        context = {
            'title': 'Import Activities',
            'opts': self.model._meta,
            'has_import_permission': True,
            'import_form': CSVUploadForm(),
        }
        return TemplateResponse(request, 'admin/activities/import.html', context)

    def export_sample(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sample_activities_import.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'title', 'company_email', 'company_name', 'description', 
            'season', 'price', 'duration_minutes', 'max_capacity', 
            'location', 'is_active'
        ])
        
        sample_data = [
            ['Winter Ski Lessons', 'ski@kopaonik.com', 'Ski School', 'Professional ski lessons for all levels', 'winter', '25.00', '120', '10', 'Main Ski Slope', 'True'],
            ['Summer Hiking', 'hiking@mountain.com', 'Mountain Adventures', 'Guided hiking tours through beautiful trails', 'summer', '15.00', '180', '15', 'Mountain Trail', 'True'],
            ['Yoga Retreat', 'yoga@wellness.com', 'Wellness Center', 'Relaxing yoga sessions with mountain views', 'summer', '20.00', '90', '8', 'Wellness Pavilion', 'True'],
            ['Snowmobile Adventure', 'snow@extreme.com', 'Extreme Sports', 'Exciting snowmobile rides through winter landscape', 'winter', '35.00', '60', '4', 'Snowmobile Park', 'True'],
            ['Mountain Biking', 'bike@rental.com', 'Bike Rentals', 'Professional mountain bike tours with guides', 'summer', '18.00', '120', '6', 'Bike Trail', 'True'],
            ['Ice Skating', 'ice@rink.com', 'Ice Rink', 'Outdoor ice skating experience for all ages', 'winter', '10.00', '60', '20', 'Ice Rink', 'True'],
            ['Photography Workshop', 'photo@studio.com', 'Photo Studio', 'Learn photography with mountain scenery', 'all_year', '30.00', '180', '12', 'Viewpoint', 'True'],
            ['Paragliding', 'para@club.com', 'Paragliding Club', 'Tandem flights over the mountains', 'summer', '45.00', '30', '2', 'Launch Point', 'True'],
            ['Nordic Skiing', 'nordic@center.com', 'Nordic Center', 'Cross-country skiing lessons', 'winter', '22.00', '120', '8', 'Nordic Trail', 'True'],
            ['Rock Climbing', 'climb@club.com', 'Climbing Club', 'Rock climbing for beginners and advanced', 'summer', '20.00', '150', '6', 'Climbing Wall', 'True'],
        ]
        
        for row in sample_data:
            writer.writerow(row)
        
        return response

    def generate_sample(self, request):
        try:
            call_command('create_sample_activities', count=20, clear=True)
            messages.success(request, 'Successfully generated 20 sample activities!')
        except Exception as e:
            messages.error(request, f'Error generating sample activities: {str(e)}')
        
        return redirect('admin:activities_activity_changelist')