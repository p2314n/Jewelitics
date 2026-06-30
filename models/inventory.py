from datetime import datetime
from models import db


class InventoryLog(db.Model):
    __tablename__ = 'inventory_logs'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)  # purchase, sale, return, damage, adjust
    quantity_change = db.Column(db.Integer, nullable=False)  # positive = in, negative = out
    quantity_after = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.String(255), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='inventory_logs')

    def __repr__(self):
        return f'<InventoryLog {self.action} {self.quantity_change}>'
