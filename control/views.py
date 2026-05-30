from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.views.decorators.http import require_POST
from products.models import Product, Category, ProductImage
from orders.models import Order
from .models import AdminLog
from . import services
from .forms import ProductForm, CategoryForm, ProductImageForm, OrderStatusForm


class ControlAccessMixin:
    @method_decorator(staff_member_required(login_url='/sd/login/'))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


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


class UserListView(ControlAccessMixin, View):
    def get(self, request):
        q = request.GET.get('q', '')
        users = User.objects.select_related('profile').order_by('-date_joined')
        if q:
            users = users.filter(email__icontains=q) | users.filter(first_name__icontains=q) | users.filter(last_name__icontains=q)
            users = users.distinct()
        if request.headers.get('HX-Request'):
            return render(request, 'control/partials/_user_rows.jinja', {'users': users})
        return render(request, 'control/users.jinja', {'users': users, 'q': q})


class UserDetailView(ControlAccessMixin, View):
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        orders = Order.objects.filter(user=user).order_by('-created_at')
        return render(request, 'control/user_detail.jinja', {'target_user': user, 'orders': orders})


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


class ProductListView(ControlAccessMixin, View):
    def get(self, request):
        q = request.GET.get('q', '')
        products = Product.objects.select_related('category').order_by('-created_at')
        if q:
            products = products.filter(name__icontains=q)
        if request.headers.get('HX-Request'):
            return render(request, 'control/partials/_product_rows.jinja', {'products': products})
        return render(request, 'control/products.jinja', {'products': products, 'q': q})


class ProductCreateView(ControlAccessMixin, View):
    def get(self, request):
        form = ProductForm()
        return render(request, 'control/product_edit.jinja', {'form': form, 'product': None})

    def post(self, request):
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            services.log_action(request.user, 'create', 'Product', product.id, f"Created product: {product.name}", request)
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
            services.log_action(request.user, 'update', 'Product', product.id, f"Updated product: {product.name}", request)
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
            services.log_action(request.user, 'create', 'Category', cat.id, f"Created category: {cat.name}", request)
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
            services.log_action(request.user, 'update', 'Category', cat.id, f"Updated category: {cat.name}", request)
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


class OrderListView(ControlAccessMixin, View):
    def get(self, request):
        status = request.GET.get('status', '')
        orders = Order.objects.select_related('user').prefetch_related('items').order_by('-created_at')
        if status:
            orders = orders.filter(status=status)
        if request.headers.get('HX-Request'):
            return render(request, 'control/partials/_order_rows.jinja', {'orders': orders})
        return render(request, 'control/orders.jinja', {
            'orders': orders,
            'status_filter': status,
            'status_choices': Order._meta.get_field('status').choices,
        })


class OrderDetailView(ControlAccessMixin, View):
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        form = OrderStatusForm(instance=order)
        return render(request, 'control/order_detail.jinja', {'order': order, 'form': form})

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            services.update_order_status(order.id, form.cleaned_data['status'], request.user, request)
            order.notes = form.cleaned_data.get('notes', '')
            order.save(update_fields=['notes'])
            messages.success(request, 'Order updated.')
            return redirect('control:order_detail', pk=pk)
        return render(request, 'control/order_detail.jinja', {'order': order, 'form': form})


class ActivityFeedView(ControlAccessMixin, View):
    def get(self, request):
        logs = AdminLog.objects.select_related('admin')[:20]
        return render(request, 'control/partials/_activity_feed.jinja', {'logs': logs})
