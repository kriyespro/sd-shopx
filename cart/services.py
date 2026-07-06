"""Cart HTMX response helpers."""
from django.shortcuts import render


def parse_quantity(raw, *, default=1, minimum=1, maximum=999):
    """Safely coerce a form quantity value, clamped to a sane range."""
    try:
        quantity = int(raw)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(quantity, maximum))


def cart_htmx_response(request, cart, *, partial='items'):
    """Return the correct cart partial for HTMX requests."""
    if partial == 'drawer':
        return render(request, 'cart/partials/cart_drawer_oob.jinja', {'cart': cart})
    return render(request, 'cart/partials/cart_items_oob.jinja', {'cart': cart})


def cart_view_mode(request):
    return request.POST.get('view') or request.headers.get('HX-Target', '')
