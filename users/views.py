from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import UserProfile, Wishlist
from products.models import Product
from orders.models import Order


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
            login(request, user)
            next_url = request.GET.get('next', 'users:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'users/login.jinja', {})


def user_logout(request):
    logout(request)
    return redirect('core:home')


@login_required
def dashboard(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    wishlist = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'users/dashboard.jinja', {
        'orders': orders,
        'wishlist': wishlist,
    })


@require_POST
def wishlist_toggle(request, product_id):
    if not request.user.is_authenticated:
        from django.http import JsonResponse
        return JsonResponse({'status': 'login_required'}, status=401)
    product = Product.objects.get(id=product_id)
    obj, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        obj.delete()
    if request.headers.get('HX-Request'):
        cart_count = request.session.get('cart', {})
        is_wishlisted = created
        return render(request, 'users/partials/wishlist_btn.jinja', {
            'product': product,
            'is_wishlisted': is_wishlisted,
        })
    return redirect('products:detail', slug=product.slug)
