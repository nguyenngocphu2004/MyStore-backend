from flask import Blueprint, jsonify,make_response,request
from .models import (Category, Product, User, UserRole, Order, OrderItem, CartItem, Comment, CommentVote,
                    ProductImage,OrderStatus,Brand,OTP,DeliveryStatus,ExtraCost,StockIn,StockInLog,SearchHistory)
from . import db,mail
from sqlalchemy.orm import contains_eager
from sqlalchemy import case,func,or_
from flask_jwt_extended import jwt_required, get_jwt_identity,create_access_token
import os, requests, random,cloudinary,cloudinary.uploader,hashlib,hmac,uuid,re
from google.auth.transport import requests as google_requests
from .utils import time_ago,send_order_success_email,generate_unique_order_code,staff_required,admin_required,send_order_delivered_email
from datetime import datetime,timedelta
from flask_mail import Message
from google.oauth2 import id_token
from werkzeug.security import generate_password_hash,check_password_hash
from dotenv import load_dotenv
from .socket_events import clients_rooms
from math import ceil
load_dotenv()
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
main = Blueprint("main", __name__)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME =  os.getenv("GOOGLE_MODEL_NAME")
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"


MOMO_PARTNER_CODE = os.getenv("MOMO_PARTNER_CODE")
MOMO_ACCESS_KEY = os.getenv("MOMO_ACCESS_KEY")
MOMO_SECRET_KEY = os.getenv("MOMO_SECRET_KEY")
MOMO_ENDPOINT = os.getenv("MOMO_ENDPOINT")
MOMO_RETURN_URL = os.getenv("MOMO_RETURN_URL")
MOMO_NOTIFY_URL = os.getenv("MOMO_NOTIFY_URL")

ZALO_APP_ID = os.getenv("ZALO_APP_ID")
ZALO_KEY1 = os.getenv("ZALO_KEY1")
ZALO_KEY2 = os.getenv("ZALO_KEY2")
ZALO_CREATE_ORDER_URL = os.getenv("ZALO_CREATE_ORDER_URL")
ZALO_NOTIFY_URL = os.getenv("ZALO_NOTIFY_URL")


def is_comment_clean(content):
    prompt = f"""
    Hãy kiểm tra nội dung sau đây có chứa từ ngữ tục tĩu, lăng mạ, xúc phạm, quấy rối, phân biệt đối xử hoặc ngôn ngữ không phù hợp không.

    Trả lời chỉ bằng "YES" nếu nội dung phù hợp, "NO" nếu không phù hợp.

    Nội dung: "{content}"
    """

    try:
        headers = {"Content-Type": "application/json"}
        body = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }

        res = requests.post(ENDPOINT, headers=headers, json=body, timeout=20)
        res.raise_for_status()
        data = res.json()
        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        ).strip().upper()

        return text == "YES"
    except Exception as e:
        print("Gemini moderation error:", e)
        # Nếu không chắc chắn thì chặn để an toàn
        return False


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

@main.route("/brandss", methods=["GET"])
def get_brandss():
    brands = Brand.query.all()
    result = [
        {
            "id": b.id,
            "name": b.name,
        } for b in brands
    ]
    return jsonify(result)


@main.route("/brands", methods=["GET"])
def get_brands():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    search = request.args.get("search", "")
    brand_id = request.args.get("brand_id", None)

    query = Brand.query

    # Tìm kiếm theo tên
    if search:
        query = query.filter(Brand.name.ilike(f"%{search}%"))

    # Lọc theo brand_id
    if brand_id:
        query = query.filter(Brand.id == brand_id)

    # Phân trang
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    items = [{"id": b.id, "name": b.name} for b in pagination.items]

    return jsonify({
        "brands": items,
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_pages": pagination.pages,
            "total_items": pagination.total
        }
    })


@main.route("/products")
def get_products():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 8, type=int)
    search = request.args.get("search", "", type=str).strip()
    category = request.args.get("category", "", type=str).strip()
    brand = request.args.get("brand", "", type=str).strip()

    query = (
        db.session.query(
            Product,
            func.coalesce(
                func.sum(
                    case(
                        (Order.status == OrderStatus.PAID, OrderItem.quantity),
                        else_=0
                    )
                ),
                0
            ).label("sold")
        )
        .outerjoin(OrderItem, OrderItem.product_id == Product.id)
        .outerjoin(Order, Order.id == OrderItem.order_id)
        .group_by(Product.id)
    )

    # --- Lọc theo search ---
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    # --- Lọc theo category ---
    if category:
        query = query.join(Category).filter(Category.name == category)

    # --- Lọc theo brand ---
    if brand:
        query = query.join(Brand).filter(Brand.name == brand)

    total = query.count()

    products = (
        query.order_by(func.rand())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    result = []
    for p, sold in products:
        result.append({
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "cost_price": p.cost_price,
            "stock": p.stock,
            "category": p.category.name if p.category else None,
            "brand": p.brand.name if p.brand else None,
            "images": [img.url for img in p.images],
            "cpu": p.cpu,
            "ram": p.ram,
            "storage": p.storage,
            "screen": p.screen,
            "battery": p.battery,
            "os": p.os,
            "camera_front": p.camera_front,
            "camera_rear": p.camera_rear,
            "weight": p.weight,
            "color": p.color,
            "dimensions": p.dimensions,
            "release_date": p.release_date.strftime("%Y-%m-%d") if p.release_date else None,
            "graphics_card": p.graphics_card,
            "ports": p.ports,
            "warranty": p.warranty,
            "sold": sold
        })

    return jsonify({
        "products": result,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    })


@main.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    phone = data.get("phone")

    # Kiểm tra username/email/phone đã tồn tại chưa
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
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Đăng nhập thất bại: sai tên tài khoản hoặc mật khẩu"}), 401

    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        "access_token": access_token,
        "user": user.username,
        "role": user.role.value   # Thêm dòng này
    }), 200


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

    sold = (
        db.session.query(func.coalesce(func.sum(OrderItem.quantity), 0))
        .join(Order, Order.id == OrderItem.order_id)
        .filter(OrderItem.product_id == product.id)
        .filter(Order.status == OrderStatus.PAID)
        .scalar()
    )

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
    email = data.get("email")
    phone = data.get("phone")
    if email:
        # Kiểm tra email tồn tại chưa
        if User.query.filter(User.email == email, User.id != user_id).first():
            return jsonify({"error": "Email đã được sử dụng"}), 400
        user.email = email
    if phone:
        # Kiểm tra email tồn tại chưa
        if User.query.filter(User.phone == phone, User.id != user_id).first():
            return jsonify({"error": "Số điện thoại đã được sử dụng"}), 400
        user.phone = phone
    db.session.commit()
    return jsonify({"message": "Cập nhật thành công"}), 200


