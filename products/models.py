from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.SET_NULL)
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['position', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('products:collection', kwargs={'slug': self.slug})


METAL_CHOICES = [
    ('yellow_gold', 'Yellow Gold'),
    ('white_gold', 'White Gold'),
    ('rose_gold', 'Rose Gold'),
    ('platinum', 'Platinum'),
    ('silver', 'Silver'),
]

DIAMOND_SHAPE_CHOICES = [
    ('round', 'Round'),
    ('oval', 'Oval'),
    ('pear', 'Pear'),
    ('cushion', 'Cushion'),
    ('emerald', 'Emerald'),
    ('heart', 'Heart'),
    ('radiant', 'Radiant'),
    ('marquise', 'Marquise'),
    ('princess', 'Princess'),
    ('asscher', 'Asscher'),
]

CERTIFICATION_CHOICES = [
    ('igi', 'IGI'),
    ('gia', 'GIA'),
    ('none', 'None'),
]


class Tag(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=500)
    slug = models.SlugField(unique=True, max_length=500)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=300, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    compare_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    metal_type = models.CharField(max_length=30, choices=METAL_CHOICES, blank=True)
    diamond_shape = models.CharField(max_length=30, choices=DIAMOND_SHAPE_CHOICES, blank=True)
    carat_weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    certification = models.CharField(max_length=10, choices=CERTIFICATION_CHOICES, default='none')
    stock = models.PositiveIntegerField(default=10)
    is_featured = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:490]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('products:detail', kwargs={'slug': self.slug})

    @property
    def primary_image(self):
        # Iterate .all() instead of a fresh .filter() so callers that
        # prefetch_related('images') get this for free instead of 1-2
        # extra queries per product in list views.
        images = list(self.images.all())
        for image in images:
            if image.is_primary:
                return image
        return images[0] if images else None

    @property
    def discount_percent(self):
        if self.compare_price and self.compare_price > self.price:
            return int(((self.compare_price - self.price) / self.compare_price) * 100)
        return 0


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    alt = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['position', 'id']

    def __str__(self):
        return f"{self.product.name} - Image {self.id}"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    metal = models.CharField(max_length=30, choices=METAL_CHOICES)
    ring_size = models.CharField(max_length=10, blank=True)
    price_modifier = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(default=5)

    def __str__(self):
        return f"{self.product.name} - {self.get_metal_display()} {self.ring_size}"

    @property
    def final_price(self):
        return self.product.price + self.price_modifier


class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}★)"
