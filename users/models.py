from django.db import models
from django.contrib.auth.models import User
from products.models import Product


ROLE_CUSTOMER = 'customer'
ROLE_STORE_MANAGER = 'store_manager'

ROLE_CHOICES = [
    (ROLE_CUSTOMER, 'Customer'),
    (ROLE_STORE_MANAGER, 'Store Manager'),
]


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    address_line1 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='India')
    pincode = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    def sync_staff_flag(self):
        """Keep User.is_staff aligned with store_manager role (never touch superusers)."""
        user = self.user
        if user.is_superuser:
            return
        should_be_staff = self.role == ROLE_STORE_MANAGER
        if user.is_staff != should_be_staff:
            user.is_staff = should_be_staff
            user.save(update_fields=['is_staff'])


class Wishlist(models.Model):
    user = models.ForeignKey(User, related_name='wishlist', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='wishlisted_by', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} → {self.product.name}"
