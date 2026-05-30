from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from cart.cart import Cart
from .models import Order, OrderItem
from .forms import CheckoutForm


def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart:detail')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order(
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
            if request.user.is_authenticated:
                order.user = request.user
            order.save()

            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    product_name=item['name'],
                    metal_type=item.get('metal', ''),
                    ring_size=item.get('ring_size', ''),
                    price=item['price'],
                    quantity=item['quantity'],
                )

            cart.clear()
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
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'orders/order_confirm.jinja', {'order': order})
