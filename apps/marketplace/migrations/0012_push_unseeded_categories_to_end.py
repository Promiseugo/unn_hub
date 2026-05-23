from django.db import migrations


MARKETPLACE_SLUGS = {
    "vehicles",
    "student-housing-accommodation",
    "electronics",
    "mobile-phones-accessories",
    "fashion-wearables",
    "books-academic-materials",
    "food-groceries",
    "appliances-hostel-essentials",
    "beauty-personal-care",
    "pets-pet-accessories",
    "sports-fitness",
    "gaming-entertainment",
}

SERVICE_SLUGS = {
    "academic-services",
    "tech-digital-services",
    "home-hostel-services",
    "beauty-fashion-services",
    "delivery-logistics",
    "event-services",
    "repair-services",
}


def push_unseeded_to_end(apps, schema_editor):
    Category = apps.get_model("marketplace", "Category")
    SubCategory = apps.get_model("marketplace", "SubCategory")
    ServiceCategory = apps.get_model("services", "ServiceCategory")
    ServiceSubCategory = apps.get_model("services", "ServiceSubCategory")

    Category.objects.exclude(slug__in=MARKETPLACE_SLUGS).filter(sort_order=0).update(sort_order=1000)
    SubCategory.objects.filter(sort_order=0).update(sort_order=1000)
    ServiceCategory.objects.exclude(slug__in=SERVICE_SLUGS).filter(sort_order=0).update(sort_order=1000)
    ServiceSubCategory.objects.filter(sort_order=0).update(sort_order=1000)


class Migration(migrations.Migration):

    dependencies = [
        ("marketplace", "0011_alter_category_sort_order_and_more"),
        ("services", "0007_alter_servicecategory_sort_order_and_more"),
    ]

    operations = [
        migrations.RunPython(push_unseeded_to_end, migrations.RunPython.noop),
    ]
