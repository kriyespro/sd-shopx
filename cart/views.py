from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from .cart import Cart
from products.models import Product


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/cart.jinja', {'cart': cart})


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    metal = request.POST.get('metal', '')
    ring_size = request.POST.get('ring_size', '')
    cart.add(product=product, quantity=quantity, metal=metal, ring_size=ring_size)

    # HTMX response: return cart count
    if request.headers.get('HX-Request'):
        return render(request, 'cart/partials/cart_count.jinja', {'cart': cart})
    messages.success(request, f'"{product.name}" added to cart.')
    return redirect('cart:detail')


@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    if quantity > 0:
        cart.add(product=product, quantity=quantity, override_qty=True)
    else:
        cart.remove(product_id)
    if request.headers.get('HX-Request'):
        return render(request, 'cart/partials/cart_items.jinja', {'cart': cart})
    return redirect('cart:detail')


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    cart.remove(product_id)
    if request.headers.get('HX-Request'):
        return render(request, 'cart/partials/cart_items.jinja', {'cart': cart})
    return redirect('cart:detail')


def cart_drawer(request):
    """HTMX endpoint for cart drawer content."""
    cart = Cart(request)
    return render(request, 'cart/partials/cart_drawer_content.jinja', {'cart': cart})
