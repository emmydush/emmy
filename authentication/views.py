from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm
from .models import User
from superadmin.models import Business
from superadmin.forms import BusinessDetailsForm
from django.conf import settings
from django.utils import translation


def login_view(request):
    if request.method == "POST":
        try:
            form = CustomAuthenticationForm(request, data=request.POST)
            if form.is_valid():
                username = form.cleaned_data.get("username")
                password = form.cleaned_data.get("password")
                user = authenticate(request, username=username, password=password)

                if user is not None:
                    login(request, user)
                    # If the user has a saved preferred language, apply it to the session
                    try:
                        user_lang = getattr(user, "language", None)
                        if user_lang:
                            request.session["_language"] = user_lang
                            translation.activate(user_lang)
                    except Exception:
                        # Be defensive: don't break login flow if language application fails
                        pass
                    # Handle remember me functionality if needed
                    if not form.cleaned_data.get("remember_me"):
                        request.session.set_expiry(0)

                    # Check if user has a business associated with them
                    user_businesses = user.businesses.all()
                    if not user_businesses.exists():
                        # Check if user owns a business (for business owners)
                        owned_businesses = Business.objects.filter(owner=user)
                        if not owned_businesses.exists():
                            # Redirect to business details page for business owners
                            return redirect("authentication:business_details")
                        else:
                            # Set the first owned business as the current business in session
                            first_business = owned_businesses.first()
                            request.session["current_business_id"] = first_business.id
                            # Also set in middleware thread-local storage
                            from superadmin.middleware import set_current_business

                            set_current_business(first_business)
                            # Redirect to success page instead of dashboard directly
                            return redirect("authentication:login_success")
                    else:
                        # Set the first associated business as the current business in session
                        first_business = user_businesses.first()
                        request.session["current_business_id"] = first_business.id
                        # Also set in middleware thread-local storage
                        from superadmin.middleware import set_current_business

                        set_current_business(first_business)
                        # Redirect to success page instead of dashboard directly
                        return redirect("authentication:login_success")
                else:
                    messages.error(request, "Invalid username or password.")
            else:
                messages.error(request, "Invalid username or password.")
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Login error: {str(e)}", exc_info=True)
            messages.error(request, "An error occurred during login. Please try again.")
    else:
        form = CustomAuthenticationForm()

    return render(request, "authentication/login.html", {"form": form})


def login_success_view(request):
    """View to show success dialog after login before redirecting to dashboard"""
    return render(request, "authentication/login_success.html")


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect("authentication:login")


def register_view(request):
    """Simplified single-step registration"""
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create the user
            user = form.save()
            messages.success(
                request, "Account created successfully! You can now log in."
            )
            return redirect("authentication:login")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()

    return render(request, "authentication/register.html", {"form": form})


@login_required
def business_details_view(request):
    """View for new users to enter their business details after registration"""
    # Check if user already has a business
    existing_business = Business.objects.filter(owner=request.user)
    if existing_business.exists():
        # If user already has a business, redirect to dashboard
        return redirect("dashboard:index")

    if request.method == "POST":
        form = BusinessDetailsForm(request.POST)
        if form.is_valid():
            # Create the business
            business = form.save(commit=False)
            business.owner = request.user
            business.plan_type = "free"
            business.status = "active"
            business.save()

            # Set the business owner as admin
            business.owner.role = "admin"
            # Associate owner with the business
            business.owner.businesses.add(business)
            business.owner.save()

            # Set the business in session
            request.session["current_business_id"] = business.id

            # Also set in middleware thread-local storage
            from superadmin.middleware import set_current_business

            set_current_business(business)

            messages.success(
                request, "Business details saved successfully! You are now an admin."
            )
            return redirect("dashboard:index")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = BusinessDetailsForm()

    return render(request, "authentication/business_details.html", {"form": form})


def profile_view(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("authentication:profile")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, "authentication/profile.html", {"form": form})


@login_required
def set_user_language(request):
    """Set the logged-in user's preferred language and update the session.

    Falls back to session-only change for anonymous users (handled by Django's
    built-in set_language view).
    """
    if request.method == "POST":
        lang = request.POST.get("language")
        next_url = request.POST.get("next") or request.META.get("HTTP_REFERER", "/")
        # Validate language
        available = dict(getattr(settings, "LANGUAGES", [("en", "English")]))
        if lang in available:
            # Save to user preference
            request.user.language = lang
            request.user.save()
            # Also set session so change takes effect immediately
            request.session["_language"] = lang
            translation.activate(lang)
    return redirect(next_url)


