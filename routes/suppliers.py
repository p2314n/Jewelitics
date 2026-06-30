from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db
from models.supplier import Supplier, PurchaseOrder
from models.product import Product
from models.inventory import InventoryLog
from utils import admin_required
import uuid

suppliers_bp = Blueprint('suppliers', __name__)


# ─── Suppliers ───────────────────────────────────────────────
@suppliers_bp.route('/suppliers')
@login_required
@admin_required
def supplier_list():
    search = request.args.get('search', '')
    query = Supplier.query
    if search:
        query = query.filter(Supplier.name.ilike(f'%{search}%'))
    suppliers = query.order_by(Supplier.name).all()
    return render_template('suppliers/list.html', suppliers=suppliers, search=search)


@suppliers_bp.route('/suppliers/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_supplier():
    if request.method == 'POST':
        supplier = Supplier(
            name=request.form.get('name', '').strip(),
            phone=request.form.get('phone', '').strip(),
            email=request.form.get('email', '').strip(),
            address=request.form.get('address', '').strip(),
            city=request.form.get('city', '').strip(),
            state=request.form.get('state', '').strip(),
        )
        db.session.add(supplier)
        db.session.commit()
        flash('Supplier added!', 'success')
        return redirect(url_for('suppliers.supplier_list'))
    return render_template('suppliers/form.html', supplier=None)


@suppliers_bp.route('/suppliers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    if request.method == 'POST':
        supplier.name = request.form.get('name', '').strip()
        supplier.phone = request.form.get('phone', '').strip()
        supplier.email = request.form.get('email', '').strip()
        supplier.address = request.form.get('address', '').strip()
        supplier.city = request.form.get('city', '').strip()
        supplier.state = request.form.get('state', '').strip()
        db.session.commit()
        flash('Supplier updated!', 'success')
        return redirect(url_for('suppliers.supplier_list'))
    return render_template('suppliers/form.html', supplier=supplier)


@suppliers_bp.route('/suppliers/delete/<int:id>')
@login_required
@admin_required
def delete_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    db.session.delete(supplier)
    db.session.commit()
    flash('Supplier deleted.', 'info')
    return redirect(url_for('suppliers.supplier_list'))


# ─── Purchase Orders ────────────────────────────────────────
@suppliers_bp.route('/purchases')
@login_required
@admin_required
def purchase_list():
    purchases = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).all()
    return render_template('suppliers/purchases.html', purchases=purchases)


@suppliers_bp.route('/purchases/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_purchase():
    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        quantity = request.form.get('quantity', 0, type=int)
        unit_price = request.form.get('unit_price', 0, type=float)

        po = PurchaseOrder(
            po_number=f"PO-{uuid.uuid4().hex[:8].upper()}",
            supplier_id=request.form.get('supplier_id', type=int),
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            total=quantity * unit_price,
            status='pending'
        )
        db.session.add(po)
        db.session.commit()
        flash('Purchase order created!', 'success')
        return redirect(url_for('suppliers.purchase_list'))

    suppliers = Supplier.query.order_by(Supplier.name).all()
    products = Product.query.order_by(Product.name).all()
    return render_template('suppliers/purchase_form.html',
                           suppliers=suppliers, products=products, purchase=None)


@suppliers_bp.route('/purchases/receive/<int:id>')
@login_required
@admin_required
def receive_purchase(id):
    po = PurchaseOrder.query.get_or_404(id)
    if po.status == 'pending':
        # Update stock
        product = Product.query.get(po.product_id)
        if product:
            product.quantity += po.quantity
            log = InventoryLog(
                product_id=product.id,
                user_id=current_user.id,
                action='purchase',
                quantity_change=po.quantity,
                quantity_after=product.quantity,
                remarks=f'Purchase order {po.po_number}'
            )
            db.session.add(log)
        po.status = 'received'
        db.session.commit()
        flash(f'Purchase {po.po_number} received! Stock updated.', 'success')
    else:
        flash('This purchase order is not pending.', 'warning')
    return redirect(url_for('suppliers.purchase_list'))


@suppliers_bp.route('/purchases/cancel/<int:id>')
@login_required
@admin_required
def cancel_purchase(id):
    po = PurchaseOrder.query.get_or_404(id)
    if po.status == 'pending':
        po.status = 'cancelled'
        db.session.commit()
        flash(f'Purchase {po.po_number} cancelled.', 'info')
    return redirect(url_for('suppliers.purchase_list'))
