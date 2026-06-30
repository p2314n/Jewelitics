from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db
from models.user import User
from utils import staff_required, admin_required

users_bp = Blueprint('users', __name__)


@users_bp.route('/users')
@login_required
@staff_required
def user_list():
    role_filter = request.args.get('role', '')
    search = request.args.get('search', '')

    query = User.query

    # Staff can only see customers
    if current_user.role == 'staff':
        query = query.filter_by(role='customer')
    else:
        # Admin sees everyone except themselves
        if role_filter:
            query = query.filter_by(role=role_filter)

    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.first_name.ilike(f'%{search}%')) |
            (User.last_name.ilike(f'%{search}%'))
        )

    users = query.order_by(User.created_at.desc()).all()

    # Counts for tabs (admin only)
    total = User.query.count()
    staff_count = User.query.filter_by(role='staff').count()
    customer_count = User.query.filter_by(role='customer').count()

    return render_template('users/list.html',
                           users=users, role_filter=role_filter, search=search,
                           total=total, staff_count=staff_count,
                           customer_count=customer_count)


@users_bp.route('/users/<int:id>')
@login_required
@staff_required
def user_detail(id):
    user = User.query.get_or_404(id)
    # Staff can only view customers
    if current_user.role == 'staff' and user.role != 'customer':
        flash('Access denied.', 'danger')
        return redirect(url_for('users.user_list'))
    return render_template('users/detail.html', user=user)


@users_bp.route('/users/delete/<int:id>')
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    # Can't delete yourself or other admins
    if user.id == current_user.id:
        flash("You can't delete your own account.", 'danger')
    elif user.role == 'admin':
        flash("You can't delete other admins.", 'danger')
    else:
        name = user.full_name
        db.session.delete(user)
        db.session.commit()
        flash(f'User "{name}" has been removed.', 'success')
    return redirect(url_for('users.user_list'))
