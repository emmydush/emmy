# Smart Solution Inventory Management System

## Table of Contents
1. [Project Overview](#project-overview)
2. [Key Features](#key-features)
3. [Technology Stack](#technology-stack)
4. [System Architecture](#system-architecture)
5. [Installation](#installation)
6. [Configuration](#configuration)
7. [Modules](#modules)
8. [API Documentation](#api-documentation)
9. [Database Schema](#database-schema)
10. [Deployment](#deployment)
11. [Testing](#testing)
12. [Troubleshooting](#troubleshooting)

## Project Overview

Smart Solution is a comprehensive inventory management system built with Django. It provides businesses with tools to efficiently manage products, track stock levels, process sales, handle purchases, monitor expenses, and generate detailed reports. The system supports multi-language interfaces and is designed with a modern, responsive UI.

## Key Features

### Core Functionality
- **Product Management**: Create, update, and organize products with categories and units
- **Stock Monitoring**: Real-time tracking of inventory levels with automatic alerts
- **Sales Processing**: Point of Sale (POS) system with cart functionality
- **Purchase Management**: Track supplier purchases and inventory replenishment
- **Expense Tracking**: Monitor business expenses with categorization
- **Customer Management**: Maintain customer database and purchase history
- **Supplier Management**: Manage supplier information and purchase records

### Advanced Features
- **Multi-language Support**: English, Kinyarwanda, Spanish, French, and German interfaces
- **Real-time Stock Alerts**: Automatic notifications for low stock and fast-moving items
- **Reporting System**: Comprehensive sales, inventory, profit/loss, and expense reports
- **User Management**: Role-based access control with admin and staff permissions
- **Bulk Upload**: Import products via CSV files for efficient data entry
- **Audit Logs**: Track all system activities for accountability
- **Backup & Restore**: Data backup functionality for disaster recovery

### Technical Features
- **Responsive Design**: Mobile-friendly interface that works on all devices
- **Multi-tenancy**: Support for multiple businesses on a single installation
- **RESTful API**: Programmatic access to system data
- **Theme Customization**: Light and dark mode support
- **Voice Assistant**: Voice-controlled navigation and commands

## Technology Stack

### Backend
- **Django 5.2**: High-level Python web framework
- **Python 3.12**: Programming language
- **PostgreSQL**: Primary database (with SQLite support for development)
- **Django REST Framework**: API development toolkit

### Frontend
- **Bootstrap 5**: CSS framework for responsive design
- **jQuery**: JavaScript library for DOM manipulation
- **Font Awesome**: Icon library
- **Chart.js**: Data visualization library

### Development & Deployment
- **Docker**: Containerization platform
- **GitHub**: Version control system
- **Black**: Code formatting tool
- **WhiteNoise**: Static file serving in production

## System Architecture

The system follows a modular Django architecture with the following key components:

```
inventory_management/
├── authentication/     # User authentication and management
├── dashboard/          # Main dashboard views
├── products/           # Product management system
├── sales/              # Sales processing and POS
├── purchases/          # Purchase order management
├── customers/          # Customer database
├── suppliers/          # Supplier management
├── expenses/           # Expense tracking
├── reports/            # Reporting engine
├── settings/           # System configuration
├── notifications/      # Notification system
├── api/                # RESTful API endpoints
├── superadmin/         # Multi-tenancy management
└── templates/          # HTML templates
```

## Installation

### Prerequisites
- Python 3.12+
- PostgreSQL (optional, SQLite used for development)
- Git

### Quick Setup

1. **Clone the repository**:
```bash
git clone https://github.com/emmydush/PROJECT_1.git
cd PROJECT_1
```

2. **Create virtual environment**:
```bash
python -m venv venv_new
source venv_new/bin/activate  # On Windows: venv_new\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Database setup**:
```bash
python manage.py migrate
```

5. **Create superuser**:
```bash
python manage.py createsuperuser
```

6. **Run development server**:
```bash
python manage.py runserver
```

### Docker Setup (Alternative)

1. **Build and run with Docker**:
```bash
docker-compose up --build
```

2. **Run migrations**:
```bash
docker-compose exec web python manage.py migrate
```

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
EMAIL_HOST=smtp.your-email-provider.com
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
```

### Settings Files

- `inventory_management/settings.py`: Main settings file
- `local_settings.py`: Local development settings (gitignored)
- `smartbusiness/settings.py`: Production settings

### Multi-tenancy Configuration

The system supports multi-business operations through the superadmin module:
- Each business has isolated data
- Users can be associated with specific businesses
- Business-specific settings and configurations

## Modules

### Authentication
Handles user registration, login, password management, and role-based access control.

**Key Features**:
- User registration with profile management
- Password reset functionality
- Role-based permissions (Admin, Staff)
- Multi-language user preferences
- Profile picture upload

### Dashboard
Central hub displaying key business metrics and quick access to important functions.

**Components**:
- Sales overview charts
- Stock level indicators
- Recent activity feed
- Quick action buttons

### Products
Comprehensive product management system.

**Features**:
- Product creation with SKU, barcode, categories, and units
- Stock level tracking with reorder points
- Expiry date monitoring
- Bulk upload via CSV
- Stock adjustment requests
- Category and unit management

### Sales
Point of Sale system for processing customer transactions.

**Components**:
- Shopping cart functionality
- Barcode scanning support
- Multiple payment methods
- Sales receipts
- Customer association
- Sales history and reporting

### Purchases
Supplier purchase order management.

**Features**:
- Purchase order creation
- Supplier management
- Purchase history tracking
- Payment status monitoring

### Customers
Customer relationship management.

**Capabilities**:
- Customer database with contact information
- Purchase history tracking
- Customer segmentation
- Communication logs

### Suppliers
Supplier management system.

**Functionality**:
- Supplier database
- Product catalog by supplier
- Purchase order history
- Performance tracking

### Expenses
Business expense tracking and categorization.

**Features**:
- Expense categories
- Payment method tracking
- Recurring expenses
- Expense reports

### Reports
Comprehensive reporting engine.

**Report Types**:
- Sales reports (daily, weekly, monthly)
- Inventory reports
- Profit and loss statements
- Expense summaries
- Product performance analysis

### Settings
System configuration and administration.

**Sections**:
- Business settings
- Barcode configuration
- User management
- Backup and restore
- Audit logs
- Theme customization
- Email settings
- Voice assistant configuration

### Notifications
Real-time notification system.

**Notification Types**:
- Stock alerts (low stock, fast-moving items)
- Sales confirmations
- Purchase order updates
- System alerts

### API
RESTful API for programmatic access.

**Endpoints**:
- Authentication endpoints
- Product data access
- Sales data retrieval
- Customer information
- Reporting data

## API Documentation

### Authentication Endpoints

**POST /api/auth/login/**
- Description: User login
- Parameters: username, password
- Response: JWT token, user information

**POST /api/auth/register/**
- Description: User registration
- Parameters: username, email, password
- Response: Success message, user information

### Product Endpoints

**GET /api/products/**
- Description: List all products
- Parameters: page, limit, search
- Response: Paginated product list

**POST /api/products/**
- Description: Create new product
- Parameters: name, sku, category, unit, price, quantity
- Response: Created product details

**GET /api/products/{id}/**
- Description: Get specific product
- Response: Product details

**PUT /api/products/{id}/**
- Description: Update product
- Parameters: Updated product fields
- Response: Updated product details

### Sales Endpoints

**GET /api/sales/**
- Description: List sales transactions
- Parameters: date range, customer
- Response: Paginated sales list

**POST /api/sales/**
- Description: Create new sale
- Parameters: items, customer, payment method
- Response: Sale details with receipt

## Database Schema

### Core Models

**User** (authentication)
- username, email, first_name, last_name
- profile_picture, phone, address
- role (admin/staff), language preference
- business association

**Business** (superadmin)
- business_name, business_logo
- contact information, settings
- subscription plan

**Product** (products)
- name, sku, barcode
- category, unit
- cost_price, selling_price
- quantity, reorder_level
- expiry_date, description
- business association

**Category** (products)
- name, description
- business association

**Unit** (products)
- name, symbol
- business association

**Sale** (sales)
- customer, total_amount
- payment_method, status
- timestamp, business association

**SaleItem** (sales)
- sale, product
- quantity, unit_price
- total_price

**Purchase** (purchases)
- supplier, total_amount
- status, payment_status
- timestamp, business association

**Customer** (customers)
- name, email, phone
- address, business association

**Supplier** (suppliers)
- name, email, phone
- address, business association

**Expense** (expenses)
- amount, category
- description, date
- business association

### Relationships
- All business-related data is associated with a specific business
- Users are associated with one or more businesses
- Products, sales, purchases, customers, suppliers, and expenses belong to a business
- Categories and units are business-specific

## Deployment

### Production Setup

1. **Environment Configuration**:
```bash
export DEBUG=False
export SECRET_KEY=your-production-secret-key
export DATABASE_URL=postgresql://user:password@localhost:5432/production_db
```

2. **Static Files Collection**:
```bash
python manage.py collectstatic --noinput
```

3. **Database Migration**:
```bash
python manage.py migrate --noinput
```

4. **Web Server Configuration**:
Use Gunicorn with Nginx for production deployment:
```bash
gunicorn inventory_management.wsgi:application --bind 0.0.0.0:8000
```

### Docker Deployment

1. **Build Production Image**:
```bash
docker build -t smart-solution .
```

2. **Run with Docker Compose**:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### SSL Configuration

For HTTPS, configure Nginx with SSL certificates:
```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Testing

### Running Tests

**Run all tests**:
```bash
python manage.py test
```

**Run specific app tests**:
```bash
python manage.py test products
python manage.py test sales
```

### Test Categories

1. **Unit Tests**: Individual function and model testing
2. **Integration Tests**: Cross-module functionality testing
3. **API Tests**: Endpoint validation
4. **UI Tests**: Frontend component testing

### Test Files
- Each app contains `tests.py` with relevant test cases
- Management commands for specific testing scenarios
- Automated test scripts in the project root

## Troubleshooting

### Common Issues

**Database Connection Error**
- Verify database credentials in settings
- Check if PostgreSQL service is running
- Ensure database exists and user has permissions

**Static Files Not Loading**
- Run `python manage.py collectstatic`
- Check STATIC_ROOT and STATIC_URL settings
- Verify web server configuration for static files

**Permission Denied Errors**
- Check user roles and permissions
- Verify business associations
- Review group-based permissions

**Language Switching Not Working**
- Ensure locale files are compiled
- Check LOCALE_PATHS setting
- Verify .mo files exist in locale directories

**Bulk Upload Failures**
- Validate CSV file format
- Check required columns (Name, SKU, Category, Unit)
- Ensure business context is set

### Debugging Tools

1. **Django Debug Toolbar**: Enabled in development
2. **Logging**: Configured in settings.py
3. **Management Commands**: Custom debugging scripts
4. **Database Queries**: Django ORM query logging

### Support

For issues not covered in this documentation:
1. Check GitHub issues
2. Review error logs
3. Contact development team
4. Refer to Django documentation for framework-specific issues

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create pull request

## License

This project is proprietary software. All rights reserved.

## Contact

For support and inquiries, contact the development team through GitHub issues.