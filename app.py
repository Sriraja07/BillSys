import webview
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy import literal
import sqlite3
import os
import csv
from io import StringIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///electrical_billing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mobile_number = db.Column(db.String(15), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, employee, owner
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    mrp_price = db.Column(db.Float, nullable=False)
    cost_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    gst_rate = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mobile_number = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mobile_number = db.Column(db.String(15), unique=True, nullable=False)
    gst_number = db.Column(db.String(15))
    address = db.Column(db.Text)
    products_supplied = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_no = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    total_amount = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0)
    cgst = db.Column(db.Float, default=0)
    sgst = db.Column(db.Float, default=0)
    igst = db.Column(db.Float, default=0)
    final_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), default='unpaid')  # paid, partial, unpaid
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    customer = db.relationship('Customer', backref='invoices')

class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    invoice = db.relationship('Invoice', backref='items')
    product = db.relationship('Product', backref='invoice_items')

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'))
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # cash, card, upi
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='completed')
    invoice = db.relationship('Invoice', backref='payments')

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    amount = db.Column(db.Float, nullable=False)
    expense_date = db.Column(db.DateTime, default=datetime.utcnow)

class VendorPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase.id'))
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(200))
    purchase = db.relationship('Purchase', backref='payments')

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_no = db.Column(db.String(20), unique=True, nullable=False)
    po_bill_no = db.Column(db.String(50), nullable=True)  # PO Bill Number from vendor
    purchase_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'))
    total_amount = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0)
    cgst = db.Column(db.Float, default=0)
    sgst = db.Column(db.Float, default=0)
    final_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), default='unpaid')  # paid, partial, unpaid
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    vendor = db.relationship('Vendor', backref='purchases')

class PurchaseItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    purchase = db.relationship('Purchase', backref='items')
    product = db.relationship('Product', backref='purchase_items')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Add datetime to template context
@app.context_processor
def inject_datetime():
    return {'datetime': datetime}

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mobile_number = request.form['mobile_number']
        password = request.form['password']
        
        user = User.query.filter_by(mobile_number=mobile_number).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid mobile number or password', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Calculate dashboard stats
    total_sales = db.session.query(db.func.sum(Invoice.final_amount)).scalar() or 0
    total_expenses = db.session.query(db.func.sum(Expense.amount)).scalar() or 0
    customer_count = Customer.query.count()
    vendor_count = Vendor.query.count()
    product_count = Product.query.count()

    # Current period data (last 30 days)
    month_ago = datetime.now() - timedelta(days=30)
    monthly_sales = db.session.query(db.func.sum(Invoice.final_amount)).filter(
        Invoice.created_at >= month_ago
    ).scalar() or 0

    # Expense uses expense_date
    monthly_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
        Expense.expense_date >= month_ago
    ).scalar() or 0

    # Previous period data (30-60 days ago)
    two_months_ago = datetime.now() - timedelta(days=60)
    previous_month_sales = db.session.query(db.func.sum(Invoice.final_amount)).filter(
        Invoice.created_at >= two_months_ago,
        Invoice.created_at < month_ago
    ).scalar() or 0

    previous_month_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
        Expense.expense_date >= two_months_ago,
        Expense.expense_date < month_ago
    ).scalar() or 0

    # Calculate percentage changes
    sales_change = 0
    if previous_month_sales > 0:
        sales_change = ((monthly_sales - previous_month_sales) / previous_month_sales) * 100

    expenses_change = 0
    if previous_month_expenses > 0:
        expenses_change = ((monthly_expenses - previous_month_expenses) / previous_month_expenses) * 100

    # New customers this month
    new_customers = Customer.query.filter(Customer.created_at >= month_ago).count()

    # Weekly sales data (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    weekly_sales = db.session.query(db.func.sum(Invoice.final_amount)).filter(
        Invoice.created_at >= week_ago
    ).scalar() or 0

    # Generate weekly chart data (last 7 days)
    from collections import defaultdict
    daily_sales = defaultdict(float)

    recent_invoices = Invoice.query.filter(Invoice.created_at >= week_ago).all()

    for i in range(7):
        date = (datetime.now() - timedelta(days=6 - i)).strftime('%a')
        daily_sales[date] = 0

    for invoice in recent_invoices:
        day_name = invoice.created_at.strftime('%a')
        daily_sales[day_name] += invoice.final_amount

    weekly_chart_data = {
        'labels': list(daily_sales.keys()),
        'data': list(daily_sales.values())
    }

    low_stock_count = Product.query.filter(Product.stock_quantity <= 5).count()

    # Recent invoices (last 5)
    recent_invoices_list = [
        {
            'bill_no': inv.bill_no,
            'date': inv.created_at.strftime('%d-%m-%Y'),
            'customer': (inv.customer.name if inv.customer else 'Walk-in'),
            'amount': inv.final_amount,
            'status': inv.payment_status or 'unpaid'
        }
        for inv in Invoice.query.order_by(Invoice.created_at.desc()).limit(5).all()
    ]

    # Low stock list (<= 10)
    low_stock_list = [
        { 'name': p.name, 'qty': p.stock_quantity, 'category':p.category,'brand':p.brand}
        for p in Product.query.filter(Product.stock_quantity <= 10).order_by(Product.stock_quantity.asc()).limit(8).all()
    ]

    stats = {
        'total_sales': total_sales,
        'total_expenses': total_expenses,
        'customer_count': customer_count,
        'vendor_count': vendor_count,
        'product_count': product_count,
        'weekly_sales': weekly_sales,
        'monthly_sales': monthly_sales,
        'sales_change': sales_change,
        'expenses_change': expenses_change,
        'new_customers': new_customers,
        'low_stock_count': low_stock_count,
        'weekly_chart_data': weekly_chart_data,
        'recent_invoices': recent_invoices_list,
        'low_stock_list': low_stock_list,
    }

    return render_template('dashboard.html', stats=stats)

