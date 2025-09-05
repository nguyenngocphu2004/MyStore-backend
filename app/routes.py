from flask import Blueprint, jsonify,make_response
from .models import Category, Product, User, UserRole, Order, OrderItem, CartItem, Comment, CommentVote, ProductImage, \
    Brand
from . import db
from flask import request
import uuid
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_jwt_extended import create_access_token
from functools import wraps
import os
from .utils import time_ago
import cloudinary
import cloudinary.uploader

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

@main.route("/brands", methods=["GET"])
def get_brands():
    brands = Brand.query.all()
    result = [
        {
            "id": b.id,
            "name": b.name,
        } for b in brands
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
            "brand": p.brand.name if p.brand else None,
            "stock": p.stock
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
        "brand": product.brand.name if product.brand else None,
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
@jwt_required(optional=True)
def buy_now():
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        guest_name = data.get('guest_name')
        guest_phone = data.get('guest_phone')
        address = data.get('address')
        delivery_method = data.get('delivery_method', 'store')

        product = Product.query.get(product_id)
        if not product:
            return jsonify({"error": "Sản phẩm không tồn tại"}), 404

        user_id = get_jwt_identity()

        if not user_id and (not guest_name or not guest_phone):
            return jsonify({"error": "Vui lòng nhập tên và số điện thoại"}), 400

        if delivery_method == "home" and not address:
            return jsonify({"error": "Vui lòng nhập địa chỉ giao hàng"}), 400

        order = Order(
            user_id=user_id,
            guest_name=guest_name if not user_id else None,
            guest_phone=guest_phone if not user_id else None,
            total_price=product.price * quantity,
            delivery_method=delivery_method,
            address=address if delivery_method == "home" else None
        )

        order_item = OrderItem(
            order=order,
            product_id=product.id,
            quantity=quantity,
            unit_price=product.price
        )

        db.session.add(order)
        db.session.add(order_item)
        db.session.commit()

        return jsonify({
            "message": "Đặt hàng thành công",
            "order": {
                "id": order.id,
                "total_price": order.total_price,
                "created_at": order.created_at.isoformat(),
                "items": [
                    {
                        "product_id": product.id,
                        "product_name": product.name,
                        "quantity": quantity,
                        "price": product.price
                    }
                ],
                "delivery_method": delivery_method,
                "address": order.address
            },
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

@main.route("/api/orders/guest", methods=["GET"])
def guest_orders():
    phone = request.args.get("phone")
    if not phone:
        return jsonify({"error": "Vui lòng nhập số điện thoại"}), 400

    orders = Order.query.filter_by(guest_phone=phone).all()
    if not orders:
        return jsonify([])

    data = []
    for order in orders:
        items = [
            {
                "product_name": item.product.name,
                "quantity": item.quantity,
                "unit_price": item.unit_price
            }
            for item in order.items
        ]
        data.append({
            "id": order.id,
            "total_price": order.total_price,
            "delivery_method": order.delivery_method,
            "address": order.address,
            "created_at": order.created_at.strftime("%Y-%m-%d %H:%M"),
            "items": items
        })

    return jsonify(data)


@main.route('/products/<int:product_id>/comments', methods=['GET'])
def get_comments(product_id):
    comments = Comment.query.filter_by(product_id=product_id).order_by(Comment.created_at.desc()).all()
    result = []
    total_rating = 0
    count_rating = 0
    for c in comments:
        result.append({
            "id": c.id,
            "username": c.user.username if c.user else None,
            "guest_name": c.guest_name,
            "guest_phone": c.guest_phone,
            "content": c.content,
            "rating": c.rating,
            "created_at": time_ago(c.created_at),
            "likes": c.likes,
        })
        if c.rating:
            total_rating += c.rating
            count_rating += 1
    average_rating = total_rating / count_rating if count_rating > 0 else 0
    return jsonify({
        "comments": result,
        "average_rating": average_rating
    })


@main.route('/products/<int:product_id>/comments', methods=['POST'])
@jwt_required(optional=True)   # Cho phép cả khách và user login
def add_comment(product_id):
    try:
        data = request.get_json()
        content = data.get("content")
        rating = data.get("rating")
        if not content:
            return jsonify({"error": "Nội dung không được để trống"}), 400

        # Mặc định là khách
        user_id = get_jwt_identity()
        guest_name = None
        guest_phone = None

        # Nếu là khách thì bắt buộc nhập tên và sđt
        if not user_id:
            guest_name = data.get("guest_name")
            guest_phone = data.get("guest_phone")
            if not guest_name or not guest_phone:
                return jsonify({"error": "Khách vãng lai phải nhập họ tên và số điện thoại"}), 400

        # Tạo comment
        comment = Comment(
            product_id=product_id,
            user_id=user_id,
            guest_name=guest_name,
            guest_phone=guest_phone,
            content=content,
            rating=rating
        )

        db.session.add(comment)
        db.session.commit()

        return jsonify({
            "message": "Bình luận thành công",
            "comment": {
                "id": comment.id,
                "username": comment.user.username if comment.user else None,
                "guest_name": comment.guest_name,
                "content": comment.content,
                "rating": comment.rating,
                "created_at": time_ago(comment.created_at),
                "likes": 0
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main.route("/comments/<int:comment_id>/vote", methods=["POST"])
@jwt_required(optional=True)  # Cho phép guest
def vote_comment(comment_id):
    data = request.get_json()
    action = data.get("action")
    if action not in ["like"]:
        return jsonify({"error": "Hành động không hợp lệ"}), 400

    comment = Comment.query.get_or_404(comment_id)

    user_id = get_jwt_identity()
    session_id = request.cookies.get("session_id")

    # Nếu guest chưa có session_id thì tạo mới
    if not user_id and not session_id:
        session_id = str(uuid.uuid4())

    # Kiểm tra đã vote
    if user_id:
        vote = CommentVote.query.filter_by(comment_id=comment.id, user_id=user_id).first()
    else:
        vote = CommentVote.query.filter_by(comment_id=comment.id, session_id=session_id).first()

    if vote:
        if vote.action == action:
            db.session.delete(vote)  # bấm lại -> hủy
        else:
            vote.action = action     # đổi like <-> dislike
    else:
        vote = CommentVote(
            comment_id=comment.id,
            user_id=user_id,
            session_id=session_id if not user_id else None,
            action=action
        )
        db.session.add(vote)

    db.session.commit()

    likes = CommentVote.query.filter_by(comment_id=comment.id, action="like").count()
    comment.likes = likes
    db.session.commit()
    resp = make_response(jsonify({"likes": likes}))
    # Nếu guest thì set cookie lưu lại session_id
    if not user_id:
        resp.set_cookie("session_id",
        session_id,
        httponly=True,
        max_age=60*60*24*30,  # 30 ngày
        samesite="None",      # 👈 cho phép cross-site
        secure=False)

    return resp

@main.route("/orders", methods=["GET"])
@jwt_required(optional=True)
def get_orders():
    user_id = get_jwt_identity()
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()

    result = []
    for o in orders:
        result.append({
            "id": o.id,
            "total_price": o.total_price,
            "created_at": o.created_at.isoformat(),
            "items": [
                {
                    "product_id": d.product_id,
                    "product_name": d.product.name,
                    "quantity": d.quantity,
                    "price": d.unit_price
                } for d in o.items
            ],
            "delivery_method": o.delivery_method,
            "address": o.address
        })

    return jsonify({"orders": result})

@main.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username, role=UserRole.ADMIN).first()
    if not user or not user.check_password(password) :
        return jsonify({"error": "Sai username hoặc password"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "username": user.username, "role": user.role.value})


def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or user.role != UserRole.ADMIN:
            return jsonify({"error": "Chỉ admin mới truy cập được"}), 403
        return fn(*args, **kwargs)
    return wrapper


@main.route("/admin/users", methods=["GET"])
@admin_required
def get_users():
    users = User.query.all()
    result = []
    for u in users:
        result.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role.value
        })
    return jsonify(result)


@main.route("/admin/products", methods=["POST"])
@admin_required
def create_product():
    data = request.get_json()
    try:
        product = Product(
            name=data.get("name"),
            price=float(data.get("price")),
            cost_price=float(data.get("cost_price")),
            stock=float(data.get("stock")),
            brand=data.get("brand"),
            category_id=int(data.get("category_id")),
            cpu=data.get("cpu"),
            ram=data.get("ram"),
            storage=data.get("storage"),
            screen=data.get("screen"),
            battery=data.get("battery"),
            os=data.get("os"),
            camera_front=data.get("camera_front"),
            camera_rear=data.get("camera_rear"),
            weight=data.get("weight"),
            color=data.get("color"),
            dimensions=data.get("dimensions"),
            release_date=data.get("release_date"),  # YYYY-MM-DD
            graphics_card=data.get("graphics_card"),
            ports=data.get("ports"),
            warranty=data.get("warranty")
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({"message": "Product created successfully", "id": product.id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@main.route("/admin/products/<int:product_id>/images", methods=["POST"])
@admin_required
def upload_product_images(product_id):
    product = Product.query.get_or_404(product_id)

    if 'images' not in request.files:
        return jsonify({"error": "No images provided"}), 400

    uploaded_files = request.files.getlist('images')  # list các file ảnh
    uploaded_urls = []

    for file in uploaded_files:
        result = cloudinary.uploader.upload(file, folder=f"products/{product.id}")
        img_url = result['secure_url']
        img = ProductImage(url=img_url, product_id=product.id)
        db.session.add(img)
        uploaded_urls.append(img_url)

    db.session.commit()
    return jsonify({"message": "Images uploaded", "urls": uploaded_urls}), 201


from sqlalchemy import func

@main.route("/admin/orders", methods=["GET"])
@admin_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()

    result = []
    total_revenue = 0

    for o in orders:
        items = [
            {
                "product_id": item.product_id,
                "product_name": item.product.name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.quantity * item.unit_price
            }
            for item in o.items
        ]
        order_total = sum([item['total_price'] for item in items])
        total_revenue += order_total

        result.append({
            "id": o.id,
            "user_id": o.user_id,
            "guest_name": o.guest_name,
            "guest_phone": o.guest_phone,
            "total_price": order_total,
            "delivery_method": o.delivery_method,
            "address": o.address,
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M"),
            "items": items
        })

    return jsonify({
        "orders": result,
        "total_revenue": total_revenue
    })

@main.route("/admin/products/<int:product_id>", methods=["PUT"])
@admin_required
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    for key in ["name","price","brand","category_id","cpu","ram","storage","screen",
                "battery","os","camera_front","camera_rear","weight","color","dimensions",
                "release_date","graphics_card","ports","warranty"]:
        if key in data:
            setattr(product, key, data[key])
    db.session.commit()
    return jsonify({"message": "Product updated successfully", "id": product.id})

# --- Xóa sản phẩm ---
@main.route("/admin/products/<int:product_id>", methods=["DELETE"])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted successfully"})

@main.route('/admin/dashboard')
def admin_dashboard():
    total_revenue = db.session.query(func.sum(Order.total_price)).scalar() or 0
    total_orders = db.session.query(func.count(Order.id)).scalar() or 0

    # Doanh thu theo tháng
    revenue_by_month = db.session.query(
        func.date_format(Order.created_at, "%Y-%m"),
        func.sum(Order.total_price)
    ).group_by(func.date_format(Order.created_at, "%Y-%m")).all()
    revenue_by_month = [[r[0], float(r[1])] for r in revenue_by_month]

    # Số lượng đơn hàng theo tháng
    orders_by_month = db.session.query(
        func.date_format(Order.created_at, "%Y-%m"),
        func.count(Order.id)
    ).group_by(func.date_format(Order.created_at, "%Y-%m")).all()
    orders_by_month = [[r[0], r[1]] for r in orders_by_month]

    # Số lượng sản phẩm theo brand
    products_by_brand = db.session.query(
        Brand.name,
        func.count(Product.id)
    ).join(Product, Brand.id == Product.brand_id) \
        .group_by(Brand.name).all()

    products_by_brand = [[r[0], r[1]] for r in products_by_brand]

    # Số lượng sản phẩm theo category
    products_by_category = db.session.query(
        Category.name,
        func.count(Product.id)
    ).join(Product, Category.id == Product.category_id) \
        .group_by(Category.name).all()

    products_by_category = [[r[0], r[1]] for r in products_by_category]

    # Doanh thu theo brand
    revenue_by_brand = db.session.query(
        Brand.name,
        func.sum(OrderItem.quantity * OrderItem.unit_price)
    ).join(Product, Brand.id == Product.brand_id) \
        .join(OrderItem, Product.id == OrderItem.product_id) \
        .join(Order, Order.id == OrderItem.order_id) \
        .group_by(Brand.name).all()

    revenue_by_brand = [[r[0], float(r[1])] for r in revenue_by_brand]

    # Doanh thu theo category
    revenue_by_category = db.session.query(
        Category.name,
        func.sum(OrderItem.quantity * OrderItem.unit_price)
    ).join(Product, Category.id == Product.category_id) \
        .join(OrderItem, Product.id == OrderItem.product_id) \
        .join(Order, Order.id == OrderItem.order_id) \
        .group_by(Category.name).all()

    revenue_by_category = [[r[0], float(r[1])] for r in revenue_by_category]

    return jsonify({
        "total_revenue": float(total_revenue),
        "total_orders": total_orders,
        "revenue_by_month": revenue_by_month,
        "orders_by_month": orders_by_month,
        "products_by_brand": products_by_brand,
        "products_by_category": products_by_category,
        "revenue_by_brand": revenue_by_brand,
        "revenue_by_category": revenue_by_category
    })


@main.route("/admin/profit")
@jwt_required()
def admin_profit():
    # Tổng doanh thu, chi phí, lợi nhuận
    totals = db.session.query(
        func.sum(OrderItem.unit_price * OrderItem.quantity),
        func.sum(Product.cost_price * OrderItem.quantity),
        func.sum((OrderItem.unit_price - Product.cost_price) * OrderItem.quantity),
    ).join(Product, Product.id == OrderItem.product_id).one()

    total_revenue = float(totals[0] or 0)
    total_cost = float(totals[1] or 0)
    total_profit = float(totals[2] or 0)

    # Theo tháng
    profit_by_month = db.session.query(
        func.date_format(Order.created_at, "%m"),
        func.sum(OrderItem.unit_price * OrderItem.quantity),
        func.sum(Product.cost_price * OrderItem.quantity),
        func.sum((OrderItem.unit_price - Product.cost_price) * OrderItem.quantity),
    ).join(OrderItem, Order.id == OrderItem.order_id)\
     .join(Product, Product.id == OrderItem.product_id)\
     .group_by(func.date_format(Order.created_at, "%m")).all()

    # Theo brand (join với bảng Brand)
    profit_by_brand = db.session.query(
        Brand.name,  # lấy tên brand thay vì id
        func.sum(OrderItem.unit_price * OrderItem.quantity),
        func.sum(Product.cost_price * OrderItem.quantity),
        func.sum((OrderItem.unit_price - Product.cost_price) * OrderItem.quantity),
    ).join(Product, Brand.id == Product.brand_id) \
        .join(OrderItem, Product.id == OrderItem.product_id) \
        .group_by(Brand.name).all()

    # Theo category (join bảng Category để lấy tên)
    profit_by_category = db.session.query(
        Category.name,
        func.sum(OrderItem.unit_price * OrderItem.quantity),
        func.sum(Product.cost_price * OrderItem.quantity),
        func.sum((OrderItem.unit_price - Product.cost_price) * OrderItem.quantity),
    ).join(Product, Category.id == Product.category_id)\
     .join(OrderItem, Product.id == OrderItem.product_id)\
     .group_by(Category.name).all()

    return jsonify({
        "totals": {
            "revenue": total_revenue,
            "cost": total_cost,
            "profit": total_profit
        },
        "profit_by_month": [[str(m), float(r or 0), float(c or 0), float(p or 0)] for m, r, c, p in profit_by_month],
        "profit_by_brand": [[b or "Không rõ", float(r or 0), float(c or 0), float(p or 0)] for b, r, c, p in profit_by_brand],
        "profit_by_category": [[cat or "Không rõ", float(r or 0), float(cst or 0), float(p or 0)] for cat, r, cst, p in profit_by_category],
    })


@main.route("/admin/categories", methods=["POST"])
@jwt_required()
def create_category():
    data = request.json
    if not data.get("name"):
        return jsonify({"error": "Tên danh mục không được để trống"}), 400
    c = Category(name=data["name"])
    db.session.add(c)
    db.session.commit()
    return jsonify({"id": c.id, "name": c.name})

@main.route("/admin/categories/<int:id>", methods=["PUT"])
@jwt_required()
def update_category(id):
    c = Category.query.get_or_404(id)
    data = request.json
    c.name = data.get("name", c.name)
    db.session.commit()
    return jsonify({"id": c.id, "name": c.name})

@main.route("/admin/categories/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_category(id):
    c = Category.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({"message": "Đã xóa danh mục"})

@main.route("/admin/brands", methods=["POST"])
@jwt_required()
def create_brand():
    data = request.json
    if not data.get("name"):
        return jsonify({"error": "Tên brand không được để trống"}), 400
    b = Brand(name=data["name"])
    db.session.add(b)
    db.session.commit()
    return jsonify({"id": b.id, "name": b.name})

@main.route("/admin/brands/<int:id>", methods=["PUT"])
@jwt_required()
def update_brand(id):
    b = Brand.query.get_or_404(id)
    data = request.json
    b.name = data.get("name", b.name)
    db.session.commit()
    return jsonify({"id": b.id, "name": b.name})

@main.route("/admin/brands/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_brand(id):
    b = Brand.query.get_or_404(id)
    db.session.delete(b)
    db.session.commit()
    return jsonify({"message": "Đã xóa brand"})