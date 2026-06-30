from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db
from models.product import Product
from models.inventory import InventoryLog
from utils import staff_required

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/inventory')
@login_required
@staff_required
def stock_list():
    search = request.args.get('search', '')
    filter_type = request.args.get('filter', '')  # low, out, all

    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    if filter_type == 'low':
        query = query.filter(Product.quantity <= Product.min_stock, Product.quantity > 0)
    elif filter_type == 'out':
        query = query.filter(Product.quantity == 0)

    products = query.order_by(Product.quantity.asc()).all()

    # Counts for tabs
    total = Product.query.count()
    low_count = Product.query.filter(Product.quantity <= Product.min_stock, Product.quantity > 0).count()
    out_count = Product.query.filter_by(quantity=0).count()

    return render_template('inventory/list.html',
                           products=products, search=search, filter_type=filter_type,
                           total=total, low_count=low_count, out_count=out_count)


@inventory_bp.route('/inventory/adjust/<int:product_id>', methods=['GET', 'POST'])
@login_required
@staff_required
def adjust_stock(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        action = request.form.get('action', 'adjust')  # adjust, damage, return, lost
        quantity = request.form.get('quantity', 0, type=int)
        remarks = request.form.get('remarks', '').strip()

        if quantity == 0:
            flash('Quantity cannot be zero.', 'danger')
        else:
            # Determine direction
            if action in ('damage', 'lost'):
                quantity = -abs(quantity)
            elif action == 'return':
                quantity = abs(quantity)
            # adjust can be positive or negative

            product.quantity = max(0, product.quantity + quantity)

            log = InventoryLog(
                product_id=product.id,
                user_id=current_user.id,
                action=action,
                quantity_change=quantity,
                quantity_after=product.quantity,
                remarks=remarks
            )
            db.session.add(log)
            db.session.commit()
            flash(f'Stock updated! New quantity: {product.quantity}', 'success')
            return redirect(url_for('inventory.stock_list'))

    logs = InventoryLog.query.filter_by(product_id=product_id).order_by(
        InventoryLog.created_at.desc()
    ).limit(20).all()

    return render_template('inventory/adjust.html', product=product, logs=logs)


@inventory_bp.route('/inventory/logs')
@login_required
@staff_required
def logs():
    page = request.args.get('page', 1, type=int)
    logs = InventoryLog.query.order_by(
        InventoryLog.created_at.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    return render_template('inventory/logs.html', logs=logs)
