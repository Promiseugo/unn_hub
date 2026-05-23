from django.db import migrations


MARKETPLACE_CATEGORIES = [
    ("Vehicles", "vehicles", "🚗", True, [
        ("Cars", "cars", "🚘"),
        ("Motorcycles", "motorcycles", "🏍️"),
        ("Scooters", "scooters", "🛵"),
        ("Bicycles", "bicycles", "🚲"),
        ("Electric Bikes", "electric-bikes", "🚲"),
        ("Tricycles", "tricycles", "🛺"),
        ("Vehicle Parts & Accessories", "vehicle-parts-accessories", "🔧"),
        ("Vehicle Rentals", "vehicle-rentals", "🔑"),
        ("Ride Sharing", "ride-sharing", "🚕"),
        ("Carpool Services", "carpool-services", "🚙"),
    ]),
    ("Student Housing & Accommodation", "student-housing-accommodation", "🏠", True, [
        ("Hostels", "hostels", "🏢"),
        ("Apartments", "apartments", "🏘️"),
        ("Shared Rooms", "shared-rooms", "🛏️"),
        ("Self-Contain Rooms", "self-contain-rooms", "🚪"),
        ("Roommates Wanted", "roommates-wanted", "👥"),
        ("Short-Term Stay", "short-term-stay", "🧳"),
        ("Off-Campus Housing", "off-campus-housing", "🏡"),
        ("Hostel Transfers", "hostel-transfers", "🔁"),
        ("Furniture for Hostels", "furniture-for-hostels", "🪑"),
        ("Utility Services", "utility-services", "💡"),
    ]),
    ("Electronics", "electronics", "💻", True, [
        ("Laptops", "laptops", "💻"),
        ("Desktop Computers", "desktop-computers", "🖥️"),
        ("Monitors", "monitors", "🖥️"),
        ("Tablets", "tablets", "📱"),
        ("Printers", "printers", "🖨️"),
        ("Projectors", "projectors", "📽️"),
        ("Computer Accessories", "computer-accessories", "⌨️"),
        ("Hard Drives & SSDs", "hard-drives-ssds", "💾"),
        ("USB Devices", "usb-devices", "🔌"),
        ("Power Banks", "power-banks", "🔋"),
        ("Smart Watches", "smart-watches", "⌚"),
        ("Gaming Consoles", "gaming-consoles", "🎮"),
        ("Cameras", "cameras", "📷"),
        ("Speakers", "speakers", "🔊"),
        ("Headphones & Earbuds", "headphones-earbuds", "🎧"),
        ("Calculators", "calculators", "🧮"),
    ]),
    ("Mobile Phones & Accessories", "mobile-phones-accessories", "📱", True, [
        ("Smartphones", "smartphones", "📱"),
        ("iPhones", "iphones", "📱"),
        ("Android Phones", "android-phones", "🤖"),
        ("Tablets", "tablets", "📲"),
        ("Phone Cases", "phone-cases", "📱"),
        ("Chargers", "chargers", "🔌"),
        ("Power Banks", "power-banks", "🔋"),
        ("Earphones", "earphones", "🎧"),
        ("Smart Watches", "smart-watches", "⌚"),
        ("Screen Protectors", "screen-protectors", "🛡️"),
        ("SIM & Data Devices", "sim-data-devices", "📶"),
        ("Phone Repairs", "phone-repairs", "🛠️"),
    ]),
    ("Fashion & Wearables", "fashion-wearables", "👕", True, [
        ("Male Clothing", "male-clothing", "👔"),
        ("Female Clothing", "female-clothing", "👗"),
        ("Shoes", "shoes", "👞"),
        ("Sneakers", "sneakers", "👟"),
        ("Bags", "bags", "👜"),
        ("Wrist Watches", "wrist-watches", "⌚"),
        ("Jewelry", "jewelry", "💍"),
        ("Native Wear", "native-wear", "🥻"),
        ("Hoodies", "hoodies", "🧥"),
        ("School Outfits", "school-outfits", "🎒"),
        ("Sportswear", "sportswear", "🏃"),
        ("Thrift/Wears (Okrika)", "thrift-wears-okrika", "♻️"),
        ("Caps & Hats", "caps-hats", "🧢"),
        ("Beauty Accessories", "beauty-accessories", "💄"),
    ]),
    ("Books & Academic Materials", "books-academic-materials", "📚", True, [
        ("Textbooks", "textbooks", "📘"),
        ("Handouts", "handouts", "📄"),
        ("Lecture Notes", "lecture-notes", "📝"),
        ("Past Questions", "past-questions", "❓"),
        ("E-books", "e-books", "📱"),
        ("Research Materials", "research-materials", "🔎"),
        ("Project Materials", "project-materials", "📁"),
        ("Calculators", "calculators", "🧮"),
        ("Lab Manuals", "lab-manuals", "🧪"),
        ("Stationery", "stationery", "✏️"),
        ("Novels", "novels", "📖"),
        ("Educational Guides", "educational-guides", "🧭"),
    ]),
    ("Food & Groceries", "food-groceries", "🍲", True, [
        ("Home-Cooked Meals", "home-cooked-meals", "🍛"),
        ("Snacks", "snacks", "🍪"),
        ("Drinks", "drinks", "🥤"),
        ("Groceries", "groceries", "🛒"),
        ("Fruits & Vegetables", "fruits-vegetables", "🥬"),
        ("Fast Food", "fast-food", "🍔"),
        ("Cakes & Pastries", "cakes-pastries", "🍰"),
        ("Campus Food Vendors", "campus-food-vendors", "🍱"),
        ("Water Supply", "water-supply", "💧"),
        ("Catering Services", "catering-services", "🍽️"),
    ]),
    ("Appliances & Hostel Essentials", "appliances-hostel-essentials", "🧰", False, [
        ("Fans", "fans", "🌀"),
        ("Refrigerators", "refrigerators", "🧊"),
        ("Microwaves", "microwaves", "♨️"),
        ("Electric Kettles", "electric-kettles", "☕"),
        ("Gas Cookers", "gas-cookers", "🔥"),
        ("Blenders", "blenders", "🥤"),
        ("Irons", "irons", "👕"),
        ("Extension Cables", "extension-cables", "🔌"),
        ("Lamps", "lamps", "💡"),
        ("Chairs & Tables", "chairs-tables", "🪑"),
        ("Mattresses", "mattresses", "🛏️"),
        ("Wardrobes", "wardrobes", "🚪"),
        ("Buckets & Bathroom Items", "buckets-bathroom-items", "🪣"),
    ]),
    ("Beauty & Personal Care", "beauty-personal-care", "💄", False, [
        ("Makeup Products", "makeup-products", "💄"),
        ("Skincare", "skincare", "🧴"),
        ("Hair Products", "hair-products", "💇"),
        ("Wigs", "wigs", "💇"),
        ("Barbing Tools", "barbing-tools", "💈"),
        ("Perfumes", "perfumes", "🧴"),
        ("Nail Accessories", "nail-accessories", "💅"),
        ("Salon Equipment", "salon-equipment", "💺"),
        ("Personal Hygiene Products", "personal-hygiene-products", "🧼"),
    ]),
    ("Pets & Pet Accessories", "pets-pet-accessories", "🐾", False, [
        ("Dogs", "dogs", "🐶"),
        ("Cats", "cats", "🐱"),
        ("Fish", "fish", "🐟"),
        ("Birds", "birds", "🐦"),
        ("Pet Food", "pet-food", "🥣"),
        ("Pet Accessories", "pet-accessories", "🦴"),
        ("Pet Grooming", "pet-grooming", "✂️"),
        ("Pet Care Services", "pet-care-services", "🩺"),
    ]),
    ("Sports & Fitness", "sports-fitness", "⚽", False, [
        ("Jerseys", "jerseys", "👕"),
        ("Football Boots", "football-boots", "👟"),
        ("Gym Equipment", "gym-equipment", "🏋️"),
        ("Dumbbells", "dumbbells", "🏋️"),
        ("Sports Bags", "sports-bags", "🎒"),
        ("Bicycles", "bicycles", "🚲"),
        ("Fitness Accessories", "fitness-accessories", "💪"),
        ("Sportswear", "sportswear", "🏃"),
        ("Campus Team Gear", "campus-team-gear", "🏆"),
    ]),
    ("Gaming & Entertainment", "gaming-entertainment", "🎮", False, [
        ("Gaming Consoles", "gaming-consoles", "🎮"),
        ("Video Games", "video-games", "🕹️"),
        ("Controllers", "controllers", "🎮"),
        ("Gaming Accessories", "gaming-accessories", "🎧"),
        ("Board Games", "board-games", "♟️"),
        ("Movies", "movies", "🎬"),
        ("Musical Instruments", "musical-instruments", "🎸"),
        ("Streaming Devices", "streaming-devices", "📺"),
    ]),
]


