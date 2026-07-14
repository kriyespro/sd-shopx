"""Order helpers: guest linking, confirm access, customer timeline."""
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.http import Http404

from .models import Order, ORDER_STATUS_CHOICES

RECENT_ORDERS_SESSION_KEY = 'recent_order_numbers'
ORDER_STATUS_FLOW = ['pending', 'confirmed', 'processing', 'shipped', 'delivered']
STATUS_LABELS = dict(ORDER_STATUS_CHOICES)


def link_guest_orders_to_user(user):
    """Attach orphan orders whose email matches the logged-in user."""
    if not user or not user.is_authenticated or not user.email:
        return 0
    return Order.objects.filter(
        user__isnull=True,
        email__iexact=user.email,
    ).update(user=user)


def resolve_order_user(email, authenticated_user=None):
    """Pick the user to attach at checkout."""
    if authenticated_user and authenticated_user.is_authenticated:
        link_guest_orders_to_user(authenticated_user)
        return authenticated_user
    if not email:
        return None
    return User.objects.filter(email__iexact=email).first()


def remember_recent_order(request, order_number):
    """Store order number in session so confirm page is not public."""
    recent = list(request.session.get(RECENT_ORDERS_SESSION_KEY, []))
    if order_number not in recent:
        recent.insert(0, order_number)
    request.session[RECENT_ORDERS_SESSION_KEY] = recent[:10]
    request.session.modified = True


def can_view_order_confirm(request, order):
    """Guest: session from checkout. Logged-in: ownership or matching email."""
    if not order:
        return False
    recent = request.session.get(RECENT_ORDERS_SESSION_KEY, [])
    if order.order_number in recent:
        return True
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        if order.user_id == user.id:
            return True
        if user.email and order.email.lower() == user.email.lower():
            return True
    return False


def get_order_for_confirm(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if not can_view_order_confirm(request, order):
        raise Http404
    return order


def get_order_timeline(order):
    """Build customer-facing status steps from current order.status."""
    status = order.status
    placed = {
        'key': 'placed',
        'label': 'Order Placed',
        'state': 'done',
        'date': order.created_at,
    }

    if status == 'cancelled':
        return [
            placed,
            {
                'key': 'cancelled',
                'label': STATUS_LABELS['cancelled'],
                'state': 'current',
                'date': order.updated_at,
            },
        ]

    if status == 'refunded':
        return [
            placed,
            {
                'key': 'refunded',
                'label': STATUS_LABELS['refunded'],
                'state': 'current',
                'date': order.updated_at,
            },
        ]

    try:
        current_idx = ORDER_STATUS_FLOW.index(status)
    except ValueError:
        current_idx = 0

    steps = [placed]
    for i, key in enumerate(ORDER_STATUS_FLOW):
        if key == 'pending':
            continue
        if i < current_idx:
            state = 'done'
        elif i == current_idx:
            state = 'current'
        else:
            state = 'upcoming'
        steps.append({
            'key': key,
            'label': STATUS_LABELS.get(key, key.title()),
            'state': state,
            'date': order.updated_at if state == 'current' else None,
        })
    return steps
