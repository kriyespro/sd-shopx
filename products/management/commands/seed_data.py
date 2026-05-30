"""
Seed command: populates the database with demo categories and products.
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import Category, Product, Tag


CATEGORIES = [
    ('Engagement Rings', 'Our finest IGI/GIA certified lab-grown diamond engagement rings. Each ring is crafted to perfection.'),
    ('Toi Et Moi Rings', 'Two-stone rings symbolizing two souls coming together. A romantic and modern design.'),
    ('Lab-Grown Diamonds', 'Loose IGI certified lab-grown diamonds in all shapes and sizes. Ethically sourced, chemically identical.'),
    ('Necklaces', 'Elegant diamond necklaces and pendants crafted in 18k gold and platinum.'),
    ('Earrings', 'From diamond studs to elaborate drops — our earring collection is timeless.'),
    ('Bracelets', 'Delicate diamond tennis bracelets and bangles for every occasion.'),
]

PRODUCTS = [
    # (name, category, price, compare_price, metal, shape, carat, is_featured, is_new_arrival)
    ('Round Brilliant Solitaire Engagement Ring', 'Engagement Rings', 85000, 95000, 'yellow_gold', 'round', 1.0, True, False),
    ('Oval Lab Diamond Halo Ring', 'Engagement Rings', 112000, 130000, 'white_gold', 'oval', 1.5, True, True),
    ('Pear Shaped Pavé Band Ring', 'Engagement Rings', 94000, None, 'rose_gold', 'pear', 1.2, True, False),
    ('Emerald Cut Three Stone Ring', 'Engagement Rings', 145000, 165000, 'platinum', 'emerald', 2.0, False, True),
    ('Cushion Halo Diamond Ring', 'Engagement Rings', 78000, 88000, 'yellow_gold', 'cushion', 0.8, True, False),
    ('Marquise Solitaire Gold Ring', 'Engagement Rings', 67000, None, 'yellow_gold', 'marquise', 0.75, False, True),
    ('Round & Oval Diamond Toi Et Moi', 'Toi Et Moi Rings', 98000, 110000, 'white_gold', 'oval', 'auto', True, True),
    ('Oval & Pear Two Stone Ring', 'Toi Et Moi Rings', 105000, None, 'rose_gold', 'pear', 'auto', True, False),
    ('Heart & Round Toi Et Moi', 'Toi Et Moi Rings', 88000, 98000, 'yellow_gold', 'heart', 'auto', False, True),
    ('Emerald & Oval Double Stone Ring', 'Toi Et Moi Rings', 125000, None, 'platinum', 'emerald', 'auto', True, False),
    ('1.5ct Round IGI Certified Diamond', 'Lab-Grown Diamonds', 45000, 55000, '', 'round', 1.5, True, False),
    ('2ct Oval Lab-Grown Diamond', 'Lab-Grown Diamonds', 62000, None, '', 'oval', 2.0, True, True),
    ('1ct Pear Shape Lab Diamond', 'Lab-Grown Diamonds', 38000, 42000, '', 'pear', 1.0, False, False),
    ('Diamond Tennis Necklace 18k Gold', 'Necklaces', 55000, 65000, 'yellow_gold', '', 'auto', True, True),
    ('Oval Diamond Solitaire Pendant', 'Necklaces', 32000, None, 'white_gold', 'oval', 0.5, False, False),
    ('Diamond Stud Earrings 18k', 'Earrings', 28000, 35000, 'yellow_gold', 'round', 0.5, True, False),
    ('Oval Halo Diamond Earrings', 'Earrings', 42000, None, 'white_gold', 'oval', 0.75, False, True),
    ('Diamond Tennis Bracelet', 'Bracelets', 68000, 80000, 'white_gold', 'round', 2.0, True, True),
    ('Bangle Diamond 18k Rose Gold', 'Bracelets', 45000, None, 'rose_gold', '', 'auto', False, False),
    ('Heart Diamond Drop Earrings', 'Earrings', 38000, 44000, 'rose_gold', 'heart', 0.6, True, True),
]

class Command(BaseCommand):
    help = 'Seeds the database with demo jewelry products and categories'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Seeding database...')

        # Create tags
        toi_tag, _ = Tag.objects.get_or_create(name='Toi Et Moi', slug='toi-et-moi')
        featured_tag, _ = Tag.objects.get_or_create(name='Featured', slug='featured')

        # Create categories
        category_map = {}
        for cat_name, cat_desc in CATEGORIES:
            cat, created = Category.objects.get_or_create(
                name=cat_name,
                defaults={'slug': slugify(cat_name), 'description': cat_desc}
            )
            category_map[cat_name] = cat
            if created:
                self.stdout.write(f'  ✅ Category: {cat_name}')

        # Create products
        for prod_data in PRODUCTS:
            name, cat_name, price, compare_price, metal, shape, carat, is_featured, is_new = prod_data
            cat = category_map.get(cat_name)
            if not cat:
                continue

            slug = slugify(name)[:490]
            # Make unique slug if needed
            if Product.objects.filter(slug=slug).exists():
                slug = slug + '-2'

            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'slug': slug,
                    'category': cat,
                    'price': price,
                    'compare_price': compare_price,
                    'metal_type': metal,
                    'diamond_shape': shape if shape else '',
                    'carat_weight': carat if carat != 'auto' and carat else None,
                    'certification': 'igi',
                    'stock': 5,
                    'is_featured': is_featured,
                    'is_new_arrival': is_new,
                    'short_description': f'Handcrafted {name.lower()}. IGI certified lab-grown diamond.',
                    'description': f'Discover our stunning {name}. Each piece is handcrafted with IGI/GIA certified lab-grown diamonds. Available in multiple metal options. Free worldwide shipping included.',
                }
            )
            if created:
                if 'Toi Et Moi' in name or cat_name == 'Toi Et Moi Rings':
                    product.tags.add(toi_tag)
                self.stdout.write(f'  ✅ Product: {name}')

        self.stdout.write(self.style.SUCCESS(
            f'\n🎉 Seeded {len(CATEGORIES)} categories and {len(PRODUCTS)} products!'
        ))
        self.stdout.write('  Run: python manage.py runserver')
        self.stdout.write('  Visit: http://127.0.0.1:8000/')
