"""Mission Control role helpers and access mixins."""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.decorators import method_decorator

from users.models import ROLE_CUSTOMER, ROLE_STORE_MANAGER, UserProfile

CONTROL_LOGIN_URL = '/admin/login/'
IMPERSONATOR_SESSION_KEY = 'impersonator_id'


def get_or_create_profile(user):
    if not user or not user.is_authenticated:
        return None
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def get_user_role(user):
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return 'superuser'
    profile = get_or_create_profile(user)
    if profile and profile.role == ROLE_STORE_MANAGER and user.is_staff:
        return ROLE_STORE_MANAGER
    return ROLE_CUSTOMER


def is_superuser_role(user):
    return bool(user and user.is_authenticated and user.is_superuser)


def is_store_manager(user):
    return get_user_role(user) == ROLE_STORE_MANAGER


def can_access_control(user):
    return is_superuser_role(user) or is_store_manager(user)


def can_manage_users(user):
    return is_superuser_role(user)


def can_ban_users(user):
    return is_superuser_role(user)


def can_impersonate(user):
    return is_superuser_role(user)


def can_view_activity_log(user):
    return is_superuser_role(user)


def role_display_label(user):
    role = get_user_role(user)
    return {
        'superuser': 'Superuser',
        ROLE_STORE_MANAGER: 'Store Manager',
        ROLE_CUSTOMER: 'Customer',
    }.get(role, 'Customer')


def control_required(view_func):
    @wraps(view_func)
    @login_required(login_url=CONTROL_LOGIN_URL)
    def _wrapped(request, *args, **kwargs):
        if not can_access_control(request.user):
            return redirect('users:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


def superuser_required(view_func):
    @wraps(view_func)
    @login_required(login_url=CONTROL_LOGIN_URL)
    def _wrapped(request, *args, **kwargs):
        if not is_superuser_role(request.user):
            if can_access_control(request.user):
                raise PermissionDenied
            return redirect('users:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


class ControlAccessMixin:
    login_url = CONTROL_LOGIN_URL

    @method_decorator(login_required(login_url=CONTROL_LOGIN_URL))
    def dispatch(self, request, *args, **kwargs):
        if not can_access_control(request.user):
            return redirect('users:dashboard')
        return super().dispatch(request, *args, **kwargs)


class SuperuserRequiredMixin(ControlAccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), self.login_url)
        if not is_superuser_role(request.user):
            if can_access_control(request.user):
                raise PermissionDenied
            return redirect('users:dashboard')
        return super(ControlAccessMixin, self).dispatch(request, *args, **kwargs)
