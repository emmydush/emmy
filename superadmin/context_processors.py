from .middleware import get_current_business


def current_business(request):
    """
    Context processor to add current business context to all templates
    """
    current_business = get_current_business()
    return {"current_business": current_business}
