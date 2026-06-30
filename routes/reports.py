from flask import Blueprint, render_template, request, send_file
from flask_login import login_required, current_user
from models import db
from models.product import Product, Category
from models.order import Order, OrderItem
from models.notification import SalesSummary
from models.supplier import Supplier
from models.user import User
from utils import staff_required
from sqlalchemy import func
from datetime import datetime, timedelta
import os, io

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/reports')
@login_required
@staff_required
def index():
    return render_template('reports/index.html')


@reports_bp.route('/analytics')
@login_required
@staff_required
def analytics():
    # Top selling products
    top_products = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('total_qty'),
        func.sum(OrderItem.price * OrderItem.quantity).label('revenue')
    ).join(OrderItem).group_by(Product.name).order_by(
        func.sum(OrderItem.quantity).desc()
    ).limit(10).all()

    # Category performance
    cat_perf = db.session.query(
        Category.name,
        func.sum(OrderItem.price * OrderItem.quantity).label('revenue')
    ).join(Product, Category.id == Product.category_id
    ).join(OrderItem, Product.id == OrderItem.product_id
    ).group_by(Category.name).all()

    # Monthly sales trend (last 6 months)
    monthly_labels = []
    monthly_sales = []
    for i in range(5, -1, -1):
        d = datetime.utcnow() - timedelta(days=30 * i)
        label = d.strftime('%b %Y')
        month_total = db.session.query(
            func.sum(SalesSummary.total_sales)
        ).filter(
            func.strftime('%Y-%m', SalesSummary.sale_date) == d.strftime('%Y-%m')
        ).scalar() or 0
        monthly_labels.append(label)
        monthly_sales.append(float(month_total))

    # Customer growth
    total_customers = User.query.filter_by(role='customer').count()

    # Stock value by material
    materials = db.session.query(
        Product.material,
        func.sum(Product.selling_price * Product.quantity).label('value')
    ).group_by(Product.material).all()

    # Most Profitable Products (Selling Price - Purchase Price)
    most_profitable = db.session.query(
        Product.name,
        (Product.selling_price - Product.purchase_price).label('profit_margin'),
        Product.selling_price
    ).order_by((Product.selling_price - Product.purchase_price).desc()).limit(5).all()

    # Dead Stock (Items with quantity > 0 but ZERO sales)
    dead_stock = db.session.query(
        Product.name, Product.quantity, Product.selling_price
    ).outerjoin(OrderItem, Product.id == OrderItem.product_id)\
     .filter(OrderItem.id == None, Product.quantity > 0)\
     .order_by(Product.quantity.desc()).limit(5).all()

    return render_template('reports/analytics.html',
        top_products=top_products,
        cat_perf=cat_perf,
        monthly_labels=monthly_labels,
        monthly_sales=monthly_sales,
        total_customers=total_customers,
        materials=materials,
        most_profitable=most_profitable,
        dead_stock=dead_stock,
    )


@reports_bp.route('/reports/download/<report_type>')
@login_required
@staff_required
def download_report(report_type):
    """Generate CSV reports."""
    import csv

    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == 'inventory':
        writer.writerow(['SKU', 'Name', 'Material', 'Quantity', 'Min Stock',
                         'Purchase Price', 'Selling Price', 'Status'])
        for p in Product.query.all():
            writer.writerow([p.sku, p.name, p.material, p.quantity,
                             p.min_stock, p.purchase_price, p.selling_price,
                             p.status])

    elif report_type == 'sales':
        writer.writerow(['Date', 'Total Sales', 'Total Profit', 'Orders'])
        for s in SalesSummary.query.order_by(SalesSummary.sale_date.desc()).all():
            writer.writerow([s.sale_date, s.total_sales, s.total_profit,
                             s.total_orders])

    elif report_type == 'orders':
        writer.writerow(['Order #', 'Customer', 'Amount', 'Status',
                         'Payment', 'Date'])
        for o in Order.query.order_by(Order.created_at.desc()).all():
            writer.writerow([o.order_number, o.customer.username,
                             o.total_amount, o.status, o.payment_status,
                             o.created_at.strftime('%Y-%m-%d')])
                             
    elif report_type == 'customers':
        writer.writerow(['Customer ID', 'Username', 'Name', 'Email', 'Phone', 'Join Date', 'Total Orders', 'Total Spent'])
        
        customers = db.session.query(
            User,
            func.count(Order.id).label('total_orders'),
            func.sum(Order.total_amount).label('total_spent')
        ).outerjoin(Order, User.id == Order.user_id)\
         .filter(User.role == 'customer')\
         .group_by(User.id)\
         .order_by(func.sum(Order.total_amount).desc()).all()
         
        for c, t_orders, t_spent in customers:
            writer.writerow([
                c.id, c.username, c.full_name, c.email, c.phone, 
                c.created_at.strftime('%Y-%m-%d'),
                t_orders, 
                t_spent or 0.0
            ])
            
    elif report_type == 'staff':
        # Only admins can download staff reports
        if current_user.role != 'admin':
            from flask import abort
            abort(403)
        writer.writerow(['Staff ID', 'Username', 'Name', 'Email', 'Phone', 'Role', 'Join Date'])
        staff_members = User.query.filter(User.role != 'customer').order_by(User.id).all()
        for s in staff_members:
            writer.writerow([
                s.id, s.username, s.full_name, s.email, s.phone,
                s.role.capitalize(),
                s.created_at.strftime('%Y-%m-%d')
            ])
            
    else:
        writer.writerow(['No data'])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{report_type}_report.csv'
    )
