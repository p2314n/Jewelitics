import os
from dotenv import load_dotenv
load_dotenv()  # Load .env file


from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
from models import db
from models.user import User

login_manager = LoginManager()
mail = Mail()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Create folders
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'products'), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'instance'), exist_ok=True)

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.products import products_bp
    from routes.inventory import inventory_bp
    from routes.suppliers import suppliers_bp
    from routes.orders import orders_bp
    from routes.reports import reports_bp
    from routes.users import users_bp
    from routes.chat import chat_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(chat_bp)

    from flask import send_from_directory
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # Create tables
    with app.app_context():
        db.create_all()

    @app.context_processor
    def inject_notifications():
        from flask_login import current_user
        from models.notification import Notification
        if current_user.is_authenticated and current_user.role in ['admin', 'staff']:
            unread_notifs = Notification.query.filter_by(is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
            unread_count = Notification.query.filter_by(is_read=False).count()
            return dict(unread_notifs=unread_notifs, unread_count=unread_count)
        return dict(unread_notifs=[], unread_count=0)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)
