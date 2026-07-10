from control.permissions import (
    can_access_control,
    is_superuser_role,
    get_user_role,
    role_display_label,
    IMPERSONATOR_SESSION_KEY,
)


def control_context(request):
    user = getattr(request, 'user', None)
    impersonator_id = None
    if hasattr(request, 'session'):
        impersonator_id = request.session.get(IMPERSONATOR_SESSION_KEY)
    return {
        'can_access_control': can_access_control(user) if user else False,
        'is_control_superuser': is_superuser_role(user) if user else False,
        'control_role': get_user_role(user) if user else None,
        'control_role_label': role_display_label(user) if user else '',
        'is_impersonating': bool(impersonator_id),
    }
