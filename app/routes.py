from flask import Blueprint, jsonify
from .models import Category, Product,User,UserRole
from . import db
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_jwt_extended import create_access_token
from datetime import datetime
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
            "image": p.image,
            "brand": p.brand,
            "category": p.category.name if p.category else None,
            "cpu": p.cpu,
            "ram": p.ram,
            "storage": p.storage,
            "screen": p.screen,
            "battery": p.battery,
            "os": p.os,
            "camera_front": p.camera_front,
            "camera_rear": p.camera_rear,
            "graphics_card": p.graphics_card,
            "weight": p.weight,
            "color": p.color,
            "dimensions": p.dimensions,
            "release_date": p.release_date.isoformat() if p.release_date else None,
            "ports": p.ports,
            "warranty": p.warranty,
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
            "image": p.image,
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
        "image": product.image,
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