@main.route('/buy', methods=['POST'])
@jwt_required(optional=True)
def buy_now():
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        guest_name = data.get('guest_name')
        guest_phone = data.get('guest_phone')
        guest_email = data.get('guest_email')
        address = data.get('address')
        delivery_method = data.get('delivery_method', 'store')

        product = Product.query.get(product_id)
        if not product:
            return jsonify({"error": "Sản phẩm không tồn tại"}), 404
        if quantity > product.stock:
            return jsonify({
                "error": f"Số lượng đặt vượt quá tồn kho. Hiện có {int(product.stock)} sản phẩm."
            }), 400
        user_id = get_jwt_identity()

        if not user_id and (not guest_name or not guest_phone):
            return jsonify({"error": "Vui lòng nhập tên và số điện thoại"}), 400

        if delivery_method == "home" and not address:
            return jsonify({"error": "Vui lòng nhập địa chỉ giao hàng"}), 400

        order = Order(
            user_id=user_id,
            guest_name=guest_name if not user_id else None,
            guest_phone=guest_phone if not user_id else None,
            guest_email=guest_email if not user_id else None,
            total_price=product.price * quantity,
            delivery_method=delivery_method,
            address=address if delivery_method == "home" else None,
            order_code=generate_unique_order_code(),
            status=OrderStatus.PENDING
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

@main.route("/orders/guest", methods=["POST"])
def guest_orders():
    data = request.get_json()
    print("Dữ liệu nhận từ client:", data)
    phone = data.get("phone")
    otp = data.get("otp")

    if not phone or not otp:
        return jsonify({"error": "Thiếu số điện thoại hoặc OTP"}), 400

    # Kiểm tra OTP trong DB
    otp_entry = OTP.query.filter_by(phone=phone).first()
    if not otp_entry or not otp_entry.is_valid(otp):
        return jsonify({"error": "OTP không hợp lệ hoặc đã hết hạn"}), 400

    # Lấy đơn hàng
    orders = Order.query.filter_by(guest_phone=phone).all()
    if not orders:
        return jsonify([])

    data = []
    for order in orders:
        data.append({
            "id": order.id,
            "total_price": order.total_price,
            "delivery_method": order.delivery_method,
            "address": order.address,
            "created_at": order.created_at,
            "delivery_status": order.delivery_status.value,
            "status": order.status.value,
            "order_code": order.order_code,
            "items": [
                {
                    "product_name": item.product.name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price
                }
                for item in order.items
            ]
        })

    db.session.delete(otp_entry)
    db.session.commit()
    return jsonify(data)


@main.route('/products/<int:product_id>/comments', methods=['GET'])
@jwt_required(optional=True)
def get_comments(product_id):
    user_id = get_jwt_identity()
    session_id = request.cookies.get("session_id")

    comments = Comment.query.filter_by(product_id=product_id)

    # Nếu là guest, chỉ trả comment mà guest_phone đã từng mua sản phẩm
    if not user_id and session_id:
        # Lấy danh sách số điện thoại đã mua sản phẩm này
        purchased_phones = db.session.query(Order.guest_phone)\
            .join(OrderItem)\
            .filter(OrderItem.product_id == product_id)\
            .distinct().all()
        purchased_phones = [p[0] for p in purchased_phones]

        comments = comments.filter(Comment.guest_phone.in_(purchased_phones))

    comments = comments.order_by(Comment.created_at.desc()).all()

    result = []
    total_rating = 0
    count_rating = 0
    for c in comments:
        result.append({
            "id": c.id,
            "username": c.user.username if c.user else None,
            "guest_name": c.guest_name,
            "content": c.content,
            "rating": c.rating,
            "admin_reply": c.admin_reply,
            "created_at": time_ago(c.created_at),
            "reply_at": time_ago(c.reply_at) if c.reply_at else None,
            "likes": c.likes or 0,
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
@jwt_required(optional=True)  # cho phép guest
def add_comment(product_id):
    try:
        data = request.get_json()
        content = data.get("content")
        if not is_comment_clean(content):
            return jsonify({"error": "Nội dung bình luận không phù hợp. Vui lòng điều chỉnh lại."}), 400
        rating = data.get("rating")
        if not content:
            return jsonify({"error": "Nội dung không được để trống"}), 400

        user_id = get_jwt_identity()
        guest_name = data.get("guest_name")
        guest_phone = data.get("guest_phone")
        # Nếu user login
        if user_id:
            user = User.query.get(user_id)
            if user.role in [UserRole.ADMIN, UserRole.STAFF]:
                purchased = True
            else:
                purchased = (
                    db.session.query(OrderItem)
                    .join(Order)
                    .filter(
                        Order.user_id == user_id,
                        OrderItem.product_id == product_id,
                    )
                    .first()
                )
                if not purchased:
                    return jsonify({"error": "Bạn phải mua sản phẩm này mới được bình luận"}), 403
        else:
            if not guest_name or not guest_phone:
                return jsonify({"error": "Khách vãng lai phải nhập họ tên và số điện thoại"}), 400

            purchased = (
                db.session.query(OrderItem)
                .join(Order)
                .filter(
                    Order.guest_phone == guest_phone,
                    OrderItem.product_id == product_id,
                )
                .first()
            )
            if not purchased:
                return jsonify({"error": "Số điện thoại này chưa mua sản phẩm, không thể bình luận"}), 403

        # Tạo comment
        comment = Comment(
            product_id=product_id,
            user_id=user_id,
            guest_name=guest_name if not user_id else None,
            guest_phone=guest_phone if not user_id else None,
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
        max_age=60*60*24*30,
        samesite="None",
        secure=False)

    return resp


@main.route("/orders", methods=["GET"])
@jwt_required(optional=True)
def get_orders():
    user_id = get_jwt_identity()

    # Lấy page và per_page từ query params, mặc định page=1, per_page=5
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 5))

    orders_query = Order.query.filter(
        Order.user_id == user_id,
        Order.status.in_([OrderStatus.PAID, OrderStatus.PENDING, OrderStatus.CANCELED])
    ).order_by(Order.created_at.desc())

    # Dùng paginate
    pagination = orders_query.paginate(page=page, per_page=per_page, error_out=False)

    result = []
    for o in pagination.items:
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
            "address": o.address,
            "status": o.status.value,
            "delivery_status": o.delivery_status.value,
            "payment_method": o.payment_method,
            "order_code": o.order_code
        })

    return jsonify({
        "orders": result,
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total_pages": pagination.pages
    })


