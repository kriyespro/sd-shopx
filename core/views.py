from django.shortcuts import render, get_object_or_404
from products.models import Category, Product


def home(request):
    featured_products = Product.objects.filter(is_featured=True, is_active=True)[:8]
    new_arrivals = Product.objects.filter(is_new_arrival=True, is_active=True)[:8]
    categories = Category.objects.filter(parent=None, is_active=True)[:6]
    toi_et_moi = Product.objects.filter(
        tags__name__icontains='toi et moi', is_active=True
    )[:6]
    context = {
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'categories': categories,
        'toi_et_moi': toi_et_moi,
    }
    return render(request, 'core/home.jinja', context)


def about(request):
    return render(request, 'core/about.jinja', {})


def contact(request):
    return render(request, 'core/contact.jinja', {})
