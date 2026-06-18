from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0004_populate_company_slugs'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='avatar',
            field=models.TextField(blank=True, null=True, verbose_name='avatar'),
        ),
    ]