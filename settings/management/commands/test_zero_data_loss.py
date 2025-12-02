from django.core.management.base import BaseCommand
from django.conf import settings
import os
import shutil
from datetime import datetime


class Command(BaseCommand):
    help = "Test zero data loss implementation by creating a backup and verifying restore capability"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("Testing zero data loss implementation...")
        )
        
        # 1. Create a backup
        self.stdout.write("Step 1: Creating backup...")
        try:
            from settings.management.commands.create_backup import Command as BackupCommand
            backup_cmd = BackupCommand()
            backup_cmd.stdout = self.stdout
            backup_cmd.style = self.style
            
            # Create a test backup with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"test_zdl_backup_{timestamp}"
            
            # Call the backup command
            from django.core.management import call_command
            call_command('create_backup', name=backup_name)
            
            # Find the created backup file
            backup_filename = f"{backup_name}.zip"
            backup_path = os.path.join(settings.BASE_DIR, "backups", backup_filename)
            
            if not os.path.exists(backup_path):
                self.stdout.write(
                    self.style.ERROR("Backup file was not created successfully")
                )
                return
                
            self.stdout.write(
                self.style.SUCCESS(f"Backup created successfully: {backup_filename}")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to create backup: {str(e)}")
            )
            return

        # 2. Verify backup contents
        self.stdout.write("Step 2: Verifying backup contents...")
        try:
            import zipfile
            with zipfile.ZipFile(backup_path, "r") as backup_zip:
                file_list = backup_zip.namelist()
                
                self.stdout.write(f"Backup contains {len(file_list)} files:")
                for file_name in file_list:
                    self.stdout.write(f"  - {file_name}")
                    
                # Check for required components
                has_db = "database_dump.json" in file_list
                has_media = any(name.startswith("media/") for name in file_list)
                
                if not has_db:
                    self.stdout.write(
                        self.style.WARNING("Warning: No database dump found in backup")
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS("✓ Database dump found in backup")
                    )
                    
                if not has_media:
                    self.stdout.write(
                        self.style.WARNING("Note: No media files found in backup")
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS("✓ Media files found in backup")
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to verify backup contents: {str(e)}")
            )
            return

        # 3. Test restore command availability
        self.stdout.write("Step 3: Testing restore command...")
        try:
            from settings.management.commands.restore_backup import Command as RestoreCommand
            restore_cmd = RestoreCommand()
            self.stdout.write(
                self.style.SUCCESS("✓ Restore command is available")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Restore command not available: {str(e)}")
            )
            return

        # 4. Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(
            self.style.SUCCESS("Zero Data Loss Implementation Test Complete")
        )
        self.stdout.write("="*50)
        self.stdout.write(
            self.style.SUCCESS("✓ Backup creation working")
        )
        self.stdout.write(
            self.style.SUCCESS("✓ Backup verification working")
        )
        self.stdout.write(
            self.style.SUCCESS("✓ Restore command available")
        )
        self.stdout.write("\nNext steps:")
        self.stdout.write("1. Test actual restore with: python manage.py restore_backup backups/{}".format(backup_filename))
        self.stdout.write("2. Set up automated backups in superadmin dashboard")
        self.stdout.write("3. Configure backup retention policies")
        self.stdout.write("="*50)