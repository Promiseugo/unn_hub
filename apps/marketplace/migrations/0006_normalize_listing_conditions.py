from django.db import migrations


def normalize_conditions(apps, schema_editor):
    Listing = apps.get_model('marketplace', 'Listing')
    Listing.objects.filter(condition__in=['new', 'like_new']).update(condition='brand_new')
    Listing.objects.filter(condition__in=['good', 'fair']).update(condition='used')


def restore_legacy_conditions(apps, schema_editor):
    Listing = apps.get_model('marketplace', 'Listing')
    Listing.objects.filter(condition='brand_new').update(condition='new')
    Listing.objects.filter(condition='used').update(condition='good')


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0005_listing_expires_at_alter_listing_condition'),
    ]

    operations = [
        migrations.RunPython(normalize_conditions, restore_legacy_conditions),
    ]
