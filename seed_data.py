"""
Seed data generator — creates demo data for testing and ML training.
Run: python seed_data.py
"""
from app import create_app
from models import db
from models.user import User
from models.product import Category, Product
from models.supplier import Supplier
from models.notification import SalesSummary
from datetime import datetime, timedelta
import random

app = create_app()

CATEGORIES = [
    'Ring', 'Necklace', 'Pendant', 'Bracelet', 'Chain',
    'Bangles', 'Earrings', 'Mangalsutra',
    'Diamond Jewelry', 'Gold Jewelry', 'Silver Jewelry',
    'Bridal Collection', 'Men Collection', 'Kids Collection'
]

PRODUCTS = [
    ('Gold Ring Classic', 'Ring', 'Gold', '22K', 8.5, 35000, 42000, 'products/demo_gold_ring.png'),
    ('Diamond Solitaire Ring', 'Ring', 'Gold', '18K', 5.2, 85000, 110000, 'products/demo_diamond_ring.png'),
    ('Silver Toe Ring Set', 'Ring', 'Silver', '925', 3.0, 1200, 1800, 'products/demo_silver_toe_ring.png'),
    ('Pearl Necklace', 'Necklace', 'Gold', '22K', 25.0, 95000, 120000, 'products/demo_pearl_necklace.png'),
    ('Gold Chain 22K', 'Chain', 'Gold', '22K', 15.0, 75000, 90000, 'products/demo_gold_chain.png'),
    ('Diamond Pendant', 'Pendant', 'Gold', '18K', 4.0, 45000, 58000, 'products/demo_diamond_pendant.png'),
    ('Gold Bangles Set', 'Bangles', 'Gold', '22K', 40.0, 180000, 220000, 'products/demo_gold_bangles.png'),
    ('Kundan Earrings', 'Earrings', 'Gold', '22K', 12.0, 52000, 65000, 'products/demo_kundan_earrings.png'),
    ('Mangalsutra Traditional', 'Mangalsutra', 'Gold', '22K', 18.0, 72000, 88000, 'products/demo_mangalsutra.png'),
    ('Silver Bracelet', 'Bracelet', 'Silver', '925', 20.0, 4000, 6500, 'products/demo_silver_bracelet.png'),
    ('Diamond Necklace Set', 'Diamond Jewelry', 'Gold', '18K', 35.0, 250000, 320000, 'products/demo_diamond_necklace.png'),
    ('Gold Coin 10g', 'Gold Jewelry', 'Gold', '24K', 10.0, 62000, 65000, 'products/demo_gold_coin.png'),
    ('Silver Anklet Pair', 'Silver Jewelry', 'Silver', '925', 30.0, 5500, 8000, 'products/demo_silver_anklet.png'),
    ('Bridal Choker Set', 'Bridal Collection', 'Gold', '22K', 80.0, 350000, 420000, 'products/demo_bridal_choker.png'),
    ('Men Gold Bracelet', 'Men Collection', 'Gold', '22K', 25.0, 110000, 135000, 'products/demo_men_bracelet.png'),
    ('Kids Gold Chain', 'Kids Collection', 'Gold', '22K', 5.0, 25000, 32000, 'products/demo_kids_chain.png'),
    ('Platinum Ring', 'Ring', 'Platinum', '950', 6.0, 65000, 82000, 'products/demo_platinum_ring.png'),
    ('Temple Necklace', 'Necklace', 'Gold', '22K', 45.0, 195000, 240000, 'products/demo_pearl_necklace.png'),
    ('Emerald Pendant', 'Pendant', 'Gold', '18K', 3.5, 35000, 48000, 'products/demo_diamond_pendant.png'),
    ('Gold Hoop Earrings', 'Earrings', 'Gold', '18K', 6.0, 28000, 36000, 'products/demo_kundan_earrings.png'),
]

SUPPLIERS = [
    ('Rajesh Gold Pvt Ltd', '9876543210', 'rajesh@gold.com', 'Mumbai', 'Maharashtra'),
    ('Diamond House India', '9876543211', 'info@diamondhouse.in', 'Surat', 'Gujarat'),
    ('Silver Craft Co', '9876543212', 'silver@craft.com', 'Jaipur', 'Rajasthan'),
    ('Tanishq Wholesale', '9876543213', 'wholesale@tanishq.com', 'Bangalore', 'Karnataka'),
]


def seed():
    with app.app_context():
        # Clear old data
        db.drop_all()
        db.create_all()
        print("✅ Tables created")

        # Create users
        admin = User(username='admin', email='admin@jewelitics.com',
                     first_name='Admin', last_name='User', role='admin', is_verified=True)
        admin.set_password('admin123')

        staff = User(username='staff', email='staff@jewelitics.com',
                     first_name='Staff', last_name='User', role='staff', is_verified=True)
        staff.set_password('staff123')

        customer = User(username='customer', email='customer@jewelitics.com',
                        first_name='Priya', last_name='Sharma', role='customer',
                        phone='9876543200', is_verified=True)
        customer.set_password('customer123')

        db.session.add_all([admin, staff, customer])
        db.session.flush()
        print("✅ Users created (admin/admin123, staff/staff123, customer/customer123)")

        # Create categories
        cat_map = {}
        for name in CATEGORIES:
            cat = Category(name=name, description=f'{name} collection')
            db.session.add(cat)
            db.session.flush()
            cat_map[name] = cat.id
        print(f"✅ {len(CATEGORIES)} categories created")

        # Create products with demo images
        for i, (name, cat, mat, pur, wt, pp, sp, img) in enumerate(PRODUCTS):
            product = Product(
                name=name,
                sku=f"JWL-{1000 + i:04d}",
                category_id=cat_map.get(cat),
                material=mat,
                purity=pur,
                weight=wt,
                purchase_price=pp,
                selling_price=sp,
                quantity=random.randint(3, 50),
                min_stock=5,
                description=f"Beautiful {name} made with {pur} {mat}.",
                image=img,
            )
            db.session.add(product)
        print(f"✅ {len(PRODUCTS)} products created with demo images")

        # Create suppliers
        for name, phone, email, city, state in SUPPLIERS:
            db.session.add(Supplier(
                name=name, phone=phone, email=email,
                address=f'{city} Main Road', city=city, state=state))
        print(f"✅ {len(SUPPLIERS)} suppliers created")

        # Create sales history (last 90 days) for ML training
        for i in range(90):
            day = datetime.utcnow().date() - timedelta(days=i)
            # Simulate varying sales
            base = random.uniform(15000, 85000)
            # Weekend boost
            if day.weekday() >= 5:
                base *= 1.4
            db.session.add(SalesSummary(
                sale_date=day,
                total_sales=round(base, 2),
                total_profit=round(base * 0.22, 2),
                total_orders=random.randint(1, 8)
            ))
        print("✅ 90 days of sales history created")

        db.session.commit()
        print("\n🎉 Seed data complete!")
        print("Login credentials:")
        print("  Admin: admin / admin123")
        print("  Staff: staff / staff123")
        print("  Customer: customer / customer123")


if __name__ == '__main__':
    seed()
