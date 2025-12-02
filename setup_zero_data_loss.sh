#!/bin/bash
# Zero Data Loss Setup Script
# This script sets up automated backups for the Inventory Management System

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up Zero Data Loss for Inventory Management System${NC}"
echo "========================================================"

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: manage.py not found. Please run this script from the project root directory.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Project directory confirmed${NC}"

# Create backups directory if it doesn't exist
if [ ! -d "backups" ]; then
    mkdir backups
    echo -e "${GREEN}✓ Created backups directory${NC}"
else
    echo -e "${GREEN}✓ Backups directory exists${NC}"
fi

# Set proper permissions
chmod 755 backups
echo -e "${GREEN}✓ Set backups directory permissions${NC}"

# Test backup creation
echo -e "${YELLOW}Testing backup creation...${NC}"
python manage.py create_backup --name "setup_test_backup" --checksum

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backup creation test successful${NC}"
else
    echo -e "${RED}✗ Backup creation test failed${NC}"
    exit 1
fi

# Test backup verification
echo -e "${YELLOW}Testing backup verification...${NC}"
python manage.py verify_backup backups/setup_test_backup.zip --checksum --structure

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backup verification test successful${NC}"
else
    echo -e "${RED}✗ Backup verification test failed${NC}"
    exit 1
fi

# Clean up test backup
rm -f backups/setup_test_backup.zip backups/setup_test_backup.zip.md5

# Setup cron jobs for automated backups
echo -e "${YELLOW}Setting up automated backup schedule...${NC}"

# Create cron job entry
CRON_JOB="0 2 * * * cd $(pwd) && python manage.py run_scheduled_backup >> backups/backup.log 2>&1"

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Automated backup scheduled for 2:00 AM daily${NC}"
else
    echo -e "${RED}✗ Failed to schedule automated backup${NC}"
fi

# Show current crontab
echo -e "${BLUE}Current crontab:${NC}"
crontab -l

# Instructions for manual setup if cron fails
echo
echo -e "${YELLOW}If cron setup failed, you can manually add this line to your crontab:${NC}"
echo "$CRON_JOB"
echo
echo -e "${BLUE}To edit crontab manually, run: crontab -e${NC}"

# Setup log rotation
echo -e "${YELLOW}Setting up log rotation...${NC}"

# Create logrotate configuration
cat > /tmp/inventory_backup_logrotate << EOF
$(pwd)/backups/backup.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 $(whoami) $(whoami)
}
EOF

# Try to copy to system logrotate directory
if [ -w "/etc/logrotate.d" ]; then
    sudo cp /tmp/inventory_backup_logrotate /etc/logrotate.d/inventory_backup
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Log rotation configured${NC}"
    else
        echo -e "${RED}✗ Failed to configure log rotation${NC}"
    fi
else
    echo -e "${YELLOW}Note: Could not configure log rotation. You may need to set it up manually.${NC}"
fi

# Cleanup
rm -f /tmp/inventory_backup_logrotate

# Final instructions
echo
echo -e "${GREEN}Zero Data Loss setup complete!${NC}"
echo "========================================================"
echo "Next steps:"
echo "1. Configure backup settings in the superadmin dashboard"
echo "2. Test restore procedure with: python manage.py restore_backup <backup_file>"
echo "3. Monitor backup logs at: backups/backup.log"
echo "4. Verify backups periodically with: python manage.py verify_backup --all"
echo
echo -e "${BLUE}Backup schedule: Daily at 2:00 AM${NC}"
echo -e "${BLUE}Retention policy: 30 days (configurable in superadmin dashboard)${NC}"
echo "========================================================"

echo -e "${GREEN}Run 'python manage.py test_zero_data_loss' to verify the complete setup${NC}"