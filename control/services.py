from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from products.models import Product, Category
from orders.models import Order
from .models import AdminLog


def get_dashboard_stats():
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)

    return {
        'total_users': User.objects.count(),
        'signups_today': User.objects.filter(date_joined__date=today).count(),
        'signups_week': User.objects.filter(date_joined__gte=week_ago).count(),
        'total_products': Product.objects.filter(is_active=True).count(),
        'total_categories': Category.objects.filter(is_active=True).count(),
        'total_orders': Order.objects.count(),
        'orders_today': Order.objects.filter(created_at__date=today).count(),
        'orders_pending': Order.objects.filter(status='pending').count(),
        'revenue_total': sum(o.total for o in Order.objects.filter(status__in=['confirmed', 'processing', 'shipped', 'delivered'])),
        'revenue_today': sum(o.total for o in Order.objects.filter(created_at__date=today)),
    }


def get_recent_orders(limit=10):
    return Order.objects.select_related('user').prefetch_related('items')[:limit]


def get_recent_signups(limit=10):
    return User.objects.order_by('-date_joined').select_related('profile')[:limit]


def ban_user(user_id, admin_user, request=None):
    user = User.objects.get(pk=user_id)
    user.is_active = False
    user.save()
    AdminLog.objects.create(
        admin=admin_user,
        action='ban',
        target_model='User',
        target_id=user.id,
        description=f"Banned user {user.email}",
        ip_address=_get_ip(request),
    )
    return user


def unban_user(user_id, admin_user, request=None):
    user = User.objects.get(pk=user_id)
    user.is_active = True
    user.save()
    AdminLog.objects.create(
        admin=admin_user,
        action='unban',
        target_model='User',
        target_id=user.id,
        description=f"Unbanned user {user.email}",
        ip_address=_get_ip(request),
    )
    return user


def update_order_status(order_id, new_status, admin_user, request=None):
    order = Order.objects.get(pk=order_id)
    old_status = order.status
    order.status = new_status
    order.save()
    AdminLog.objects.create(
        admin=admin_user,
        action='order_status',
        target_model='Order',
        target_id=order.id,
        description=f"Order #{order.order_number} status: {old_status} → {new_status}",
        ip_address=_get_ip(request),
    )
    return order


def log_action(admin_user, action, model, obj_id, description, request=None):
    AdminLog.objects.create(
        admin=admin_user,
        action=action,
        target_model=model,
        target_id=obj_id,
        description=description,
        ip_address=_get_ip(request),
    )


def _get_ip(request):
    if not request:
        return None
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0]
    return request.META.get('REMOTE_ADDR')
