from datetime import datetime
from flask_mail import Message
from . import mail


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

def send_order_success_email(user_email, order):
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
        extra_info = "\n\nBạn có thể tra cứu đơn hàng của mình trên website bằng mã đơn hàng."

    # Tạo email
    msg = Message(
        subject="Xác nhận đơn hàng thành công",
        recipients=[user_email]
    )
    msg.body = f"""
{greeting}

Đơn hàng #{order.id} của bạn đã được thanh toán thành công!

Chi tiết đơn hàng:
{items_detail}

Tổng cộng: {total} VND
{extra_info}

Cảm ơn bạn đã mua sắm tại cửa hàng chúng tôi!
"""
    mail.send(msg)
