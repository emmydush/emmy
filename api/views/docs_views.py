from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


class APIDocumentationView(APIView):
    """
    Simple API Documentation View
    """

    def get(self, request):
        api_endpoints = {
            "Authentication": {
                "POST /api/v1/auth/login/": "User login",
                "POST /api/v1/auth/logout/": "User logout",
                "POST /api/v1/auth/register/": "User registration",
                "GET /api/v1/auth/profile/": "Get user profile",
                "POST /api/v1/auth/password/change/": "Change user password",
            },
            "Products": {
                "GET /api/v1/products/": "List all products",
                "POST /api/v1/products/create/": "Create a new product",
                "GET /api/v1/products/{id}/": "Get product details",
                "PUT /api/v1/products/{id}/update/": "Update a product",
                "DELETE /api/v1/products/{id}/delete/": "Delete a product",
            },
            "Sales": {
                "GET /api/v1/sales/": "List all sales",
                "POST /api/v1/sales/create/": "Create a new sale",
                "GET /api/v1/sales/{id}/": "Get sale details",
            },
            "Dashboard": {
                "GET /api/v1/dashboard/stats/": "Get dashboard statistics",
            },
        }

        return Response(
            {
                "message": "Inventory Management System API",
                "version": "v1",
                "endpoints": api_endpoints,
                "authentication": "Session-based authentication required for most endpoints",
            }
        )