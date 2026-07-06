from django.shortcuts import render, get_object_or_404
from django.http import Http404
from products.models import Category, Product
from products.services import resolve_collection


def collection(request, slug):
    try:
        category, products = resolve_collection(slug, sort=request.GET.get('sort', 'newest'))
    except Category.DoesNotExist as exc:
        raise Http404('No Category matches the given query.') from exc

    context = {
        'category': category,
        'products': products,
        'sort': request.GET.get('sort', 'newest'),
        'product_count': products.count(),
    }
    return render(request, 'products/collection.jinja', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    images = product.images.all()
    related = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(id=product.id).prefetch_related('images')[:4]
    reviews = product.reviews.filter(is_approved=True)[:10]
    context = {
        'product': product,
        'images': images,
        'related': related,
        'reviews': reviews,
    }
    return render(request, 'products/product_detail.jinja', context)


def shop(request):
    """All products view."""
    products = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')
    categories = Category.objects.filter(parent=None, is_active=True)

    # Filter by category
    cat_slug = request.GET.get('category')
    if cat_slug:
        products = products.filter(category__slug=cat_slug)

    # Filter by metal
    metal = request.GET.get('metal')
    if metal:
        products = products.filter(metal_type=metal)

    # Filter by shape
    shape = request.GET.get('shape')
    if shape:
        products = products.filter(diamond_shape=shape)

    # Price filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Sorting
    sort = request.GET.get('sort', 'newest')
    sort_map = {
        'az': 'name',
        'za': '-name',
        'price_asc': 'price',
        'price_desc': '-price',
        'newest': '-created_at',
    }
    products = products.order_by(sort_map.get(sort, '-created_at'))

    context = {
        'products': products,
        'categories': categories,
        'sort': sort,
        'product_count': products.count(),
        'selected_category': cat_slug,
        'selected_metal': metal,
        'selected_shape': shape,
    }
    return render(request, 'products/shop.jinja', context)


def search(request):
    q = request.GET.get('q', '')
    products = Product.objects.none()
    if q:
        products = Product.objects.filter(
            is_active=True,
            name__icontains=q
        ) | Product.objects.filter(
            is_active=True,
            description__icontains=q
        )
        products = products.distinct().prefetch_related('images')
    return render(request, 'products/search.jinja', {'products': products, 'query': q})
