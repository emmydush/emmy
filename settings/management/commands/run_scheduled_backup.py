from django.core.management.base import BaseCommand
from django.conf import settings
from django.core import management
from django.utils import timezone
import os
import zipfile
import tempfile
import datetime
from settings.models import BackupSettings, BusinessSettings

class Command(BaseCommand):
    help = 'Run scheduled backup based on backup settings'

    def handle(self, *args, **options):
        # Get backup settings
        try:
            backup_settings = BackupSettings.objects.get(id=1)
        except BackupSettings.DoesNotExist:
            self.stdout.write(
                self.style.WARNING('Backup settings not configured. Skipping scheduled backup.')
            )
            return
        
        # Check if backups are enabled
        if not backup_settings.is_active:
            self.stdout.write(
                self.style.WARNING('Automated backups are disabled. Skipping scheduled backup.')
            )
            return
        
        # Check if it's time to run a backup
        now = timezone.now()
        current_time = now.strftime('%H:%M')
        
        # Determine if we should run a backup based on frequency
        should_run = False
        backup_type = None
        
        if backup_settings.frequency == 'daily' and current_time == backup_settings.backup_time:
            should_run = True
            backup_type = 'daily'
        elif backup_settings.frequency == 'weekly' and current_time == backup_settings.backup_time:
            # Run on Sundays (weekday 6 in Python, where Monday is 0)
            if now.weekday() == 6:
                should_run = True
                backup_type = 'weekly'
        elif backup_settings.frequency == 'monthly' and current_time == backup_settings.backup_time:
            # Run on the first day of the month
            if now.day == 1:
                should_run = True
                backup_type = 'monthly'
        
        if not should_run:
            self.stdout.write(
                self.style.WARNING(f'Not time to run {backup_settings.frequency} backup. Current time: {current_time}')
            )
            return
        
        # Check if we already ran a backup today
        if backup_settings.last_run:
            last_run_date = backup_settings.last_run.date()
            if last_run_date == now.date():
                self.stdout.write(
                    self.style.WARNING('Backup already run today. Skipping.')
                )
                return
        
        # Run the backup
        self.stdout.write(
            self.style.SUCCESS(f'Running scheduled {backup_type} backup...')
        )
        
        try:
            # Create backup name with timestamp
            timestamp = now.strftime('%Y%m%d_%H%M%S')
            backup_name = f'{backup_type}_backup_{timestamp}'
            backup_filename = f'{backup_name}.zip'
            backup_path = os.path.join(settings.BASE_DIR, 'backups', backup_filename)
            
            # Create backups directory if it doesn't exist
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Create the backup zip file
            with zipfile.ZipFile(backup_path, 'w') as backup_zip:
                # Create database dump using Django's dumpdata
                try:
                    # Create a temporary file for the dump
                    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
                        temp_filename = temp_file.name
                    
                    # Use Django's dumpdata command to export all data
                    with open(temp_filename, 'w') as temp_file:
                        management.call_command('dumpdata', format='json', indent=2, stdout=temp_file)
                    
                    # Add the dump file to the backup
                    if os.path.exists(temp_filename) and os.path.getsize(temp_filename) > 0:
                        backup_zip.write(temp_filename, 'database_dump.json')
                        os.unlink(temp_filename)  # Remove temporary file
                        self.stdout.write(
                            self.style.SUCCESS('Added database dump to backup')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING('Database dump was empty or not created')
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Could not create database dump: {str(e)}')
                    )
                
                # Add media files to backup
                media_root = settings.MEDIA_ROOT
                media_files_added = 0
                if os.path.exists(media_root):
                    for root, dirs, files in os.walk(media_root):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arc_path = os.path.relpath(file_path, media_root)
                            backup_zip.write(file_path, f'media/{arc_path}')
                            media_files_added += 1
                
                self.stdout.write(
                    self.style.SUCCESS(f'Added {media_files_added} media files to backup')
                )
            
            # Get file size for reporting
            file_size = os.path.getsize(backup_path)
            
            # Update last run time
            backup_settings.last_run = now
            backup_settings.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {backup_type} backup: {backup_filename} ({self.format_file_size(file_size)})'
                )
            )
            
            # Clean up old backups based on retention settings
            self.cleanup_old_backups(backup_settings.retention_days)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating scheduled backup: {str(e)}')
            )
            # Clean up partial backup file if it exists
            if 'backup_path' in locals() and os.path.exists(backup_path):
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
    
    def cleanup_old_backups(self, retention_days):
        """Remove backups older than retention_days"""
        backups_dir = os.path.join(settings.BASE_DIR, 'backups')
        if not os.path.exists(backups_dir):
            return
        
        cutoff_date = timezone.now() - datetime.timedelta(days=retention_days)
        
        deleted_count = 0
        for filename in os.listdir(backups_dir):
            if filename.endswith('.zip'):
                file_path = os.path.join(backups_dir, filename)
                file_modified = datetime.datetime.fromtimestamp(
                    os.path.getmtime(file_path)
                ).replace(tzinfo=timezone.utc)
                
                if file_modified < cutoff_date:
                    try:
                        os.unlink(file_path)
                        deleted_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Deleted old backup: {filename}')
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Failed to delete old backup {filename}: {str(e)}')
                        )
        
        if deleted_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Cleaned up {deleted_count} old backups')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('No old backups to clean up')
            )