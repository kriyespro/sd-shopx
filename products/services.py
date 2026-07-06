"""Product catalog helpers."""
from django.db.models import Q

from products.models import Category, Product


# Legacy / marketing slugs → real category slugs
SLUG_ALIASES = {
    'toi-et-moi': 'toi-et-moi-rings',
}

# Style and grouped collections backed by keyword filters (no extra DB rows required)
STYLE_COLLECTIONS = {
    'solitaire-rings': {
        'name': 'Solitaire Rings',
        'description': 'Classic solitaire engagement rings with IGI/GIA certified lab-grown center stones.',
        'parent_slug': 'engagement-rings',
        'keywords': ['solitaire'],
    },
    'halo-rings': {
        'name': 'Halo Rings',
        'description': 'Brilliant halo settings that amplify your center diamond.',
        'parent_slug': 'engagement-rings',
        'keywords': ['halo'],
    },
    'three-stone': {
        'name': 'Three Stone Rings',
        'description': 'Past, present, and future — three-stone diamond rings.',
        'parent_slug': 'engagement-rings',
        'keywords': ['three stone', 'three-stone'],
    },
    'vintage-rings': {
        'name': 'Vintage Rings',
        'description': 'Vintage-inspired settings with timeless character.',
        'parent_slug': 'engagement-rings',
        'keywords': ['vintage'],
    },
    'pave-rings': {
        'name': 'Pavé Rings',
        'description': 'Micro pavé bands that add extra sparkle to every angle.',
        'parent_slug': 'engagement-rings',
        'keywords': ['pavé', 'pave'],
    },
    'pendants': {
        'name': 'Pendants',
        'description': 'Diamond pendants and solitaire necklaces for everyday elegance.',
        'parent_slug': 'necklaces',
        'keywords': ['pendant'],
    },
    'bangles': {
        'name': 'Bangles',
        'description': 'Diamond bangles and tennis styles for the wrist.',
        'parent_slug': 'bracelets',
        'keywords': ['bangle'],
    },
    'jewelry': {
        'name': 'Jewelry',
        'description': 'Necklaces, earrings, bracelets, and more fine jewelry.',
        'category_slugs': ['necklaces', 'earrings', 'bracelets'],
    },
}


def _sort_products(queryset, sort):
    sort_map = {
        'az': 'name',
        'za': '-name',
        'price_asc': 'price',
        'price_desc': '-price',
        'newest': '-created_at',
    }
    return queryset.order_by(sort_map.get(sort, '-created_at'))


def _category_product_ids(category):
    child_ids = category.children.filter(is_active=True).values_list('id', flat=True)
    return [category.id, *child_ids]


def _virtual_category(slug, config):
    return Category(
        name=config['name'],
        slug=slug,
        description=config.get('description', ''),
        is_active=True,
    )


def _style_products(config):
    if 'category_slugs' in config:
        categories = Category.objects.filter(slug__in=config['category_slugs'], is_active=True)
        return Product.objects.filter(category__in=categories, is_active=True).prefetch_related('images')

    parent = Category.objects.filter(slug=config['parent_slug'], is_active=True).first()
    if not parent:
        return Product.objects.none()

    keyword_query = Q()
    for keyword in config.get('keywords', []):
        keyword_query |= Q(name__icontains=keyword)

    products = parent.products.filter(is_active=True).prefetch_related('images')
    if keyword_query:
        return products.filter(keyword_query)
    return products


def resolve_collection(slug, sort='newest'):
    """
    Return (category, products queryset) for a collection slug.
    Raises Category.DoesNotExist when slug cannot be resolved.
    """
    slug = SLUG_ALIASES.get(slug, slug)

    category = Category.objects.filter(slug=slug, is_active=True).first()
    if category:
        products = Product.objects.filter(
            category_id__in=_category_product_ids(category),
            is_active=True,
        ).prefetch_related('images')
        return category, _sort_products(products, sort)

    style = STYLE_COLLECTIONS.get(slug)
    if style:
        category = _virtual_category(slug, style)
        products = _style_products(style)
        return category, _sort_products(products, sort)

    raise Category.DoesNotExist(f'No collection for slug: {slug}')
