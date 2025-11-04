# Setup script for Windows Task Scheduler to run automated backups
# This script creates a scheduled task that runs the backup management command daily

# Get the current directory (project root)
$ProjectRoot = Get-Location
$PythonPath = "python.exe"  # Adjust this if python is not in PATH
$ManagePyPath = Join-Path $ProjectRoot "manage.py"

# Task name
$TaskName = "InventoryManagementBackup"

# Check if task already exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Write-Host "Task $TaskName already exists. Deleting existing task..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create the scheduled task
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "manage.py run_scheduled_backup" -WorkingDirectory $ProjectRoot
$Trigger = New-ScheduledTaskTrigger -Daily -At "2:00AM"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# Register the task
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal

Write-Host "Scheduled task '$TaskName' created successfully!"
Write-Host "The backup task will run daily at 2:00 AM"
Write-Host "To modify the schedule, edit the task in Task Scheduler or modify the Backup Settings in the application"