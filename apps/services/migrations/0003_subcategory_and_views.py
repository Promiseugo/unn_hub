from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0002_serviceoffer_video'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicecategory',
            name='icon',
            field=models.CharField(blank=True, help_text='Emoji icon e.g. 🎨', max_length=10, default=''),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='ServiceSubCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField()),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subcategories', to='services.servicecategory')),
            ],
            options={
                'verbose_name_plural': 'Service Sub Categories',
                'ordering': ['name'],
                'unique_together': {('category', 'slug')},
            },
        ),
        migrations.AddField(
            model_name='serviceoffer',
            name='subcategory',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='services', to='services.servicesubcategory'),
        ),
        migrations.AddField(
            model_name='serviceoffer',
            name='view_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
