from django import template
from ..utils import check_user_permission

register = template.Library()


@register.simple_tag
def check_permission(user, permission_type):
    """
    Template tag to check if a user has a specific permission.

    Usage: {% check_permission user 'can_edit' as can_edit %}
    """
    # Account owners have access to everything
    if user.role.lower() == "admin":
        return True

    return check_user_permission(user, permission_type)
