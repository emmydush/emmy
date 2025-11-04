# Automated Backup System

This document explains how to set up and use the automated backup system for the Inventory Management System.

## Features

1. **Scheduled Backups**: Automatically create backups daily, weekly, or monthly
2. **Retention Policy**: Automatically delete old backups based on retention settings
3. **Backup Contents**: Complete database and media files
4. **Flexible Configuration**: Customize backup frequency, time, and retention period

## Setting Up Automated Backups

### Step 1: Configure Backup Settings

1. Navigate to **Settings** > **Backup & Restore** in your application
2. Click on **Configure Backup Settings**
3. Set your preferences:
   - **Backup Frequency**: Daily, Weekly, or Monthly
   - **Backup Time**: Time of day when backups should run
   - **Retention Period**: Number of days to keep backups
   - **Enable Automated Backups**: Toggle to enable/disable automated backups

### Step 2: Set Up Task Scheduler

#### Option 1: Windows Task Scheduler

Run the provided PowerShell script to set up a scheduled task:

```powershell
# Navigate to your project directory
cd C:\path\to\your\project

# Run the setup script
.\setup_backup_schedule.ps1
```

This will create a scheduled task that runs daily at 2:00 AM to check if a backup should be created based on your settings.

#### Option 2: Manual Task Scheduler Setup

1. Open **Task Scheduler**
2. Click **Create Task**
3. General tab:
   - Name: `InventoryManagementBackup`
   - Security options: Run whether user is logged on or not
4. Triggers tab:
   - New > Daily > 2:00 AM
5. Actions tab:
   - New > Start a program
   - Program: `python`
   - Arguments: `manage.py run_scheduled_backup`
   - Start in: `C:\path\to\your\project`
6. Settings tab:
   - Allow task to be run on demand
   - Run task as soon as possible after a scheduled start is missed

#### Option 3: Cron (Linux/macOS)

Add the following line to your crontab (`crontab -e`):

```bash
# Run backup check every day at 2:00 AM
0 2 * * * cd /path/to/your/project && python manage.py run_scheduled_backup
```

## How It Works

1. The scheduled task runs daily at the configured time
2. The system checks the backup settings to determine if a backup should be created:
   - **Daily**: Runs every day at the specified time
   - **Weekly**: Runs on Sundays at the specified time
   - **Monthly**: Runs on the 1st of each month at the specified time
3. If it's time for a backup, the system creates a timestamped backup file
4. Old backups are automatically deleted based on the retention period

## Backup Contents

Each backup includes:
- Complete database dump (JSON format)
- All uploaded media files (product images, logos, etc.)
- System configuration

## Backup Storage

Backups are stored in the `backups/` directory in your project folder. Each backup is a ZIP file containing:
- `database_dump.json`: Complete database export
- `media/`: Directory with all uploaded files

## Manual Backup Commands

You can also create backups manually using management commands:

```bash
# Create a basic backup
python manage.py create_backup

# Create a daily backup with timestamp
python manage.py create_backup --daily

# Create a weekly backup with timestamp
python manage.py create_backup --weekly

# Create a backup with custom name
python manage.py create_backup --name "my_custom_backup"
```

## Restoring Backups

1. Navigate to **Settings** > **Backup & Restore**
2. In the **Restore Backup** section, select your backup file
3. Click **Restore Backup**
4. The system will restore both the database and media files

## Troubleshooting

### Backup Not Running

1. Check that the scheduled task is enabled in Task Scheduler
2. Verify backup settings in the application are configured correctly
3. Check the application logs for any error messages

### Backup File Too Large

1. Consider reducing the retention period
2. Clean up unnecessary media files in your system
3. Check if there are large files in your media directory that could be archived separately

### Restore Issues

1. Ensure the backup file is not corrupted
2. Check that the backup file contains both database and media files
3. Verify that the database schema is compatible with the backup

## Best Practices

1. **Regular Testing**: Periodically test restoring from backups to ensure they work correctly
2. **Multiple Locations**: Store backups in multiple locations (cloud storage, external drives)
3. **Monitor Size**: Keep an eye on backup file sizes and storage usage
4. **Security**: Protect backup files as they contain sensitive business data
5. **Documentation**: Keep documentation of your backup schedule and procedures

## Security Considerations

- Backup files contain sensitive business data and should be protected
- Limit access to the backups directory
- Consider encrypting backup files if they contain highly sensitive information
- Store backups in secure locations with appropriate access controls