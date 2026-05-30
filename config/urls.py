from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = f'{settings.SITE_BRAND} Administration'
admin.site.site_title = settings.SITE_BRAND
admin.site.index_title = 'Store Management'

urlpatterns = [
    path('sd/', admin.site.urls),
    path('admin/', include('control.urls', namespace='control')),
    path('', include('core.urls')),
    path('shop/', include('products.urls')),
    path('cart/', include('cart.urls')),
    path('checkout/', include('orders.urls')),
    path('accounts/', include('users.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
