from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from .models import UserProfile, Wishlist
from .forms import ProfileEditForm
from . import services
from products.models import Product
from orders.models import Order
from orders import services as order_services
from control.permissions import can_access_control


def register(request):
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
        else:
            user = User.objects.create_user(
                username=email, email=email, password=password1,
                first_name=first_name, last_name=last_name
            )
            UserProfile.objects.create(user=user)
            order_services.link_guest_orders_to_user(user)
            login(request, user)
            messages.success(request, f'Welcome, {first_name}!')
            return redirect('users:dashboard')
    return render(request, 'users/register.jinja', {})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user:
            order_services.link_guest_orders_to_user(user)
            login(request, user)
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('users:dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'users/login.jinja', {})


def user_logout(request):
    logout(request)
    return redirect('core:home')


@login_required
def dashboard(request):
    order_services.link_guest_orders_to_user(request.user)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    order_count = Order.objects.filter(user=request.user).count()
    wishlist = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'users/dashboard.jinja', {
        'orders': orders,
        'order_count': order_count,
        'wishlist': wishlist,
        'show_mission_control_link': can_access_control(request.user),
    })


@login_required
def order_list(request):
    order_services.link_guest_orders_to_user(request.user)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'users/order_list.jinja', {'orders': orders})


@login_required
def order_detail(request, order_number):
    order = services.get_user_order(request.user, order_number)
    timeline = order_services.get_order_timeline(order)
    payment = getattr(order, 'payment', None)
    return render(request, 'users/order_detail.jinja', {
        'order': order,
        'timeline': timeline,
        'payment': payment,
    })


@login_required
def profile_edit(request):
    profile = services.get_or_create_profile(request.user)
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('users:profile')
    else:
        form = ProfileEditForm(instance=profile, user=request.user)
    return render(request, 'users/profile.jinja', {'form': form})


@require_POST
def wishlist_toggle(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    if not request.user.is_authenticated:
        if request.headers.get('HX-Request'):
            response = HttpResponse(status=204)
            response['HX-Redirect'] = reverse('users:login')
            return response
        return redirect('users:login')
    obj, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        obj.delete()
    if request.headers.get('HX-Request'):
        return render(request, 'users/partials/wishlist_btn.jinja', {
            'product': product,
            'is_wishlisted': created,
        })
    return redirect('products:detail', slug=product.slug)
