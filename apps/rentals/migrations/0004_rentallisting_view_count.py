from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rentals', '0003_rentallisting_subsequent_payment_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='rentallisting',
            name='view_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
