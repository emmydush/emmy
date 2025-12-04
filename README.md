# Inventory Management System

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- PostgreSQL (recommended) or SQLite (for development only)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd inventory-management-system
   ```

2. Create a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure local settings:
   - Copy `inventory_management/local_settings_template.py` to `inventory_management/local_settings.py`
   - Update the database configuration in `local_settings.py`

### Database Configuration

#### For Production (PostgreSQL - Recommended):
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_database_name',
        'USER': 'your_database_user',
        'PASSWORD': 'your_database_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

#### For Development (SQLite):
The system will automatically use SQLite if no local_settings.py is found.

### Running the Application

1. Apply migrations:
   ```
   python manage.py migrate
   ```

2. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

3. Run the development server:
   ```
   python manage.py runserver
   ```

### Deployment

For production deployment, ensure you:
1. Set `DEBUG = False` in your local_settings.py
2. Use a proper PostgreSQL database
3. Configure a secure SECRET_KEY
4. Set appropriate ALLOWED_HOSTS
5. Configure email settings for production

### Common Issues

1. **Missing local_settings.py**: The application will fall back to SQLite for development.
2. **Database connection errors**: Check your database credentials and ensure the database server is running.