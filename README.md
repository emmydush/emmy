# Smart Solution Inventory Management System

![Django](https://img.shields.io/badge/Django-5.2-green)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![License](https://img.shields.io/badge/License-Proprietary-red)

Smart Solution is a comprehensive inventory management system designed for businesses of all sizes. Built with Django, it provides powerful tools to manage products, track stock levels, process sales, handle purchases, and generate detailed reports.

## Features

### 📦 Product Management
- Create and organize products with categories and units
- Track stock levels with real-time monitoring
- Set reorder points for automatic alerts
- Monitor expiry dates
- Bulk upload via CSV files

### 🛒 Sales Processing
- Point of Sale (POS) system with cart functionality
- Barcode scanning support
- Multiple payment methods
- Sales receipts and history

### 📊 Reporting & Analytics
- Sales reports (daily, weekly, monthly)
- Inventory status reports
- Profit and loss statements
- Expense summaries
- Product performance analysis

### 👥 User Management
- Role-based access control (Admin, Staff)
- Multi-language support (English, Kinyarwanda, Spanish, French, German)
- Profile management
- Activity audit logs

### 🚨 Stock Monitoring
- Automatic low stock alerts
- Fast-moving item notifications
- Theft detection alerts
- Email notifications for critical alerts

### 📱 Modern Interface
- Responsive design for all devices
- Light and dark theme support
- Voice assistant integration
- Intuitive navigation

## Technology Stack

- **Backend**: Django 5.2, Python 3.12
- **Database**: PostgreSQL (SQLite for development)
- **Frontend**: Bootstrap 5, jQuery, Chart.js
- **API**: Django REST Framework
- **Deployment**: Docker, Gunicorn, Nginx

## Quick Start

### Prerequisites
- Python 3.12+
- Git
- PostgreSQL (optional)

### Installation

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
```bash
docker-compose up --build
```

## Documentation

Detailed documentation is available in [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md), covering:

- System architecture
- API endpoints
- Database schema
- Deployment instructions
- Troubleshooting guide

## Key Modules

- **Authentication**: User management and access control
- **Dashboard**: Business overview and metrics
- **Products**: Complete product management system
- **Sales**: POS and transaction processing
- **Purchases**: Supplier order management
- **Customers**: Customer relationship management
- **Suppliers**: Vendor management
- **Expenses**: Business expense tracking
- **Reports**: Comprehensive reporting engine
- **Settings**: System configuration and administration

## Multi-language Support

The system supports multiple languages:
- English
- Kinyarwanda
- Spanish
- French
- German

Language preferences can be set per user and switched dynamically.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

## License

This project is proprietary software. All rights reserved.

## Support

For support, please open an issue on GitHub or contact the development team.