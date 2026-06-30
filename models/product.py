from datetime import datetime
from models import db


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship('Product', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    material = db.Column(db.String(50), default='Gold')  # Gold, Silver, Platinum, Diamond
    purity = db.Column(db.String(20), default='22K')  # 24K, 22K, 18K, 14K, 925
    weight = db.Column(db.Float, default=0.0)  # in grams
    purchase_price = db.Column(db.Float, default=0.0)
    selling_price = db.Column(db.Float, default=0.0)
    quantity = db.Column(db.Integer, default=0)
    min_stock = db.Column(db.Integer, default=5)
    image = db.Column(db.String(255), default='')
    description = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default='active')  # active, inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    inventory_logs = db.relationship('InventoryLog', backref='product', lazy=True)

    @property
    def profit_margin(self):
        if self.selling_price and self.purchase_price:
            return self.selling_price - self.purchase_price
        return 0

    @property
    def is_low_stock(self):
        return self.quantity <= self.min_stock and self.quantity > 0

    @property
    def is_out_of_stock(self):
        return self.quantity == 0

    def __repr__(self):
        return f'<Product {self.name}>'
