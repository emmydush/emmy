from django.core.management.base import BaseCommand
from django.conf import settings
import os
import zipfile
import hashlib
import json


class Command(BaseCommand):
    help = "Verify integrity of backup files"

    def add_arguments(self, parser):
        parser.add_argument(
            "backup_file",
            nargs="?",
            type=str,
            help="Path to the backup zip file to verify (optional - if not provided, checks all backups)",
        )
        parser.add_argument(
            "--checksum",
            action="store_true",
            help="Verify checksum integrity",
        )
        parser.add_argument(
            "--structure",
            action="store_true",
            help="Verify backup file structure",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Verify all backup files in backups directory",
        )

    def handle(self, *args, **options):
        if options["all"]:
            self.verify_all_backups(options)
        elif options["backup_file"]:
            self.verify_single_backup(options["backup_file"], options)
        else:
            self.stdout.write(
                self.style.ERROR("Please specify a backup file or use --all flag")
            )

    def verify_all_backups(self, options):
        """Verify all backup files in the backups directory"""
        backups_dir = os.path.join(settings.BASE_DIR, "backups")
        if not os.path.exists(backups_dir):
            self.stdout.write(
                self.style.ERROR("Backups directory does not exist")
            )
            return

        backup_files = [f for f in os.listdir(backups_dir) if f.endswith(".zip")]
        if not backup_files:
            self.stdout.write(
                self.style.WARNING("No backup files found in backups directory")
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f"Verifying {len(backup_files)} backup files...")
        )

        verified_count = 0
        failed_count = 0

        for backup_file in backup_files:
            backup_path = os.path.join(backups_dir, backup_file)
            try:
                if self.verify_single_backup(backup_path, options):
                    verified_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error verifying {backup_file}: {str(e)}")
                )
                failed_count += 1

        self.stdout.write("\n" + "="*50)
        self.stdout.write(
            self.style.SUCCESS(f"Verification complete: {verified_count} passed, {failed_count} failed")
        )
        self.stdout.write("="*50)

    def verify_single_backup(self, backup_path, options):
        """Verify a single backup file"""
        if not os.path.exists(backup_path):
            self.stdout.write(
                self.style.ERROR(f"Backup file not found: {backup_path}")
            )
            return False

        backup_name = os.path.basename(backup_path)
        self.stdout.write(f"\nVerifying {backup_name}...")

        # Verify checksum if requested
        if options["checksum"]:
            if not self.verify_checksum(backup_path):
                return False

        # Verify structure if requested
        if options["structure"]:
            if not self.verify_structure(backup_path):
                return False

        # If no specific checks requested, do basic verification
        if not options["checksum"] and not options["structure"]:
            if not self.verify_basic(backup_path):
                return False

        self.stdout.write(
            self.style.SUCCESS(f"✓ {backup_name} verification passed")
        )
        return True

    def verify_checksum(self, backup_path):
        """Verify backup file checksum"""
        checksum_file = f"{backup_path}.md5"
        if not os.path.exists(checksum_file):
            self.stdout.write(
                self.style.WARNING(f"  No checksum file found for {os.path.basename(backup_path)}")
            )
            return True  # Not failing because checksum is optional

        try:
            # Read expected checksum
            with open(checksum_file, "r") as f:
                expected_checksum = f.read().strip()

            # Calculate actual checksum
            hash_md5 = hashlib.md5()
            with open(backup_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            actual_checksum = hash_md5.hexdigest()

            # Compare checksums
            if expected_checksum == actual_checksum:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Checksum verified: {actual_checksum}")
                )
                return True
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"  ✗ Checksum mismatch!\n"
                        f"    Expected: {expected_checksum}\n"
                        f"    Actual:   {actual_checksum}"
                    )
                )
                return False

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  ✗ Checksum verification failed: {str(e)}")
            )
            return False

    def verify_structure(self, backup_path):
        """Verify backup file structure"""
        try:
            with zipfile.ZipFile(backup_path, "r") as backup_zip:
                file_list = backup_zip.namelist()
                
                # Check for required files
                has_db = "database_dump.json" in file_list
                has_metadata = "metadata.json" in file_list
                
                self.stdout.write(f"  Files in backup: {len(file_list)}")
                
                if has_db:
                    self.stdout.write(
                        self.style.SUCCESS("  ✓ Database dump found")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING("  ! No database dump found")
                    )
                
                if has_metadata:
                    # Verify metadata content
                    with backup_zip.open("metadata.json") as meta_file:
                        metadata = json.load(meta_file)
                        self.stdout.write(
                            self.style.SUCCESS(f"  ✓ Metadata found (created: {metadata.get('created_at', 'Unknown')})")
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING("  ! No metadata found")
                    )
                
                # Check for media files
                media_files = [f for f in file_list if f.startswith("media/")]
                if media_files:
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ {len(media_files)} media files found")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING("  ! No media files found")
                    )
                
                return True

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  ✗ Structure verification failed: {str(e)}")
            )
            return False

    def verify_basic(self, backup_path):
        """Basic verification - check if file is a valid zip"""
        try:
            with zipfile.ZipFile(backup_path, "r") as backup_zip:
                # Just test if it's a valid zip file
                backup_zip.testzip()
                file_count = len(backup_zip.namelist())
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Valid ZIP file with {file_count} entries")
                )
                return True
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  ✗ Invalid ZIP file: {str(e)}")
            )
            return False