@main.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if not user or user.role not in [UserRole.ADMIN, UserRole.STAFF] or not user.check_password(password):
        return jsonify({"error": "Sai username hoặc password"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "username": user.username, "role": user.role.value})


@main.route("/admin/users", methods=["GET"])
@staff_required
def get_users():
    # Lấy page và per_page từ query string (vd: /admin/users?page=2&per_page=10)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    search = request.args.get("search", "").strip()
    role = request.args.get("role", "").strip()
    query = User.query
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )
    if role:
        query = query.filter(User.role == role)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    users = []
    for u in pagination.items:
        users.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role.value
        })

    return jsonify({
        "users": users,
        "total": pagination.total,        # tổng số user
        "pages": pagination.pages,        # tổng số trang
        "current_page": pagination.page,  # trang hiện tại
        "per_page": pagination.per_page   # số lượng user mỗi trang
    })


@main.route("/admin/users", methods=["POST"])
@admin_required
def create_user():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "CUSTOMER")

    # Kiểm tra trùng
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username đã tồn tại"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email đã tồn tại"}), 400

    # Tạo user
    user = User(username=username, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value
    }), 201

@main.route("/admin/users/<int:user_id>", methods=["PUT"])
@staff_required
def update_user(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    user = User.query.get_or_404(user_id)

    data = request.get_json()

    if current_user.role == UserRole.STAFF and user.role == UserRole.ADMIN:
        return jsonify({"error": "Không có quyền sửa tài khoản ADMIN"}), 403

    if "username" in data:
        user.username = data["username"]
    if "email" in data:
        user.email = data["email"]
    if "role" in data:
        user.role = data["role"]
    if "password" in data and data["password"].strip():
        user.set_password(data["password"])

    db.session.commit()
    return jsonify({"message": "Cập nhật user thành công"}), 200

@main.route("/admin/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Xóa user thành công"}), 200