SERVICE_CATEGORIES = [
    ("Academic Services", "academic-services", "🎓", True, [
        ("Assignment Help", "assignment-help", "📝"),
        ("Tutoring", "tutoring", "👩‍🏫"),
        ("Project Assistance", "project-assistance", "📁"),
        ("Research Assistance", "research-assistance", "🔎"),
        ("CV Writing", "cv-writing", "📄"),
        ("Typing Services", "typing-services", "⌨️"),
        ("Printing & Photocopy", "printing-photocopy", "🖨️"),
        ("Graphic Design for Projects", "graphic-design-for-projects", "🎨"),
        ("Presentation Design", "presentation-design", "📊"),
        ("Exam Coaching", "exam-coaching", "📚"),
    ]),
    ("Tech & Digital Services", "tech-digital-services", "💻", True, [
        ("Web Development", "web-development", "🌐"),
        ("Mobile App Development", "mobile-app-development", "📱"),
        ("UI/UX Design", "ui-ux-design", "🎨"),
        ("Graphic Design", "graphic-design", "🖌️"),
        ("Video Editing", "video-editing", "🎬"),
        ("Photo Editing", "photo-editing", "📷"),
        ("Social Media Management", "social-media-management", "📣"),
        ("Digital Marketing", "digital-marketing", "📈"),
        ("Data Analysis", "data-analysis", "📊"),
        ("Cybersecurity Services", "cybersecurity-services", "🔐"),
        ("Computer Repairs", "computer-repairs", "🛠️"),
        ("Software Installation", "software-installation", "💿"),
    ]),
    ("Home & Hostel Services", "home-hostel-services", "🏠", False, [
        ("Cleaning Services", "cleaning-services", "🧹"),
        ("Laundry", "laundry", "🧺"),
        ("Plumbing", "plumbing", "🚰"),
        ("Electrical Repairs", "electrical-repairs", "💡"),
        ("Interior Decoration", "interior-decoration", "🛋️"),
        ("Furniture Assembly", "furniture-assembly", "🪑"),
        ("Painting", "painting", "🎨"),
        ("Moving/Logistics", "moving-logistics", "🚚"),
    ]),
    ("Beauty & Fashion Services", "beauty-fashion-services", "💄", False, [
        ("Makeup Artist", "makeup-artist", "💄"),
        ("Hair Styling", "hair-styling", "💇"),
        ("Barbing", "barbing", "💈"),
        ("Nail Technician", "nail-technician", "💅"),
        ("Fashion Designing", "fashion-designing", "🧵"),
        ("Wig Installation", "wig-installation", "💇"),
        ("Photography", "photography", "📷"),
    ]),
    ("Delivery & Logistics", "delivery-logistics", "🚚", True, [
        ("Campus Delivery", "campus-delivery", "🚲"),
        ("Food Delivery", "food-delivery", "🍱"),
        ("Errand Services", "errand-services", "🏃"),
        ("Moving Assistance", "moving-assistance", "📦"),
        ("Courier Services", "courier-services", "📮"),
    ]),
    ("Event Services", "event-services", "🎤", False, [
        ("DJs", "djs", "🎧"),
        ("MCs", "mcs", "🎙️"),
        ("Event Planning", "event-planning", "📋"),
        ("Photography", "photography", "📷"),
        ("Videography", "videography", "🎥"),
        ("Catering", "catering", "🍽️"),
        ("Decorations", "decorations", "🎈"),
    ]),
    ("Repair Services", "repair-services", "🛠️", True, [
        ("Phone Repairs", "phone-repairs", "📱"),
        ("Laptop Repairs", "laptop-repairs", "💻"),
        ("Appliance Repairs", "appliance-repairs", "🔧"),
        ("Vehicle Repairs", "vehicle-repairs", "🚗"),
        ("Gadget Unlocking", "gadget-unlocking", "🔓"),
    ]),
]


