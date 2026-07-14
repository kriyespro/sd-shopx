from jinja2 import Environment
from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse as django_reverse
from django.contrib.messages import get_messages
from django.middleware.csrf import get_token
from django.utils.html import format_html


def url(viewname, *args, **kwargs):
    """
    Wrapper around Django's reverse() that supports both positional and keyword arguments.
    Usage in templates:
        url('app:view')
        url('app:view', slug='my-slug')
        url('app:view', product_id=5)
    """
    if kwargs:
        return django_reverse(viewname, kwargs=kwargs)
    elif args:
        return django_reverse(viewname, args=args)
    return django_reverse(viewname)


def csrf_input(request):
    """Return HTML hidden input with CSRF token."""
    return format_html(
        '<input type="hidden" name="csrfmiddlewaretoken" value="{0}">',
        get_token(request)
    )


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': static,
        'url': url,
        'get_messages': get_messages,
        'csrf_input': csrf_input,
        'site_brand': getattr(settings, 'SITE_BRAND', 'Mnxworld'),
        'site_email': getattr(settings, 'SITE_EMAIL', 'hello@mnxstore.com'),
        'site_tagline': getattr(settings, 'SITE_TAGLINE', ''),
        'default_product_image': getattr(
            settings,
            'DEFAULT_PRODUCT_IMAGE',
            'https://images.unsplash.com/photo-1605100804763-247f67b3557e'
            '?w=600&q=80&fit=crop&crop=center',
        ),
        'default_site_logo': static(getattr(settings, 'DEFAULT_SITE_LOGO', 'images/mnxworld-logo-nav.png')),
        'default_site_logo_full': static(getattr(settings, 'DEFAULT_SITE_LOGO_FULL', 'images/mnxworld-logo.png')),
        'default_site_mark': static(getattr(settings, 'DEFAULT_SITE_MARK', 'images/mnxworld-mark.png')),
    })
    env.install_null_translations()
    return env
