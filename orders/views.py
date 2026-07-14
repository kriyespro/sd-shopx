from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from cart.cart import Cart
from products.models import Product
from .models import Order, OrderItem
from .forms import CheckoutForm
from . import services


def checkout(request):
    cart = Cart(request)
    cart.prune_invalid_products()
    if len(cart) == 0:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart:detail')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            items = list(cart)
            if not items:
                messages.warning(request, 'Your cart is empty.')
                return redirect('cart:detail')

            with transaction.atomic():
                locked_products = Product.objects.select_for_update().in_bulk(
                    [item['product'].id for item in items]
                )
                shortages = [
                    item['name'] for item in items
                    if locked_products[item['product'].id].stock < item['quantity']
                ]
                if shortages:
                    messages.error(
                        request,
                        f"Not enough stock for: {', '.join(shortages)}. Please update your cart.",
                    )
                    return redirect('cart:detail')

                order_user = services.resolve_order_user(
                    form.cleaned_data['email'],
                    request.user if request.user.is_authenticated else None,
                )
                order = Order(
                    user=order_user,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    email=form.cleaned_data['email'],
                    phone=form.cleaned_data.get('phone', ''),
                    address_line1=form.cleaned_data['address_line1'],
                    address_line2=form.cleaned_data.get('address_line2', ''),
                    city=form.cleaned_data['city'],
                    state=form.cleaned_data['state'],
                    country=form.cleaned_data.get('country', 'India'),
                    pincode=form.cleaned_data['pincode'],
                    subtotal=cart.get_total_price(),
                    shipping_cost=0,
                    total=cart.get_total_price(),
                )
                order.save()

                for item in items:
                    product = locked_products[item['product'].id]
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=item['name'],
                        metal_type=item.get('metal', ''),
                        ring_size=item.get('ring_size', ''),
                        price=item['price'],
                        quantity=item['quantity'],
                    )
                    product.stock -= item['quantity']
                    product.save(update_fields=['stock'])

                cart.clear()

            services.remember_recent_order(request, order.order_number)
            return redirect('orders:confirm', order_number=order.order_number)
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
            }
        form = CheckoutForm(initial=initial)

    return render(request, 'orders/checkout.jinja', {'cart': cart, 'form': form})


def order_confirm(request, order_number):
    order = services.get_order_for_confirm(request, order_number)
    return render(request, 'orders/order_confirm.jinja', {'order': order})
