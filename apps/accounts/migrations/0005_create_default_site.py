# Migration to create the required Site object for django.contrib.sites
# Railway/Neon starts with empty DB so initial_data fixtures don't run
from django.db import migrations


def create_site(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.update_or_create(
        pk=1,
        defaults={
            'domain': 'unitrax.up.railway.app',
            'name': 'UniTraX',
        },
    )


def delete_site(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.filter(pk=1).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('accounts', '0004_user_matric_number'),
    ]

    operations = [
        migrations.RunPython(create_site, delete_site),
    ]
