from flask import Blueprint, jsonify,url_for
from .models import Category, Product,User,UserRole,Order,OrderItem,CartItem
from . import db
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_jwt_extended import create_access_token
from datetime import datetime
from flask_login import current_user

main = Blueprint("main", __name__)

@main.route("/categories", methods=["GET"])
def get_categories():
    categories = Category.query.all()
    result = [
        {
            "id": c.id,
            "name": c.name,
        } for c in categories
    ]
    return jsonify(result)


@main.route("/products")
def get_products():
    products = Product.query.all()
    result = []

    for p in products:
        product_data = {
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "images": [img.url for img in p.images],
            "category": p.category.name if p.category else None,
            "brand": p.brand
        }
        result.append(product_data)

    return jsonify(result)


@main.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    phone = data.get("phone")

    # Kiểm tra thông tin bắt buộc
    if not username or not email or not password or not phone:
        return jsonify({"error": "Vui lòng nhập đầy đủ thông tin"}), 400

    # Kiểm tra username/email trùng
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Tên đăng nhập đã tồn tại"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email đã tồn tại"}), 400

    if User.query.filter_by(phone=phone).first():
        return jsonify({"error": "Số điện thoại đã tồn tại"}), 400

    # Tạo user mới với role mặc định CUSTOMER
    new_user = User(
        username=username,
        email=email,
        phone=phone,
        role=UserRole.CUSTOMER
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Đăng ký thành công"}), 201



@main.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    print("Dữ liệu nhận được từ frontend:", data)  # In ra toàn bộ JSON

    username = data.get("username")
    password = data.get("password")
    print("User nhập:", username)
    print("Password nhập:", password)

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        print("Đăng nhập thất bại: sai email hoặc mật khẩu")
        return jsonify({"error": "Sai email hoặc mật khẩu"}), 401

    access_token = create_access_token(identity=str(user.id))
    print("Đăng nhập thành công, tạo access token:", access_token)
    return jsonify({"access_token": access_token, "user": user.username}), 200


@main.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    user_id = get_jwt_identity()  # Lấy ID user từ token
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User không tồn tại"}), 404
    return jsonify({
        "username": user.username,
        "email": user.email,
        "phone": user.phone
    }), 200

@main.route("/products/search", methods=["GET"])
def search_products():
    keyword = request.args.get("q", "").strip()
    if not keyword:
        return jsonify([])

    results = Product.query.filter(Product.name.ilike(f"%{keyword}%")).all()

    return jsonify([
        {
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "images": [img.url for img in p.images],
            "category": p.category.name if p.category else None
        }
        for p in results
    ])

@main.route("/products/<int:product_id>")
def get_product_detail(product_id):
    product = Product.query.get_or_404(product_id)

    return jsonify({
        "id": product.id,
        "name": product.name,
        "price": product.price,  # Format tiền tệ
        "images": [img.url for img in product.images],
        "brand": product.brand,
        "category": product.category.name if product.category else None,

        # Thông số kỹ thuật
        "cpu": product.cpu,
        "ram": product.ram,
        "storage": product.storage,
        "screen": product.screen,
        "battery": product.battery,
        "os": product.os,
        "camera_front": product.camera_front,
        "camera_rear": product.camera_rear,
        "weight": product.weight,
        "color": product.color,
        "dimensions": product.dimensions,
        "release_date": product.release_date.strftime("%d/%m/%Y") if product.release_date else None,
        "graphics_card": product.graphics_card,
        "ports": product.ports,
        "warranty": product.warranty
    })

@main.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User không tồn tại"}), 404

    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    phone = data.get("phone")
    if username:
        user.username = username
    if email:
        # Kiểm tra email tồn tại chưa
        if User.query.filter(User.email == email, User.id != user_id).first():
            return jsonify({"error": "Email đã được sử dụng"}), 400
        user.email = email
    if phone:
        # Kiểm tra email tồn tại chưa
        if User.query.filter(User.phone == phone, User.id != user_id).first():
            return jsonify({"error": "Số điênj thoại đã được sử dụng"}), 400
        user.phone = phone
    db.session.commit()
    return jsonify({"message": "Cập nhật thành công"}), 200


@main.route('/api/buy', methods=['POST'])
def buy_now():
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        guest_name = data.get('guest_name')
        guest_phone = data.get('guest_phone')

        product = Product.query.get(product_id)
        if not product:
            return jsonify({"error": "Sản phẩm không tồn tại"}), 404

        total_price = product.price * quantity

        user_id = current_user.get_id() if current_user.is_authenticated else None

        # Nếu là khách nhưng không điền tên/SĐT → báo lỗi
        if not user_id and (not guest_name or not guest_phone):
            return jsonify({"error": "Vui lòng nhập tên và số điện thoại"}), 400

        # Tạo đơn hàng
        order = Order(
            user_id=user_id,
            guest_name=guest_name if not user_id else None,
            guest_phone=guest_phone if not user_id else None,
            total_price=total_price
        )

        db.session.add(order)
        db.session.commit()

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=product.price
        )

        db.session.add(order_item)
        db.session.commit()

        return jsonify({
            "message": "Đặt hàng thành công",
            "order_id": order.id,
            "is_guest": user_id is None
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main.route("/cart", methods=["GET"])
@jwt_required()
def get_cart():
    user_id = get_jwt_identity()
    cart_items = CartItem.query.filter_by(user_id=user_id).all()

    result = [
        {
            "id": item.id,
            "product_id": item.product.id,
            "name": item.product.name,
            "images": [img.url for img in item.product.images],
            "unit_price": item.product.price,
            "quantity": item.quantity,
            "total_price": item.quantity * item.product.price
        }
        for item in cart_items
    ]
    return jsonify(result), 200


@main.route("/cart/add", methods=["POST"])
@jwt_required()
def add_to_cart():
    user_id = get_jwt_identity()
    data = request.get_json()

    product_id = data.get("product_id")
    quantity = int(data.get("quantity", 1))

    if not product_id:
        return jsonify({"error": "Thiếu product_id"}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Sản phẩm không tồn tại"}), 404

    # Kiểm tra sản phẩm đã tồn tại trong giỏ hàng
    existing_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    if existing_item:
        existing_item.quantity += quantity
    else:
        new_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(new_item)

    db.session.commit()
    return jsonify({"message": "Thêm vào giỏ hàng thành công"}), 200


@main.route("/cart/update/<int:product_id>", methods=["PUT"])
@jwt_required()
def update_cart_item(product_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    quantity = int(data.get("quantity", 1))

    item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    if not item:
        return jsonify({"error": "Không tìm thấy mục giỏ hàng"}), 404

    item.quantity = quantity
    db.session.commit()
    return jsonify({"message": "Cập nhật số lượng thành công"}), 200



@main.route("/cart/delete/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete_cart_item(item_id):
    user_id = get_jwt_identity()

    # Lấy bản ghi CartItem theo id (item_id) và kiểm tra user_id
    item = CartItem.query.filter_by(id=item_id, user_id=user_id).first()
    if not item:
        return jsonify({"error": "Không tìm thấy mục giỏ hàng"}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Xóa khỏi giỏ hàng thành công"}), 200



