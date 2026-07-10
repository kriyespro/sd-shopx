"""
Seed command: populates the database with demo categories and products.
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import Category, Product, Tag
from products.services import CATALOG_CATEGORIES, ensure_catalog_categories


PRODUCTS = [
    # (name, category_slug, price, compare_price, metal, shape, carat, is_featured, is_new_arrival)
    ('Round Brilliant Solitaire Engagement Ring', 'engagement-rings', 85000, 95000, 'yellow_gold', 'round', 1.0, True, False),
    ('Oval Lab Diamond Halo Ring', 'engagement-rings', 112000, 130000, 'white_gold', 'oval', 1.5, True, True),
    ('Pear Shaped Pavé Band Ring', 'engagement-rings', 94000, None, 'rose_gold', 'pear', 1.2, True, False),
    ('Emerald Cut Three Stone Ring', 'engagement-rings', 145000, 165000, 'platinum', 'emerald', 2.0, False, True),
    ('Cushion Halo Diamond Ring', 'engagement-rings', 78000, 88000, 'yellow_gold', 'cushion', 0.8, True, False),
    ('Marquise Solitaire Gold Ring', 'engagement-rings', 67000, None, 'yellow_gold', 'marquise', 0.75, False, True),
    ('Round & Oval Diamond Toi Et Moi', 'toi-et-moi-rings', 98000, 110000, 'white_gold', 'oval', 'auto', True, True),
    ('Oval & Pear Two Stone Ring', 'toi-et-moi-rings', 105000, None, 'rose_gold', 'pear', 'auto', True, False),
    ('Heart & Round Toi Et Moi', 'toi-et-moi-rings', 88000, 98000, 'yellow_gold', 'heart', 'auto', False, True),
    ('Emerald & Oval Double Stone Ring', 'toi-et-moi-rings', 125000, None, 'platinum', 'emerald', 'auto', True, False),
    ('1.5ct Round IGI Certified Diamond', 'lab-grown-diamonds', 45000, 55000, '', 'round', 1.5, True, False),
    ('2ct Oval Lab-Grown Diamond', 'lab-grown-diamonds', 62000, None, '', 'oval', 2.0, True, True),
    ('1ct Pear Shape Lab Diamond', 'lab-grown-diamonds', 38000, 42000, '', 'pear', 1.0, False, False),
    ('Diamond Tennis Necklace 18k Gold', 'necklaces', 55000, 65000, 'yellow_gold', '', 'auto', True, True),
    ('Oval Diamond Solitaire Pendant', 'necklaces', 32000, None, 'white_gold', 'oval', 0.5, False, False),
    ('Diamond Stud Earrings 18k', 'earrings', 28000, 35000, 'yellow_gold', 'round', 0.5, True, False),
    ('Oval Halo Diamond Earrings', 'earrings', 42000, None, 'white_gold', 'oval', 0.75, False, True),
    ('Diamond Tennis Bracelet', 'bracelets', 68000, 80000, 'white_gold', 'round', 2.0, True, True),
    ('Bangle Diamond 18k Rose Gold', 'bracelets', 45000, None, 'rose_gold', '', 'auto', False, False),
    ('Heart Diamond Drop Earrings', 'earrings', 38000, 44000, 'rose_gold', 'heart', 0.6, True, True),
]


class Command(BaseCommand):
    help = 'Seeds the database with demo jewelry products and categories'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')

        Tag.objects.get_or_create(name='Toi Et Moi', slug='toi-et-moi')
        Tag.objects.get_or_create(name='Featured', slug='featured')
        toi_tag = Tag.objects.get(slug='toi-et-moi')

        ensure_catalog_categories()
        category_map = {
            slug: Category.objects.get(slug=slug)
            for slug in CATALOG_CATEGORIES
        }
        self.stdout.write(f'  Categories ready: {len(category_map)}')

        created_count = 0
        for prod_data in PRODUCTS:
            name, cat_slug, price, compare_price, metal, shape, carat, is_featured, is_new = prod_data
            cat = category_map.get(cat_slug)
            if not cat:
                continue

            slug = slugify(name)[:490]
            product, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'category': cat,
                    'price': price,
                    'compare_price': compare_price,
                    'metal_type': metal,
                    'diamond_shape': shape if shape else '',
                    'carat_weight': carat if carat != 'auto' and carat else None,
                    'certification': 'igi',
                    'stock': 5,
                    'is_active': True,
                    'is_featured': is_featured,
                    'is_new_arrival': is_new,
                    'short_description': f'Handcrafted {name.lower()}. IGI certified lab-grown diamond.',
                    'description': (
                        f'Discover our stunning {name}. Each piece is handcrafted with '
                        f'IGI/GIA certified lab-grown diamonds. Available in multiple metal '
                        f'options. Free worldwide shipping included.'
                    ),
                },
            )
            if created:
                created_count += 1
                if 'toi et moi' in name.lower() or cat_slug == 'toi-et-moi-rings':
                    product.tags.add(toi_tag)
                self.stdout.write(f'  Product: {name}')

        self.stdout.write(self.style.SUCCESS(
            f'Done. {len(CATALOG_CATEGORIES)} categories, {created_count} new products '
            f'({Product.objects.filter(is_active=True).count()} active total).'
        ))