@main.route("/admin/products", methods=["POST"])
@admin_required
def create_product():
    data = request.get_json()
    try:
        product = Product(
            name=data.get("name"),
            price=float(data.get("price")),
            cost_price=float(data.get("cost_price")),
            stock=int(data.get("stock")),
            brand_id=int(data.get("brand_id")),
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


@main.route("/admin/orders", methods=["GET"])
@staff_required
def admin_get_orders():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    search = request.args.get("search", "", type=str)

    query = Order.query

    if search:
        query = query.join(User, isouter=True).options(contains_eager(Order.user)).filter(
            or_(
                User.phone.ilike(f"%{search}%"),
                Order.guest_phone.ilike(f"%{search}%")
            )
        )

    pagination = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    orders = pagination.items

    result = []
    for o in orders:
        result.append({
            "id": o.id,
            "user": {
                "username": o.user.username,
                "phone": o.user.phone
            } if o.user else None,
            "guest_name": o.guest_name,
            "guest_phone": o.guest_phone,
            "created_at": o.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "total_price": o.total_price,
            "delivery_method": o.delivery_method,
            "delivery_status": o.delivery_status.value,
            "address": o.address,
            "items_count": len(o.items),
            "status": o.status.value,
            "payment_method": o.payment_method,
            "order_code": o.order_code
        })

    return jsonify({
        "orders": result,
        "page": pagination.page,
        "pages": pagination.pages,
        "total": pagination.total
    })

@main.route("/admin/orders/<int:order_id>/delivery_status", methods=["PUT"])
@staff_required
def update_delivery_status(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    new_status = data.get("delivery_status")

    if new_status not in DeliveryStatus.__members__:
        return jsonify({"error": "Trạng thái giao hàng không hợp lệ"}), 400

    if new_status == "DELIVERED":
        return jsonify({"error": "Admin không được phép đặt trạng thái là Đã giao"}), 403


    order.delivery_status = DeliveryStatus[new_status]
    db.session.commit()

    return jsonify({
        "id": order.id,
        "delivery_status": order.delivery_status.value
    })


@main.route("/admin/orders/<int:order_id>", methods=["GET"])
def admin_get_order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    items = []
    for item in order.items:
        product_name = item.product.name if item.product else "Sản phẩm đã xóa"
        items.append({
            "product_name": product_name,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total_price": item.quantity * item.unit_price
        })

    user_info = None
    if order.user:
        user_info = {
            "username": order.user.username,
            "phone": order.user.phone
        }

    return jsonify({
        "id": order.id,
        "user": user_info,
        "guest_name": order.guest_name,
        "guest_phone": order.guest_phone,
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "total_price": order.total_price,
        "delivery_method": order.delivery_method,
        "address": order.address,
        "delivery_status": order.delivery_status.value,
        "items": items,
        "payment_method": order.payment_method,
        "order_code": order.order_code
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
@staff_required
def admin_dashboard():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 3))
    month = request.args.get("month")  # format: "YYYY-MM"

    # ========================
    # Tổng doanh thu & đơn hàng
    # ========================
    total_query = Order.query.filter(Order.status == 'PAID')
    if month:
        year, month_num = map(int, month.split("-"))
        total_query = total_query.filter(
            func.extract('year', Order.created_at) == year,
            func.extract('month', Order.created_at) == month_num
        )

    total_revenue = total_query.with_entities(func.sum(Order.total_price)).scalar() or 0
    total_orders = total_query.with_entities(func.count(Order.id)).scalar() or 0

    # ========================
    # Doanh thu & đơn hàng theo tháng
    # ========================
    if month:
        # Chỉ 1 tháng -> không phân trang
        revenue_by_month = [[month, float(total_revenue)]]
        orders_by_month = [[month, total_orders]]
        total_months = 1
    else:
        # Query tất cả các tháng đã có đơn -> phân trang
        query_revenue = db.session.query(
            func.date_format(Order.created_at, "%Y-%m"),
            func.sum(Order.total_price)
        ).filter(Order.status == 'PAID') \
         .group_by(func.date_format(Order.created_at, "%Y-%m")) \
         .order_by(func.date_format(Order.created_at, "%Y-%m").desc())

        total_months = query_revenue.count()
        revenue_by_month = query_revenue.limit(per_page).offset((page - 1) * per_page).all()
        revenue_by_month = [[r[0], float(r[1])] for r in revenue_by_month]

        query_orders = db.session.query(
            func.date_format(Order.created_at, "%Y-%m"),
            func.count(Order.id)
        ).filter(Order.status == 'PAID') \
         .group_by(func.date_format(Order.created_at, "%Y-%m")) \
         .order_by(func.date_format(Order.created_at, "%Y-%m").desc())
        orders_by_month = query_orders.limit(per_page).offset((page - 1) * per_page).all()
        orders_by_month = [[r[0], r[1]] for r in orders_by_month]

    # ========================
    # Sản phẩm theo brand
    # ========================
    products_by_brand = db.session.query(
        Brand.name, func.count(Product.id)
    ).join(Product, Brand.id == Product.brand_id) \
     .group_by(Brand.name).all()
    products_by_brand = [[r[0], r[1]] for r in products_by_brand]

    # Sản phẩm theo category
    products_by_category = db.session.query(
        Category.name, func.count(Product.id)
    ).join(Product, Category.id == Product.category_id) \
     .group_by(Category.name).all()
    products_by_category = [[r[0], r[1]] for r in products_by_category]

    # Doanh thu theo brand
    revenue_by_brand = db.session.query(
        Brand.name, func.sum(OrderItem.quantity * OrderItem.unit_price)
    ).join(Product, Brand.id == Product.brand_id) \
     .join(OrderItem, Product.id == OrderItem.product_id) \
     .join(Order, Order.id == OrderItem.order_id) \
     .filter(Order.status == 'PAID') \
     .group_by(Brand.name).all()
    revenue_by_brand = [[r[0], float(r[1])] for r in revenue_by_brand]

    # Doanh thu theo category
    revenue_by_category = db.session.query(
        Category.name, func.sum(OrderItem.quantity * OrderItem.unit_price)
    ).join(Product, Category.id == Product.category_id) \
     .join(OrderItem, Product.id == OrderItem.product_id) \
     .join(Order, Order.id == OrderItem.order_id) \
     .filter(Order.status == 'PAID') \
     .group_by(Category.name).all()
    revenue_by_category = [[r[0], float(r[1])] for r in revenue_by_category]

    # ========================
    # Trả dữ liệu JSON
    # ========================
    return jsonify({
        "total_revenue": float(total_revenue),
        "total_orders": total_orders,
        "revenue_by_month": revenue_by_month,
        "orders_by_month": orders_by_month,
        "products_by_brand": products_by_brand,
        "products_by_category": products_by_category,
        "revenue_by_brand": revenue_by_brand,
        "revenue_by_category": revenue_by_category,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_months": total_months,
            "total_pages": (total_months + per_page - 1) // per_page
        }
    })


@main.route("/admin/profit")
@jwt_required()
def admin_profit():
    """
    API lấy dữ liệu lợi nhuận theo tháng, hỗ trợ:
    - tìm kiếm theo tháng (month=YYYY-MM)
    - phân trang (page, per_page)
    """
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 5))
    month_filter = request.args.get("month")  # YYYY-MM

    # Truy vấn cơ bản: doanh thu, chi phí, lợi nhuận gốc
    query = db.session.query(
        func.date_format(Order.created_at, "%Y-%m"),
        func.sum(OrderItem.unit_price * OrderItem.quantity),
        func.sum(Product.cost_price * OrderItem.quantity),
        func.sum((OrderItem.unit_price - Product.cost_price) * OrderItem.quantity)
    ).join(OrderItem, Order.id == OrderItem.order_id) \
     .join(Product, Product.id == OrderItem.product_id) \
     .filter(Order.status == 'PAID')

    if month_filter:
        year, month = month_filter.split("-")
        query = query.filter(
            func.extract("year", Order.created_at) == int(year),
            func.extract("month", Order.created_at) == int(month)
        )

    query = query.group_by(func.date_format(Order.created_at, "%Y-%m")) \
                 .order_by(func.date_format(Order.created_at, "%Y-%m").desc())

    # Tính tổng số tháng để phân trang
    total_months = query.count()
    total_pages = (total_months + per_page - 1) // per_page

    # Phân trang
    profit_by_month = query.offset((page - 1) * per_page).limit(per_page).all()

    # Lấy chi phí bổ sung từ ExtraCost
    result = []
    for m, r, c, p in profit_by_month:
        extra = ExtraCost.query.filter_by(month=str(m)).first()
        staff = extra.staff if extra else 0
        rent = extra.rent if extra else 0
        living = extra.living if extra else 0
        other = extra.other if extra else 0
        total_extra = staff + rent + living + other
        total_cost = c + total_extra
        profit_new = r - total_cost

        result.append([
            str(m), float(r or 0), float(c or 0), float(p or 0),
            float(staff), float(rent), float(living), float(other),
            float(total_cost), float(profit_new)
        ])

    return jsonify({
        "profit_by_month": result,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_months": total_months,
            "total_pages": total_pages
        }
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
@staff_required
def delete_category(id):
    c = Category.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({"message": "Đã xóa danh mục"})

@main.route("/admin/brands", methods=["POST"])
@staff_required
def create_brand():
    data = request.json
    if not data.get("name"):
        return jsonify({"error": "Tên brand không được để trống"}), 400
    b = Brand(name=data["name"])
    db.session.add(b)
    db.session.commit()
    return jsonify({"id": b.id, "name": b.name})

@main.route("/admin/brands/<int:id>", methods=["PUT"])
@staff_required
def update_brand(id):
    b = Brand.query.get_or_404(id)
    data = request.json
    b.name = data.get("name", b.name)
    db.session.commit()
    return jsonify({"id": b.id, "name": b.name})

@main.route("/admin/brands/<int:id>", methods=["DELETE"])
@staff_required
def delete_brand(id):
    b = Brand.query.get_or_404(id)
    db.session.delete(b)
    db.session.commit()
    return jsonify({"message": "Đã xóa brand"})

@main.route("/comments/<int:comment_id>/reply", methods=["POST"])
@staff_required
def reply_comment(comment_id):
    data = request.json
    reply_content = data.get("content")

    if not reply_content:
        return jsonify({"error": "Nội dung trả lời không được để trống"}), 400

    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({"error": "Không tìm thấy bình luận"}), 404
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    # Lưu trả lời vào cột admin_reply
    comment.admin_reply = reply_content
    comment.reply_at = datetime.now()
    comment.reply_role = user.role.value
    db.session.commit()

    return jsonify({
        "message": "Trả lời thành công",
        "reply": {
            "admin_reply": comment.admin_reply,
            "reply_at": time_ago(comment.reply_at),
            "reply_role": comment.reply_role
        }
    })


@main.route("/admin/sales_by_product", methods=["GET"])
@staff_required
def sales_by_product():
    from sqlalchemy import func

    results = (
        db.session.query(
            Product.id,
            Product.name,
            Product.stock,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("total_sold"),
            Category.name.label("category_name")
        )
        .outerjoin(OrderItem, Product.id == OrderItem.product_id)
        .outerjoin(Order, Order.id == OrderItem.order_id)
        .outerjoin(Category, Product.category_id == Category.id)
        .filter((Order.id == None) | (Order.status == OrderStatus.PAID))
        .group_by(Product.id, Category.name)
        .all()
    )

    # Gom sản phẩm theo danh mục
    categories = {}
    for r in results:
        total_sold = int(r[3] or 0)
        if total_sold >= 50:
            status = "Bán chạy"
        elif total_sold >= 20:
            status = "Bình thường"
        else:
            status = "Bán chậm"

        product_data = {
            "id": r[0],
            "name": r[1],
            "stock": r[2],
            "total_sold": total_sold,
            "status": status
        }

        cat_name = r[4] or "Khác"
        if cat_name not in categories:
            categories[cat_name] = []
        categories[cat_name].append(product_data)

    return jsonify(categories)



@main.route("/api/create_momo_payment/<int:order_id>", methods=["POST"])
def create_momo_payment(order_id):
    order = Order.query.get_or_404(order_id)
    order.payment_method = "MOMO"
    db.session.commit()
    if order.status != OrderStatus.PENDING:
        return jsonify({"error": "Đơn hàng đã được thanh toán hoặc hủy"}), 400

    amount = int(order.total_price)
    order_info = f"Thanh toán đơn hàng #{order.id}"
    request_id = str(uuid.uuid4())
    momo_order_id = str(uuid.uuid4())  # orderId riêng cho Momo

    order.momo_order_id = momo_order_id
    db.session.commit()

    raw_signature = f"accessKey={MOMO_ACCESS_KEY}&amount={amount}&extraData=&ipnUrl={MOMO_NOTIFY_URL}&orderId={momo_order_id}&orderInfo={order_info}&partnerCode={MOMO_PARTNER_CODE}&redirectUrl={MOMO_RETURN_URL}&requestId={request_id}&requestType=captureWallet"
    signature = hmac.new(bytes(MOMO_SECRET_KEY, 'utf-8'), bytes(raw_signature, 'utf-8'), hashlib.sha256).hexdigest()

    payload = {
        "partnerCode": MOMO_PARTNER_CODE,
        "accessKey": MOMO_ACCESS_KEY,
        "requestId": request_id,
        "amount": str(amount),
        "orderId": momo_order_id,
        "orderInfo": order_info,
        "redirectUrl": MOMO_RETURN_URL,
        "ipnUrl": MOMO_NOTIFY_URL,
        "extraData": "",
        "requestType": "captureWallet",
        "signature": signature
    }

    resp = requests.post(MOMO_ENDPOINT, json=payload)
    data = resp.json()

    if data.get("payUrl"):
        return jsonify({"payUrl": data["payUrl"]})
    else:
        return jsonify({"error": data.get("message", "Không tạo được link thanh toán")}), 400


# Callback từ Momo
@main.route("/api/payment_callback/<string:order_id>", methods=["POST"])
def payment_callback_confirm(order_id):
    result_code = int(request.args.get("resultCode", -1))
    order = Order.query.filter_by(momo_order_id=order_id).first()  # vì orderId của Momo là UUID
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order.status == OrderStatus.PENDING:
        if result_code == 0:
            # Thanh toán thành công
            order.status = OrderStatus.PAID
            order.delivery_status = DeliveryStatus.PROCESSING

            # Giảm stock từng sản phẩm
            for item in order.items:  # giả sử order.items liên kết đến OrderItem
                product = Product.query.get(item.product_id)
                if product:
                    product.stock -= item.quantity
                    if product.stock < 0:
                        product.stock = 0  # tránh stock âm
            db.session.commit()
            if order.user and order.user.email:
                send_order_success_email(order.user.email, order, is_cod=False)
            elif order.guest_email:
                send_order_success_email(order.guest_email, order, is_cod=False)
        else:
            # Thanh toán thất bại
            order.status = OrderStatus.FAILED

        db.session.commit()

    return jsonify({
        "orderId": order.id,
        "status": order.status.value
    })


# Lấy thông tin đơn hàng
@main.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify({
        "id": order.id,
        "total_price": order.total_price,
        "status": order.status.value,
        "items": [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price
            } for item in order.items
        ]
    })

