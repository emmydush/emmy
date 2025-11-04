# How to Remove the Business Logo

This guide explains how to remove the business logo from your application.

## Method 1: Through the Web Interface (Recommended)

1. Navigate to **Settings** > **Business Settings** in your application
2. Scroll down to the **Business Logo** section
3. If you have an existing logo, you'll see:
   - The current logo displayed
   - A checkbox labeled "Delete current logo"
4. Check the "Delete current logo" checkbox
5. Click **Save Settings**
6. The logo will be removed from your business settings

## Method 2: Direct Database Update (Advanced)

If you need to remove the logo directly from the database:

```python
# In Django shell (python manage.py shell)
from settings.models import BusinessSettings

# Get the business settings
settings = BusinessSettings.objects.get(id=1)

# Delete the logo file and clear the field
if settings.business_logo:
    settings.business_logo.delete(save=False)
    settings.business_logo = None
    settings.save()
```

## How It Works

The logo removal functionality works through:

1. A `delete_logo` Boolean field in the [BusinessSettingsForm](file://e:\AI\settings\forms.py#L7-L32)
2. Custom form processing that:
   - Checks if the delete_logo checkbox is selected
   - Deletes the actual file from storage
   - Clears the database field
3. Template updates that display the checkbox when a logo exists

## Verification

After removing the logo:
- The navbar will show the business name without a logo
- The business settings page will no longer show a logo preview
- The database field will be NULL/empty

## Re-adding a Logo

To add a new logo after removing the current one:
1. Go to **Settings** > **Business Settings**
2. Use the file upload field under **Business Logo**
3. Select your new logo image file
4. Click **Save Settings**

The application supports common image formats (PNG, JPG, GIF, WebP) with a recommended size of 200x200 pixels.