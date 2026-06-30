from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import db
from models.product import Product, Category
from models.order import Order, OrderItem
from models.supplier import Supplier
from models.user import User
from models.notification import SalesSummary
from sqlalchemy import func
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    # If customer, redirect to shop
    if current_user.role == 'customer':
        return redirect(url_for('orders.shop'))

    # --- Stat cards ---
    total_products = Product.query.count()
    total_categories = Category.query.count()
    total_customers = User.query.filter_by(role='customer').count()
    total_suppliers = Supplier.query.count()

    # Inventory value
    inventory_value = db.session.query(
        func.sum(Product.selling_price * Product.quantity)
    ).scalar() or 0

    # Orders
    pending_orders = Order.query.filter_by(status='pending').count()
    completed_orders = Order.query.filter_by(status='delivered').count()
    cancelled_orders = Order.query.filter_by(status='cancelled').count()

    # Sales - today / month / year
    today = datetime.utcnow().date()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    today_sales = db.session.query(func.sum(Order.total_amount)).filter(
        func.date(Order.created_at) == today,
        Order.payment_status == 'paid'
    ).scalar() or 0

    monthly_sales = db.session.query(func.sum(Order.total_amount)).filter(
        func.date(Order.created_at) >= month_start,
        Order.payment_status == 'paid'
    ).scalar() or 0

    yearly_sales = db.session.query(func.sum(Order.total_amount)).filter(
        func.date(Order.created_at) >= year_start,
        Order.payment_status == 'paid'
    ).scalar() or 0

    # Stock alerts
    low_stock = Product.query.filter(
        Product.quantity <= Product.min_stock,
        Product.quantity > 0
    ).count()
    out_of_stock = Product.query.filter_by(quantity=0).count()

    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()

    # Chart data - daily sales for last 7 days
    chart_labels = []
    chart_sales = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        chart_labels.append(day.strftime('%b %d'))
        day_total = db.session.query(func.sum(Order.total_amount)).filter(
            func.date(Order.created_at) == day,
            Order.payment_status == 'paid'
        ).scalar() or 0
        chart_sales.append(float(day_total))

    # Category distribution
    cat_labels = []
    cat_counts = []
    categories = db.session.query(
        Category.name, func.count(Product.id)
    ).join(Product, isouter=True).group_by(Category.name).all()
    for name, count in categories:
        cat_labels.append(name)
        cat_counts.append(count)



    return render_template('dashboard/index.html',
        total_products=total_products,
        total_categories=total_categories,
        total_customers=total_customers,
        total_suppliers=total_suppliers,
        inventory_value=inventory_value,
        today_sales=today_sales,
        monthly_sales=monthly_sales,
        yearly_sales=yearly_sales,
        pending_orders=pending_orders,
        completed_orders=completed_orders,
        cancelled_orders=cancelled_orders,
        low_stock=low_stock,
        out_of_stock=out_of_stock,
        recent_orders=recent_orders,
        chart_labels=chart_labels,
        chart_sales=chart_sales,
        cat_labels=cat_labels,
        cat_counts=cat_counts,
    )


@dashboard_bp.route('/notifications/clear')
@login_required
def clear_notifications():
    from flask import request
    if current_user.role not in ['admin', 'staff']:
        return redirect(url_for('dashboard.index'))
    
    from models.notification import Notification
    unread = Notification.query.filter_by(is_read=False).all()
    for n in unread:
        n.is_read = True
    db.session.commit()
    
    return redirect(request.referrer or url_for('dashboard.index'))
