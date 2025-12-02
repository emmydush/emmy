from django.urls import path
from . import views

app_name = "authentication"

urlpatterns = [
    path("login/", views.custom_login_view, name="login"),
    path("users/", views.user_list, name="user_list"),
    path("users/create/", views.create_user, name="create_user"),  # Add this line
    path("users/edit/<int:user_id>/", views.edit_user, name="edit_user"),
    path("users/edit-styled/<int:user_id>/", views.edit_user_styled, name="edit_user_styled"),
    path("profile/change-password/", views.change_password, name="change_password"),
    path("profile/", views.profile, name="profile"),
    path("set-user-language/", views.set_user_language, name="set_user_language"),
    path("create-business/", views.create_business_view, name="create_business"),
    path("register/", views.register_view, name="register"),
]