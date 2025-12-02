from django import template
from ..models import Branch

register = template.Library()

@register.simple_tag
def get_business_branches(business_id):
    """Get all active branches for a business"""
    try:
        branches = Branch.objects.filter(business_id=business_id, is_active=True)
        return branches
    except:
        return []

@register.simple_tag
def get_branch_name(branch_id):
    """Get the name of a branch by its ID"""
    try:
        branch = Branch.objects.get(id=branch_id)
        return branch.name
    except Branch.DoesNotExist:
        return "Unknown Branch"