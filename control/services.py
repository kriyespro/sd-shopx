from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import timedelta
from decimal import Decimal
from products.models import Product, Category
from orders.models import Order, Payment, Refund
from .models import AdminLog


def get_dashboard_stats():
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    paid_statuses = ['confirmed', 'processing', 'shipped', 'delivered']

    revenue_total = Order.objects.filter(status__in=paid_statuses).aggregate(t=Sum('total'))['t'] or Decimal('0')
    revenue_today = Order.objects.filter(status__in=paid_statuses, created_at__date=today).aggregate(t=Sum('total'))['t'] or Decimal('0')
    revenue_month = Order.objects.filter(status__in=paid_statuses, created_at__gte=month_ago).aggregate(t=Sum('total'))['t'] or Decimal('0')

    return {
        'total_users': User.objects.count(),
        'signups_today': User.objects.filter(date_joined__date=today).count(),
        'signups_week': User.objects.filter(date_joined__gte=week_ago).count(),
        'total_products': Product.objects.filter(is_active=True).count(),
        'low_stock_products': Product.objects.filter(is_active=True, stock__lte=5).count(),
        'total_categories': Category.objects.filter(is_active=True).count(),
        'total_orders': Order.objects.count(),
        'orders_today': Order.objects.filter(created_at__date=today).count(),
        'orders_pending': Order.objects.filter(status='pending').count(),
        'orders_processing': Order.objects.filter(status__in=['confirmed', 'processing']).count(),
        'orders_refunded': Order.objects.filter(status='refunded').count(),
        'revenue_total': revenue_total,
        'revenue_today': revenue_today,
        'revenue_month': revenue_month,
        'refunds_pending': Refund.objects.filter(status__in=['requested', 'approved']).count(),
        'payments_failed': Payment.objects.filter(status='failed').count(),
    }


def get_recent_orders(limit=10):
    return Order.objects.select_related('user').prefetch_related('items')[:limit]


def get_recent_signups(limit=10):
    return User.objects.order_by('-date_joined').select_related('profile')[:limit]


def get_customer_list(q=''):
    users = User.objects.filter(orders__isnull=False).distinct().select_related('profile')
    if q:
        users = users.filter(
            Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        )
    return users.annotate(
        order_count=Count('orders'),
        lifetime_value=Sum('orders__total'),
    ).order_by('-lifetime_value')


def get_customer_stats(user):
    orders = Order.objects.filter(user=user)
    paid = orders.filter(status__in=['confirmed', 'processing', 'shipped', 'delivered'])
    return {
        'total_orders': orders.count(),
        'lifetime_value': paid.aggregate(t=Sum('total'))['t'] or Decimal('0'),
        'avg_order_value': paid.aggregate(t=Sum('total'))['t'] / paid.count() if paid.count() else Decimal('0'),
        'cancelled': orders.filter(status='cancelled').count(),
        'refunded': orders.filter(status='refunded').count(),
    }


def get_payment_list(status='', q=''):
    payments = Payment.objects.select_related('order', 'order__user').order_by('-created_at')
    if status:
        payments = payments.filter(status=status)
    if q:
        payments = payments.filter(
            Q(order__order_number__icontains=q) |
            Q(transaction_id__icontains=q) |
            Q(order__email__icontains=q)
        )
    return payments


def get_refund_list(status='', q=''):
    refunds = Refund.objects.select_related('order', 'order__user', 'processed_by').order_by('-requested_at')
    if status:
        refunds = refunds.filter(status=status)
    if q:
        refunds = refunds.filter(
            Q(order__order_number__icontains=q) |
            Q(order__email__icontains=q)
        )
    return refunds


def create_refund(order, amount, reason, notes, admin_user, request=None):
    payment = getattr(order, 'payment', None)
    refund = Refund.objects.create(
        order=order,
        payment=payment,
        amount=amount,
        reason=reason,
        notes=notes,
        status='requested',
    )
    log_action(admin_user, 'create', 'Refund', refund.id,
               f"Refund requested for Order #{order.order_number} — ₹{amount}", request)
    return refund


