from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.conf import settings
from django.utils.encoding import smart_str
from django.core import management
from django.db import connections, utils
from django.contrib.auth.decorators import user_passes_test
from functools import wraps
import os
import zipfile
import tempfile
import io
import json
import subprocess
from datetime import datetime
from .models import (
    BusinessSettings,
    BarcodeSettings,
    EmailSettings,
    BackupSettings,
    AuditLog,
)
from .forms import (
    BusinessSettingsForm,
    BarcodeSettingsForm,
    EmailSettingsForm,
    BackupSettingsForm,
)
from authentication.models import User, UserThemePreference
from authentication.forms import UserThemePreferenceForm


def is_admin(user):
    return user.is_authenticated and user.role == "admin"


def can_access_settings(user):
    return user.is_authenticated


def admin_required(view_func):
    """
    Decorator that checks if the user is an admin.
    If not, shows a permission denied message instead of redirecting to login.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("authentication:login")
        if request.user.role != "admin":
            messages.error(
                request,
                "You do not have permission to access this page. Only administrators can manage users.",
            )
            return redirect("settings:index")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


@login_required
@user_passes_test(can_access_settings)
def settings_list(request):
    return render(request, "settings/list.html")


@login_required
@user_passes_test(can_access_settings)
def business_settings(request):
    business_settings, created = BusinessSettings.objects.get_or_create(id=1)

    if request.method == "POST":
        form = BusinessSettingsForm(
            request.POST, request.FILES, instance=business_settings
        )
        if form.is_valid():
            # Handle logo deletion
            if form.cleaned_data.get("delete_logo") and business_settings.business_logo:
                # Delete the logo file
                if business_settings.business_logo and hasattr(
                    business_settings.business_logo, "delete"
                ):
                    business_settings.business_logo.delete(save=False)
                # Clear the logo field
                business_settings.business_logo = None

            form.save()
            messages.success(request, "Business settings updated successfully!")
            return redirect("settings:business")
    else:
        form = BusinessSettingsForm(instance=business_settings)

    return render(
        request, "settings/business.html", {"form": form, "settings": business_settings}
    )


@login_required
@user_passes_test(can_access_settings)
def barcode_settings(request):
    barcode_settings, created = BarcodeSettings.objects.get_or_create(id=1)

    if request.method == "POST":
        form = BarcodeSettingsForm(request.POST, instance=barcode_settings)
        if form.is_valid():
            form.save()
            messages.success(request, "Barcode settings updated successfully!")
            return redirect("settings:barcode")
    else:
        form = BarcodeSettingsForm(instance=barcode_settings)

    return render(
        request, "settings/barcode.html", {"form": form, "settings": barcode_settings}
    )


# Only admins can manage users
@login_required
@admin_required
def user_management(request):
    # Only show users from the same business
    from superadmin.middleware import get_current_business

    current_business = get_current_business()
    if current_business:
        # Get all users associated with this business
        users = User.objects.filter(businesses=current_business).order_by(
            "-date_joined"
        )
    else:
        users = User.objects.none()
    return render(request, "settings/users.html", {"users": users})


@login_required
@user_passes_test(can_access_settings)
def email_settings(request):
    # Get or create email settings
    email_settings, created = EmailSettings.objects.get_or_create(id=1)

    if request.method == "POST":
        form = EmailSettingsForm(request.POST, instance=email_settings)
        if form.is_valid():
            form.save()
            messages.success(request, "Email settings updated successfully!")
            return redirect("settings:email")
    else:
        form = EmailSettingsForm(instance=email_settings)

    return render(
        request, "settings/email.html", {"form": form, "settings": email_settings}
    )


@login_required
@user_passes_test(can_access_settings)
def backup_restore(request):
    # Handle backup creation
    if request.method == "POST":
        # Create backup functionality
        if "create_backup" in request.POST:
            try:
                # Create a timestamp for the backup
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"backup_{timestamp}.zip"
                backup_path = os.path.join(
                    settings.BASE_DIR, "backups", backup_filename
                )

                # Create backups directory if it doesn't exist
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)

                # Create the backup zip file
                with zipfile.ZipFile(backup_path, "w") as backup_zip:
                    # For PostgreSQL, try to create a dump using Django's dumpdata
                    try:
                        # Create a temporary file for the dump
                        with tempfile.NamedTemporaryFile(
                            suffix=".json", delete=False
                        ) as temp_file:
                            temp_filename = temp_file.name

                        # Use Django's dumpdata command to export all data
                        with open(temp_filename, "w") as temp_file:
                            management.call_command(
                                "dumpdata", format="json", indent=2, stdout=temp_file
                            )

                        # Add the dump file to the backup
                        if (
                            os.path.exists(temp_filename)
                            and os.path.getsize(temp_filename) > 0
                        ):
                            backup_zip.write(temp_filename, "database_dump.json")
                            os.unlink(temp_filename)  # Remove temporary file
                            print(
                                f"Added PostgreSQL database dump using Django dumpdata"
                            )
                    except Exception as e:
                        print(f"Could not create database dump: {e}")

                    # Add media files to backup
                    media_root = settings.MEDIA_ROOT
                    if os.path.exists(media_root):
                        for root, dirs, files in os.walk(media_root):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arc_path = os.path.relpath(file_path, media_root)
                                backup_zip.write(file_path, f"media/{arc_path}")

                messages.success(
                    request, f"Backup created successfully: {backup_filename}"
                )
            except Exception as e:
                messages.error(request, f"Error creating backup: {str(e)}")
                import traceback

                print(f"Backup error: {traceback.format_exc()}")

            return redirect("settings:backup")

        # Restore backup
        elif "restore_backup" in request.POST:
            backup_file = request.FILES.get("backup_file")
            if not backup_file:
                messages.error(request, "Please select a backup file to restore.")
                return redirect("settings:backup")

            try:
                # Create a temporary file for the uploaded backup
                with tempfile.NamedTemporaryFile(
                    suffix=".zip", delete=False
                ) as temp_file:
                    for chunk in backup_file.chunks():
                        temp_file.write(chunk)
                    temp_filename = temp_file.name

                # Extract the backup file
                with zipfile.ZipFile(temp_filename, "r") as backup_zip:
                    # Look for database dump
                    database_dump = None
                    for filename in backup_zip.namelist():
                        if filename == "database_dump.json":
                            database_dump = filename
                            break

                    # Restore database if dump exists
                    if database_dump:
                        # Create a temporary file for the database dump
                        with tempfile.NamedTemporaryFile(
                            suffix=".json", delete=False
                        ) as db_temp_file:
                            db_temp_filename = db_temp_file.name

                        # Extract database dump to temporary file
                        with backup_zip.open(database_dump) as source, open(
                            db_temp_filename, "wb"
                        ) as target:
                            target.write(source.read())

                        # Use Django's loaddata command to restore the database
                        try:
                            management.call_command(
                                "loaddata", db_temp_filename, verbosity=0
                            )
                            messages.success(request, "Database restored successfully!")
                        except Exception as e:
                            messages.error(
                                request, f"Error restoring database: {str(e)}"
                            )
                        finally:
                            # Clean up temporary database dump file
                            if os.path.exists(db_temp_filename):
                                os.unlink(db_temp_filename)
                    else:
                        messages.warning(
                            request, "No database dump found in backup file."
                        )

                    # Restore media files
                    media_files_restored = 0
                    media_root = settings.MEDIA_ROOT
                    for filename in backup_zip.namelist():
                        if filename.startswith("media/"):
                            # Extract media file
                            extracted_path = backup_zip.extract(
                                filename, tempfile.gettempdir()
                            )
                            # Move to correct location
                            target_path = os.path.join(
                                media_root, filename[6:]
                            )  # Remove 'media/' prefix
                            os.makedirs(os.path.dirname(target_path), exist_ok=True)
                            os.replace(extracted_path, target_path)
                            media_files_restored += 1

                    if media_files_restored > 0:
                        messages.success(
                            request, f"Restored {media_files_restored} media files."
                        )

                # Clean up temporary backup file
                os.unlink(temp_filename)

            except Exception as e:
                messages.error(request, f"Error restoring backup: {str(e)}")
                import traceback

                print(f"Restore error: {traceback.format_exc()}")

            return redirect("settings:backup")

    # List existing backups
    backups_dir = os.path.join(settings.BASE_DIR, "backups")
    backup_files = []

    if os.path.exists(backups_dir):
        for filename in os.listdir(backups_dir):
            if filename.endswith(".zip"):
                file_path = os.path.join(backups_dir, filename)
                stat = os.stat(file_path)
                backup_files.append(
                    {
                        "name": filename,
                        "size": stat.st_size,
                        "date": datetime.fromtimestamp(stat.st_mtime).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    }
                )

    # Sort by date, newest first
    backup_files.sort(key=lambda x: x["date"], reverse=True)

    return render(request, "settings/backup.html", {"backup_files": backup_files})


@login_required
@user_passes_test(can_access_settings)
def download_backup(request, filename):
    backups_dir = os.path.join(settings.BASE_DIR, "backups")
    file_path = os.path.join(backups_dir, filename)

    if not os.path.exists(file_path):
        raise Http404("Backup file not found")

    # Read the file content
    with open(file_path, "rb") as f:
        file_content = f.read()

    response = HttpResponse(file_content, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{smart_str(filename)}"'
    return response


@login_required
@user_passes_test(can_access_settings)
def backup_settings(request):
    # Get or create backup settings
    backup_settings, created = BackupSettings.objects.get_or_create(id=1)

    if request.method == "POST":
        form = BackupSettingsForm(request.POST, instance=backup_settings)
        if form.is_valid():
            form.save()
            messages.success(request, "Backup settings updated successfully!")
            return redirect("settings:backup_settings")
    else:
        form = BackupSettingsForm(instance=backup_settings)

    return render(
        request,
        "settings/backup_settings.html",
        {"form": form, "backup_settings": backup_settings},
    )


@login_required
@user_passes_test(can_access_settings)
def voice_assistant(request):
    return render(request, "voice_assistant_test.html")


@login_required
@user_passes_test(can_access_settings)
def voice_test(request):
    return render(request, "voice_test.html")


@login_required
@user_passes_test(can_access_settings)
def voice_debug(request):
    return render(request, "voice_debug.html")


@login_required
@user_passes_test(can_access_settings)
def voice_permissions(request):
    return render(request, "voice_permissions.html")


@login_required
@user_passes_test(can_access_settings)
def voice_troubleshooting(request):
    return render(request, "voice_troubleshooting.html")


@login_required
@user_passes_test(can_access_settings)
def voice_response_test(request):
    return render(request, "voice_response_test.html")


@login_required
@user_passes_test(can_access_settings)
def voice_error_fix(request):
    return render(request, "voice_error_fix.html")


@login_required
@user_passes_test(can_access_settings)
def theme_settings(request):
    # Get or create user theme preference
    theme_preference, created = UserThemePreference.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":
        form = UserThemePreferenceForm(request.POST, instance=theme_preference)
        if form.is_valid():
            form.save()
            messages.success(request, "Theme settings updated successfully!")
            return redirect("settings:theme")
    else:
        form = UserThemePreferenceForm(instance=theme_preference)

    return render(
        request,
        "settings/theme.html",
        {"form": form, "theme_preference": theme_preference},
    )


@login_required
@user_passes_test(is_admin)
def audit_logs(request):
    """
    View to display audit logs with filtering capabilities.
    Only accessible by admin users.
    """
    # Get filter parameters
    action_filter = request.GET.get("action", "")
    user_filter = request.GET.get("user", "")
    model_filter = request.GET.get("model", "")
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")

    # Start with all audit logs
    logs = AuditLog.objects.select_related("user").all()

    # Apply filters
    if action_filter:
        logs = logs.filter(action=action_filter)

    if user_filter:
        logs = logs.filter(user_id=user_filter)

    if model_filter:
        logs = logs.filter(model_name=model_filter)

    if date_from:
        logs = logs.filter(timestamp__gte=date_from)

    if date_to:
        logs = logs.filter(timestamp__lte=date_to)

    # Get filter options
    users = User.objects.all()
    models = AuditLog.objects.values_list("model_name", flat=True).distinct()
    actions = [choice[0] for choice in AuditLog.ACTION_CHOICES]

    # Paginate the logs
    from django.core.paginator import Paginator

    paginator = Paginator(logs, 50)  # Show 50 logs per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "users": users,
        "models": models,
        "actions": actions,
        "action_filter": action_filter,
        "user_filter": user_filter,
        "model_filter": model_filter,
        "date_from": date_from,
        "date_to": date_to,
    }

    return render(request, "settings/audit_logs.html", context)


@login_required
@user_passes_test(is_admin)
def bulky_upload(request):
    """
    View to handle bulky CSV uploads for products.
    """
    import os
    from django.conf import settings

    # Get uploads directory
    uploads_dir = os.path.join(settings.BASE_DIR, "uploads")

    # Create uploads directory if it doesn't exist
    os.makedirs(uploads_dir, exist_ok=True)

    # Handle file upload
    if request.method == "POST":
        uploaded_file = request.FILES.get("bulky_file")
        if uploaded_file:
            # Save file to uploads directory
            file_path = os.path.join(uploads_dir, uploaded_file.name)
            with open(file_path, "wb+") as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            messages.success(
                request, f"File {uploaded_file.name} uploaded successfully!"
            )
        else:
            messages.error(request, "Please select a file to upload.")

    # List existing bulky upload files
    bulky_files = []
    if os.path.exists(uploads_dir):
        for filename in os.listdir(uploads_dir):
            if filename.endswith(".csv"):
                file_path = os.path.join(uploads_dir, filename)
                stat = os.stat(file_path)
                bulky_files.append(
                    {
                        "name": filename,
                        "size": stat.st_size,
                        "date": datetime.fromtimestamp(stat.st_mtime).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    }
                )

    # Sort by date, newest first
    bulky_files.sort(key=lambda x: x["date"], reverse=True)

    # Get businesses and users for the modal
    from superadmin.models import Business

    businesses = Business.objects.all()
    users = User.objects.all()

    context = {"bulky_files": bulky_files, "businesses": businesses, "users": users}

    return render(request, "settings/backup.html", context)


@login_required
@user_passes_test(is_admin)
def process_bulky_file(request, filename):
    """
    Process a bulky upload file.
    """
    if request.method == "POST":
        business_id = request.POST.get("business_id")
        user_id = request.POST.get("user_id")

        try:
            # Run the management command to process the file
            from django.core import management

            cmd_args = [filename]
            if business_id:
                cmd_args.extend(["--business-id", business_id])
            if user_id:
                cmd_args.extend(["--user-id", user_id])

            management.call_command("process_bulky_upload", *cmd_args)
            messages.success(request, f"Successfully processed file: {filename}")
        except Exception as e:
            messages.error(request, f"Error processing file {filename}: {str(e)}")

    return redirect("settings:bulky_upload")


@login_required
@user_passes_test(is_admin)
def delete_bulky_file(request, filename):
    """
    Delete a bulky upload file.
    """
    if request.method == "POST":
        import os
        from django.conf import settings

        file_path = os.path.join(settings.BASE_DIR, "uploads", filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            messages.success(request, f"File {filename} deleted successfully!")
        else:
            messages.error(request, f"File {filename} not found.")

    return redirect("settings:bulky_upload")