# Product CRUD Routes
@app.route('/products')
@login_required
def products():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    category = request.args.get('category', '', type=str)
    
    query = Product.query
    
    if search:
        query = query.filter(Product.name.contains(search))
    if category:
        query = query.filter(Product.category == category)
    
    products = query.paginate(
        page=page, per_page=10, error_out=False
    )
    
    categories = db.session.query(Product.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('products.html', products=products, categories=categories, search=search, category=category)

@app.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        product = Product(
            name=request.form['name'],
            category=request.form['category'],
            brand=request.form['brand'],
            mrp_price=float(request.form['mrp_price']),
            cost_price=float(request.form['cost_price']),
            selling_price=float(request.form['selling_price']),
            gst_rate=float(request.form['gst_rate']),
            stock_quantity=int(request.form['stock_quantity']),
            vendor_id=int(request.form['vendor_id']) if request.form['vendor_id'] else None
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('products'))
    
    vendors = Vendor.query.all()
    return render_template('add_product.html', vendors=vendors)

@app.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form['name']
        product.category = request.form['category']
        product.brand = request.form['brand']
        product.mrp_price = float(request.form['mrp_price'])
        product.cost_price = float(request.form['cost_price'])
        product.selling_price = float(request.form['selling_price'])
        product.gst_rate = float(request.form['gst_rate'])
        product.stock_quantity = int(request.form['stock_quantity'])
        product.vendor_id = int(request.form['vendor_id']) if request.form['vendor_id'] else None
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('products'))
    
    vendors = Vendor.query.all()
    return render_template('edit_product.html', product=product, vendors=vendors)

@app.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('products'))

# Customer CRUD Routes
@app.route('/customers')
@login_required
def customers():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = Customer.query
    if search:
        query = query.filter(
            db.or_(
                Customer.name.contains(search),
                Customer.mobile_number.contains(search)
            )
        )
    
    customers = query.paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('customers.html', customers=customers, search=search)

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        customer = Customer(
            name=request.form['name'],
            mobile_number=request.form['mobile_number'],
            email=request.form.get('email'),
            address=request.form.get('address')
        )
        try:
            db.session.add(customer)
            db.session.commit()
            flash('Customer added successfully!', 'success')
            return redirect(url_for('customers'))
        except Exception as e:
            db.session.rollback()
            flash('Mobile number already exists!', 'error')
    
    return render_template('add_customer.html')

