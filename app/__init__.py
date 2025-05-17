from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_dropzone import Dropzone
from flask_mail import Mail
from datetime import timedelta

db = SQLAlchemy()
dropzone = Dropzone()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.secret_key = 'magic2004'
    app.permanent_session_lifetime = timedelta(days=1)

    # Cấu hình database và Dropzone
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DROPZONE_UPLOAD_MULTIPLE'] = True
    app.config['DROPZONE_MAX_FILE_SIZE'] = 3
    app.config['DROPZONE_UPLOAD_DEST'] = 'app/static/image'

    # Cấu hình email với Flask-Mail
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'vipvuigkhj@gmail.com'
    app.config['MAIL_PASSWORD'] = '25620041234'
    app.config['MAIL_DEFAULT_SENDER'] = 'vipvuigkhj@gmail.com'
    app.config['APP_NAME'] = 'Book Store'

    # Khởi tạo các extension
    db.init_app(app)
    dropzone.init_app(app)
    mail.init_app(app)

    # Đăng ký routes
    from app.routes.admin import init_admin_routes
    from app.routes.user import init_user_routes
    init_admin_routes(app)
    init_user_routes(app)

    # Tạo database và dữ liệu mẫu
    with app.app_context():
        db.create_all()
        from app.models import User, Product, Order
        if not User.query.first():
            admin = User(lastname='Admin', firstname='User', username='admin', email='admin123@gmail.com', phone='0123456789', password='admin123', is_admin=True, is_locked=False)
            db.session.add(admin)
            db.session.commit()
        if not Product.query.first():
            sample_products = [
                Product(name='Sách Harry Potter', author='J.K. Rowling', price=200000, discount=10, image='/static/image/logo.png', description='Cuốn sách nổi tiếng', category='Truyện trinh thám'),
                Product(name='Văn Học Việt Nam', author='Nguyễn Nhật Ánh', price=150000, discount=5, image='', description='Tuyển tập văn học', category='Văn học Việt Nam'),
            ]
            db.session.bulk_save_objects(sample_products)
            db.session.commit()

    return app