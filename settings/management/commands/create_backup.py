from django.core.management.base import BaseCommand
from django.conf import settings
from django.core import management
import os
import zipfile
import tempfile
import datetime
from settings.models import BusinessSettings


class Command(BaseCommand):
    help = "Create automated backup of database and media files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--daily",
            action="store_true",
            help="Create daily backup with timestamp",
        )
        parser.add_argument(
            "--weekly",
            action="store_true",
            help="Create weekly backup with timestamp",
        )
        parser.add_argument(
            "--name",
            type=str,
            help="Custom name for the backup file",
        )

    def handle(self, *args, **options):
        # Determine backup name
        if options["name"]:
            backup_name = options["name"]
        elif options["weekly"]:
            backup_name = (
                f'weekly_backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'
            )
        elif options["daily"]:
            backup_name = (
                f'daily_backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'
            )
        else:
            backup_name = f'backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'

        backup_filename = f"{backup_name}.zip"
        backup_path = os.path.join(settings.BASE_DIR, "backups", backup_filename)

        # Create backups directory if it doesn't exist
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)

        try:
            # Create the backup zip file
            with zipfile.ZipFile(backup_path, "w") as backup_zip:
                # Create database dump using Django's dumpdata
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
                        self.stdout.write(
                            self.style.SUCCESS(f"Added database dump to backup")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING("Database dump was empty or not created")
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Could not create database dump: {str(e)}")
                    )

                # Add media files to backup
                media_root = settings.MEDIA_ROOT
                media_files_added = 0
                if os.path.exists(media_root):
                    for root, dirs, files in os.walk(media_root):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arc_path = os.path.relpath(file_path, media_root)
                            backup_zip.write(file_path, f"media/{arc_path}")
                            media_files_added += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Added {media_files_added} media files to backup"
                    )
                )

            # Get file size for reporting
            file_size = os.path.getsize(backup_path)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created backup: {backup_filename} ({self.format_file_size(file_size)})"
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating backup: {str(e)}"))
            # Clean up partial backup file if it exists
            if os.path.exists(backup_path):
                os.unlink(backup_path)
            raise

    def format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f}{size_names[i]}"