@main.route("/create_order_from_cart", methods=["POST"])
@jwt_required()
def create_order_from_cart():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Dữ liệu không hợp lệ"}), 400

    selected_products = data.get("products")

    if len(selected_products) == 0:
        return jsonify({"error": "Danh sách sản phẩm rỗng"}), 400

    product_ids = [item["product_id"] for item in selected_products]
    products = Product.query.filter(Product.id.in_(product_ids)).all()
    product_map = {p.id: p for p in products}

    total_price = 0
    for item in selected_products:
        pid = item["product_id"]
        quantity = item["quantity"]
        product = product_map.get(pid)
        if not product:
            return jsonify({"error": f"Sản phẩm ID {pid} không tồn tại"}), 400
        total_price += quantity * product.price

    # Tạo đơn hàng
    order = Order(
        user_id=user_id,
        total_price=total_price,
        status=OrderStatus.PENDING,
        order_code=generate_unique_order_code(),
    )

    db.session.add(order)
    db.session.flush()  # để lấy order.id

    # Tạo từng chi tiết đơn hàng
    for item in selected_products:
        product = product_map[item["product_id"]]
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item["quantity"],
            unit_price=product.price
        )
        db.session.add(order_item)

    CartItem.query.filter(
        CartItem.user_id == user_id,
        CartItem.product_id.in_(product_ids)
    ).delete(synchronize_session=False)
    db.session.commit()
    return jsonify({"order_id": order.id, "total_price": total_price}), 201


