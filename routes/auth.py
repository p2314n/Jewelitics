import os
import random
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from models import db
from models.user import User

# IMPORTANT: You must import 'mail' from the app module, but to avoid circular imports, 
# we'll import current_app inside the helper function instead.
from flask import current_app

auth_bp = Blueprint('auth', __name__)

def generate_otp():
    """Generate a 6-digit OTP code."""
    return str(random.randint(100000, 999999))

def send_otp_email(user):
    """Sends the OTP email to the user."""
    from app import mail # Import here to avoid circular dependency
    otp = generate_otp()
    user.otp_code = otp
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()
    
    msg = Message('Verify your Jewelitics Account', recipients=[user.email])
    msg.body = f"Hello {user.first_name or user.username},\n\nYour verification code is: {otp}\n\nThis code will expire in 10 minutes.\n\nThank you,\nJewelitics Team"
    msg.html = f"<p>Hello {user.first_name or user.username},</p><p>Your verification code is: <strong style='font-size:24px;'>{otp}</strong></p><p>This code will expire in 10 minutes.</p>"
    
    # ALWAYS print OTP to terminal for developer convenience
    print(f"\n==========================================")
    print(f"🔑 OTP CODE FOR {user.email}: {otp}")
    print(f"==========================================\n")

    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    # Store next url for oauth callback
    if 'next' in request.args:
        session['next_url'] = request.args.get('next')

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if user and user.check_password(password):
            if not user.is_verified:
                # Require OTP verification before allowing login
                send_otp_email(user)
                flash('Please verify your email address to log in. A new code has been sent.', 'warning')
                return redirect(url_for('auth.verify_otp', user_id=user.id))

            login_user(user, remember=bool(remember))
            flash(f'Welcome back, {user.full_name}!', 'success')
            next_page = session.pop('next_url', None) or request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()

        # Validation
        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if not email or '@' not in email:
            errors.append('Please enter a valid email.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            if existing_username.is_verified:
                errors.append('Username already taken.')
            else:
                db.session.delete(existing_username)
                db.session.commit()

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            if existing_email.is_verified:
                errors.append('Email already registered.')
            else:
                db.session.delete(existing_email)
                db.session.commit()

        if errors:
            for e in errors:
                flash(e, 'danger')
        else:
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role='customer',
                is_verified=False
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            # Send the OTP
            send_otp_email(user)
            flash('Account created! Please check your email for the verification code.', 'success')
            return redirect(url_for('auth.verify_otp', user_id=user.id))

    return render_template('auth/register.html')

@auth_bp.route('/verify-otp/<int:user_id>', methods=['GET', 'POST'])
def verify_otp(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_verified:
        flash('Your account is already verified. Please log in.', 'info')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()
        if not user.otp_code or not user.otp_expiry:
            flash('Invalid session. Please request a new code.', 'danger')
        elif datetime.utcnow() > user.otp_expiry:
            flash('Verification code has expired. Please request a new one.', 'danger')
        elif entered_otp == user.otp_code:
            user.is_verified = True
            user.otp_code = None
            user.otp_expiry = None
            db.session.commit()
            flash('Email verified successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Invalid verification code. Please try again.', 'danger')

    return render_template('auth/verify_otp.html', user=user)

@auth_bp.route('/resend-otp/<int:user_id>')
def resend_otp(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_verified:
        flash('Account already verified.', 'info')
        return redirect(url_for('auth.login'))
    
    send_otp_email(user)
    flash('A new verification code has been sent to your email.', 'success')
    return redirect(url_for('auth.verify_otp', user_id=user.id))


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html')
