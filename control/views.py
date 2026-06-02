from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.views.decorators.http import require_POST
from products.models import Product, Category, ProductImage
from products.models import Review
from orders.models import Order, Payment, Refund
from .models import AdminLog
from . import services
from .forms import (ProductForm, CategoryForm, ProductImageForm,
                    OrderStatusForm, PaymentForm, RefundForm, RefundStatusForm)


class ControlAccessMixin:
    @method_decorator(staff_member_required(login_url='/sd/login/'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


# ── Dashboard ──────────────────────────────────────────────────────────────────

class DashboardView(ControlAccessMixin, View):
    def get(self, request):
        stats = services.get_dashboard_stats()
        recent_orders = services.get_recent_orders(5)
        recent_users = services.get_recent_signups(5)
        recent_logs = AdminLog.objects.select_related('admin')[:10]
        return render(request, 'control/dashboard.jinja', {
            'stats': stats,
            'recent_orders': recent_orders,
            'recent_users': recent_users,
            'recent_logs': recent_logs,
        })


class StatsCardView(ControlAccessMixin, View):
    def get(self, request):
        stats = services.get_dashboard_stats()
        return render(request, 'control/partials/_stats_card.jinja', {'stats': stats})


class ActivityFeedView(ControlAccessMixin, View):
    def get(self, request):
        logs = AdminLog.objects.select_related('admin')[:20]
        return render(request, 'control/partials/_activity_feed.jinja', {'logs': logs})


# ── Users / Customers ──────────────────────────────────────────────────────────

class UserListView(ControlAccessMixin, View):
    def get(self, request):
        q = request.GET.get('q', '')
        users = User.objects.select_related('profile').order_by('-date_joined')
        if q:
            users = (users.filter(email__icontains=q) |
                     users.filter(first_name__icontains=q) |
                     users.filter(last_name__icontains=q)).distinct()
        if request.headers.get('HX-Request'):
            return render(request, 'control/partials/_user_rows.jinja', {'users': users})
        return render(request, 'control/users.jinja', {'users': users, 'q': q})


class UserDetailView(ControlAccessMixin, View):
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        orders = Order.objects.filter(user=user).prefetch_related('items').order_by('-created_at')
        cstats = services.get_customer_stats(user)
        return render(request, 'control/user_detail.jinja', {
            'target_user': user,
            'orders': orders,
            'cstats': cstats,
        })


class CustomerListView(ControlAccessMixin, View):
    def get(self, request):
        q = request.GET.get('q', '')
        customers = services.get_customer_list(q)
        if request.headers.get('HX-Request'):
            return render(request, 'control/partials/_customer_rows.jinja', {'customers': customers})
        return render(request, 'control/customers.jinja', {'customers': customers, 'q': q})


class CustomerDetailView(ControlAccessMixin, View):
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        orders = Order.objects.filter(user=user).prefetch_related('items', 'payment').order_by('-created_at')
        cstats = services.get_customer_stats(user)
        wishlist = user.wishlist.select_related('product').all()
        return render(request, 'control/customer_detail.jinja', {
            'target_user': user,
            'orders': orders,
            'cstats': cstats,
            'wishlist': wishlist,
        })


@staff_member_required(login_url='/sd/login/')
@require_POST
def ban_user(request, pk):
    services.ban_user(pk, request.user, request)
    messages.success(request, 'User banned.')
    return redirect('control:users')


@staff_member_required(login_url='/sd/login/')
@require_POST
def unban_user(request, pk):
    services.unban_user(pk, request.user, request)
    messages.success(request, 'User unbanned.')
    return redirect('control:users')


# ── Products ───────────────────────────────────────────────────────────────────

class ProductListView(ControlAccessMixin, View):
    def get(self, request):
        q = request.GET.get('q', '')
        status = request.GET.get('status', '')
        products = Product.objects.select_related('category').order_by('-created_at')
        if q:
            products = products.filter(name__icontains=q)
        if status == 'active':
            products = products.filter(is_active=True)
        elif status == 'inactive':
            products = products.filter(is_active=False)
        elif status == 'featured':
            products = products.filter(is_featured=True)
        elif status == 'low_stock':
            products = products.filter(stock__lte=5)
        if request.headers.get('HX-Request'):
            return render(request, 'control/partials/_product_rows.jinja', {'products': products})
        return render(request, 'control/products.jinja', {
            'products': products, 'q': q, 'status_filter': status,
        })


class ProductCreateView(ControlAccessMixin, View):
    def get(self, request):
        form = ProductForm()
        return render(request, 'control/product_edit.jinja', {'form': form, 'product': None})

    def post(self, request):
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            services.log_action(request.user, 'create', 'Product', product.id,
                                f"Created product: {product.name}", request)
            messages.success(request, f'Product "{product.name}" created.')
            return redirect('control:product_edit', pk=product.pk)
        return render(request, 'control/product_edit.jinja', {'form': form, 'product': None})


class ProductEditView(ControlAccessMixin, View):
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        form = ProductForm(instance=product)
        image_form = ProductImageForm()
        images = product.images.all()
        return render(request, 'control/product_edit.jinja', {
            'form': form, 'product': product,
            'image_form': image_form, 'images': images,
        })

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            services.log_action(request.user, 'update', 'Product', product.id,
                                f"Updated product: {product.name}", request)
            messages.success(request, 'Product updated.')
            return redirect('control:product_edit', pk=pk)
        image_form = ProductImageForm()
        images = product.images.all()
        return render(request, 'control/product_edit.jinja', {
            'form': form, 'product': product,
            'image_form': image_form, 'images': images,
        })


class ProductImageUploadView(ControlAccessMixin, View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        form = ProductImageForm(request.POST, request.FILES)
        if form.is_valid():
            img = form.save(commit=False)
            img.product = product
            img.save()
            if img.is_primary:
                product.images.exclude(pk=img.pk).update(is_primary=False)
        messages.success(request, 'Image uploaded.')
        return redirect('control:product_edit', pk=pk)


@staff_member_required(login_url='/sd/login/')
@require_POST
def toggle_product_status(request, pk):
    field = request.POST.get('field', 'is_active')
    product = services.toggle_product_field(pk, field, request.user, request)
    if product and request.headers.get('HX-Request'):
        return render(request, 'control/partials/_product_status_toggle.jinja', {
            'product': product, 'field': field,
        })
    return redirect('control:products')


@staff_member_required(login_url='/sd/login/')
@require_POST
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    name = product.name
    product.delete()
    services.log_action(request.user, 'delete', 'Product', pk, f"Deleted product: {name}", request)
    messages.success(request, f'Product "{name}" deleted.')
    return redirect('control:products')


@staff_member_required(login_url='/sd/login/')
@require_POST
def delete_product_image(request, pk):
    img = get_object_or_404(ProductImage, pk=pk)
    product_pk = img.product_id
    img.image.delete(save=False)
    img.delete()
    return redirect('control:product_edit', pk=product_pk)


# ── Categories ─────────────────────────────────────────────────────────────────

class CategoryListView(ControlAccessMixin, View):
    def get(self, request):
        categories = Category.objects.order_by('position', 'name')
        return render(request, 'control/categories.jinja', {'categories': categories})


class CategoryCreateView(ControlAccessMixin, View):
    def get(self, request):
        form = CategoryForm()
        return render(request, 'control/category_edit.jinja', {'form': form, 'category': None})

    def post(self, request):
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            cat = form.save()
            services.log_action(request.user, 'create', 'Category', cat.id,
                                f"Created category: {cat.name}", request)
            messages.success(request, f'Category "{cat.name}" created.')
            return redirect('control:categories')
        return render(request, 'control/category_edit.jinja', {'form': form, 'category': None})


class CategoryEditView(ControlAccessMixin, View):
    def get(self, request, pk):
        cat = get_object_or_404(Category, pk=pk)
        form = CategoryForm(instance=cat)
        return render(request, 'control/category_edit.jinja', {'form': form, 'category': cat})

    def post(self, request, pk):
        cat = get_object_or_404(Category, pk=pk)
        form = CategoryForm(request.POST, request.FILES, instance=cat)
        if form.is_valid():
            form.save()
            services.log_action(request.user, 'update', 'Category', cat.id,
                                f"Updated category: {cat.name}", request)
            messages.success(request, 'Category updated.')
            return redirect('control:categories')
        return render(request, 'control/category_edit.jinja', {'form': form, 'category': cat})


@staff_member_required(login_url='/sd/login/')
@require_POST
def delete_category(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    name = cat.name
    cat.delete()
    services.log_action(request.user, 'delete', 'Category', pk, f"Deleted category: {name}", request)
    messages.success(request, f'Category "{name}" deleted.')
    return redirect('control:categories')


# ── Orders ─────────────────────────────────────────────────────────────────────

class OrderListView(ControlAccessMixin, View):
    def get(self, request):
        status = request.GET.get('status', '')
        q = request.GET.get('q', '')
        orders = Order.objects.select_related('user').prefetch_related('items').order_by('-created_at')
        if status:
            orders = orders.filter(status=status)
        if q:
            orders = orders.filter(order_number__icontains=q) | orders.filter(email__icontains=q)
            orders = orders.distinct()
        if request.headers.get('HX-Request'):
            return render(request, 'control/partials/_order_rows.jinja', {'orders': orders})
        return render(request, 'control/orders.jinja', {
            'orders': orders,
            'status_filter': status,
            'q': q,
            'status_choices': Order._meta.get_field('status').choices,
        })


class OrderDetailView(ControlAccessMixin, View):
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        form = OrderStatusForm(instance=order)
        payment = getattr(order, 'payment', None)
        payment_form = PaymentForm(instance=payment) if payment else PaymentForm(initial={'amount': order.total})
        refunds = order.refunds.all()
        refund_form = RefundForm(initial={'amount': order.total})
        return render(request, 'control/order_detail.jinja', {
            'order': order,
            'form': form,
            'payment': payment,
            'payment_form': payment_form,
            'refunds': refunds,
            'refund_form': refund_form,
        })

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            services.update_order_status(order.id, form.cleaned_data['status'], request.user, request)
            order.notes = form.cleaned_data.get('notes', '')
            order.save(update_fields=['notes'])
            messages.success(request, 'Order updated.')
            return redirect('control:order_detail', pk=pk)
        payment = getattr(order, 'payment', None)
        return render(request, 'control/order_detail.jinja', {
            'order': order, 'form': form,
            'payment': payment,
            'payment_form': PaymentForm(instance=payment),
            'refunds': order.refunds.all(),
            'refund_form': RefundForm(),
        })


class PaymentSaveView(ControlAccessMixin, View):
    def post(self, request, order_pk):
        order = get_object_or_404(Order, pk=order_pk)
        payment = getattr(order, 'payment', None)
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            p = form.save(commit=False)
            p.order = order
            p.save()
            services.log_action(request.user, 'update', 'Payment', p.id,
                                f"Payment updated for Order #{order.order_number}", request)
            messages.success(request, 'Payment saved.')
        return redirect('control:order_detail', pk=order_pk)


# ── Payments ───────────────────────────────────────────────────────────────────

class PaymentListView(ControlAccessMixin, View):
    def get(self, request):
        status = request.GET.get('status', '')
        q = request.GET.get('q', '')
        payments = services.get_payment_list(status, q)
        if request.headers.get('HX-Request'):
            return render(request, 'control/partials/_payment_rows.jinja', {'payments': payments})
        return render(request, 'control/payments.jinja', {
            'payments': payments,
            'status_filter': status,
            'q': q,
            'status_choices': Payment._meta.get_field('status').choices,
        })


# ── Refunds ────────────────────────────────────────────────────────────────────

class RefundListView(ControlAccessMixin, View):
    def get(self, request):
        status = request.GET.get('status', '')
        q = request.GET.get('q', '')
        refunds = services.get_refund_list(status, q)
        if request.headers.get('HX-Request'):
            return render(request, 'control/partials/_refund_rows.jinja', {'refunds': refunds})
        return render(request, 'control/refunds.jinja', {
            'refunds': refunds,
            'status_filter': status,
            'q': q,
            'status_choices': Refund._meta.get_field('status').choices,
            'pending_count': Refund.objects.filter(status__in=['requested', 'approved']).count(),
        })


class RefundCreateView(ControlAccessMixin, View):
    def post(self, request, order_pk):
        order = get_object_or_404(Order, pk=order_pk)
        form = RefundForm(request.POST)
        if form.is_valid():
            services.create_refund(
                order=order,
                amount=form.cleaned_data['amount'],
                reason=form.cleaned_data['reason'],
                notes=form.cleaned_data.get('notes', ''),
                admin_user=request.user,
                request=request,
            )
            messages.success(request, f'Refund created for Order #{order.order_number}.')
        return redirect('control:order_detail', pk=order_pk)


class RefundDetailView(ControlAccessMixin, View):
    def get(self, request, pk):
        refund = get_object_or_404(Refund, pk=pk)
        form = RefundStatusForm(instance=refund)
        return render(request, 'control/refund_detail.jinja', {'refund': refund, 'form': form})

    def post(self, request, pk):
        refund = get_object_or_404(Refund, pk=pk)
        form = RefundStatusForm(request.POST, instance=refund)
        if form.is_valid():
            services.update_refund_status(
                refund_id=refund.id,
                status=form.cleaned_data['status'],
                transaction_id=form.cleaned_data.get('transaction_id', ''),
                notes=form.cleaned_data.get('notes', ''),
                processed_at=form.cleaned_data.get('processed_at'),
                admin_user=request.user,
                request=request,
            )
            messages.success(request, 'Refund updated.')
            return redirect('control:refund_detail', pk=pk)
        return render(request, 'control/refund_detail.jinja', {'refund': refund, 'form': form})


# ── Inventory ──────────────────────────────────────────────────────────────────

class InventoryView(ControlAccessMixin, View):
    def get(self, request):
        low_only = request.GET.get('low', '') == '1'
        products = services.get_inventory_list(low_only)
        return render(request, 'control/inventory.jinja', {
            'products': products,
            'low_only': low_only,
        })

    def post(self, request):
        product_id = request.POST.get('product_id')
        new_stock = request.POST.get('stock')
        if product_id and new_stock is not None:
            product = get_object_or_404(Product, pk=product_id)
            old = product.stock
            product.stock = int(new_stock)
            product.save(update_fields=['stock'])
            services.log_action(request.user, 'update', 'Product', product.id,
                                f"Stock updated: {product.name} {old} → {new_stock}", request)
            if request.headers.get('HX-Request'):
                return render(request, 'control/partials/_stock_cell.jinja', {'product': product})
        return redirect('control:inventory')


# ── Reviews ────────────────────────────────────────────────────────────────────

class ReviewListView(ControlAccessMixin, View):
    def get(self, request):
        approved = request.GET.get('approved', '')
        reviews = Review.objects.select_related('user', 'product').order_by('-created_at')
        if approved == '1':
            reviews = reviews.filter(is_approved=True)
        elif approved == '0':
            reviews = reviews.filter(is_approved=False)
        return render(request, 'control/reviews.jinja', {
            'reviews': reviews,
            'approved_filter': approved,
            'pending_count': Review.objects.filter(is_approved=False).count(),
        })


@staff_member_required(login_url='/sd/login/')
@require_POST
def toggle_review(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.is_approved = not review.is_approved
    review.save(update_fields=['is_approved'])
    services.log_action(request.user, 'update', 'Review', review.id,
                        f"Review {'approved' if review.is_approved else 'rejected'}: {review.product.name}", request)
    if request.headers.get('HX-Request'):
        return render(request, 'control/partials/_review_row.jinja', {'review': review})
    return redirect('control:reviews')


@staff_member_required(login_url='/sd/login/')
@require_POST
def delete_review(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.delete()
    messages.success(request, 'Review deleted.')
    return redirect('control:reviews')
