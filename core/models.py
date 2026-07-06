from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.db.utils import OperationalError, ProgrammingError

SITE_SETTINGS_CACHE_KEY = 'core:site_settings'


class SiteSettings(models.Model):
    """Singleton row holding common public store info, edited at /sd/."""

    site_name = models.CharField(max_length=200, default='MnxStore')
    logo = models.ImageField(upload_to='site/', blank=True, null=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    whatsapp_number = models.CharField(max_length=30, blank=True)
    address_line1 = models.CharField(max_length=250, blank=True)
    address_line2 = models.CharField(max_length=250, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=20, blank=True)
    business_hours = models.CharField(max_length=200, blank=True, help_text='e.g. Mon–Sat: 10am–6pm IST')
    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete(SITE_SETTINGS_CACHE_KEY)

    def delete(self, *args, **kwargs):
        pass

    @property
    def full_address(self):
        parts = [
            self.address_line1, self.address_line2,
            self.city, self.state, self.pincode, self.country,
        ]
        return ', '.join(p for p in parts if p)

    @classmethod
    def load(cls):
        obj = cache.get(SITE_SETTINGS_CACHE_KEY)
        if obj is not None:
            return obj
        try:
            obj, _ = cls.objects.get_or_create(pk=1, defaults={
                'site_name': getattr(settings, 'SITE_BRAND', 'MnxStore'),
                'email': getattr(settings, 'SITE_EMAIL', ''),
            })
        except (OperationalError, ProgrammingError):
            # Migration for this model hasn't been applied yet — fall back
            # to settings.py defaults instead of taking every page down.
            return cls(
                site_name=getattr(settings, 'SITE_BRAND', 'MnxStore'),
                email=getattr(settings, 'SITE_EMAIL', ''),
            )
        cache.set(SITE_SETTINGS_CACHE_KEY, obj, 300)
        return obj
