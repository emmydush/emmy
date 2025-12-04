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

#### For Render Deployment:
Render deployments should use the DATABASE_URL environment variable which is automatically provided by Render.
No additional configuration is needed in `local_settings.py` for database configuration.

#### For Development (SQLite):
The system will automatically use SQLite if no local_settings.py is found and no DATABASE_URL environment variable is set.

### Environment Variables

For Render and other cloud deployments, the following environment variables can be used:

- `DATABASE_URL`: PostgreSQL database connection string (automatically provided by Render)
- `SECRET_KEY`: Django secret key for production
- `DEBUG`: Set to False for production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts

Example .env file for local development with Render-like configuration:
```
DATABASE_URL=postgresql://user:password@localhost:5432/database_name
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
```

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
1. Set `DEBUG = False` in your local_settings.py or environment variables
2. Use a proper PostgreSQL database (via DATABASE_URL environment variable on Render)
3. Configure a secure SECRET_KEY
4. Set appropriate ALLOWED_HOSTS
5. Configure email settings for production

### Common Issues

1. **Missing local_settings.py**: The application will fall back to SQLite for development or use DATABASE_URL if available.
2. **Database connection errors**: Check your database credentials and ensure the database server is running.
3. **Environment variables not loading**: Ensure the .env file is in the project root directory.