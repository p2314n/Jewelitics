from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import db
from models.product import Category, Product
from utils import admin_required
import os, uuid
from werkzeug.utils import secure_filename

products_bp = Blueprint('products', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─── Categories ──────────────────────────────────────────────
@products_bp.route('/categories')
@login_required
def categories():
    cats = Category.query.order_by(Category.name).all()
    return render_template('products/categories.html', categories=cats)


@products_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_category():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        desc = request.form.get('description', '').strip()
        if not name:
            flash('Category name is required.', 'danger')
        elif Category.query.filter_by(name=name).first():
            flash('Category already exists.', 'danger')
        else:
            db.session.add(Category(name=name, description=desc))
            db.session.commit()
            flash('Category added!', 'success')
            return redirect(url_for('products.categories'))
    return render_template('products/category_form.html', category=None)


@products_bp.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(id):
    cat = Category.query.get_or_404(id)
    if request.method == 'POST':
        cat.name = request.form.get('name', '').strip()
        cat.description = request.form.get('description', '').strip()
        db.session.commit()
        flash('Category updated!', 'success')
        return redirect(url_for('products.categories'))
    return render_template('products/category_form.html', category=cat)


@products_bp.route('/categories/delete/<int:id>')
@login_required
@admin_required
def delete_category(id):
    cat = Category.query.get_or_404(id)
    db.session.delete(cat)
    db.session.commit()
    flash('Category deleted.', 'info')
    return redirect(url_for('products.categories'))


# ─── Products ────────────────────────────────────────────────
@products_bp.route('/products')
@login_required
def product_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    cat_id = request.args.get('category', '', type=str)
    material = request.args.get('material', '')

    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    if cat_id:
        query = query.filter_by(category_id=int(cat_id))
    if material:
        query = query.filter_by(material=material)

    products = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    categories = Category.query.order_by(Category.name).all()
    return render_template('products/list.html',
                           products=products, categories=categories,
                           search=search, cat_id=cat_id, material=material)


@products_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    if request.method == 'POST':
        # Generate SKU
        sku = f"JWL-{uuid.uuid4().hex[:8].upper()}"

        product = Product(
            name=request.form.get('name', '').strip(),
            sku=sku,
            category_id=request.form.get('category_id', type=int),
            material=request.form.get('material', 'Gold'),
            purity=request.form.get('purity', '22K'),
            weight=request.form.get('weight', 0, type=float),
            purchase_price=request.form.get('purchase_price', 0, type=float),
            selling_price=request.form.get('selling_price', 0, type=float),
            quantity=request.form.get('quantity', 0, type=int),
            min_stock=request.form.get('min_stock', 5, type=int),
            description=request.form.get('description', '').strip(),
        )

        # Handle image upload
        from flask import current_app
        file = request.files.get('image')
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{sku}_{file.filename}")
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products')
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))
            product.image = f"products/{filename}"

        db.session.add(product)
        db.session.commit()
        flash('Product added!', 'success')
        return redirect(url_for('products.product_list'))

    categories = Category.query.order_by(Category.name).all()
    return render_template('products/form.html', product=None, categories=categories)


@products_bp.route('/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.name = request.form.get('name', '').strip()
        product.category_id = request.form.get('category_id', type=int)
        product.material = request.form.get('material', 'Gold')
        product.purity = request.form.get('purity', '22K')
        product.weight = request.form.get('weight', 0, type=float)
        product.purchase_price = request.form.get('purchase_price', 0, type=float)
        product.selling_price = request.form.get('selling_price', 0, type=float)
        product.quantity = request.form.get('quantity', 0, type=int)
        product.min_stock = request.form.get('min_stock', 5, type=int)
        product.description = request.form.get('description', '').strip()

        from flask import current_app
        file = request.files.get('image')
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{product.sku}_{file.filename}")
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products')
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))
            product.image = f"products/{filename}"

        db.session.commit()
        flash('Product updated!', 'success')
        return redirect(url_for('products.product_list'))

    categories = Category.query.order_by(Category.name).all()
    return render_template('products/form.html', product=product, categories=categories)


@products_bp.route('/products/delete/<int:id>')
@login_required
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted.', 'info')
    return redirect(url_for('products.product_list'))


@products_bp.route('/products/<int:id>')
@login_required
def product_detail(id):
    product = Product.query.get_or_404(id)
    return render_template('products/detail.html', product=product)
