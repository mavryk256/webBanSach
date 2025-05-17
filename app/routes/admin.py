from flask import render_template, request, redirect, url_for, flash, session
from app import db, mail
from app.models import User, Product, Order
from werkzeug.utils import secure_filename
import os
from flask_mail import Message
from datetime import datetime

def init_admin_routes(app):
    def is_admin():
        return 'username' in session and User.query.filter_by(username=session['username'], is_admin=True).first()

    @app.route('/admin/products', methods=['GET', 'POST'])
    def manage_products():
        if not is_admin():
            flash('Bạn không có quyền truy cập trang này.')
            return redirect(url_for('login'))

        VALID_CATEGORIES = [
            "Sách tiểu thuyết", "Sách truyện ngắn", "Truyện trinh thám", "Truyện ngôn tình",
            "Văn học Việt Nam", "Sách marketing", "Sách đầu tư tài chính", "Cẩm nang làm bố mẹ",
            "Sách thiếu nhi", "Sách khoa học", "Sách lịch sử", "Sách kỹ năng"
        ]

        if request.method == 'POST':
            action = request.form.get('action')
            if action == 'add':
                name = request.form['name']
                author = request.form.get('author', '')
                price = float(request.form['price'])
                discount = float(request.form['discount']) if request.form['discount'] else 0.0
                description = request.form['description']
                category = request.form.get('category')
                if category not in VALID_CATEGORIES:
                    flash('Thể loại không hợp lệ!')
                    return redirect(url_for('manage_products'))
                image = 'default.jpg'
                if 'file' in request.files:
                    file = request.files['file']
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        file.save(os.path.join('app/static/image', filename))
                        image = filename
                new_product = Product(
                    name=name,
                    author=author,
                    price=price,
                    discount=discount,
                    image=image,
                    description=description,
                    category=category
                )
                db.session.add(new_product)
                db.session.commit()
                flash('Thêm sản phẩm thành công!')
            elif action == 'edit':
                product_id = int(request.form['product_id'])
                product = Product.query.get(product_id)
                if product:
                    product.name = request.form['name']
                    product.author = request.form.get('author', '')
                    product.price = float(request.form['price'])
                    product.discount = float(request.form['discount']) if request.form['discount'] else 0.0
                    product.description = request.form['description']
                    category = request.form['category']
                    if category not in VALID_CATEGORIES:
                        flash('Thể loại không hợp lệ!')
                        return redirect(url_for('manage_products'))
                    product.category = category
                    if 'file' in request.files:
                        file = request.files['file']
                        if file and file.filename:
                            filename = secure_filename(file.filename)
                            file.save(os.path.join('app/static/image', filename))
                            product.image = filename
                    db.session.commit()
                    flash('Sửa sản phẩm thành công!')
            elif action == 'delete':
                product_id = int(request.form['product_id'])
                product = Product.query.get(product_id)
                if product:
                    db.session.delete(product)
                    db.session.commit()
                    flash('Xóa sản phẩm thành công!')

        products = Product.query.all()
        return render_template('admin/manage_products.html', products=products)

    @app.route('/admin/users', methods=['GET', 'POST'])
    def manage_users():
        if not is_admin():
            flash('Bạn không có quyền truy cập trang này.')
            return redirect(url_for('login'))

        if request.method == 'POST':
            user_id = int(request.form['user_id'])
            action = request.form['action']
            user = User.query.get(user_id)
            if user:
                if action == 'delete':
                    db.session.delete(user)
                    db.session.commit()
                    flash('Xóa tài khoản thành công!')
                elif action == 'lock':
                    user.is_locked = True
                    db.session.commit()
                    flash('Khóa tài khoản thành công!')
                elif action == 'unlock':
                    user.is_locked = False
                    db.session.commit()
                    flash('Mở khóa tài khoản thành công!')

        users = User.query.filter_by(is_admin=False).all()
        return render_template('admin/manage_users.html', users=users)

    @app.route('/admin/orders', methods=['GET', 'POST'])
    def manage_orders():
        if not is_admin():
            flash('Bạn không có quyền truy cập trang này.')
            return redirect(url_for('login'))

        if request.method == 'POST':
            action = request.form.get('action')
            if action == 'ship_all':
                pending_orders = Order.query.filter_by(delivery_status='Chưa giao hàng').all()
                if pending_orders:
                    for order in pending_orders:
                        order.delivery_status = 'Đang giao hàng'
                        # Gửi email thông báo cho người dùng
                        msg = Message(
                            subject='Thông Báo Giao Hàng',
                            recipients=[order.contact_email],
                            sender='vipvuigkhj@gmail.com'
                        )
                        msg.body = f"""
Chào {order.contact_name},

Đơn hàng của bạn (Mã đơn: {order.id}) đang được giao đến địa chỉ:
{order.shipping_address}

Trạng thái: Đang giao hàng
Tổng tiền: {order.total_price} VND

Cảm ơn bạn đã mua sắm!
Đội ngũ {app.config.get('APP_NAME', 'Cửa Hàng Sách')}
(Hiện tại là {datetime.now().strftime('%H:%M %d/%m/%Y')})
"""
                        mail.send(msg)
                    db.session.commit()
                    flash('Đã cập nhật trạng thái giao hàng và gửi thông báo qua email!')
                else:
                    flash('Không có đơn hàng nào để giao!')

        orders = Order.query.all()
        return render_template('admin/manage_orders.html', orders=orders)

    @app.route('/admin/user/<int:user_id>')
    def view_user(user_id):
        if not is_admin():
            flash('Bạn không có quyền truy cập trang này.')
            return redirect(url_for('login'))

        user = User.query.get_or_404(user_id)
        orders = Order.query.filter_by(user_id=user.id, payment_status='Đã thanh toán').all()
        return render_template('admin/view_user.html', user=user, orders=orders)