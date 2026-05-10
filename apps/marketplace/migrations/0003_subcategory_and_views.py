from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0002_listing_video'),
    ]

    operations = [
        # Add icon field to Category
        migrations.AddField(
            model_name='category',
            name='icon',
            field=models.CharField(blank=True, help_text='Emoji icon e.g. 👕', max_length=10, default=''),
            preserve_default=False,
        ),
        # Create SubCategory
        migrations.CreateModel(
            name='SubCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField()),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subcategories', to='marketplace.category')),
            ],
            options={
                'verbose_name_plural': 'Sub Categories',
                'ordering': ['name'],
                'unique_together': {('category', 'slug')},
            },
        ),
        # Add subcategory FK to Listing
        migrations.AddField(
            model_name='listing',
            name='subcategory',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='listings', to='marketplace.subcategory'),
        ),
        # Add view_count to Listing
        migrations.AddField(
            model_name='listing',
            name='view_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
