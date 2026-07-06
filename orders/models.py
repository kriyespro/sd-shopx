from django.db import models
from django.contrib.auth.models import User
from products.models import Product


ORDER_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('processing', 'Processing'),
    ('shipped', 'Shipped'),
    ('delivered', 'Delivered'),
    ('cancelled', 'Cancelled'),
    ('refunded', 'Refunded'),
]

PAYMENT_METHOD_CHOICES = [
    ('card', 'Credit / Debit Card'),
    ('upi', 'UPI'),
    ('bank_transfer', 'Bank Transfer'),
    ('cod', 'Cash on Delivery'),
    ('wallet', 'Wallet'),
    ('other', 'Other'),
]

PAYMENT_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('paid', 'Paid'),
    ('failed', 'Failed'),
    ('refunded', 'Refunded'),
    ('partially_refunded', 'Partially Refunded'),
]

REFUND_STATUS_CHOICES = [
    ('requested', 'Requested'),
    ('approved', 'Approved'),
    ('processing', 'Processing'),
    ('processed', 'Processed'),
    ('rejected', 'Rejected'),
]


class Order(models.Model):
    user = models.ForeignKey(User, related_name='orders', null=True, blank=True, on_delete=models.SET_NULL)
    order_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address_line1 = models.CharField(max_length=250)
    address_line2 = models.CharField(max_length=250, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    pincode = models.CharField(max_length=20)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            import uuid
            self.order_number = 'MX' + str(uuid.uuid4().hex[:8]).upper()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=500)
    metal_type = models.CharField(max_length=50, blank=True)
    ring_size = models.CharField(max_length=10, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    @property
    def total_price(self):
        # Unsaved admin inline rows have price=None before the form is filled.
        if self.price is None or self.quantity is None:
            return 0
        return self.price * self.quantity


class Payment(models.Model):
    order = models.OneToOneField(Order, related_name='payment', on_delete=models.CASCADE)
    method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='card')
    status = models.CharField(max_length=25, choices=PAYMENT_STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_id = models.CharField(max_length=200, blank=True)
    gateway = models.CharField(max_length=50, blank=True, help_text='e.g. Razorpay, Stripe')
    gateway_response = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment for {self.order.order_number} — {self.get_status_display()}"


class Refund(models.Model):
    order = models.ForeignKey(Order, related_name='refunds', on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, related_name='refunds', null=True, blank=True, on_delete=models.SET_NULL)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='requested')
    transaction_id = models.CharField(max_length=200, blank=True)
    processed_by = models.ForeignKey(User, null=True, blank=True, related_name='processed_refunds', on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"Refund #{self.id} for {self.order.order_number} — {self.get_status_display()}"
