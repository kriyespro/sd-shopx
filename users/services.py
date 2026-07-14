from django.shortcuts import get_object_or_404

from orders.models import Order
from orders import services as order_services

from .models import UserProfile


def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def get_user_order(user, order_number):
    """Return an order owned by the user, or 404."""
    order_services.link_guest_orders_to_user(user)
    return get_object_or_404(
        Order.objects.prefetch_related('items'),
        user=user,
        order_number=order_number,
    )
