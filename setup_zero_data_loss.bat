@echo off
:: Zero Data Loss Setup Script for Windows
:: This script sets up automated backups for the Inventory Management System on Windows

echo Setting up Zero Data Loss for Inventory Management System
echo ========================================================

:: Check if we're in the right directory
if not exist "manage.py" (
    echo Error: manage.py not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

echo ✓ Project directory confirmed

:: Create backups directory if it doesn't exist
if not exist "backups" (
    mkdir backups
    echo ✓ Created backups directory
) else (
    echo ✓ Backups directory exists
)

:: Set proper permissions (Windows version - limited compared to Linux)
icacls backups /grant Everyone:(OI)(CI)F /T >nul 2>&1
echo ✓ Set backups directory permissions

:: Test backup creation
echo Testing backup creation...
python manage.py create_backup --name "setup_test_backup" --checksum

if %errorlevel% neq 0 (
    echo ✗ Backup creation test failed
    pause
    exit /b 1
)

echo ✓ Backup creation test successful

:: Test backup verification
echo Testing backup verification...
python manage.py verify_backup backups/setup_test_backup.zip --checksum --structure

if %errorlevel% neq 0 (
    echo ✗ Backup verification test failed
    del backups\setup_test_backup.zip
    del backups\setup_test_backup.zip.md5
    pause
    exit /b 1
)

echo ✓ Backup verification test successful

:: Clean up test backup
del backups\setup_test_backup.zip
del backups\setup_test_backup.zip.md5

:: Setup scheduled task for automated backups
echo Setting up automated backup schedule...

:: Create a batch file for the scheduled task
echo cd /d %cd% > run_backup.bat
echo python manage.py run_scheduled_backup >> run_backup.bat
echo exit /b 0 >> run_backup.bat

:: Create scheduled task (requires administrator privileges)
schtasks /create /tn "InventoryManagementBackup" /tr "%cd%\run_backup.bat" /sc daily /st 02:00 /f >nul 2>&1

if %errorlevel% equ 0 (
    echo ✓ Automated backup scheduled for 2:00 AM daily
) else (
    echo ✗ Failed to schedule automated backup. You may need to run this script as Administrator.
    echo   Alternatively, you can set up the task manually through Task Scheduler.
)

:: Show current scheduled tasks (filter for our task)
echo Current backup task:
schtasks /query /tn "InventoryManagementBackup" 2>nul | findstr "InventoryManagementBackup"

if %errorlevel% neq 0 (
    echo (Task not found or query failed)
)

:: Final instructions
echo.
echo Zero Data Loss setup complete!
echo ========================================================
echo Next steps:
echo 1. Configure backup settings in the superadmin dashboard
echo 2. Test restore procedure with: python manage.py restore_backup ^<backup_file^>
echo 3. Monitor backup logs in the backups directory
echo 4. Verify backups periodically with: python manage.py verify_backup --all
echo.
echo Backup schedule: Daily at 2:00 AM
echo Retention policy: 30 days (configurable in superadmin dashboard)
echo ========================================================
echo.
echo Run 'python manage.py test_zero_data_loss' to verify the complete setup
pause