def seo_title(name):
    return f"{name} | UniTraX"


def category_description(name):
    return f"Browse {name.lower()} from trusted students and campus vendors on UniTraX."


def service_description(name):
    return f"Find {name.lower()} offered by students and campus vendors on UniTraX."


def get_or_create_by_slug_or_name(model, name, slug, defaults):
    obj = model.objects.filter(slug=slug).first()
    if obj is None:
        obj = model.objects.filter(name=name).first()
    if obj is None:
        return model.objects.create(name=name, slug=slug, **defaults)

    for key, value in defaults.items():
        setattr(obj, key, value)
    obj.slug = slug
    obj.name = name
    obj.save()
    return obj


def seed_tree(category_model, subcategory_model, rows, description_func):
    for category_index, (name, slug, icon, is_featured, subcategories) in enumerate(rows, start=1):
        category = get_or_create_by_slug_or_name(
            category_model,
            name,
            slug,
            {
                "icon": icon,
                "is_featured": is_featured,
                "sort_order": category_index,
                "seo_title": seo_title(name),
                "seo_description": description_func(name),
            },
        )

        for subcategory_index, (sub_name, sub_slug, sub_icon) in enumerate(subcategories, start=1):
            subcategory, _ = subcategory_model.objects.get_or_create(
                category=category,
                slug=sub_slug,
                defaults={"name": sub_name},
            )
            subcategory.name = sub_name
            subcategory.icon = sub_icon
            subcategory.sort_order = subcategory_index
            subcategory.seo_title = seo_title(sub_name)
            subcategory.seo_description = description_func(sub_name)
            subcategory.save()


def seed_categories(apps, schema_editor):
    Category = apps.get_model("marketplace", "Category")
    SubCategory = apps.get_model("marketplace", "SubCategory")
    ServiceCategory = apps.get_model("services", "ServiceCategory")
    ServiceSubCategory = apps.get_model("services", "ServiceSubCategory")

    seed_tree(Category, SubCategory, MARKETPLACE_CATEGORIES, category_description)
    seed_tree(ServiceCategory, ServiceSubCategory, SERVICE_CATEGORIES, service_description)


class Migration(migrations.Migration):

    dependencies = [
        ("marketplace", "0009_alter_category_options_alter_subcategory_options_and_more"),
        ("services", "0006_alter_servicecategory_options_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_categories, migrations.RunPython.noop),
    ]
