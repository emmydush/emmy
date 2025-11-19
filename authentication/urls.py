from django.urls import path
from . import views

app_name = "authentication"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("login/success/", views.login_success_view, name="login_success"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("profile/", views.profile_view, name="profile"),
    path("set-language/", views.set_user_language, name="set_user_language"),
    path("password-reset/", views.password_reset_view, name="password_reset"),
    path("users/", views.user_list_view, name="user_list"),
    path("users/create/", views.create_user_view, name="create_user"),
    path("users/edit/<int:user_id>/", views.edit_user_view, name="edit_user"),
    path("business-details/", views.business_details_view, name="business_details"),
    path("create-business/", views.create_business_view, name="create_business"),
]