def update_refund_status(refund_id, status, transaction_id, notes, processed_at, admin_user, request=None):
    refund = Refund.objects.get(pk=refund_id)
    old_status = refund.status
    refund.status = status
    refund.transaction_id = transaction_id
    refund.notes = notes
    if processed_at:
        refund.processed_at = processed_at
    if status == 'processed' and not refund.processed_at:
        refund.processed_at = timezone.now()
    refund.processed_by = admin_user
    refund.save()
    log_action(admin_user, 'update', 'Refund', refund.id,
               f"Refund #{refund.id} status: {old_status} → {status}", request)
    return refund


def get_inventory_list(low_stock_only=False):
    products = Product.objects.select_related('category').order_by('stock')
    if low_stock_only:
        products = products.filter(stock__lte=5)
    return products


def ban_user(user_id, admin_user, request=None):
    user = User.objects.get(pk=user_id)
    if user.is_superuser:
        raise ValueError('Cannot ban a superuser.')
    user.is_active = False
    user.save()
    log_action(admin_user, 'ban', 'User', user.id, f"Banned user {user.email}", request)
    return user


def unban_user(user_id, admin_user, request=None):
    user = User.objects.get(pk=user_id)
    user.is_active = True
    user.save()
    log_action(admin_user, 'unban', 'User', user.id, f"Unbanned user {user.email}", request)
    return user


def assign_user_role(user_id, role, admin_user, request=None):
    from users.models import ROLE_CUSTOMER, ROLE_STORE_MANAGER, UserProfile

    if role not in (ROLE_CUSTOMER, ROLE_STORE_MANAGER):
        raise ValueError('Invalid role.')
    user = User.objects.get(pk=user_id)
    if user.is_superuser:
        raise ValueError('Cannot change role of a superuser.')
    profile, _ = UserProfile.objects.get_or_create(user=user)
    old = profile.role
    profile.role = role
    profile.save(update_fields=['role'])
    profile.sync_staff_flag()
    log_action(
        admin_user, 'update', 'User', user.id,
        f"Role for {user.email}: {old} → {role}", request,
    )
    return profile


def start_impersonation(request, target_user_id, admin_user):
    target = User.objects.get(pk=target_user_id)
    if target.is_superuser or target.is_staff:
        raise ValueError('Cannot impersonate staff or superusers.')
    from control.permissions import IMPERSONATOR_SESSION_KEY
    request.session[IMPERSONATOR_SESSION_KEY] = admin_user.pk
    log_action(
        admin_user, 'impersonate', 'User', target.pk,
        f"Started impersonating {target.email}", request,
    )
    return target


def stop_impersonation(request):
    from control.permissions import IMPERSONATOR_SESSION_KEY
    from django.contrib.auth import login
    from django.contrib.auth.models import User

    admin_id = request.session.pop(IMPERSONATOR_SESSION_KEY, None)
    if not admin_id:
        return None
    admin = User.objects.filter(pk=admin_id, is_superuser=True).first()
    if admin:
        login(request, admin, backend='django.contrib.auth.backends.ModelBackend')
        log_action(admin, 'impersonate', 'User', admin.pk, 'Stopped impersonation', request)
    return admin


def update_order_status(order_id, new_status, admin_user, request=None):
    order = Order.objects.get(pk=order_id)
    old_status = order.status
    order.status = new_status
    order.save()
    log_action(admin_user, 'order_status', 'Order', order.id,
               f"Order #{order.order_number} status: {old_status} → {new_status}", request)
    return order


def toggle_product_field(product_id, field, admin_user, request=None):
    allowed = {'is_active', 'is_featured', 'is_new_arrival'}
    if field not in allowed:
        return None
    product = Product.objects.get(pk=product_id)
    new_val = not getattr(product, field)
    setattr(product, field, new_val)
    product.save(update_fields=[field])
    log_action(admin_user, 'update', 'Product', product.id,
               f"Toggled {field}={new_val} on {product.name}", request)
    return product


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
