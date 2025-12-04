from threading import local

# Thread-local storage for the current business context
_thread_locals = local()


def set_current_business(business):
    """Set the current business in thread-local storage"""
    _thread_locals.current_business = business


def get_current_business():
    """Get the current business from thread-local storage"""
    return getattr(_thread_locals, "current_business", None)


def clear_current_business():
    """Clear the current business from thread-local storage"""
    if hasattr(_thread_locals, "current_business"):
        delattr(_thread_locals, "current_business")


def set_current_branch(branch):
    """Set the current branch in thread-local storage"""
    _thread_locals.current_branch = branch


def get_current_branch():
    """Get the current branch from thread-local storage"""
    return getattr(_thread_locals, "current_branch", None)


def clear_current_branch():
    """Clear the current branch from thread-local storage"""
    if hasattr(_thread_locals, "current_branch"):
        delattr(_thread_locals, "current_branch")


class BusinessContextMiddleware:
    """
    Middleware to manage business context for multi-tenancy.
    This middleware ensures that each request has access to the current business context.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # NOTE: do not clear the thread-local business context here. Tests and
        # some programmatic flows call `set_current_business` outside of a
        # request (for example in test setup). Clearing the context at the
        # start of each request removes that information and causes views to
        # behave as if no business is selected. Instead, prefer to read the
        # business from the session if present and only set it when applicable.
        # Try to get the current business from the session
        business_id = request.session.get("current_business_id")
        if business_id:
            try:
                from .models import Business

                business = Business.objects.get(id=business_id)
                set_current_business(business)
            except Business.DoesNotExist:
                # If the business doesn't exist, clear the session value
                request.session.pop("current_business_id", None)

        # Try to get the current branch from the session
        branch_id = request.session.get("current_branch_id")
        if branch_id:
            try:
                from .models import Branch

                branch = Branch.objects.get(id=branch_id)
                set_current_branch(branch)
            except Branch.DoesNotExist:
                # If the branch doesn't exist, clear the session value
                request.session.pop("current_branch_id", None)

        response = self.get_response(request)

        # Clear the business context after the request is processed so that
        # programmatic callers (tests) that set the context before a request
        # will have it available during the request, but it won't leak to
        # subsequent requests or tests.
        clear_current_business()
        clear_current_branch()

        return response
