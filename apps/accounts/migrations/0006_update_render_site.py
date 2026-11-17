from django.db import migrations


def update_site(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.update_or_create(
        pk=2,
        defaults={
            'domain': 'unitrax-7a80.onrender.com',
            'name': 'UniTraX',
        },
    )


def reverse_site(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.filter(pk=2, domain='unitrax-7a80.onrender.com').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('accounts', '0005_create_default_site'),
    ]

    operations = [
        migrations.RunPython(update_site, reverse_site),
    ]
