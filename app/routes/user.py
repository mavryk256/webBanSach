import re
from flask import render_template, request, redirect, url_for, session, make_response, jsonify
from app import db
from app.models import User, Product, Order, Review

def init_user_routes(app):
    VALID_CATEGORIES = [
        "Sách tiểu thuyết", "Sách truyện ngắn", "Truyện trinh thám", "Truyện ngôn tình",
        "Văn học Việt Nam", "Sách marketing", "Sách đầu tư tài chính", "Cẩm nang làm bố mẹ",
        "Sách thiếu nhi", "Sách khoa học", "Sách lịch sử", "Sách kỹ năng",
        "Sách đồng giá 19k", "Sách bán chạy", "Sách đồng giá 29k", "Sách đồng giá 9k",
        "Truyện cổ tích Việt Nam", "Sách kỹ năng sống"
    ]

    @app.route('/home')
    @app.route('/home/category/<string:category>')
    def home(category=None):
        if 'username' in session:
            user = User.query.filter_by(username=session['username']).first()
            if user and user.is_admin:
                return redirect(url_for('manage_products'))
            cart_count = Order.query.filter_by(user_id=user.id, payment_status='Chưa thanh toán').count() if user else 0
        else:
            cart_count = 0

        products = Product.query.all()
        user = User.query.filter_by(username=session.get('username')).first() if 'username' in session else None
        orders = Order.query.filter_by(user_id=user.id, payment_status='Chưa thanh toán').all() if user else []

        if category and category in VALID_CATEGORIES:
            products = [p for p in products if p.category == category]

        return render_template('home.html', products=products, orders=orders, cart_count=cart_count, selected_category=category)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            lastname = request.form['lastname']
            firstname = request.form['firstname']
            username = request.form['username']
            email = request.form['email']
            phone = request.form['phone']
            password = request.form['password']
            confirm_password = request.form['confirm-password']

            email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
            if not re.match(email_pattern, email):
                return render_template('register.html', alert_message="Email không hợp lệ!")

            if len(password) < 8:
                return render_template('register.html', alert_message="Mật khẩu phải từ 8 ký tự trở lên!")

            if User.query.filter((User.username == username) | (User.email == email)).first():
                return render_template('register.html', alert_message="Tên người dùng hoặc email đã tồn tại!")

            if password != confirm_password:
                return render_template('register.html', alert_message="Mật khẩu không khớp!")

            new_user = User(lastname=lastname, firstname=firstname, username=username, email=email, phone=phone,
                            password=password, address="")
            db.session.add(new_user)
            db.session.commit()
            return render_template('register.html', alert_message="Đăng ký thành công! Vui lòng đăng nhập.")

        response = make_response(render_template('register.html'))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if 'username' in session:
            user = User.query.filter_by(username=session['username']).first()
            if user:
                return redirect(url_for('home' if not user.is_admin else 'manage_products'))
            else:
                session.pop('username', None)

        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter((User.username == username) | (User.email == username)).first()
            if user:
                if user.password == password:
                    if user.is_locked:
                        return render_template('login.html', alert_message="Tài khoản của bạn đã bị khóa!")
                    session.permanent = True
                    session['username'] = user.username
                    return render_template('login.html', alert_message="Đăng nhập thành công!",
                                           redirect_url=url_for('home' if not user.is_admin else 'manage_products'))
                else:
                    return render_template('login.html', alert_message="Mật khẩu không đúng!")
            else:
                return render_template('login.html', alert_message="Tên người dùng hoặc email không tồn tại!")

        response = make_response(render_template('login.html'))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response

    @app.route('/logout')
    def logout():
        if 'username' in session:
            user = User.query.filter_by(username=session['username']).first()
            session.pop('username', None)
        return redirect(url_for('home'))

    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        if request.method == "POST":
            name = request.form["name"]
            email = request.form["email"]
            phone = request.form["phone"]
            message = request.form["message"]
            # TODO: xử lý dữ liệu ở đây (gửi email, lưu DB, ...)
            return redirect("/contact")
        return render_template("contact.html")

    @app.route('/products')
    def products():
        products = Product.query.all()
        return render_template('products.html', products=products)

    @app.route('/products/<int:product_id>')
    def product_detail(product_id):
        product = Product.query.get_or_404(product_id)
        return render_template('product_detail.html', product=product)

    @app.route('/submit_review/<int:product_id>', methods=['POST'])
    def submit_review(product_id):
        if 'username' not in session:
            return render_template('login.html', alert_message="Vui lòng đăng nhập để đánh giá sản phẩm!",
                                   redirect_url=url_for('login'))

        user = User.query.filter_by(username=session['username']).first()
        if not user:
            session.pop('username', None)
            return render_template('login.html', alert_message="Phiên đăng nhập không hợp lệ! Vui lòng đăng nhập lại.",
                                   redirect_url=url_for('login'))

        product = Product.query.get_or_404(product_id)
        rating = request.form.get('rating')
        comment = request.form.get('comment', '').strip()

        if not rating or not rating.isdigit() or int(rating) < 1 or int(rating) > 5:
            return render_template('product_detail.html', product=product,
                                   alert_message="Vui lòng chọn điểm đánh giá từ 1 đến 5 sao!")

        # Check if user has already reviewed this product
        existing_review = Review.query.filter_by(user_id=user.id, product_id=product.id).first()
        if existing_review:
            return render_template('product_detail.html', product=product,
                                   alert_message="Bạn đã đánh giá sản phẩm này rồi!")

        try:
            new_review = Review(
                user_id=user.id,
                product_id=product.id,
                rating=int(rating),
                comment=comment if comment else None
            )
            db.session.add(new_review)
            db.session.commit()
            return render_template('product_detail.html', product=product,
                                   alert_message="Đánh giá của bạn đã được gửi thành công!")
        except Exception as e:
            db.session.rollback()
            return render_template('product_detail.html', product=product,
                                   alert_message=f"Lỗi khi gửi đánh giá: {str(e)}")

    @app.route('/cart', methods=['GET', 'POST'])
    def cart():
        if 'username' not in session:
            return render_template('login.html', alert_message="Vui lòng đăng nhập để đặt hàng!",
                                   redirect_url=url_for('login'))

        user = User.query.filter_by(username=session['username']).first()
        if not user:
            session.pop('username', None)
            return render_template('login.html', alert_message="Phiên đăng nhập không hợp lệ! Vui lòng đăng nhập lại.",
                                   redirect_url=url_for('login'))

        if request.method == 'POST' and 'product_id' in request.form:
            product_id = int(request.form['product_id'])
            quantity = int(request.form.get('quantity', 1))

            product = Product.query.get(product_id)
            if product:
                effective_discount = min(product.discount, 1.0)
                total_price = max(0, (product.price - (product.price * effective_discount) / 100) * quantity)
                new_order = Order(user_id=user.id, product_id=product_id, quantity=quantity, total_price=total_price,
                                  payment_status='Chưa thanh toán', delivery_status='Chưa giao hàng')
                db.session.add(new_order)
                db.session.commit()

                session['alert_message'] = f"Đã thêm {quantity} {product.name} vào giỏ hàng!"
                return redirect(url_for('cart'))

        alert_message = session.pop('alert_message', None)
        orders = Order.query.filter_by(user_id=user.id, payment_status='Chưa thanh toán').all()
        cart_count = len(orders)
        return render_template('user/cart.html', orders=orders, alert_message=alert_message, cart_count=cart_count)

    @app.route('/cart/delete/<int:order_id>', methods=['POST'])
    def delete_order(order_id):
        if 'username' not in session:
            return render_template('login.html', alert_message="Vui lòng đăng nhập để thực hiện thao tác này!",
                                   redirect_url=url_for('login'))

        user = User.query.filter_by(username=session['username']).first()
        if not user:
            session.pop('username', None)
            return render_template('login.html', alert_message="Phiên đăng nhập không hợp lệ! Vui lòng đăng nhập lại.",
                                   redirect_url=url_for('login'))

        order = Order.query.filter_by(id=order_id, user_id=user.id, payment_status='Chưa thanh toán').first()
        if not order:
            session['alert_message'] = "Đơn hàng không tồn tại hoặc bạn không có quyền xóa!"
            return redirect(url_for('cart'))

        try:
            db.session.delete(order)
            db.session.commit()
            session['alert_message'] = "Đã xóa sản phẩm khỏi giỏ hàng!"
        except Exception as e:
            db.session.rollback()
            session['alert_message'] = f"Lỗi khi xóa sản phẩm: {str(e)}"

        return redirect(url_for('cart'))

    @app.route('/cart/update/<int:order_id>', methods=['POST'])
    def update_order_quantity(order_id):
        if 'username' not in session:
            return jsonify({"success": False, "message": "Vui lòng đăng nhập để thực hiện thao tác này!"}), 401

        user = User.query.filter_by(username=session['username']).first()
        if not user:
            return jsonify({"success": False, "message": "Phiên đăng nhập không hợp lệ! Vui lòng đăng nhập lại."}), 401

        order = Order.query.filter_by(id=order_id, user_id=user.id, payment_status='Chưa thanh toán').first()
        if not order:
            return jsonify({"success": False, "message": "Đơn hàng không tồn tại hoặc bạn không có quyền chỉnh sửa!"}), 404

        try:
            new_quantity = int(request.form.get('quantity', 1))
            if new_quantity < 1:
                return jsonify({"success": False, "message": "Số lượng phải lớn hơn 0!"}), 400

            product = Product.query.get(order.product_id)
            if not product:
                return jsonify({"success": False, "message": "Sản phẩm không tồn tại!"}), 404

            effective_discount = min(product.discount, 1.0)
            order.quantity = new_quantity
            order.total_price = max(0, (product.price - (product.price * effective_discount) / 100) * new_quantity)

            db.session.commit()
            return jsonify({
                "success": True,
                "message": f"Đã cập nhật số lượng cho {product.name}!",
                "total_price": order.total_price
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": f"Lỗi khi cập nhật số lượng: {str(e)}"}), 500

    @app.route('/checkout', methods=['GET', 'POST'])
    def checkout():
        if 'username' not in session:
            return render_template('login.html', alert_message="Vui lòng đăng nhập để thanh toán!",
                                   redirect_url=url_for('login'))

        user = User.query.filter_by(username=session['username']).first()
        if not user:
            session.pop('username', None)
            return render_template('login.html', alert_message="Phiên đăng nhập không hợp lệ! Vui lòng đăng nhập lại.",
                                   redirect_url=url_for('login'))

        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'enter_checkout':
                selected_order_ids = request.form.getlist('selected_orders')
                if not selected_order_ids:
                    orders = Order.query.filter_by(user_id=user.id, payment_status='Chưa thanh toán').all()
                    return render_template('checkout.html', user=user, orders=orders, total_price=0,
                                           alert_message="Vui lòng chọn ít nhất một sản phẩm để thanh toán!")

                selected_order_ids = [int(oid) for oid in selected_order_ids]
                orders = Order.query.filter(Order.id.in_(selected_order_ids), Order.user_id == user.id,
                                            Order.payment_status == 'Chưa thanh toán').all()
                if not orders:
                    return render_template('checkout.html', user=user, orders=[], total_price=0,
                                           alert_message="Không tìm thấy đơn hàng để thanh toán!")

                total_price = sum(order.total_price for order in orders)
                return render_template('checkout.html', user=user, orders=orders, total_price=total_price)

            selected_order_ids = request.form.getlist('selected_orders')
            if not selected_order_ids:
                orders = Order.query.filter_by(user_id=user.id, payment_status='Chưa thanh toán').all()
                return render_template('checkout.html', user=user, orders=orders, total_price=0,
                                       alert_message="Vui lòng chọn ít nhất một sản phẩm để thanh toán!")

            selected_order_ids = [int(oid) for oid in selected_order_ids]
            orders = Order.query.filter(Order.id.in_(selected_order_ids), Order.user_id == user.id,
                                        Order.payment_status == 'Chưa thanh toán').all()
            if not orders:
                return render_template('checkout.html', user=user, orders=[], total_price=0,
                                       alert_message="Không tìm thấy đơn hàng để thanh toán!")

            total_price = sum(order.total_price for order in orders)

            contact_name = request.form.get('contact_name', user.firstname + ' ' + user.lastname)
            contact_phone = request.form.get('contact_phone', user.phone)
            contact_email = request.form.get('contact_email', user.email)
            shipping_address = f"{request.form.get('shipping_address', '')}, {request.form.get('ward', '')}, {request.form.get('district', '')}, {request.form.get('city', '')}"

            email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
            phone_pattern = r'^[0-9]{10}$'
            if not contact_name or not shipping_address or 'Chọn' in shipping_address:
                return render_template('checkout.html', user=user, orders=orders, total_price=total_price,
                                       alert_message="Vui lòng điền đầy đủ họ tên và địa chỉ!")
            if not re.match(phone_pattern, contact_phone):
                return render_template('checkout.html', user=user, orders=orders, total_price=total_price,
                                       alert_message="Số điện thoại không hợp lệ!")
            if not re.match(email_pattern, contact_email):
                return render_template('checkout.html', user=user, orders=orders, total_price=total_price,
                                       alert_message="Email không hợp lệ!")

            for order in orders:
                order.contact_name = contact_name
                order.contact_phone = contact_phone
                order.contact_email = contact_email
                order.shipping_address = shipping_address
                order.payment_status = 'Đã thanh toán'
                order.delivery_status = 'Chưa giao hàng'
            db.session.commit()

            if user.address != shipping_address:
                user.address = shipping_address
                db.session.commit()

            session['alert_message'] = "Đặt hàng thành công! Bạn có thể theo dõi đơn hàng trong hồ sơ."
            return redirect(url_for('profile'))

        orders = Order.query.filter_by(user_id=user.id, payment_status='Chưa thanh toán').all()
        total_price = sum(order.total_price for order in orders)
        return render_template('checkout.html', user=user, orders=orders, total_price=total_price)

    @app.route('/account')
    def profile():
        if 'username' not in session:
            return render_template('login.html', alert_message="Vui lòng đăng nhập để xem trang này!",
                                   redirect_url=url_for('login'))
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            session.pop('username', None)
            return render_template('login.html', alert_message="Phiên đăng nhập không hợp lệ! Vui lòng đăng nhập lại.",
                                   redirect_url=url_for('login'))
        orders = Order.query.filter_by(user_id=user.id, payment_status='Đã thanh toán').all()
        cart_count = Order.query.filter_by(user_id=user.id, payment_status='Chưa thanh toán').count()
        alert_message = session.pop('alert_message', None)
        return render_template('user/profile.html', user=user, orders=orders, cart_count=cart_count,
                               alert_message=alert_message)

    @app.route('/account/update', methods=['POST'])
    def update_profile():
        if 'username' not in session:
            return render_template('login.html', alert_message="Vui lòng đăng nhập để thực hiện thao tác này!",
                                   redirect_url=url_for('login'))

        user = User.query.filter_by(username=session['username']).first()
        if not user:
            session.pop('username', None)
            return render_template('login.html', alert_message="Phiên đăng nhập không hợp lệ! Vui lòng đăng nhập lại.",
                                   redirect_url=url_for('login'))

        if request.method == 'POST':
            lastname = request.form['lastname']
            firstname = request.form['firstname']
            email = request.form['email']
            phone = request.form['phone']
            address = request.form.get('address', user.address or '')

            email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
            if not re.match(email_pattern, email):
                return render_template('user/profile.html', user=user, orders=Order.query.filter_by(user_id=user.id,
                                                                                                    payment_status='Đã thanh toán').all(),
                                       alert_message="Email không hợp lệ!")

            existing_user = User.query.filter(User.email == email, User.id != user.id).first()
            if existing_user:
                return render_template('user/profile.html', user=user, orders=Order.query.filter_by(user_id=user.id,
                                                                                                    payment_status='Đã thanh toán').all(),
                                       alert_message="Email đã được sử dụng bởi người dùng khác!")

            user.lastname = lastname
            user.firstname = firstname
            user.email = email
            user.phone = phone
            user.address = address
            db.session.commit()
            return render_template('user/profile.html', user=user,
                                   orders=Order.query.filter_by(user_id=user.id, payment_status='Đã thanh toán').all(),
                                   alert_message="Cập nhật thông tin thành công!")

    @app.route('/admin/products')
    def admin():
        if 'username' not in session:
            return render_template('login.html', alert_message="Vui lòng đăng nhập với vai trò admin!",
                                   redirect_url=url_for('login'))
        user = User.query.filter_by(username=session['username']).first()
        if not user.is_admin:
            return render_template('home.html', alert_message="Bạn không có quyền truy cập trang admin!")
        return render_template('admin/manage_products.html', user=user)

    @app.route('/search')
    def search():
        category = request.args.get('category', '').strip()
        query = request.args.get('q', '').strip()
        products = Product.query.all()

        if query:
            products = [
                p for p in products
                if query.lower() in p.name.lower() or (p.author and query.lower() in p.author.lower())
            ]

        if category and category in VALID_CATEGORIES:
            products = [p for p in products if p.category == category]

        return render_template('search_results.html', products=products, query=query, category=category,
                               categories=VALID_CATEGORIES)