@app.route('/customers/edit/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    if request.method == 'POST':
        customer.name = request.form['name']
        customer.mobile_number = request.form['mobile_number']
        customer.email = request.form.get('email')
        customer.address = request.form.get('address')
        
        try:
            db.session.commit()
            flash('Customer updated successfully!', 'success')
            return redirect(url_for('customers'))
        except Exception as e:
            db.session.rollback()
            flash('Mobile number already exists!', 'error')
    
    return render_template('edit_customer.html', customer=customer)

@app.route('/customers/delete/<int:customer_id>', methods=['POST'])
@login_required
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    flash('Customer deleted successfully!', 'success')
    return redirect(url_for('customers'))

# Vendor CRUD Routes
@app.route('/vendors')
@login_required
def vendors():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = Vendor.query
    if search:
        query = query.filter(
            db.or_(
                Vendor.name.contains(search),
                Vendor.mobile_number.contains(search)
            )
        )
    
    vendors = query.paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('vendors.html', vendors=vendors, search=search)

@app.route('/vendors/add', methods=['GET', 'POST'])
@login_required
def add_vendor():
    if request.method == 'POST':
        vendor = Vendor(
            name=request.form['name'],
            mobile_number=request.form['mobile_number'],
            gst_number=request.form.get('gst_number'),
            address=request.form.get('address'),
            products_supplied=request.form.get('products_supplied')
        )
        try:
            db.session.add(vendor)
            db.session.commit()
            flash('Vendor added successfully!', 'success')
            return redirect(url_for('vendors'))
        except Exception as e:
            db.session.rollback()
            flash('Mobile number already exists!', 'error')
    
    return render_template('add_vendor.html')

@app.route('/vendors/edit/<int:vendor_id>', methods=['GET', 'POST'])
@login_required
def edit_vendor(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    
    if request.method == 'POST':
        vendor.name = request.form['name']
        vendor.mobile_number = request.form['mobile_number']
        vendor.gst_number = request.form.get('gst_number')
        vendor.address = request.form.get('address')
        vendor.products_supplied = request.form.get('products_supplied')
        
        db.session.commit()
        flash('Vendor updated successfully!', 'success')
        return redirect(url_for('vendors'))
    
    return render_template('edit_vendor.html', vendor=vendor)

@app.route('/vendors/delete/<int:vendor_id>', methods=['POST'])
@login_required
def delete_vendor(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    db.session.delete(vendor)
    db.session.commit()
    flash('Vendor deleted successfully!', 'success')
    return redirect(url_for('vendors'))

# Stock Management Routes
@app.route('/stock')
@login_required
def stock_management():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    low_stock = request.args.get('low_stock', False, type=bool)
    
    query = Product.query
    
    if search:
        query = query.filter(Product.name.contains(search))
    if low_stock:
        query = query.filter(Product.stock_quantity <= 10)
    
    products = query.paginate(
        page=page, per_page=15, error_out=False
    )

    return render_template('stock_management.html', products=products, search=search, low_stock=low_stock)

@app.route('/stock/update/<int:product_id>', methods=['POST'])
@login_required
def update_stock(product_id):
    product = Product.query.get_or_404(product_id)
    action = request.form['action']
    quantity = int(request.form['quantity'])
    
    if action == 'add':
        product.stock_quantity += quantity
        flash(f'Added {quantity} items to {product.name}', 'success')
    elif action == 'remove':
        if product.stock_quantity >= quantity:
            product.stock_quantity -= quantity
            flash(f'Removed {quantity} items from {product.name}', 'success')
        else:
            flash('Insufficient stock!', 'error')
            return redirect(url_for('stock_management'))
    
    db.session.commit()
    return redirect(url_for('stock_management'))

# POS Billing Routes
@app.route('/pos')
@login_required
def pos_billing():
    products = Product.query.filter(Product.stock_quantity > 0).all()
    customers = Customer.query.all()
    categories = db.session.query(Product.category).distinct().all()
    categories = [cat[0] for cat in categories]
    last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
    bill_no = f"INV-{(last_invoice.id + 1) if last_invoice else 1:03d}"

    # Provide JSON-serializable product dicts for client-side pagination
    product_dicts = [
        {
            'id': p.id,
            'name': p.name,
            'category': p.category or '',
            'brand': p.brand or '',
            'selling_price': p.selling_price,
            'cost_price': p.cost_price,
            'gst_rate': p.gst_rate,
            'stock_quantity': p.stock_quantity,
        }
        for p in products
    ]

    customer_dicts = [
        {
            'id': c.id,
            'name': c.name,
            'mobile_number': c.mobile_number or ''
        }
        for c in customers
    ]

    return render_template(
        'pos_billing.html',
        products=products,  # still used for server-rendered cards if any
        customers=customers,
        categories=categories,
        bill_no=bill_no,
        products_json=product_dicts,
        customers_json=customer_dicts,
    )

@app.route('/pos/addCustomer', methods=['POST'])
@login_required
def addCustomerFromPOS():
    data=request.get_json()
    customer = Customer(
            name=data.get('name'),
            mobile_number=data.get('mobile'),
            email=data.get('email'),
            address=""
        )
    try:
        db.session.add(customer)
        db.session.commit()
        #flash('Customer added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Mobile number already exists!', 'error')

    return jsonify({'success': True, 'customerId': customer.id})



@app.route('/pos/addVendor', methods=['POST'])
@login_required
def addVendorFromPO():
    data=request.get_json()
    vendor = Vendor(
            name=data.get('name'),
            mobile_number=data.get('mobile')
        )
    try:
        db.session.add(vendor)
        db.session.commit()
        #flash('Customer added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Mobile number already exists!', 'error')

    return jsonify({'success': True, 'vendorId': vendor.id})


@app.route('/pos/create-invoice', methods=['POST'])
@login_required
def create_invoice():
    data = request.get_json()
    
    # Generate bill number
    last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
    bill_no = f"INV-{(last_invoice.id + 1) if last_invoice else 1:03d}"
    
    # Create invoice
    invoice = Invoice(
        bill_no=bill_no,
        customer_id=data.get('customer_id'),
        total_amount=data['total_amount'],
        discount=data.get('discount', 0),
        cgst=data.get('cgst', 0),
        sgst=data.get('sgst', 0),
        igst=data.get('igst', 0),
        final_amount=data['final_amount']
    )
    
    db.session.add(invoice)
    db.session.flush()  # Get the invoice ID

    if float(data.get('payment_amount'))!=0.0:
        payment = Payment(
        invoice_id=invoice.id,
        amount=float(data.get('payment_amount')),
        payment_method=data.get('payment_method'),
        status='completed'
        )
        db.session.add(payment)
        if float(data.get('payment_amount')) >= invoice.final_amount:
            invoice.payment_status = 'paid'
        else:
            invoice.payment_status = 'partial'
    
    # Add invoice items
    for item in data['items']:
        invoice_item = InvoiceItem(
            invoice_id=invoice.id,
            product_id=item['product_id'],
            quantity=item['quantity'],
            unit_price=item['unit_price'],
            total_price=item['total_price']
        )
        db.session.add(invoice_item)
        
        # Update stock
        product = Product.query.get(item['product_id'])
        product.stock_quantity -= item['quantity']
    
    db.session.commit()
    
    return jsonify({'success': True, 'bill_no': bill_no, 'invoice_id': invoice.id})



# Expense Routes
@app.route('/expenses')
@login_required
def expenses():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '', type=str)
    month = request.args.get('month', datetime.now().strftime('%Y-%m'), type=str)
    current_month = datetime.now().strftime('%Y-%m')
    
    
    if not month:
        month = current_month


    query = Expense.query
    
    if category:
        query = query.filter(Expense.category == category)
    
    if month:
        year, month_num = month.split('-')
        start_date = datetime(int(year), int(month_num), 1)
        if int(month_num) == 12:
            end_date = datetime(int(year) + 1, 1, 1)
        else:
            end_date = datetime(int(year), int(month_num) + 1, 1)
        query = query.filter(Expense.expense_date >= start_date, Expense.expense_date < end_date)
    
    expenses = query.order_by(Expense.expense_date.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    categories = db.session.query(Expense.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    # Calculate monthly total
    monthly_total = query.with_entities(db.func.sum(Expense.amount)).scalar() or 0

    
    # Financial Year Calculation (April 1st to March 31st)
    selected_year, selected_month = map(int, month.split('-'))
    if selected_month >= 4:
        fy_start_year = selected_year
    else:
        fy_start_year = selected_year - 1

    fy_start = datetime(fy_start_year, 4, 1)
    fy_end = datetime(fy_start_year + 1, 3, 31, 23, 59, 59)

    # Apply category filter to financial year query if needed
    fy_query = Expense.query.filter(Expense.expense_date >= fy_start, Expense.expense_date < fy_end)
    if category:
        fy_query = fy_query.filter(Expense.category == category)

    financial_year_total = fy_query.with_entities(db.func.sum(Expense.amount)).scalar() or 0
    
    filtered_month_display = datetime(int(year), int(month_num), 1).strftime('%B %Y')
    
    return render_template('expenses.html', expenses=expenses, categories=categories, monthly_total=monthly_total,yearly=financial_year_total,fy_start=fy_start,fy_end=fy_end,month=filtered_month_display)

@app.route('/expenses/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        expense = Expense(
            category=request.form['category'],
            description=request.form.get('description'),
            amount=float(request.form['amount']),
            expense_date=datetime.strptime(request.form['expense_date'], '%Y-%m-%d')
        )
        db.session.add(expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('expenses'))
    
    return render_template('add_expense.html')

@app.route('/expenses/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    db.session.delete(expense)
    db.session.commit()
    flash('Expenses deleted successfully!', 'success')
    return redirect(url_for('expenses'))

@app.route('/expenses/edit/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    
    if request.method == 'POST':
        expense.category=request.form['category']
        expense.description=request.form.get('description')
        expense.amount=float(request.form['amount'])
        expense.expense_date=datetime.strptime(request.form['expense_date'], '%Y-%m-%d')
        try:
            db.session.commit()
            flash('Expense updated successfully!', 'success')
            return redirect(url_for('expenses'))
        except Exception as e:
            db.session.rollback()
            flash('Expense Update Failed!', 'error')
    
    return render_template('edit_expense.html', expense=expense)



# Sales Routes
@app.route('/sales')
@login_required
def sales():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    status = request.args.get('status', '', type=str)
    
    query = Invoice.query.order_by(Invoice.created_at.desc())
    
    if search:
        query = query.filter(Invoice.bill_no.contains(search))
    if status:
        query = query.filter(Invoice.payment_status==status)
    
    
    sales = query.paginate(page=page, per_page=10, error_out=False)
    
    return render_template('sales.html', sales=sales, search=search,status=status)

@app.route('/sales/<int:invoice_id>')
@login_required
def sales_detail(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    invoice = Invoice.query.get(invoice_id)
    total_paid = sum([p.amount for p in invoice.payments])
    return jsonify({
        'bill_no': invoice.bill_no,
        'customer_name': invoice.customer.name if invoice.customer else 'Walk-in Customer',
        'customer_mobile': invoice.customer.mobile_number if invoice.customer else '',
        'total_products': len(invoice.items),
        'date': invoice.created_at.strftime('%Y-%m-%d %H:%M'),
        'payment_status': invoice.payment_status,
        'final_amount': invoice.final_amount,
        'paid':total_paid,
        'items': [{
            'product_name': item.product.name,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'total_price': item.total_price
        } for item in invoice.items],
        'Payment': [{
            'date':item.payment_date.strftime('%Y-%m-%d %H:%M'),
            'method':item.payment_method,
            'paid':item.amount,
            'status':item.status
        } for item in invoice.payments]
    })


# Purchase Routes
@app.route('/purchases')
@login_required
def purchases():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    status = request.args.get('status', '', type=str)
    
    query = Purchase.query.order_by(Purchase.created_at.desc())
    
    if search:
        query = query.filter(Purchase.bill_no.contains(search))
    if status:
        query = query.filter(Purchase.payment_status==status)
    
    purchases = query.paginate(page=page, per_page=10, error_out=False)
    
    return render_template('purchases.html', purchases=purchases, search=search)

@app.route('/purchases/add', methods=['GET', 'POST'])
@login_required
def add_purchase():
    if request.method == 'POST':
        data = request.get_json()
        
        # Generate bill number
        last_purchase = Purchase.query.order_by(Purchase.id.desc()).first()
        bill_no = f"PUR-{(last_purchase.id + 1) if last_purchase else 1:03d}"
        
        # Create purchase
        purchase = Purchase(
            bill_no=bill_no,
            po_bill_no=data.get('po_bill_no'),
            purchase_date=datetime.strptime(data['purchase_date'], '%Y-%m-%d').date(),
            vendor_id=data['vendor_id'],
            total_amount=data['total_amount'],
            discount=data.get('discount', 0),
            cgst=data.get('cgst', 0),
            sgst=data.get('sgst', 0),
            final_amount=data['final_amount'],
            payment_status=data.get('payment_status', 'unpaid')
        )
        
        db.session.add(purchase)
        db.session.flush()  # Get the purchase ID
        
        # Add purchase items
        for item in data['items']:
            purchase_item = PurchaseItem(
                purchase_id=purchase.id,
                product_id=item['product_id'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                total_price=item['total_price']
            )
            db.session.add(purchase_item)
            
            # Update stock
            product = Product.query.get(item['product_id'])
            product.stock_quantity += item['quantity']
        
        # Add vendor payment if payment is made
        if data.get('payment_amount') and float(data['payment_amount']) > 0:
            vendor_payment = VendorPayment(
                purchase_id=purchase.id,
                amount=float(data['payment_amount']),
                payment_method=data.get('payment_method', 'cash'),
                description=f"Payment for purchase {bill_no}"
            )
            db.session.add(vendor_payment)
        
        db.session.commit()
        
        return jsonify({'success': True, 'bill_no': bill_no, 'purchase_id': purchase.id})
    
    vendors = Vendor.query.all()
    products = Product.query.all()

    product_dicts = [
        {
            'id': p.id,
            'name': p.name,
            'category': p.category or '',
            'brand': p.brand or '',
            'selling_price': p.selling_price,
            'cost_price': p.cost_price,
            'gst_rate': p.gst_rate,
            'stock_quantity': p.stock_quantity,
        }
        for p in products
    ]

    return render_template('add_purchase.html', vendors=vendors, products=products, products_json=product_dicts)

@app.route('/purchases/<int:purchase_id>')
@login_required
def purchase_detail(purchase_id):
    purchase = Purchase.query.get_or_404(purchase_id)
    total_paid = sum([p.amount for p in purchase.payments])
    return jsonify({
        'bill_no': purchase.bill_no,
        'vendor_name': purchase.vendor.name if purchase.vendor else 'Unknown Vendor',
        'vendor_mobile': purchase.vendor.mobile_number if purchase.vendor else '',
        'total_products': len(purchase.items),
        'date': purchase.created_at.strftime('%Y-%m-%d %H:%M'),
        'payment_status': purchase.payment_status,
        'final_amount': purchase.final_amount,
        'total_paid':total_paid,
        'items': [{
            'product_name': item.product.name,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'total_price': item.total_price
        } for item in purchase.items],
        'Payment': [{
            'date':item.payment_date.strftime('%Y-%m-%d %H:%M'),
            'method':item.payment_method,
            'paid':item.amount,
            'status':'completed'
        } for item in purchase.payments]
    })

# Payments Routes
@app.route('/payments')
@login_required
def payments():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '', type=str)
    status = request.args.get('status', '', type=str)
    
    # Get all invoice payments with explicit joins
    invoice_payments = db.session.query(
        Payment.id,
        Payment.amount,
        Payment.payment_method,
        Payment.payment_date,
        Payment.status,
        Invoice.bill_no,
        Customer.name.label('party_name'),
        literal('customer').label('category')
    ).select_from(Payment).join(Invoice, Payment.invoice_id == Invoice.id).outerjoin(Customer, Invoice.customer_id == Customer.id).all()
    
    # Get all vendor payments with explicit joins
    vendor_payments = db.session.query(
        VendorPayment.id,
        VendorPayment.amount,
        VendorPayment.payment_method,
        VendorPayment.payment_date,
        Purchase.bill_no,
        literal('completed').label('status'),
        Vendor.name.label('party_name'),
        literal('vendor').label('category')
    ).select_from(VendorPayment).join(Purchase, VendorPayment.purchase_id == Purchase.id).outerjoin(Vendor, Purchase.vendor_id == Vendor.id).all()
    
    # Combine and filter
    all_payments = list(invoice_payments) + list(vendor_payments)
    
    if category:
        all_payments = [p for p in all_payments if p.category == category]
    if status:
        all_payments = [p for p in all_payments if p.status == status]
    
    # Sort by date (newest first)
    all_payments.sort(key=lambda x: x.payment_date, reverse=True)
    
    # Manual pagination
    per_page = 10
    start = (page - 1) * per_page
    end = start + per_page
    paginated_payments = all_payments[start:end]
    
    total_pages = (len(all_payments) + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    return render_template('payments.html', 
                         payments=paginated_payments,
                         page=page,
                         total_pages=total_pages,
                         has_prev=has_prev,
                         has_next=has_next,
                         category=category,
                         status=status)

@app.route('/payments/add', methods=['POST'])
@login_required
def add_payment():
    invoice_id = request.form.get('invoice_id')
    amount = float(request.form['amount'])
    payment_method = request.form['payment_method']

    # Update invoice payment status
    invoice = Invoice.query.get(invoice_id)
    total_paid = sum([p.amount for p in invoice.payments]) + amount
    
    payment = Payment(
        invoice_id=invoice_id,
        amount=amount,
        payment_method=payment_method,
        status='completed'
    )
    
    db.session.add(payment)
    
    if total_paid >= invoice.final_amount:
        invoice.payment_status = 'paid'
    else:
        invoice.payment_status = 'partial'
    
    db.session.commit()
    flash('Payment recorded successfully!', 'success')
    return redirect(url_for('payments'))

@app.route('/vendor-payments/add', methods=['POST'])
@login_required
def add_vendor_payment():
    purchase_id = request.form.get('purchase_id')
    amount = float(request.form['amount'])
    payment_method = request.form['payment_method']

    #update purchase payment status
    purchase = Purchase.query.get(purchase_id)
    total_paid = sum([p.amount for p in purchase.payments]) + amount
    
    vendor_payment = VendorPayment(
        purchase_id=purchase_id,
        amount=amount,
        payment_method=payment_method
    )
    
    db.session.add(vendor_payment)
    db.session.commit()


    if total_paid >= purchase.final_amount:
        purchase.payment_status = 'paid'
    else:
        purchase.payment_status = 'partial'
    
    db.session.commit()
    flash('Vendor payment recorded successfully!', 'success')
    return redirect(url_for('purchases'))

# Customer and Vendor detail views
@app.route('/customers/<int:customer_id>')
@login_required
def customer_detail(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    # Get customer's invoices
    invoices = Invoice.query.filter_by(customer_id=customer_id).order_by(Invoice.created_at.desc()).all()
    
    # Calculate totals
    total_sales = sum([inv.final_amount for inv in invoices])
    total_paid = sum([sum([p.amount for p in inv.payments]) for inv in invoices])
    total_pending = total_sales - total_paid
    
    return render_template('customer_detail.html', 
                         customer=customer,
                         invoices=invoices,
                         total_sales=total_sales,
                         total_paid=total_paid,
                         total_pending=total_pending)

@app.route('/vendors/<int:vendor_id>')
@login_required
def vendor_detail(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    
    # Get vendor's purchases
    purchases = Purchase.query.filter_by(vendor_id=vendor_id).order_by(Purchase.created_at.desc()).all()
    
    # Get vendor's products
    products = Product.query.filter_by(vendor_id=vendor_id).all()
    
    # Calculate totals
    total_purchases = sum([purch.final_amount for purch in purchases])
    total_paid = sum([sum([p.amount for p in purchase.payments]) for purchase in purchases])
    total_pending = total_purchases - total_paid
    
    return render_template('vendor_detail.html', 
                         vendor=vendor,
                         purchases=purchases,
                         products=products,
                         total_purchases=total_purchases,
                         total_paid=total_paid,
                         total_pending=total_pending)

# Report Routes
@app.route('/reports/sales')
@login_required
def sales_report():
    # Get filter parameters
    page = request.args.get('page', 1, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    customer_id = request.args.get('customer_id')
    
    # Base query
    query = Invoice.query
    
    # Apply filters
    if start_date:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(Invoice.created_at >= start_date_obj)
    if end_date:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(Invoice.created_at <= end_date_obj)
    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)
    
    # Get invoices
    invoices = query.order_by(Invoice.created_at.desc()).all()
    
    # Calculate summary
    total_sales = sum([inv.final_amount for inv in invoices])
    total_transactions = len(invoices)
    total_customers = len(set([inv.customer_id for inv in invoices if inv.customer_id]))
    avg_order_value = total_sales / total_transactions if total_transactions > 0 else 0
    
    summary = {
        'total_sales': total_sales,
        'total_transactions': total_transactions,
        'total_customers': total_customers,
        'avg_order_value': avg_order_value
    }
    
    # Get all customers for filter dropdown
    customers = Customer.query.all()
    
    # Prepare chart data - Daily sales for last 30 days or filtered period
    from datetime import timedelta
    
    if start_date and end_date:
        chart_start = datetime.strptime(start_date, '%Y-%m-%d')
        chart_end = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        chart_end = datetime.now()
        chart_start = chart_end - timedelta(days=30)
    
    # Generate daily sales data
    daily_sales = {}
    current_date = chart_start
    while current_date <= chart_end:
        daily_sales[current_date.strftime('%Y-%m-%d')] = 0
        current_date += timedelta(days=1)
    
    # Fill with actual sales data
    for invoice in invoices:
        date_key = invoice.created_at.strftime('%Y-%m-%d')
        if date_key in daily_sales:
            daily_sales[date_key] += invoice.final_amount
    
    chart_data = {
        'labels': list(daily_sales.keys()),
        'sales': list(daily_sales.values())
    }
    
    # Top customers data
    customer_sales = {}
    for invoice in invoices:
        if invoice.customer_id:
            customer_name = invoice.customer.name
            if customer_name not in customer_sales:
                customer_sales[customer_name] = 0
            customer_sales[customer_name] += invoice.final_amount
    
    # Sort and get top 5 customers
    sorted_customers = sorted(customer_sales.items(), key=lambda x: x[1], reverse=True)[:5]
    
    top_customers = {
        'names': [item[0] for item in sorted_customers],
        'amounts': [item[1] for item in sorted_customers]
    }
    # Manual pagination
    per_page = 10
    start = (page - 1) * per_page
    end = start + per_page
    paginated_invoices = invoices[start:end]
    
    total_pages = (len(invoices) + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    
    return render_template('sales_report.html', 
                         invoices=paginated_invoices,
                         page=page,
                         total_pages=total_pages,
                         has_prev=has_prev,
                         has_next=has_next,
                         summary=summary,
                         customers=customers,
                         chart_data=chart_data,
                         top_customers=top_customers,
                         start_date=start_date,end_date=end_date,customer_id=customer_id)

@app.route('/reports/payment')
@login_required
def payment_report():
    # Get filter parameters
    page = request.args.get('page', 1, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    payment_type = request.args.get('payment_type')
    
    # Get invoice payments
    invoice_payments_query = db.session.query(
        Payment.id,
        Payment.amount,
        Payment.payment_method,
        Payment.payment_date,
        Payment.status,
        Invoice.bill_no,
        Customer.name.label('party_name'),
        literal('customer').label('category')
    ).select_from(Payment).join(Invoice, Payment.invoice_id == Invoice.id).outerjoin(Customer, Invoice.customer_id == Customer.id)
    
    # Get vendor payments
    vendor_payments_query = db.session.query(
        VendorPayment.id,
        VendorPayment.amount,
        VendorPayment.payment_method,
        VendorPayment.payment_date,
        Purchase.bill_no,
        literal('completed').label('status'),
        Vendor.name.label('party_name'),
        literal('vendor').label('category')
    ).select_from(VendorPayment).join(Purchase, VendorPayment.purchase_id == Purchase.id).outerjoin(Vendor, Purchase.vendor_id==Vendor.id)
    
    # Apply date filters
    if start_date:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        invoice_payments_query = invoice_payments_query.filter(Payment.payment_date >= start_date_obj)
        vendor_payments_query = vendor_payments_query.filter(VendorPayment.payment_date >= start_date_obj)
    if end_date:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        invoice_payments_query = invoice_payments_query.filter(Payment.payment_date <= end_date_obj)
        vendor_payments_query = vendor_payments_query.filter(VendorPayment.payment_date <= end_date_obj)
    
    # Get payments
    invoice_payments = invoice_payments_query.all()
    vendor_payments = vendor_payments_query.all()
    
    # Combine payments
    all_payments = list(invoice_payments) + list(vendor_payments)
    
    # Apply payment type filter
    if payment_type:
        all_payments = [p for p in all_payments if p.category == payment_type]
    
    # Sort by date
    all_payments.sort(key=lambda x: x.payment_date, reverse=True)
    
    # Calculate summary
    total_received = sum([p.amount for p in all_payments if p.category == 'customer'])
    total_paid = sum([p.amount for p in all_payments if p.category == 'vendor'])
    total_transactions = len(all_payments)
    
    summary = {
        'total_received': total_received,
        'total_paid': total_paid,
        'total_transactions': total_transactions
    }
    
    # Generate chart data for payment methods
    payment_method_counts = {}
    for payment in all_payments:
        method = payment.payment_method
        if method not in payment_method_counts:
            payment_method_counts[method] = 0
        payment_method_counts[method] += payment.amount
    
    payment_methods = {
        'labels': list(payment_method_counts.keys()),
        'data': list(payment_method_counts.values())
    }
    
    # Generate monthly trend data
    from datetime import timedelta
    from collections import defaultdict
    
    # Group payments by month
    monthly_received = defaultdict(float)
    monthly_paid = defaultdict(float)
    
    for payment in all_payments:
        month_key = payment.payment_date.strftime('%Y-%m')
        if payment.category == 'customer':
            monthly_received[month_key] += payment.amount
        else:
            monthly_paid[month_key] += payment.amount
    
    # Get all months in range
    if start_date and end_date:
        start_month = datetime.strptime(start_date, '%Y-%m-%d')
        end_month = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end_month = datetime.now()
        start_month = end_month - timedelta(days=365)  # Last 12 months
    
    # Generate month labels
    month_labels = []
    current_month = start_month.replace(day=1)
    while current_month <= end_month:
        month_key = current_month.strftime('%Y-%m')
        month_labels.append(month_key)
        # Move to next month
        if current_month.month == 12:
            current_month = current_month.replace(year=current_month.year + 1, month=1)
        else:
            current_month = current_month.replace(month=current_month.month + 1)
    
    monthly_trend = {
        'labels': month_labels,
        'received': [monthly_received[month] for month in month_labels],
        'paid': [monthly_paid[month] for month in month_labels]
    }

    # Manual pagination
    per_page = 10
    start = (page - 1) * per_page
    end = start + per_page
    paginated_payments = all_payments[start:end]
    
    total_pages = (len(all_payments) + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    return render_template('payment_report.html',
                         payments=paginated_payments,
                         has_next=has_next,
                         has_prev=has_prev,
                         page=page,
                         total_pages=total_pages,
                         summary=summary,
                         payment_methods=payment_methods,
                         monthly_trend=monthly_trend,
                         start_date=start_date,end_date=end_date,payment_type=payment_type)



@app.route('/reports/gst')
@login_required
def gst_report():
    # Get filter parameters
    page = request.args.get('page', 1, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Base query
    query = Invoice.query
    
    # Apply filters
    if start_date:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(Invoice.created_at >= start_date_obj)
    if end_date:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(Invoice.created_at <= end_date_obj)
    
    # Get invoices
    invoices = query.order_by(Invoice.created_at.desc()).all()
    
    # Calculate GST summary
    total_cgst = sum([inv.cgst for inv in invoices])
    total_sgst = sum([inv.sgst for inv in invoices])
    total_igst = sum([inv.igst for inv in invoices])
    total_gst = total_cgst + total_sgst + total_igst
    
    gst_summary = {
        'total_cgst': total_cgst,
        'total_sgst': total_sgst,
        'total_igst': total_igst,
        'total_gst': total_gst
    }
    
    # Calculate GST by rate (simplified)
    gst_by_rate = [
        {'rate': 5, 'transaction_count': 0, 'total_gst': 0, 'taxable_amount': 0},
        {'rate': 12, 'transaction_count': 0, 'total_gst': 0, 'taxable_amount': 0},
        {'rate': 18, 'transaction_count': 0, 'total_gst': 0, 'taxable_amount': 0},
        {'rate': 28, 'transaction_count': 0, 'total_gst': 0, 'taxable_amount': 0}
    ]
    
    # Generate monthly GST trend data
    from datetime import timedelta
    from collections import defaultdict
    
    # Group GST by month
    monthly_cgst = defaultdict(float)
    monthly_sgst = defaultdict(float)
    monthly_igst = defaultdict(float)
    
    for invoice in invoices:
        month_key = invoice.created_at.strftime('%Y-%m')
        monthly_cgst[month_key] += invoice.cgst
        monthly_sgst[month_key] += invoice.sgst
        monthly_igst[month_key] += invoice.igst
    
    # Get month range
    if start_date and end_date:
        start_month = datetime.strptime(start_date, '%Y-%m-%d')
        end_month = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end_month = datetime.now()
        start_month = end_month - timedelta(days=365)  # Last 12 months
    
    # Generate month labels
    month_labels = []
    current_month = start_month.replace(day=1)
    while current_month <= end_month:
        month_key = current_month.strftime('%Y-%m')
        month_labels.append(month_key)
        # Move to next month
        if current_month.month == 12:
            current_month = current_month.replace(year=current_month.year + 1, month=1)
        else:
            current_month = current_month.replace(month=current_month.month + 1)
    
    monthly_gst = {
        'labels': month_labels,
        'cgst': [monthly_cgst[month] for month in month_labels],
        'sgst': [monthly_sgst[month] for month in month_labels],
        'igst': [monthly_igst[month] for month in month_labels]
    }
    
    # If export is requested, save CSV to server
    if request.args.get('export') == 'csv':
        filename = f"gst_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join("exports", filename)  # Ensure 'exports' folder exists
        os.makedirs("exports", exist_ok=True)

        with open(filepath, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Invoice ID', 'Date', 'CGST', 'SGST', 'IGST', 'Total GST'])

            for inv in invoices:
                total_gst = inv.cgst + inv.sgst + inv.igst
                writer.writerow([
                    inv.id,
                    inv.created_at.strftime('%Y-%m-%d'),
                    inv.cgst,
                    inv.sgst,
                    inv.igst,
                    total_gst
                ])

        flash(f"CSV report saved to server at: {filepath}")
    

    # Manual pagination
    per_page = 10
    start = (page - 1) * per_page
    end = start + per_page
    paginated_invoices = invoices[start:end]
    
    total_pages = (len(invoices) + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    
    return render_template('gst_report.html',
                        page=page,  
                        has_next=has_next,
                         has_prev=has_prev,
                         total_pages=total_pages,
                         start_date=start_date,end_date=end_date,
                         invoices=paginated_invoices,
                         gst_summary=gst_summary,
                         gst_by_rate=gst_by_rate,
                         monthly_gst=monthly_gst)


# Admin Routes
@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role not in ['admin', 'owner']:
        flash('Access denied. Admin/Owner privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    
    # Calculate user statistics
    user_stats = {
        'total_users': len(users),
        'total_admins': len([u for u in users if u.role == 'admin']),
        'total_employees': len([u for u in users if u.role == 'employee']),
        'total_owners': len([u for u in users if u.role == 'owner']),
        'active_users': len([u for u in users if u.is_active])
    }
    
    return render_template('admin_users.html', users=users, user_stats=user_stats)

@app.route('/admin/passwords')
@login_required
def manage_passwords():
    if current_user.role not in ['admin', 'owner']:
        flash('Access denied. Admin/Owner privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    return render_template('manage_passwords.html', users=users)

@app.route('/admin/users/add', methods=['POST'])
@login_required
def add_user():
    if current_user.role not in ['admin', 'owner']:
        flash('Access denied. Admin/Owner privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User(
        mobile_number=request.form['mobile_number'],
        name=request.form['name'],
        role=request.form['role']
    )
    user.set_password(request.form['password'])
    
    try:
        db.session.add(user)
        db.session.commit()
        flash('User added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding user. Mobile number might already exist.', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role not in ['admin', 'owner']:
        flash('Access denied. Admin/Owner privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    if user_id == current_user.id:
        flash('Cannot delete your own account.', 'error')
        return redirect(url_for('admin_users'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/reset-password/<int:user_id>', methods=['POST'])
@login_required
def reset_user_password_by_id(user_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    new_password = request.form['new_password']
    user.set_password(new_password)
    db.session.commit()
    flash(f'Password reset successfully for {user.name}!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form.get('confirm_password', '')
    
    # Validate current password
    if not current_user.check_password(current_password):
        flash('Current password is incorrect.', 'error')
        return redirect(request.referrer or url_for('manage_passwords'))
    
    # Validate new password
    if len(new_password) < 6:
        flash('New password must be at least 6 characters long.', 'error')
        return redirect(request.referrer or url_for('manage_passwords'))
    
    # Validate password confirmation if provided
    if confirm_password and new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(request.referrer or url_for('manage_passwords'))
    
    current_user.set_password(new_password)
    db.session.commit()
    flash('Password changed successfully!', 'success')
    return redirect(request.referrer or url_for('manage_passwords'))

@app.route('/admin/reset-password', methods=['POST'])
@login_required
def reset_user_password():
    if current_user.role not in ['admin', 'owner']:
        flash('Access denied. Admin/Owner privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    user_id = request.form['user_id']
    new_password = request.form['new_password']
    confirm_password = request.form.get('confirm_password', '')
    
    # Validate inputs
    if not user_id or not new_password:
        flash('User and password are required.', 'error')
        return redirect(url_for('manage_passwords'))
    
    # Validate password length
    if len(new_password) < 6:
        flash('Password must be at least 6 characters long.', 'error')
        return redirect(url_for('manage_passwords'))
    
    # Validate password confirmation if provided
    if confirm_password and new_password != confirm_password:
        flash('Passwords do not match.', 'error')
        return redirect(url_for('manage_passwords'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent self-reset
    if user.id == current_user.id:
        flash('Cannot reset your own password. Use change password instead.', 'error')
        return redirect(url_for('manage_passwords'))
    
    user.set_password(new_password)
    db.session.commit()
    flash(f'Password reset successfully for {user.name}!', 'success')
    return redirect(url_for('manage_passwords'))

@app.route('/admin/settings')
@login_required
def admin_settings():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    return render_template('admin_settings.html')

def create_default_admin():
    """Create default admin user if none exists"""
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(
            mobile_number='9999999999',
            role='admin',
            name='Administrator'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Default admin created - Mobile: 9999999999, Password: admin123")

if __name__ == '__main__':
    #with app.app_context():
        #db.create_all()
        #create_default_admin()
    app.run(debug=True) 
    #webview.create_window('Electrical Billing App', app,min_size=(700,500),frameless=False,resizable=True)
    #webview.start(ssl=True, http_server=True,debug=False)