@main.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.get_json()
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Message is required"}), 400

    try:
        # ===== 1️⃣ NẠP NGỮ CẢNH TỪ DATABASE =====
        products = Product.query.join(Brand).join(Category).all()
        product_context = "\n".join([
            f"- {p.name} ({p.category.name if p.category else 'Không rõ'} - {p.brand.name if p.brand else 'Không rõ'}): "
            f"Giá {p.price:,.0f}₫, RAM {p.ram}, CPU {p.cpu}, bộ nhớ {p.storage}, "
            f"màn hình {p.screen}, pin {p.battery}, màu {p.color}."
            for p in products[:30]
        ])

        context_prompt = f"""
        Bạn là chatbot tư vấn bán hàng của Cửa hàng điện tử PhuStore.
        - Địa chỉ: 35c đường 109, Phước Long B, Quận 9, TP.HCM.
        - Bảo hành sản phẩm: 12 tháng tiêu chuẩn, đổi mới 7 ngày nếu lỗi nhà sản xuất.
        - Sản phẩm gồm: điện thoại, laptop và phụ kiện công nghệ.
        - Khi được hỏi về giá, sản phẩm, thương hiệu → hãy trả lời dựa trên dữ liệu có sẵn bên dưới.
        - Nếu người dùng hỏi các câu xã giao (như “khỏe không”, “hôm nay ngày mấy”, “bạn là ai”) → hãy trả lời thân thiện, ngắn gọn.
        - Nếu câu hỏi không liên quan đến sản phẩm → vẫn cố gắng trả lời một cách tự nhiên.
        - Hotline: 0123456789

        Dưới đây là dữ liệu sản phẩm trong cửa hàng:
        {product_context}

        Câu hỏi của khách hàng: {message}
        """

        headers = {"Content-Type": "application/json"}
        body = {
            "contents": [
                {
                    "parts": [
                        {"text": context_prompt}
                    ]
                }
            ]
        }

        # ===== 3️⃣ GỌI GEMINI API =====
        response = requests.post(ENDPOINT, headers=headers, json=body, timeout=25)
        response.raise_for_status()

        data = response.json()
        reply = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        if not reply:
            reply = "Xin lỗi, tôi chưa hiểu câu hỏi của bạn. Bạn có thể nói rõ hơn không ạ?"

        return jsonify({"response": reply})

    except Exception as e:
        print("Lỗi chatbot:", e)
        return jsonify({"response": "Có lỗi xảy ra, vui lòng thử lại sau."}), 500


def mask_email(email):
    parts = email.split("@")
    if len(parts[0]) <= 3:
        masked = parts[0][0] + "***"
    else:
        masked = parts[0][:3] + "***"
    return masked + "@" + parts[1]


@main.route("/request-otp", methods=["POST"])
def request_otp():
    data = request.get_json()
    phone = data.get("phone")
    otp_type = data.get("type", "order_lookup")  # 'password_reset' hoặc 'order_lookup'

    if not phone:
        return jsonify({"error": "Vui lòng nhập số điện thoại"}), 400

    if otp_type == "password_reset":
        user = User.query.filter_by(phone=phone).first()
        if not user or not user.email:
            return jsonify({"error": "Không tìm thấy email cho số điện thoại này"}), 404
        email = user.email
    else:
        order = Order.query.filter_by(guest_phone=phone).first()
        if not order or not order.guest_email:
            return jsonify({"error": "Không tìm thấy email cho số điện thoại này"}), 404
        email = order.guest_email

    # Tạo OTP và expiry
    otp_code = str(random.randint(100000, 999999))
    expiry = datetime.now() + timedelta(minutes=5)

    # Xoá OTP cũ nếu có
    OTP.query.filter_by(phone=phone).delete()

    # Lưu OTP mới
    otp_entry = OTP(phone=phone, otp_code=otp_code, expiry=expiry)
    db.session.add(otp_entry)
    db.session.commit()

    # Gửi mail OTP
    try:
        msg = Message(
            subject="Mã OTP xác thực",
            recipients=[email],
            body=f"Mã OTP của bạn là: {otp_code}\nMã có hiệu lực trong 5 phút."
        )
        mail.send(msg)
    except Exception as e:
        return jsonify({"error": f"Gửi email thất bại: {str(e)}"}), 500

    return jsonify({
        "message": "OTP đã được gửi đến email",
        "masked_email": mask_email(email)
    }), 200

def make_app_trans_id(order_id):
    date_str = datetime.now().strftime("%y%m%d")
    rand_suffix = random.randint(1000, 9999)
    return f"{date_str}_{order_id}_{rand_suffix}"


@main.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json()
    phone = data.get("phone")
    code = data.get("otp")

    if not phone or not code:
        return jsonify({"error": "Vui lòng nhập đủ thông tin"}), 400

    otp_entry = OTP.query.filter_by(phone=phone).first()
    print(f"OTP from DB: {otp_entry.otp_code}, OTP input: {code}")
    print(f"Now: {datetime.now()}, Expiry: {otp_entry.expiry}")
    if not otp_entry or not otp_entry.is_valid(code):
        return jsonify({"error": "Mã OTP không hợp lệ hoặc đã hết hạn"}), 400

    return jsonify({"message": "Xác thực OTP thành công"}), 200


@main.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    phone = data.get("phone")
    otp_code = data.get("otp")
    new_password = data.get("password")

    if not phone or not otp_code or not new_password:
        return jsonify({"error": "Vui lòng nhập đủ thông tin"}), 400

    otp_entry = OTP.query.filter_by(phone=phone).first()
    if not otp_entry or not otp_entry.is_valid(otp_code):
        return jsonify({"error": "Mã OTP không hợp lệ hoặc đã hết hạn"}), 400

    user = User.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({"error": "Người dùng không tồn tại"}), 404

    user.set_password(new_password)
    db.session.delete(otp_entry)  # Xóa OTP sau khi sử dụng
    db.session.commit()

    return jsonify({"message": "Đổi mật khẩu thành công"}), 200


