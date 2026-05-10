"""
Data migration — adds emoji icons to all categories and creates
subcategories for Marketplace and Services.
"""
from django.db import migrations


MARKETPLACE_DATA = [
    {
        'slug': 'books-study',
        'icon': '📚',
        'subcategories': [
            ('Textbooks',       'textbooks'),
            ('Past Questions',  'past-questions'),
            ('Novels & Fiction','novels-fiction'),
            ('Stationery',      'stationery'),
            ('Course Materials','course-materials'),
        ],
    },
    {
        'slug': 'clothing',
        'icon': '👗',
        'subcategories': [
            ('Men\'s Clothing',  'mens-clothing'),
            ('Women\'s Clothing','womens-clothing'),
            ('Shoes',           'shoes'),
            ('Bags & Accessories', 'bags-accessories'),
            ('Unisex',          'unisex'),
        ],
    },
    {
        'slug': 'electronics',
        'icon': '💻',
        'subcategories': [
            ('Phones',          'phones'),
            ('Laptops',         'laptops'),
            ('Accessories',     'accessories'),
            ('Tablets',         'tablets'),
            ('Audio & Headphones', 'audio-headphones'),
            ('Gaming',          'gaming'),
        ],
    },
    {
        'slug': 'food-groceries',
        'icon': '🍱',
        'subcategories': [
            ('Cooked Food',     'cooked-food'),
            ('Snacks & Drinks', 'snacks-drinks'),
            ('Raw Foodstuff',   'raw-foodstuff'),
            ('Confectionery',   'confectionery'),
        ],
    },
    {
        'slug': 'other',
        'icon': '📦',
        'subcategories': [
            ('Furniture',       'furniture'),
            ('Appliances',      'appliances'),
            ('Sports & Fitness','sports-fitness'),
            ('Art & Crafts',    'art-crafts'),
            ('Miscellaneous',   'miscellaneous'),
        ],
    },
    {
        'slug': 'part-time-jobs',
        'icon': '💼',
        'subcategories': [
            ('On-Campus Jobs',  'on-campus-jobs'),
            ('Off-Campus Jobs', 'off-campus-jobs'),
            ('Remote / Online', 'remote-online'),
            ('Internships',     'internships'),
        ],
    },
    {
        'slug': 'room-accomodation',
        'icon': '🏠',
        'subcategories': [
            ('Single Room',     'single-room'),
            ('Self Contain',    'self-contain'),
            ('Flat / Apartment','flat-apartment'),
            ('Hostel Space',    'hostel-space'),
            ('Roommate Wanted', 'roommate-wanted'),
        ],
    },
]

SERVICE_DATA = [
    {
        'slug': 'delivery',
        'icon': '🚴',
        'subcategories': [
            ('Campus Delivery',   'campus-delivery'),
            ('Off-Campus Delivery', 'off-campus-delivery'),
            ('Errand Running',    'errand-running'),
        ],
    },
    {
        'slug': 'graphics-design',
        'icon': '🎨',
        'subcategories': [
            ('Logo Design',       'logo-design'),
            ('Poster & Flyers',   'poster-flyers'),
            ('Social Media Graphics', 'social-media-graphics'),
            ('CV / Resume Design','cv-resume-design'),
        ],
    },
    {
        'slug': 'laundry',
        'icon': '👕',
        'subcategories': [
            ('Wash & Fold',       'wash-fold'),
            ('Iron Only',         'iron-only'),
            ('Wash, Iron & Fold', 'wash-iron-fold'),
            ('Dry Cleaning',      'dry-cleaning'),
        ],
    },
    {
        'slug': 'photography',
        'icon': '📸',
        'subcategories': [
            ('Portrait Sessions', 'portrait-sessions'),
            ('Events Coverage',   'events-coverage'),
            ('Product Photography','product-photography'),
            ('Videography',       'videography'),
        ],
    },
    {
        'slug': 'repairs-tech',
        'icon': '🔧',
        'subcategories': [
            ('Phone Repair',      'phone-repair'),
            ('Laptop Repair',     'laptop-repair'),
            ('Accessories Repair','accessories-repair'),
            ('Data Recovery',     'data-recovery'),
        ],
    },
    {
        'slug': 'tutoring',
        'icon': '✏️',
        'subcategories': [
            ('Mathematics',       'mathematics'),
            ('Sciences',          'sciences'),
            ('Languages',         'languages'),
            ('Engineering Courses','engineering-courses'),
            ('Business / Accounting', 'business-accounting'),
            ('Test Prep',         'test-prep'),
        ],
    },
    {
        'slug': 'web-development',
        'icon': '💻',
        'subcategories': [
            ('Website Design',    'website-design'),
            ('Mobile Apps',       'mobile-apps'),
            ('WordPress / CMS',   'wordpress-cms'),
            ('Backend / APIs',    'backend-apis'),
        ],
    },
]


def apply_icons_and_subcats(apps, schema_editor):
    Category = apps.get_model('marketplace', 'Category')
    SubCategory = apps.get_model('marketplace', 'SubCategory')
    ServiceCategory = apps.get_model('services', 'ServiceCategory')
    ServiceSubCategory = apps.get_model('services', 'ServiceSubCategory')

    for item in MARKETPLACE_DATA:
        try:
            cat = Category.objects.get(slug=item['slug'])
            cat.icon = item['icon']
            cat.save()
            for name, slug in item['subcategories']:
                SubCategory.objects.get_or_create(
                    category=cat, slug=slug,
                    defaults={'name': name},
                )
        except Category.DoesNotExist:
            pass

    for item in SERVICE_DATA:
        try:
            cat = ServiceCategory.objects.get(slug=item['slug'])
            cat.icon = item['icon']
            cat.save()
            for name, slug in item['subcategories']:
                ServiceSubCategory.objects.get_or_create(
                    category=cat, slug=slug,
                    defaults={'name': name},
                )
        except ServiceCategory.DoesNotExist:
            pass


def reverse_migration(apps, schema_editor):
    # Just clear the icons — don't delete subcategories (could have real data)
    Category = apps.get_model('marketplace', 'Category')
    ServiceCategory = apps.get_model('services', 'ServiceCategory')
    Category.objects.all().update(icon='')
    ServiceCategory.objects.all().update(icon='')


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0003_subcategory_and_views'),
        ('services',    '0003_subcategory_and_views'),
    ]

    operations = [
        migrations.RunPython(apply_icons_and_subcats, reverse_migration),
    ]
