from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from .cart import Cart
from .services import cart_htmx_response, parse_quantity
from products.models import Product


def cart_detail(request):
    cart = Cart(request)
    cart.prune_invalid_products()
    return render(request, 'cart/cart.jinja', {'cart': cart})


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    cart.prune_invalid_products()
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = parse_quantity(request.POST.get('quantity', 1))
    metal = request.POST.get('metal', '')
    ring_size = request.POST.get('ring_size', '')
    cart.add(product=product, quantity=quantity, metal=metal, ring_size=ring_size)

    if request.headers.get('HX-Request'):
        return render(request, 'cart/partials/cart_count.jinja', {'cart': cart})
    messages.success(request, f'"{product.name}" added to cart.')
    return redirect('cart:detail')


@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = parse_quantity(request.POST.get('quantity', 1), minimum=0)
    if quantity > 0:
        cart.add(product=product, quantity=quantity, override_qty=True)
    else:
        cart.remove(product_id)
    if request.headers.get('HX-Request'):
        partial = 'drawer' if request.POST.get('view') == 'drawer' else 'items'
        return cart_htmx_response(request, cart, partial=partial)
    return redirect('cart:detail')


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    cart.prune_invalid_products()
    cart.remove(product_id)
    if request.headers.get('HX-Request'):
        partial = 'drawer' if request.POST.get('view') == 'drawer' else 'items'
        return cart_htmx_response(request, cart, partial=partial)
    return redirect('cart:detail')


def cart_drawer(request):
    """HTMX endpoint for cart drawer content."""
    cart = Cart(request)
    cart.prune_invalid_products()
    return render(request, 'cart/partials/cart_drawer_content.jinja', {'cart': cart})