@main.route("/google-login", methods=["POST"])
def google_login():
    data = request.get_json()
    id_token_received = data.get("token")
    if not id_token_received:
        return jsonify({"error": "Thiếu id_token"}), 400

    try:
        # Dùng Request() của google.auth.transport
        idinfo = id_token.verify_oauth2_token(
            id_token_received,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )

        email = idinfo.get("email")
        sub = idinfo.get("sub")

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                username=email.split("@")[0],
                email=email,
                role=UserRole.CUSTOMER,
                password_hash=generate_password_hash(sub),
            )
            db.session.add(user)
            db.session.commit()

        access_token = create_access_token(identity=str(user.id))

        return jsonify({
            "access_token": access_token,
            "username": user.username,
            "email": user.email,
            "role": user.role.value
        })
    except ValueError:
        return jsonify({"error": "Token không hợp lệ"}), 400

@main.route("/api/pay_cod/<int:order_id>", methods=["POST"])
def pay_cod(order_id):
    order = Order.query.get(order_id)
    order.payment_method = "COD"
    db.session.commit()
    if not order:
        return jsonify({"error": "Không tìm thấy đơn hàng"}), 404

    if order.status != OrderStatus.PENDING:
        return jsonify({"error": "Đơn hàng đã được thanh toán hoặc đang xử lý"}), 400

    # Cập nhật trạng thái thanh toán và giao hàng
    order.status = OrderStatus.PENDING
    order.delivery_status = DeliveryStatus.PENDING

    try:
        db.session.commit()
        if order.user and order.user.email:
            send_order_success_email(order.user.email, order, is_cod=True)
        elif order.guest_email:
            send_order_success_email(order.guest_email, order,is_cod=True)
        return jsonify({"message": "Thanh toán COD thành công. Đơn hàng đang được xử lý."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Không thể xác nhận đơn hàng"}), 500

@main.route("/admin/orders/<int:order_id>/payment_status", methods=["PUT"])
@staff_required
def update_payment_status(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    new_status = data.get("status")  # hoặc "payment_status" nếu bạn muốn
    if order.delivery_status == DeliveryStatus.DELIVERED:
        return jsonify({"error": "Đơn hàng đã được giao, không thể thay đổi trạng thái"}), 400
    if new_status == "DELIVERED":
        return jsonify({"error": "Admin không được phép đặt trạng thái là Đã giao"}), 403

    if new_status not in OrderStatus.__members__:
        return jsonify({"error": "Trạng thái thanh toán không hợp lệ"}), 400

    order.status = OrderStatus[new_status]
    db.session.commit()

    return jsonify({
        "id": order.id,
        "status": order.status.value
    })


@main.route("/orders/<int:order_id>/confirm_received", methods=["PUT"])
@jwt_required()
def user_confirm_received(order_id):
    user_id = get_jwt_identity()
    order = Order.query.filter_by(id=order_id).first_or_404()

    if int(user_id) != order.user_id:
        return jsonify({"error": "Không có quyền xác nhận đơn hàng này"}), 403

    if order.delivery_status != DeliveryStatus.SHIPPING:
        return jsonify({"error": "Đơn hàng chưa ở trạng thái đang giao"}), 400

    if order.status != OrderStatus.PAID:
        return jsonify({"error": "Đơn hàng chưa thanh toán"}), 400

    # Trừ stock cho từng sản phẩm trong đơn
    for item in order.items:
        product = item.product
        if product.stock < item.quantity:
            return jsonify({"error": f"Sản phẩm '{product.name}' không đủ hàng tồn kho"}), 400
        product.stock -= item.quantity
    send_order_delivered_email(order.user.email, order)
    order.delivery_status = DeliveryStatus.DELIVERED
    db.session.commit()

    return jsonify({"message": "Xác nhận đã nhận hàng thành công và trừ kho thành công"})


@main.route("/orders/<int:order_id>/cancel", methods=["PUT"])
@jwt_required()
def cancel_order(order_id):
    user_id = get_jwt_identity()
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()

    if not order:
        return jsonify({"error": "Đơn hàng không tồn tại"}), 404

    if order.status != OrderStatus.PENDING:
        return jsonify({"error": "Chỉ có thể hủy đơn ở trạng thái chờ xác nhận"}), 400

    order.status = OrderStatus.CANCELED
    db.session.commit()
    return jsonify({"message": "Hủy đơn hàng thành công"})

@main.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    data = request.get_json()
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        return jsonify({"error": "Thiếu dữ liệu"}), 400

    if len(new_password) < 8:
        return jsonify({"error": "Mật khẩu mới phải có ít nhất 8 ký tự"}), 400

    # Lấy user hiện tại từ JWT
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "Người dùng không tồn tại"}), 404

    # Kiểm tra mật khẩu cũ
    if not check_password_hash(user.password_hash, old_password):
        return jsonify({"error": "Mật khẩu cũ không đúng"}), 400

    # Cập nhật mật khẩu mới
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({"message": "Đổi mật khẩu thành công"}), 200


@main.route("/admin/extra_costs", methods=["POST"])
@staff_required
def save_extra_costs():
    data = request.json  # { month: { staff, rent, living, other } }
    saved_months = []

    for month, costs in data.items():
        extra = ExtraCost.query.filter_by(month=month).first()
        if not extra:
            extra = ExtraCost(month=month)
            db.session.add(extra)

        extra.staff = float(costs.get("staff", 0))
        extra.rent = float(costs.get("rent", 0))
        extra.living = float(costs.get("living", 0))
        extra.other = float(costs.get("other", 0))
        saved_months.append(month)

    db.session.commit()
    return jsonify({"message": f"Saved extra costs for months: {saved_months}"})

@main.route('/admin/comments', methods=['GET'])
@staff_required
def admin_get_comments():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str)

    query = Comment.query.join(Product, isouter=True).order_by(Comment.created_at.desc())

    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    comments = pagination.items

    result = []
    for c in comments:
        first_image = None
        if c.product and c.product.images:
            first_image = c.product.images[0].url

        result.append({
            "id": c.id,
            "product_id": c.product_id,
            "product_name": c.product.name if c.product else None,
            "product_image": first_image,
            "username": c.user.username if c.user else None,
            "guest_name": c.guest_name,
            "content": c.content,
            "rating": c.rating,
            "admin_reply": c.admin_reply,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "likes": c.likes or 0,
        })

    return jsonify({
        "comments": result,
        "page": pagination.page,
        "pages": pagination.pages,
        "total": pagination.total
    })


