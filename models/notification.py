from datetime import datetime
from models import db


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, default='')
    link = db.Column(db.String(255), nullable=True)
    type = db.Column(db.String(30), default='system')  # stock, order, system, forecast
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Notification {self.title}>'




class SalesSummary(db.Model):
    __tablename__ = 'sales_summary'

    id = db.Column(db.Integer, primary_key=True)
    sale_date = db.Column(db.Date, nullable=False)
    total_sales = db.Column(db.Float, default=0.0)
    total_profit = db.Column(db.Float, default=0.0)
    total_orders = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<SalesSummary {self.sale_date}>'
