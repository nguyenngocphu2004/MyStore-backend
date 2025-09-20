from datetime import datetime
from flask_mail import Message
from flask import jsonify
from . import mail
import random
import string
from .models import Order,User,UserRole
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
def time_ago(dt):
    now = datetime.now()
    diff = now - dt
    seconds = diff.total_seconds()

    if seconds < 60:
        return f"{int(seconds)} giây trước"
    elif seconds < 3600:
        return f"{int(seconds // 60)} phút trước"
    elif seconds < 86400:
        return f"{int(seconds // 3600)} giờ trước"
    elif seconds < 2592000:
        return f"{int(seconds // 86400)} ngày trước"
    else:
        return dt.strftime("%Y-%m-%d")

def send_order_success_email(user_email, order, is_cod=False):
    # Chuẩn bị chi tiết các sản phẩm
    items_detail = "\n".join(
        [f"- {item.product.name} x {item.quantity} = {item.unit_price * item.quantity} VND" for item in order.items]
    )
    total = order.total_price

    # Kiểm tra user hay guest
    if order.user:
        greeting = f"Xin chào {order.user.username},"
        extra_info = ""
    else:
        greeting = "Xin chào Khách hàng,"
        extra_info = "\n\nBạn có thể tra cứu đơn hàng của mình trên website bằng số điện thoại bạn đã đặt đơn hàng."

    # Nội dung email tùy theo is_cod
    if is_cod:
        payment_info = "Phương thức thanh toán: Thanh toán khi nhận hàng (COD). Bạn sẽ thanh toán khi nhận đơn hàng."
        subject = "Xác nhận đơn hàng đã được ghi nhận"
    else:
        payment_info = "Đơn hàng của bạn đã được thanh toán thành công!"
        subject = "Xác nhận thanh toán đơn hàng thành công"

    # Tạo email
    msg = Message(
        subject=subject,
        recipients=[user_email]
    )
    msg.body = f"""
{greeting}

Đơn hàng #{order.order_code} của bạn đã được ghi nhận.
{payment_info}

Chi tiết đơn hàng:
{items_detail}

Tổng cộng: {total} VND
{extra_info}

Cảm ơn bạn đã mua sắm tại cửa hàng chúng tôi!
"""
    mail.send(msg)


def send_order_delivered_email(user_email, order):
    # Chuẩn bị chi tiết các sản phẩm
    items_detail = "\n".join(
        [f"- {item.product.name} x {item.quantity} = {item.unit_price * item.quantity} VND" for item in order.items]
    )
    total = order.total_price

    # Kiểm tra user hay guest
    if order.user:
        greeting = f"Xin chào {order.user.username},"
        extra_info = ""
    else:
        greeting = "Xin chào Khách hàng,"
        extra_info = "\n\nBạn có thể liên hệ với chúng tôi nếu có thắc mắc về đơn hàng."

    # Tạo email
    msg = Message(
        subject="Xác nhận đơn hàng đã được giao",
        recipients=[user_email]
    )
    msg.body = f"""
{greeting}

Đơn hàng #{order.order_code} của bạn đã được giao đến bạn thành công!

Chi tiết đơn hàng:
{items_detail}

Tổng cộng: {total} VND

Chúng tôi rất vui vì bạn đã nhận được hàng. Cảm ơn bạn đã tin tưởng và mua sắm tại cửa hàng chúng tôi!
{extra_info}
"""
    mail.send(msg)



def generate_order_code():
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))  # 3 ký tự chữ in hoa
    numbers = ''.join(random.choices(string.digits, k=7))            # 7 chữ số
    return letters + numbers

def generate_unique_order_code():
    while True:
        code = generate_order_code()
        existing = Order.query.filter_by(order_code=code).first()
        if not existing:
            return code

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

def staff_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or user.role not in [UserRole.ADMIN, UserRole.STAFF]:
            return jsonify({"error": "Chỉ admin hoặc nhân viên mới truy cập được"}), 403
        return fn(*args, **kwargs)
    return wrapper