@main.route("/admin/comments/<int:comment_id>", methods=["DELETE"])
@staff_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    try:
        db.session.delete(comment)
        db.session.commit()
        return jsonify({"message": f"Bình luận {comment_id} đã được xóa thành công."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Xóa bình luận thất bại.", "details": str(e)}), 500

@main.route("/admin/comments/<int:comment_id>/reply", methods=["PUT"])
@staff_required
def update_admin_reply(comment_id):
    data = request.json
    admin_reply = data.get("admin_reply", "").strip()

    comment = Comment.query.get_or_404(comment_id)
    try:
        comment.admin_reply = admin_reply
        db.session.commit()
        return jsonify({"message": "Cập nhật trả lời thành công."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Cập nhật trả lời thất bại.", "details": str(e)}), 500

@main.route('/connected-clients')
def get_connected_clients():
    # Trả về danh sách các room_id (chính là request.sid) của client đang online
    return jsonify(list(clients_rooms.values()))

@main.route("/admin/stockin", methods=["POST"])
@staff_required
def stock_in():
    data = request.json
    items = data.get("items", [])   # danh sách sản phẩm nhập
    user_id = get_jwt_identity()

    if not items:
        return jsonify({"error": "Chưa có sản phẩm nào để nhập"}), 400

    for item in items:
        product_id = item.get("product_id")
        quantity = int(item.get("quantity", 0))
        price = float(item.get("price", 0))

        product = Product.query.get(product_id)
        if not product:
            return jsonify({"error": f"Sản phẩm ID {product_id} không tồn tại"}), 404

        # Cập nhật tồn kho và giá vốn
        old_value = product.stock * product.cost_price
        new_value = quantity * price

        product.stock += quantity
        if product.stock > 0:
            product.cost_price = (old_value + new_value) / product.stock

        # Ghi lịch sử nhập kho
        entry = StockIn(
            product_id=product.id,
            quantity=quantity,
            price=price,
            date=datetime.now(),
            user_id=user_id,
        )
        db.session.add(entry)

    db.session.commit()
    return jsonify({"message": "Nhập sản phẩm thành công"}), 201


@main.route("/admin/stockin", methods=["GET"])
@staff_required
def stock_in_history():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    search = request.args.get("search", "", type=str)
    product_id = request.args.get("product_id", type=int)
    imported_by = request.args.get("imported_by", "", type=str)
    query = StockIn.query.join(Product).join(User)

    if search:
        query = query.filter(Product.name.ilike(f"%{search}%") | User.username.ilike(f"%{search}%"))

    if product_id:
        query = query.filter(StockIn.product_id == product_id)

    if imported_by:
        query = query.filter(User.username.ilike(f"%{imported_by}%"))
    pagination = query.order_by(StockIn.date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    entries = pagination.items

    result = []
    for e in entries:
        result.append({
            "id": e.id,
            "product_name": e.product.name if e.product else "N/A",
            "quantity": e.quantity,
            "price": e.price,
            "total": e.quantity * e.price,
            "date": e.date.strftime("%Y-%m-%d"),
            "imported_by": e.user.username if e.user else "Unknown"
        })

    return jsonify({
        "entries": result,
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages
    })

@main.route("/admin/products", methods=["GET"])
def get_productss():
    try:
        products = Product.query.all()
        result = [
            {
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "stock": p.stock
            }
            for p in products
        ]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@main.route("/admin/stockin/<int:id>", methods=["PUT"])
@staff_required
def update_stockin(id):
    data = request.json
    entry = StockIn.query.get(id)
    user_id = get_jwt_identity()
    if not entry:
        return jsonify({"error": "Bản ghi không tồn tại"}), 404

    # Lấy sản phẩm liên quan
    product = Product.query.get(entry.product_id)
    if not product:
        return jsonify({"error": "Sản phẩm không tồn tại"}), 404

    # Cập nhật tồn kho: trừ đi số lượng cũ, cộng số lượng mới
    old_quantity = entry.quantity
    old_price = entry.price
    old_price_total = entry.quantity * entry.price

    new_quantity = int(data.get("quantity", entry.quantity))
    new_price = float(data.get("price", entry.price))
    new_price_total = new_quantity * new_price

    # Điều chỉnh tồn kho
    product.stock = product.stock - old_quantity + new_quantity

    # Cập nhật giá gốc nếu cần
    if product.stock > 0:
        product.cost_price = (product.cost_price * (product.stock - new_quantity + old_quantity) - old_price_total + new_price_total) / product.stock

    # Cập nhật entry
    entry.quantity = new_quantity
    entry.price = new_price
    entry.updated_by = user_id
    log = StockInLog(
        stockin_id=entry.id,
        old_quantity=old_quantity,
        new_quantity=new_quantity,
        old_price=old_price,
        new_price=new_price,
        user_id=user_id
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({"message": "Cập nhật nhập kho thành công"})

@main.route("/admin/stockin/<int:id>/logs", methods=["GET"])
@staff_required
def get_stockin_logs(id):
    logs = StockInLog.query.filter_by(stockin_id=id).order_by(StockInLog.created_at.desc()).all()
    return jsonify([
        {
            "old_quantity": log.old_quantity,
            "new_quantity": log.new_quantity,
            "old_price": log.old_price,
            "new_price": log.new_price,
            "username": log.user.username if log.user else None,
            "created_at": log.created_at.isoformat()
        }
        for log in logs
    ])

@main.route("/save_search", methods=["POST"])
@jwt_required()
def save_search():
    current_user = get_jwt_identity()
    keyword = request.json.get("keyword", "").strip()

    if not keyword:
        return jsonify({"message": "Thiếu từ khóa"}), 400

    new_search = SearchHistory(user_id=current_user, keyword=keyword)
    db.session.add(new_search)
    db.session.commit()

    return jsonify({"message": "Đã lưu vào database"})

@main.route("/get_searches", methods=["GET"])
@jwt_required()
def get_searches():
    current_user = get_jwt_identity()
    searches = (
        SearchHistory.query.filter_by(user_id=current_user)
        .order_by(SearchHistory.id.desc())
        .limit(10)
        .all()
    )
    return jsonify([s.keyword for s in searches])
