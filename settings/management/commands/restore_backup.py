from django.core.management.base import BaseCommand
from django.conf import settings
from django.core import management
from django.db import transaction
import os
import zipfile
import tempfile
import json
from settings.models import BusinessSettings


class Command(BaseCommand):
    help = "Restore database and media files from backup"

    def add_arguments(self, parser):
        parser.add_argument(
            "backup_file",
            type=str,
            help="Path to the backup zip file to restore from",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Do not prompt for confirmation",
        )
        parser.add_argument(
            "--skip-media",
            action="store_true",
            help="Skip restoring media files",
        )
        parser.add_argument(
            "--skip-db",
            action="store_true",
            help="Skip restoring database",
        )

    def handle(self, *args, **options):
        backup_file = options["backup_file"]

        # Check if backup file exists
        if not os.path.exists(backup_file):
            self.stdout.write(self.style.ERROR(f"Backup file not found: {backup_file}"))
            return

        # Confirm restoration unless --no-input is specified
        if not options["no_input"]:
            confirm = input(
                f"This will restore data from {backup_file}. This operation cannot be undone. "
                "Are you sure you want to continue? (yes/no): "
            )
            if confirm.lower() not in ["yes", "y"]:
                self.stdout.write(self.style.WARNING("Restore operation cancelled."))
                return

        try:
            with zipfile.ZipFile(backup_file, "r") as backup_zip:
                # Restore database if not skipped
                if not options["skip_db"]:
                    self.restore_database(backup_zip)

                # Restore media files if not skipped
                if not options["skip_media"]:
                    self.restore_media_files(backup_zip)

            self.stdout.write(
                self.style.SUCCESS(f"Successfully restored data from {backup_file}")
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error restoring from backup: {str(e)}")
            )
            raise

    def restore_database(self, backup_zip):
        """Restore database from backup"""
        self.stdout.write("Restoring database...")

        # Check if database dump exists in backup
        if "database_dump.json" not in backup_zip.namelist():
            self.stdout.write(self.style.WARNING("No database dump found in backup"))
            return

        try:
            # Extract database dump to temporary file
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
                temp_filename = temp_file.name

            # Extract the database dump
            with backup_zip.open("database_dump.json") as dump_file:
                with open(temp_filename, "wb") as temp_file:
                    temp_file.write(dump_file.read())

            # Load the data to check if it's valid
            with open(temp_filename, "r") as temp_file:
                data = json.load(temp_file)

            if not data:
                self.stdout.write(self.style.WARNING("Database dump is empty"))
                os.unlink(temp_filename)
                return

            # Clear existing data and load the backup
            with transaction.atomic():
                # Load the data using Django's loaddata command
                management.call_command(
                    "loaddata",
                    temp_filename,
                    verbosity=0,
                    ignorenonexistent=True,  # Skip fields that don't exist
                )

            # Clean up temporary file
            os.unlink(temp_filename)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully restored {len(data)} database records"
                )
            )

        except Exception as e:
            # Clean up temporary file if it exists
            if "temp_filename" in locals() and os.path.exists(temp_filename):
                os.unlink(temp_filename)
            raise Exception(f"Database restore failed: {str(e)}")

    def restore_media_files(self, backup_zip):
        """Restore media files from backup"""
        self.stdout.write("Restoring media files...")

        media_files_restored = 0

        # Get list of media files in backup
        media_files = [
            name for name in backup_zip.namelist() if name.startswith("media/")
        ]

        if not media_files:
            self.stdout.write(self.style.WARNING("No media files found in backup"))
            return

        # Create media directory if it doesn't exist
        media_root = settings.MEDIA_ROOT
        os.makedirs(media_root, exist_ok=True)

        # Extract media files
        for media_file in media_files:
            try:
                # Get the relative path within media directory
                relative_path = media_file[len("media/") :]
                if not relative_path:  # Skip if it's just "media/"
                    continue

                # Create directory structure if needed
                target_path = os.path.join(media_root, relative_path)
                target_dir = os.path.dirname(target_path)
                os.makedirs(target_dir, exist_ok=True)

                # Extract file
                with backup_zip.open(media_file) as source:
                    with open(target_path, "wb") as target:
                        target.write(source.read())

                media_files_restored += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to restore media file {media_file}: {str(e)}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully restored {media_files_restored} media files"
            )
        )
