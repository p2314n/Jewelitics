from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db
from models.product import Product, Category
from models.order import Order, OrderItem, CartItem
from models.inventory import InventoryLog
from models.notification import SalesSummary, Notification
from utils import admin_required, staff_required
import uuid
from datetime import datetime

orders_bp = Blueprint('orders', __name__)


@orders_bp.route('/shop')
@login_required
def shop():
    search = request.args.get('search', '')
    cat_id = request.args.get('category', '')
    query = Product.query.filter_by(status='active')
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    if cat_id:
        query = query.filter_by(category_id=int(cat_id))
    products = query.order_by(Product.created_at.desc()).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template('orders/shop.html',
                           products=products, categories=categories, search=search)


@orders_bp.route('/shop/<int:id>')
@login_required
def shop_detail(id):
    product = Product.query.get_or_404(id)
    related = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id
    ).limit(4).all()
    return render_template('orders/shop_detail.html', product=product, related=related)


@orders_bp.route('/cart')
@login_required
def cart():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.selling_price * item.quantity for item in items)
    return render_template('orders/cart.html', items=items, total=total)


@orders_bp.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    qty = request.form.get('quantity', 1, type=int)
    book_order = request.form.get('book_order')
    
    existing = CartItem.query.filter_by(
        user_id=current_user.id, product_id=product_id).first()
    if existing:
        existing.quantity += qty
    else:
        db.session.add(CartItem(
            user_id=current_user.id, product_id=product_id, quantity=qty))
    db.session.commit()
    
    if book_order:
        return redirect(url_for('orders.checkout'))
        
    flash(f'{product.name} added to cart!', 'success')
    return redirect(request.referrer or url_for('orders.shop'))


@orders_bp.route('/cart/remove/<int:id>')
@login_required
def remove_from_cart(id):
    item = CartItem.query.get_or_404(id)
    if item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('orders.cart'))


@orders_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('orders.shop'))

    if request.method == 'POST':
        order = Order(
            order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
            user_id=current_user.id,
            total_amount=sum(
                i.product.selling_price * i.quantity for i in items),
            payment_method='contact',
            shipping_address=request.form.get('address', '').strip(),
            status='pending',
            payment_status='pending'
        )
        db.session.add(order)
        db.session.flush()

        for item in items:
            db.session.add(OrderItem(
                order_id=order.id, product_id=item.product_id,
                quantity=item.quantity, price=item.product.selling_price))
            product = item.product
            product.quantity = max(0, product.quantity - item.quantity)
            db.session.add(InventoryLog(
                product_id=product.id, user_id=current_user.id,
                action='sale', quantity_change=-item.quantity,
                quantity_after=product.quantity,
                remarks=f'Order {order.order_number}'))

        CartItem.query.filter_by(user_id=current_user.id).delete()
        today = datetime.utcnow().date()
        summary = SalesSummary.query.filter_by(sale_date=today).first()
        if summary:
            summary.total_sales += order.total_amount
            summary.total_orders += 1
        else:
            db.session.add(SalesSummary(
                sale_date=today, total_sales=order.total_amount,
                total_profit=order.total_amount * 0.25, total_orders=1))

        db.session.add(Notification(
            title='New Booking Request',
            message=f"Customer {current_user.username} has booked an order ({order.order_number}). Please contact them.",
            type='order',
            link=url_for('orders.order_detail', id=order.id)
        ))

        db.session.commit()
        flash('Thank you for booking an order! Our team will contact you through call or email.', 'success')
        return redirect(url_for('orders.my_orders'))

    total = sum(i.product.selling_price * i.quantity for i in items)
    return render_template('orders/checkout.html', items=items, total=total)


@orders_bp.route('/my-orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(
        Order.created_at.desc()).all()
    return render_template('orders/my_orders.html', orders=orders)


@orders_bp.route('/orders')
@login_required
@staff_required
def order_list():
    status_filter = request.args.get('status', '')
    query = Order.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    orders = query.order_by(Order.created_at.desc()).all()
    return render_template('orders/list.html',
                           orders=orders, status_filter=status_filter)


@orders_bp.route('/orders/<int:id>')
@login_required
def order_detail(id):
    order = Order.query.get_or_404(id)
    if current_user.role == 'customer' and order.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('orders.my_orders'))
    return render_template('orders/detail.html', order=order)


@orders_bp.route('/orders/<int:id>/status/<status>')
@login_required
@staff_required
def update_order_status(id, status):
    valid_statuses = [
        'accepted', 'processing', 'packed',
        'shipped', 'delivered', 'cancelled', 'rejected']
    if status not in valid_statuses:
        flash('Invalid status.', 'danger')
        return redirect(url_for('orders.order_list'))

    order = Order.query.get_or_404(id)
    order.status = status
    if status == 'delivered':
        order.payment_status = 'paid'
    elif status in ('cancelled', 'rejected'):
        for item in order.items:
            product = Product.query.get(item.product_id)
            if product:
                product.quantity += item.quantity
                db.session.add(InventoryLog(
                    product_id=product.id, user_id=current_user.id,
                    action='return', quantity_change=item.quantity,
                    quantity_after=product.quantity,
                    remarks=f'Order {order.order_number} {status}'))
        order.payment_status = 'refunded'
    db.session.commit()
    flash(f'Order → {status.upper()}', 'success')
    return redirect(url_for('orders.order_detail', id=id))