@login_required
def user_list_view(request):
    from .models import User
    from .utils import check_user_permission

    # Account owners and admins have access to everything
    if request.user.role.lower() != "admin" and not check_user_permission(
        request.user, "can_manage_users"
    ):
        messages.error(request, "You do not have permission to manage users.")
        return redirect("dashboard:index")

    # For admins, show all users. For other users, show only users from the same business
    if request.user.role.lower() == "admin":
        # Admins can see all users
        users = User.objects.all().order_by("-date_joined")
    else:
        # Only show users from the same business
        from superadmin.middleware import get_current_business

        current_business = get_current_business()
        if current_business:
            # Get all users associated with this business
            users = User.objects.filter(businesses=current_business).exclude(
                id=request.user.id
            )  # Exclude current user
        else:
            users = User.objects.none()
    return render(request, "authentication/user_list.html", {"users": users})


def password_reset_view(request):
    # For now, we'll just render a simple template
    # In In a real application, you would implement password reset functionality
    return render(request, "authentication/password_reset.html")


@login_required
def create_user_view(request):
    from .forms import AdminUserCreationForm
    from .models import User
    from .utils import check_user_permission
    from superadmin.middleware import get_current_business

    current_business = get_current_business()
    if not current_business:
        messages.error(request, "No business context found.")
        return redirect("dashboard:index")

    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_create_users"
    ):
        messages.error(request, "You do not have permission to create users.")
        return redirect("dashboard:index")

    if request.method == "POST":
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(current_business)
            messages.success(request, f"User {user.username} created successfully!")
            return redirect("authentication:user_list")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AdminUserCreationForm()

    return render(request, "authentication/create_user.html", {"form": form})


@login_required
def edit_user_view(request, user_id):
    from .forms import UserProfileForm, UserPermissionForm
    from .models import User, UserPermission
    from .utils import check_user_permission
    from superadmin.middleware import get_current_business

    current_business = get_current_business()
    if not current_business:
        messages.error(request, "No business context found.")
        return redirect("dashboard:index")

    # Account owners have access to everything
    if request.user.role != "admin" and not check_user_permission(
        request.user, "can_edit_users"
    ):
        messages.error(request, "You do not have permission to edit users.")
        return redirect("dashboard:index")

    # Get the user to edit
    try:
        user_to_edit = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("authentication:user_list")

    # Check if the user belongs to the same business
    # Admins can edit any user in their business, others are restricted by business membership
    if (
        request.user.role != "admin"
        and not user_to_edit.businesses.filter(id=current_business.id).exists()
    ):
        messages.error(request, "You do not have permission to edit this user.")
        return redirect("authentication:user_list")

    # Get or create user permissions
    user_permission, created = UserPermission.objects.get_or_create(user=user_to_edit)

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=user_to_edit)
        permission_form = UserPermissionForm(request.POST, instance=user_permission)
        if form.is_valid() and permission_form.is_valid():
            form.save()
            permission_form.save()
            messages.success(
                request, f"User {user_to_edit.username} updated successfully!"
            )
            return redirect("authentication:user_list")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserProfileForm(instance=user_to_edit)
        permission_form = UserPermissionForm(instance=user_permission)

    return render(
        request,
        "authentication/edit_user.html",
        {
            "form": form,
            "permission_form": permission_form,
            "user_to_edit": user_to_edit,
        },
    )


@login_required
def create_business_view(request):
    """View for users to create a new business"""
    # Check if user already has a business
    from superadmin.models import Business

    existing_business = Business.objects.filter(owner=request.user)
    if existing_business.exists():
        # If user already has a business, redirect to dashboard
        messages.info(request, "You already have a business.")
        return redirect("dashboard:index")

    from superadmin.forms import BusinessDetailsForm

    if request.method == "POST":
        form = BusinessDetailsForm(request.POST)
        if form.is_valid():
            # Create the business
            business = form.save(commit=False)
            business.owner = request.user
            business.plan_type = "free"
            business.status = "active"
            business.save()

            # Set the business owner as admin
            business.owner.role = "admin"
            # Associate owner with the business
            business.owner.businesses.add(business)
            business.owner.save()

            # Set the business in session
            request.session["current_business_id"] = business.id

            # Also set in middleware thread-local storage
            from superadmin.middleware import set_current_business

            set_current_business(business)

            messages.success(request, "Business created successfully!")
            return redirect("dashboard:index")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = BusinessDetailsForm()

    return render(request, "authentication/create_business.html", {"form": form})
