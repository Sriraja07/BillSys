# ⚡ Electrical Billing Software

A comprehensive desktop application for electrical shop billing and inventory management built with Flask, SQLite, and PyWebView.

## 🚀 Features

### 📱 Complete Offline Application
- Fully functional without internet connection
- Desktop application using PyWebView
- Responsive design works on all screen sizes

### 🔐 User Management
- Role-based access (Admin, Employee, Owner)
- Secure login with mobile number and password
- Default admin account included

### 📊 Dashboard
- Real-time business analytics
- Sales, expenses, and inventory overview
- Interactive charts with Chart.js
- Low stock alerts

### 📦 Product Management
- Complete CRUD operations
- Category-wise product organization
- Stock tracking with alerts
- Profit margin calculations
- GST rate management

### 👥 Customer Management
- Customer database with unique mobile numbers
- Complete contact information
- Purchase history tracking

### 🚚 Vendor Management
- Vendor contact details
- GST number management
- Products supplied tracking

### 💰 POS Billing System
- Intuitive point-of-sale interface
- Real-time cart management
- GST calculations (CGST, SGST, IGST)
- Multiple payment methods
- Printable invoices
- Discount management

### 💳 Payment Tracking
- Customer payment history
- Vendor payment management
- Multiple payment methods (Cash, Card, UPI)
- Partial payment support

### 💸 Expense Management
- Category-wise expense tracking
- Monthly expense summaries
- Receipt management

### 📈 GST Tracking
- Automatic GST calculations
- Monthly GST summaries
- Compliance reporting

### 📊 Reports
- Monthly/Yearly sales reports
- Financial reports with GST
- Payment reports
- Best-selling products
- Stock reports

## 🛠️ Installation

### Prerequisites
- Python 3.7 or higher
- Windows 10/11 (for PyWebView desktop mode)

### Step 1: Clone or Download
```bash
git clone <repository-url>
cd electrical-billing-software
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application

#### Option A: Desktop Application (Recommended)
```bash
python desktop_app.py
```

#### Option B: Web Application
```bash
python app.py
```
Then open http://localhost:5000 in your browser

## 🔑 Default Login Credentials

- **Mobile Number:** 9999999999
- **Password:** admin123
- **Role:** Administrator

## 📱 Usage Guide

### 1. Login
- Use the default credentials or create new users
- Select appropriate role (Admin/Employee/Owner)

### 2. Dashboard Overview
- View business statistics
- Monitor low stock items
- Track sales and expenses

### 3. Product Management
- Add new products with all details
- Set GST rates and pricing
- Track stock levels
- Manage categories

### 4. Customer Management
- Add customer details
- Unique mobile number identification
- Track purchase history

### 5. POS Billing
- Select products for billing
- Add customer information
- Apply discounts
- Generate and print invoices
- Process payments

### 6. Inventory Management
- Monitor stock levels
- Update stock quantities
- Low stock alerts
- Category-wise viewing

### 7. Reports
- Generate various business reports
- Export and print capabilities
- Filter by date ranges

## 🏗️ Technical Architecture

### Backend
- **Framework:** Flask (Python)
- **Database:** SQLite
- **ORM:** SQLAlchemy
- **Authentication:** Flask-Login

### Frontend
- **Styling:** TailwindCSS
- **Icons:** Font Awesome
- **Charts:** Chart.js
- **JavaScript:** Vanilla JS

### Desktop Integration
- **Framework:** PyWebView
- **Window Management:** Native OS integration

### Database Schema
- Users (authentication and roles)
- Products (inventory management)
- Customers (contact management)
- Vendors (supplier management)
- Invoices & Invoice Items (billing)
- Payments (transaction tracking)
- Expenses (cost management)

## 📁 Project Structure
```
electrical-billing-software/
├── app.py                 # Main Flask application
├── desktop_app.py         # PyWebView desktop launcher
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── login.html        # Login page
│   ├── dashboard.html    # Dashboard
│   ├── products.html     # Product listing
│   ├── add_product.html  # Add product form
│   ├── pos_billing.html  # POS system
│   └── ...              # Other templates
└── electrical_billing.db # SQLite database (auto-created)
```

## 🔧 Configuration

### Database
The application uses SQLite database which is automatically created on first run. The database file `electrical_billing.db` will be created in the project root directory.

### Security
- Change the default `SECRET_KEY` in `app.py` for production use
- Update default admin credentials after first login
- Consider implementing additional security measures for production deployment

## 🆘 Troubleshooting

### Common Issues

1. **Port Already in Use**
   - Change the port in `app.py` and `desktop_app.py`

2. **PyWebView Not Starting**
   - Ensure you have the latest version installed
   - Check Windows compatibility

3. **Database Errors**
   - Delete `electrical_billing.db` and restart the application

4. **Module Not Found**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`

## 🚀 Features Roadmap

- [ ] Barcode scanning integration
- [ ] Multi-store management
- [ ] Cloud backup and sync
- [ ] Advanced reporting with PDF export
- [ ] SMS/Email notifications
- [ ] Accounting software integration

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the usage guide

## 💡 Contributing

Contributions are welcome! Please read the contributing guidelines before submitting pull requests.

---

**Note:** This is a complete offline application designed for electrical shops and similar retail businesses. All data is stored locally in SQLite database for maximum privacy and reliability. 