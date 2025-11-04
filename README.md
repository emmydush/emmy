# Inventory Management System

A comprehensive inventory management system built with Django, Python, and PostgreSQL for small shops, retail stores, alimentation, and boutiques.

## Features

### Authentication & User Management
- User signup/login with roles (Admin, Manager, Cashier, Stock Manager)
- Role-based access control
- Profile management
- Password reset functionality

### Dashboard
- Overview cards (Total Sales, Total Products, Total Customers, Low Stock Alerts)
- Graphs & charts (Sales trends, Top-selling products)
- Daily/Monthly revenue summary
- Recent transactions list

### Product & Inventory Management
- Add/Edit/Delete products
- Product categories & subcategories
- Units of measure (kg, pcs, box)
- Product barcode or SKU system
- Product images
- Stock tracking (available, incoming, outgoing)
- Low stock alerts & reorder levels
- Expiry date tracking (for alimentation)

### Supplier Management
- Add/Edit suppliers
- Track supplier transactions (purchases)
- Supplier contact info & balances
- Purchase order history

### Purchase Management
- Create purchase orders
- Record supplier invoices
- Update stock automatically when items received
- Handle partial deliveries
- Generate purchase receipts

### Sales Management / POS (Point of Sale)
- Add sales manually or through POS interface
- Barcode scanning
- Real-time stock deduction after sale
- Discounts, tax, and promotions
- Invoice & receipt generation (PDF)
- Return/refund management

### Customer Management
- Add/Edit customers
- Track customer purchase history
- Loyalty points or membership system
- Customer balances (credit sales)

### Expense Management
- Record daily/weekly/monthly expenses (rent, electricity, etc.)
- Category-wise expense tracking
- Add notes and attachments

### Financial / Accounting Module
- Cash flow tracking
- Profit & loss report
- Sales vs Purchase comparison
- Payment tracking (cash, credit, mobile money, etc.)
- Supplier and customer balances

### Reports & Analytics
- Sales report (daily, monthly, yearly)
- Stock report (in/out, current level)
- Profit report
- Expense report
- Supplier & customer statements
- Export data to CSV, PDF, or Excel

### Notifications & Alerts
- Low stock or expiry alerts
- Unpaid invoice reminders
- Email or in-app notifications

### Settings
- Business details (name, address, logo with removal option)
- Currency & tax settings
- Barcode format options
- Backup & restore database
- User permissions management

## Technology Stack

- **Backend**: Django 5.1+
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Authentication**: Django Authentication System
- **File Storage**: Django Media Files
- **Charts**: Chart.js

## Installation

### Option 1: Traditional Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure PostgreSQL database settings in `inventory_management/settings.py`

5. Run migrations:
   ```
   python manage.py migrate
   ```

6. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```
   python manage.py runserver
   ```

### Option 2: Docker Installation (Recommended)

For easier setup and deployment, you can use Docker and Docker Compose:

1. Make sure Docker Desktop is running
2. Open a terminal in the project root directory
3. Build and start the containers:
   ```bash
   docker-compose up -d
   ```
4. The application will be available at http://localhost:8000

See [DOCKER_README.md](DOCKER_README.md) for detailed Docker setup instructions.

## Usage

1. Access the admin panel at `http://localhost:8000/admin/`
2. Access the main application at `http://localhost:8000/`
3. Register a new user or login with the superuser account
4. Configure business settings in the admin panel
5. Start adding products, suppliers, and customers
6. Use the POS system for sales transactions
7. Generate reports to analyze business performance

## Modules

- `authentication`: User authentication and management
- `dashboard`: Main dashboard with overview statistics
- `products`: Product and inventory management
- `suppliers`: Supplier management
- `purchases`: Purchase order management
- `sales`: Sales and POS system
- `customers`: Customer management
- `expenses`: Expense tracking
- `reports`: Business reporting and analytics
- `notifications`: System notifications and alerts
- `settings`: System configuration and settings

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.