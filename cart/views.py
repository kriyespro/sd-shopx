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
    result = cart.add(product=product, quantity=quantity, metal=metal, ring_size=ring_size)

    if result.get('out_of_stock'):
        msg = f'"{product.name}" is out of stock.'
    elif result.get('clamped'):
        msg = f'Only {result["quantity"]} of "{product.name}" available — cart updated.'
    elif result.get('ok'):
        msg = f'"{product.name}" added to cart.'
    else:
        msg = f'Could not add "{product.name}" to cart.'

    if request.headers.get('HX-Request'):
        return render(request, 'cart/partials/cart_add_oob.jinja', {
            'cart': cart,
            'cart_message': msg,
        })

    if result.get('ok'):
        messages.success(request, msg)
    else:
        messages.warning(request, msg)
    return redirect('cart:detail')


@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = parse_quantity(request.POST.get('quantity', 1), minimum=0)
    if quantity > 0:
        result = cart.add(product=product, quantity=quantity, override_qty=True)
        if result.get('clamped') and not request.headers.get('HX-Request'):
            messages.warning(
                request,
                f'Only {result["quantity"]} of "{product.name}" in stock.',
            )
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
