"""
Download and attach free jewelry images from Unsplash to products.
Run: python manage.py download_images
"""
import urllib.request
import ssl
import os
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings
from products.models import Product, ProductImage, Category

# SSL context that skips certificate verification (safe for downloading public images)
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


# Curated free Unsplash images for each category/product type
HERO_IMAGES = {
    'engagement_rings': [
        'https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=1200&q=85&fit=crop',
        'https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=1200&q=85&fit=crop',
        'https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?w=1200&q=85&fit=crop',
        'https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=1200&q=85&fit=crop',
        'https://images.unsplash.com/photo-1629798083534-fd3db77eab23?w=1200&q=85&fit=crop',
        'https://images.unsplash.com/photo-1611591437281-460bfbe1220a?w=1200&q=85&fit=crop',
    ],
    'toi_et_moi': [
        'https://images.unsplash.com/photo-1573408301185-9519f94533f0?w=1200&q=85&fit=crop',
        'https://images.unsplash.com/photo-1617038260897-41a1f14a8ca0?w=1200&q=85&fit=crop',
        'https://images.unsplash.com/photo-1551614659-97a22a94a53c?w=1200&q=85&fit=crop',
        'https://images.unsplash.com/photo-1602173574767-37ac01994b2a?w=1200&q=85&fit=crop',
    ],
    'diamonds': [
        'https://images.unsplash.com/photo-1589308078059-be1415eab4c3?w=1200&q=85&fit=crop',
        'https://images.unsplash.com/photo-1594736797933-d0501ba2fe65?w=1200&q=85&fit=crop',
        'https://images.unsplash.com/photo-1571871271148-5d3e2b8c6dbf?w=1200&q=85&fit=crop',
    ],
    'necklaces': [
        'https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=1200&q=85&fit=crop',
        'https://images.unsplash.com/photo-1596944924616-7b38e7cfac36?w=1200&q=85&fit=crop',
        'https://images.unsplash.com/photo-1506630448388-4e683c67ddb0?w=1200&q=85&fit=crop',
    ],
    'earrings': [
        'https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?w=1200&q=85&fit=crop',
        'https://images.unsplash.com/photo-1567855286844-f0ee2a1f54cf?w=1200&q=85&fit=crop',
        'https://images.unsplash.com/photo-1590736704728-f4730bb30770?w=1200&q=85&fit=crop',
    ],
    'bracelets': [
        'https://images.unsplash.com/photo-1573408301185-9519f94533f0?w=1200&q=85&fit=crop',
        'https://images.unsplash.com/photo-1601121141461-9d6647bef0a1?w=1200&q=85&fit=crop',
        'https://images.unsplash.com/photo-1620656798579-1984d9e87df7?w=1200&q=85&fit=crop',
    ],
}

# Map category names to image pools
CATEGORY_MAP = {
    'Engagement Rings': 'engagement_rings',
    'Toi Et Moi Rings': 'toi_et_moi',
    'Lab-Grown Diamonds': 'diamonds',
    'Necklaces': 'necklaces',
    'Earrings': 'earrings',
    'Bracelets': 'bracelets',
}


class Command(BaseCommand):
    help = 'Downloads free jewelry images from Unsplash and attaches to products/categories'

    def handle(self, *args, **options):
        self.stdout.write('🖼️  Downloading jewelry images from Unsplash...\n')
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'products'), exist_ok=True)
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'categories'), exist_ok=True)

        # Download category images
        self._download_category_images()

        # Download product images
        self._download_product_images()

        self.stdout.write(self.style.SUCCESS('\n✅ All images downloaded!'))
        self.stdout.write('Restart the dev server to see images.')

    def _fetch_image(self, url, filename):
        """Download an image and return its bytes."""
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=20, context=SSL_CTX) as r:
                return r.read()
        except Exception as e:
            self.stdout.write(f'  ⚠️  Failed to download {filename}: {e}')
            return None

    def _download_category_images(self):
        self.stdout.write('\n📁 Category images:')
        for cat in Category.objects.all():
            if cat.image:
                self.stdout.write(f'  ⏭️  {cat.name} already has image')
                continue
            pool_key = CATEGORY_MAP.get(cat.name)
            if not pool_key:
                continue
            urls = HERO_IMAGES.get(pool_key, [])
            if not urls:
                continue
            url = urls[0]
            data = self._fetch_image(url, cat.name)
            if data:
                filename = f'category_{cat.slug}.jpg'
                cat.image.save(filename, ContentFile(data), save=True)
                self.stdout.write(f'  ✅ {cat.name}')

    def _download_product_images(self):
        self.stdout.write('\n📦 Product images:')
        products = Product.objects.all()
        image_counters = {k: 0 for k in HERO_IMAGES}

        for product in products:
            if product.images.exists():
                self.stdout.write(f'  ⏭️  {product.name[:40]} already has images')
                continue

            # Pick image pool based on category
            pool_key = CATEGORY_MAP.get(product.category.name, 'engagement_rings')
            urls = HERO_IMAGES.get(pool_key, [])
            if not urls:
                continue

            # Cycle through images
            idx = image_counters[pool_key] % len(urls)
            image_counters[pool_key] += 1

            # Download first (primary) image
            url = urls[idx]
            data = self._fetch_image(url, product.name)
            if data:
                filename = f'product_{product.slug[:30]}_1.jpg'
                img = ProductImage(product=product, is_primary=True, position=0,
                                   alt=product.name)
                img.image.save(filename, ContentFile(data), save=True)
                self.stdout.write(f'  ✅ {product.name[:40]}')

                # Try to get a second image from adjacent slot
                idx2 = (idx + 1) % len(urls)
                url2 = urls[idx2]
                data2 = self._fetch_image(url2, product.name + ' 2')
                if data2 and url2 != url:
                    filename2 = f'product_{product.slug[:30]}_2.jpg'
                    img2 = ProductImage(product=product, is_primary=False, position=1,
                                        alt=product.name)
                    img2.image.save(filename2, ContentFile(data2), save=True)
