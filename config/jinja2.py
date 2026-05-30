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
        'site_brand': getattr(settings, 'SITE_BRAND', 'MnxStore'),
        'site_email': getattr(settings, 'SITE_EMAIL', 'hello@mnxstore.com'),
        'site_tagline': getattr(settings, 'SITE_TAGLINE', ''),
    })
    env.install_null_translations()
    return env
