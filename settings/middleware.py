from django.utils.deprecation import MiddlewareMixin
from .utils import log_activity, apply_email_settings
import json
import threading

# Thread local storage for current user
_user = threading.local()


class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log user activities
    """

    def process_request(self, request):
        # Store the current user in thread local storage
        _user.value = getattr(request, "user", None)

        # Store the request body for POST requests
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            request._body_copy = request.body
        return None

    def process_response(self, request, response):
        # Clear the thread local storage
        if hasattr(_user, "value"):
            del _user.value

        # Skip logging for static files and media
        if (
            request.path.startswith("/static/")
            or request.path.startswith("/media/")
            or request.path.startswith("/favicon.ico")
        ):
            return response

        # Skip logging for AJAX requests that are not important
        if request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest" and not self.should_log_ajax(request):
            return response

        # Log login/logout events
        if (
            "/accounts/login/" in request.path
            and request.method == "POST"
            and response.status_code == 302
        ):
            # Successful login
            user = getattr(request, "user", None)
            if user and user.is_authenticated:
                log_activity(
                    user=user,
                    action="LOGIN",
                    model_name="Authentication",
                    object_repr=f"User {user.username} logged in",
                    change_message=f'IP: {self.get_client_ip(request)}, User Agent: {request.META.get("HTTP_USER_AGENT", "")[:100]}',
                    request=request,
                )

        elif (
            "/accounts/logout/" in request.path
            and request.method == "POST"
            and response.status_code == 302
        ):
            # Successful logout
            user = getattr(request, "user", None)
            if user and user.is_authenticated:
                log_activity(
                    user=user,
                    action="LOGOUT",
                    model_name="Authentication",
                    object_repr=f"User {user.username} logged out",
                    change_message=f'IP: {self.get_client_ip(request)}, User Agent: {request.META.get("HTTP_USER_AGENT", "")[:100]}',
                    request=request,
                )

        # Log model changes for CRUD operations
        self.log_model_changes(request, response)

        return response

    def should_log_ajax(self, request):
        """
        Determine if AJAX requests should be logged
        """
        # Log AJAX requests that modify data
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            return True
        return False

    def log_model_changes(self, request, response):
        """
        Log changes to models based on request method and URL patterns
        """
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return

        # Skip if not a data modification request
        if request.method not in ["POST", "PUT", "PATCH", "DELETE"]:
            return

        # Extract model name from URL
        model_name = self.extract_model_name(request.path)
        if not model_name:
            return

        # Log based on HTTP method
        if request.method == "POST" and "/create/" in request.path:
            log_activity(
                user=user,
                action="CREATE",
                model_name=model_name,
                object_repr=f"Created new {model_name}",
                change_message=self.get_request_details(request),
                request=request,
            )
        elif request.method in ["PUT", "PATCH"] and "/update/" in request.path:
            log_activity(
                user=user,
                action="UPDATE",
                model_name=model_name,
                object_repr=f"Updated {model_name}",
                change_message=self.get_request_details(request),
                request=request,
            )
        elif request.method == "DELETE":
            log_activity(
                user=user,
                action="DELETE",
                model_name=model_name,
                object_repr=f"Deleted {model_name}",
                change_message=self.get_request_details(request),
                request=request,
            )
        elif request.method == "POST" and "/receive/" in request.path:
            log_activity(
                user=user,
                action="UPDATE",
                model_name=model_name,
                object_repr=f"Received items for {model_name}",
                change_message=self.get_request_details(request),
                request=request,
            )

    def extract_model_name(self, path):
        """
        Extract model name from URL path
        """
        # Common model paths
        model_paths = {
            "/products/": "Product",
            "/suppliers/": "Supplier",
            "/customers/": "Customer",
            "/expenses/": "Expense",
            "/purchases/": "PurchaseOrder",
            "/sales/": "Sale",
            "/categories/": "Category",
            "/accounts/users/": "User",
        }

        for url_path, model_name in model_paths.items():
            if url_path in path:
                return model_name

        return None

    def get_request_details(self, request):
        """
        Get details about the request for logging
        """
        details = []

        # Add form data for POST requests
        if request.method == "POST":
            if request.content_type == "application/x-www-form-urlencoded":
                for key, value in request.POST.items():
                    # Skip CSRF token and passwords
                    if key != "csrfmiddlewaretoken" and "password" not in key.lower():
                        details.append(f"{key}: {value}")
            elif request.content_type == "application/json":
                try:
                    data = json.loads(request.body.decode("utf-8"))
                    for key, value in data.items():
                        if "password" not in key.lower():
                            details.append(f"{key}: {value}")
                except:
                    pass

        # Add query parameters
        for key, value in request.GET.items():
            details.append(f"GET {key}: {value}")

        return "\n".join(details)

    def get_client_ip(self, request):
        """
        Get the client's IP address from the request.
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class EmailSettingsMiddleware(MiddlewareMixin):
    """
    Middleware to apply email settings from the database to Django's email configuration.
    This ensures that the correct email settings are always used for sending emails.
    """

    def process_request(self, request):
        # Apply email settings from database
        apply_email_settings()
        return None


def get_current_user():
    """
    Get the current user from thread local storage
    """
    return getattr(_user, "value", None)
