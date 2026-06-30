from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import all models so they register with SQLAlchemy
from models.user import User
from models.product import Category, Product
from models.inventory import InventoryLog
from models.supplier import Supplier, PurchaseOrder
from models.order import Order, OrderItem, CartItem
from models.notification import Notification, SalesSummary
