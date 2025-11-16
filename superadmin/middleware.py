from threading import local

# Thread-local storage for the current business context
_thread_locals = local()

def set_current_business(business):
    """Set the current business in thread-local storage"""
    _thread_locals.current_business = business

def get_current_business():
    """Get the current business from thread-local storage"""
    return getattr(_thread_locals, 'current_business', None)

def clear_current_business():
    """Clear the current business from thread-local storage"""
    if hasattr(_thread_locals, 'current_business'):
        delattr(_thread_locals, 'current_business')

class BusinessContextMiddleware:
    """
    Middleware to manage business context for multi-tenancy.
    This middleware ensures that each request has access to the current business context.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Clear any existing business context at the start of each request
        clear_current_business()
        
        # Try to get the current business from the session
        business_id = request.session.get('current_business_id')
        if business_id:
            try:
                from .models import Business
                business = Business.objects.get(id=business_id)
                set_current_business(business)
            except Business.DoesNotExist:
                # If the business doesn't exist, clear the session value
                request.session.pop('current_business_id', None)
        
        response = self.get_response(request)
        
        # Note: We don't clear the business context here anymore
        # It will be cleared at the start of the next request
        
        return response