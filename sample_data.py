from app import app, db, User, Product, Customer, Vendor, Expense
from datetime import datetime, timedelta
import random

def create_sample_data():
    """Create sample data for testing the application"""
    with app.app_context():
        print("🔄 Creating sample data...")
        
        # Create sample users
        users_data = [
            {"mobile_number": "9876543210", "password": "emp123", "role": "employee", "name": "Rajesh Kumar"},
            {"mobile_number": "9876543211", "password": "owner123", "role": "owner", "name": "Suresh Patel"},
        ]
        
        for user_data in users_data:
            if not User.query.filter_by(mobile_number=user_data["mobile_number"]).first():
                user = User(
                    mobile_number=user_data["mobile_number"],
                    role=user_data["role"],
                    name=user_data["name"]
                )
                user.set_password(user_data["password"])
                db.session.add(user)
        
        # Create sample vendors
        vendors_data = [
            {
                "name": "Philips Electronics Ltd",
                "mobile_number": "9123456789",
                "gst_number": "29ABCDE1234F1Z5",
                "address": "Industrial Area, Phase-1, Chandigarh",
                "products_supplied": "LED Bulbs, Tube Lights, Street Lights"
            },
            {
                "name": "Havells India Ltd",
                "mobile_number": "9123456790",
                "gst_number": "29FGHIJ5678K2M6",
                "address": "Sector 59, Noida, Uttar Pradesh",
                "products_supplied": "Switches, Sockets, Ceiling Fans, Motors"
            },
            {
                "name": "Polycab Wires Pvt Ltd",
                "mobile_number": "9123456791",
                "gst_number": "29KLMNO9012P3Q7",
                "address": "Halol, Gujarat",
                "products_supplied": "Electrical Cables, Wires, MCBs"
            }
        ]
        
        for vendor_data in vendors_data:
            if not Vendor.query.filter_by(mobile_number=vendor_data["mobile_number"]).first():
                vendor = Vendor(**vendor_data)
                db.session.add(vendor)
        
        db.session.commit()
        
        # Get vendors for product assignment
        vendors = Vendor.query.all()
        
        # Create sample products
        products_data = [
            # Lighting Products
            {"name": "LED Bulb 9W", "category": "Lighting", "brand": "Philips", "mrp_price": 150.00, "cost_price": 100.00, "selling_price": 130.00, "gst_rate": 18, "stock_quantity": 50},
            {"name": "LED Bulb 12W", "category": "Lighting", "brand": "Philips", "mrp_price": 200.00, "cost_price": 140.00, "selling_price": 170.00, "gst_rate": 18, "stock_quantity": 30},
            {"name": "LED Tube Light 18W", "category": "Lighting", "brand": "Philips", "mrp_price": 350.00, "cost_price": 250.00, "selling_price": 300.00, "gst_rate": 18, "stock_quantity": 25},
            {"name": "LED Panel Light 12W", "category": "Lighting", "brand": "Philips", "mrp_price": 450.00, "cost_price": 320.00, "selling_price": 390.00, "gst_rate": 18, "stock_quantity": 15},
            
            # Switches and Sockets
            {"name": "Modular Switch 1 Way", "category": "Switches", "brand": "Havells", "mrp_price": 85.00, "cost_price": 60.00, "selling_price": 75.00, "gst_rate": 18, "stock_quantity": 100},
            {"name": "Modular Switch 2 Way", "category": "Switches", "brand": "Havells", "mrp_price": 120.00, "cost_price": 85.00, "selling_price": 105.00, "gst_rate": 18, "stock_quantity": 80},
            {"name": "6A Socket", "category": "Sockets", "brand": "Havells", "mrp_price": 95.00, "cost_price": 65.00, "selling_price": 80.00, "gst_rate": 18, "stock_quantity": 60},
            {"name": "16A Socket", "category": "Sockets", "brand": "Havells", "mrp_price": 150.00, "cost_price": 110.00, "selling_price": 135.00, "gst_rate": 18, "stock_quantity": 40},
            
            # Cables and Wires
            {"name": "House Wire 1.5 sq mm", "category": "Cables", "brand": "Polycab", "mrp_price": 45.00, "cost_price": 35.00, "selling_price": 40.00, "gst_rate": 18, "stock_quantity": 200},
            {"name": "House Wire 2.5 sq mm", "category": "Cables", "brand": "Polycab", "mrp_price": 65.00, "cost_price": 50.00, "selling_price": 58.00, "gst_rate": 18, "stock_quantity": 150},
            {"name": "Armoured Cable 4 sq mm", "category": "Cables", "brand": "Polycab", "mrp_price": 120.00, "cost_price": 90.00, "selling_price": 105.00, "gst_rate": 18, "stock_quantity": 80},
            
            # Fans and Motors
            {"name": "Ceiling Fan 1200mm", "category": "Fans", "brand": "Havells", "mrp_price": 2500.00, "cost_price": 1800.00, "selling_price": 2200.00, "gst_rate": 12, "stock_quantity": 20},
            {"name": "Exhaust Fan 6 inch", "category": "Fans", "brand": "Havells", "mrp_price": 800.00, "cost_price": 580.00, "selling_price": 720.00, "gst_rate": 18, "stock_quantity": 25},
            {"name": "Water Motor 0.5 HP", "category": "Motors", "brand": "Havells", "mrp_price": 3500.00, "cost_price": 2500.00, "selling_price": 3200.00, "gst_rate": 18, "stock_quantity": 10},
            
            # MCBs and Protection
            {"name": "MCB 16A Single Pole", "category": "MCB", "brand": "Polycab", "mrp_price": 180.00, "cost_price": 130.00, "selling_price": 160.00, "gst_rate": 18, "stock_quantity": 50},
            {"name": "MCB 32A Double Pole", "category": "MCB", "brand": "Polycab", "mrp_price": 350.00, "cost_price": 250.00, "selling_price": 310.00, "gst_rate": 18, "stock_quantity": 30},
            
            # Low stock items for alerts
            {"name": "Emergency Light", "category": "Lighting", "brand": "Philips", "mrp_price": 450.00, "cost_price": 320.00, "selling_price": 400.00, "gst_rate": 18, "stock_quantity": 3},
            {"name": "Extension Board 4 Socket", "category": "Others", "brand": "Havells", "mrp_price": 250.00, "cost_price": 180.00, "selling_price": 220.00, "gst_rate": 18, "stock_quantity": 5},
        ]
        
        for i, product_data in enumerate(products_data):
            if not Product.query.filter_by(name=product_data["name"]).first():
                product = Product(**product_data)
                # Assign vendor based on brand
                if product.brand == "Philips" and vendors:
                    product.vendor_id = vendors[0].id
                elif product.brand == "Havells" and len(vendors) > 1:
                    product.vendor_id = vendors[1].id
                elif product.brand == "Polycab" and len(vendors) > 2:
                    product.vendor_id = vendors[2].id
                db.session.add(product)
        
        # Create sample customers
        customers_data = [
            {
                "name": "Amit Sharma",
                "mobile_number": "9988776655",
                "email": "amit.sharma@email.com",
                "address": "A-123, Sector 15, Noida, UP"
            },
            {
                "name": "Priya Singh",
                "mobile_number": "9988776656",
                "email": "priya.singh@email.com",
                "address": "B-456, Model Town, Delhi"
            },
            {
                "name": "Rahul Gupta",
                "mobile_number": "9988776657",
                "email": "rahul.gupta@email.com",
                "address": "C-789, Lajpat Nagar, Delhi"
            },
            {
                "name": "Sneha Patel",
                "mobile_number": "9988776658",
                "email": None,
                "address": "D-101, Satellite, Ahmedabad, Gujarat"
            },
            {
                "name": "Vikash Kumar",
                "mobile_number": "9988776659",
                "email": "vikash.kumar@email.com",
                "address": "E-202, Boring Road, Patna, Bihar"
            }
        ]
        
        for customer_data in customers_data:
            if not Customer.query.filter_by(mobile_number=customer_data["mobile_number"]).first():
                customer = Customer(**customer_data)
                db.session.add(customer)
        
        # Create sample expenses
        expense_categories = ["Electricity", "Rent", "Commission", "Transportation", "Office Supplies", "Marketing"]
        current_date = datetime.now()
        
        for i in range(20):  # Create 20 sample expenses
            expense_date = current_date - timedelta(days=random.randint(1, 90))
            expense = Expense(
                category=random.choice(expense_categories),
                description=f"Sample expense for {random.choice(expense_categories).lower()}",
                amount=random.uniform(500, 5000),
                expense_date=expense_date
            )
            db.session.add(expense)
        
        db.session.commit()
        print("✅ Sample data created successfully!")
        print("\n📊 Summary:")
        print(f"   • Users: {User.query.count()}")
        print(f"   • Vendors: {Vendor.query.count()}")
        print(f"   • Products: {Product.query.count()}")
        print(f"   • Customers: {Customer.query.count()}")
        print(f"   • Expenses: {Expense.query.count()}")
        print("\n🔑 Login Credentials:")
        print("   Admin: 9999999999 / admin123")
        print("   Employee: 9876543210 / emp123")
        print("   Owner: 9876543211 / owner123")

if __name__ == '__main__':
    create_sample_data() 