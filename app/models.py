from backend.app import create_app, db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import Enum
import enum


class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"
    STAFF = "STAFF"

class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

class User(BaseModel, UserMixin):
    __tablename__ = "users"

    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    user = db.relationship("Order", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(BaseModel):
    __tablename__ = "categories"

    name = db.Column(db.String(100), unique=True, nullable=False)
    products = db.relationship("Product", backref="category", lazy=True)

    def __str__(self):
        return self.name
class Brand(BaseModel):
    __tablename__ = "brands"

    name = db.Column(db.String(200), unique=True, nullable=False)
    products = db.relationship("Product", backref="brand", lazy=True)

    def __str__(self):
        return self.name




class Product(BaseModel):
    __tablename__ = "products"

    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    cost_price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey("brands.id"), nullable=False)
    images = db.relationship("ProductImage", backref="product",cascade="all, delete-orphan", lazy=True)
    # Thông số kỹ thuật
    cpu = db.Column(db.String(200), nullable=True)
    ram = db.Column(db.String(100), nullable=True)
    storage = db.Column(db.String(100), nullable=True)  # bộ nhớ trong
    screen = db.Column(db.String(200), nullable=True)  # màn hình
    battery = db.Column(db.String(100), nullable=True)
    os = db.Column(db.String(100), nullable=True)  # hệ điều hành
    camera_front = db.Column(db.String(100), nullable=True)
    camera_rear = db.Column(db.String(100), nullable=True)
    weight = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(100), nullable=True)
    dimensions = db.Column(db.String(100), nullable=True)
    release_date = db.Column(db.Date, nullable=True)
    graphics_card = db.Column(db.String(200), nullable=True)  # card đồ họa (cho laptop)
    ports = db.Column(db.String(255), nullable=True)  # các cổng kết nối
    warranty = db.Column(db.String(100), nullable=True)

    def __str__(self):
        return self.name


class ProductImage(BaseModel):
    __tablename__ = "product_images"
    url = db.Column(db.String(255), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

class StockIn(BaseModel):
    __tablename__ = "stock_in"

    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.now)
    product = db.relationship("Product", backref="stock_entries")

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user = db.relationship("User", backref="stock_entries")

    def __str__(self):
        return f"{self.user.username} nhập {self.quantity} {self.product.name} ngày {self.date.strftime('%d/%m/%Y')}"


class StockInLog(BaseModel):
    __tablename__ = "stockin_logs"

    stockin_id = db.Column(db.Integer, db.ForeignKey("stock_in.id"), nullable=False)
    old_quantity = db.Column(db.Integer)
    new_quantity = db.Column(db.Integer)
    old_price = db.Column(db.Float)
    new_price = db.Column(db.Float)
    note = db.Column(db.String(200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship("User", backref="stockin_logs")
    def __repr__(self):
        return f"<StockInLog {self.action} by {self.user_id} at {self.created_at}>"

class OrderStatus(enum.Enum):
    PENDING = "PENDING"  # Chưa thanh toán
    PAID = "PAID"        # Thanh toán thành công
    FAILED = "FAILED"  # Thanh toán thất bại
    CANCELED = "CANCELED"# Hủy đơn hàng

class DeliveryStatus(enum.Enum):
    PENDING = "PENDING"     # Chưa xử lý giao
    PROCESSING = "PROCESSING"  # Đang xử lý
    SHIPPING = "SHIPPING"      # Đang giao
    DELIVERED = "DELIVERED"    # Đã giao

class Order(BaseModel):
    __tablename__ = "orders"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # có thể là None
    guest_name = db.Column(db.String(100), nullable=True)   # tên khách vãng lai
    guest_phone = db.Column(db.String(20), nullable=True)
    guest_email = db.Column(db.String(120),nullable =True)# SĐT khách vãng lai
    created_at = db.Column(db.DateTime, default=datetime.now)
    total_price = db.Column(db.Float, nullable=False)
    delivery_method = db.Column(db.String(20), default="store")
    momo_order_id = db.Column(db.String(36), unique=True, nullable=True)
    address = db.Column(db.String(255), nullable=True)
    items = db.relationship("OrderItem", backref="order", lazy=True)
    status = db.Column( db.Enum(OrderStatus),default=OrderStatus.PENDING,nullable=False)
    delivery_status = db.Column(db.Enum(DeliveryStatus), default=DeliveryStatus.PENDING, nullable=False)
    payment_method = db.Column(db.String(20), nullable=True)
    order_code = db.Column(db.String(20), unique=True, nullable=False)



class OrderItem(BaseModel):
    __tablename__ = "order_items"

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    product = db.relationship("Product", lazy=True)


class CartItem(BaseModel):
    __tablename__ = "cart_items"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    user = db.relationship("User", backref="cart_items")
    product = db.relationship("Product")


class Comment(BaseModel):
    __tablename__ = "comments"

    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # null nếu khách
    guest_name = db.Column(db.String(100), nullable=True)
    guest_phone = db.Column(db.String(20), nullable=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=5)
    likes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    admin_reply = db.Column(db.Text, nullable=True)
    reply_at = db.Column(db.DateTime, nullable=True)
    reply_role = db.Column(db.String(20), nullable=True)
    product = db.relationship('Product', backref=db.backref('comments', lazy=True))
    user = db.relationship('User', backref=db.backref('comments', lazy=True))

class CommentVote(BaseModel):
    __tablename__ = "comment_votes"
    comment_id = db.Column(db.Integer, db.ForeignKey("comments.id"), nullable=False)

    # Nếu user login thì dùng user_id
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # Nếu khách thì lưu session_id
    session_id = db.Column(db.String(100), nullable=True)

    action = db.Column(db.String(10), nullable=False)  # "like" hoặc "dislike"
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship("User", backref="votes")
    comment = db.relationship("Comment", backref="votes")

class OTP(BaseModel):
    __tablename__ = "otps"
    phone = db.Column(db.String(20), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    expiry = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def is_valid(self, code):
        return (
            self.otp_code == code
            and datetime.now() <= self.expiry
        )

class ExtraCost(BaseModel):
    __tablename__ = "extra_costs"
    month = db.Column(db.String(7), nullable=False)  # YYYY-MM
    staff = db.Column(db.Float, default=0)
    rent = db.Column(db.Float, default=0)
    living = db.Column(db.Float, default=0)
    other = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)

class SearchHistory(BaseModel):
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    keyword = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship("User", backref="searches")

def seed_data(db):
    if not Category.query.first():
        phone = Category(name="Điện thoại")
        laptop = Category(name="Laptop")
        brand = Brand(name="Apple")
        brand1 = Brand(name="Samsung")
        brand2 = Brand(name="Oppo")
        brand3 = Brand(name="Xiaomi")
        brand4 = Brand(name="Dell")
        brand5 = Brand(name="Gigabyte")
        brand6 = Brand(name="Acer")
        brand7 = Brand(name="Lenovo")
        brand8 = Brand(name="Macbook")
        brand9 = Brand(name="Hp")
        brand11 = Brand(name="Asus")
        brand12 = Brand(name="Vivo")
        brand13 = Brand(name="Realme")
        db.session.add_all([phone, laptop,brand,brand1,brand2,brand3,brand4,brand5,brand6,brand7,brand8,brand9,brand11,brand12,brand13])
        db.session.commit()

        p1 = Product(name="IPhone 14 Pro Max", price=1000, brand_id=brand.id, cost_price=100,stock=100,
                     category_id=phone.id, cpu="Apple A16 Bionic", ram="6GB", storage="256GB",
                     screen="6.7 inch Super Retina XDR OLED, 1290 x 2796 pixels, 120Hz", battery="4323mAh", os="iOS 17",
                     camera_front="12MP", camera_rear="48MP + 12MP + 12MP", weight="240g", color="Tím",
                     dimensions="160.7 x 77.6 x 7.85 mm", release_date=datetime(2022, 9, 16), graphics_card=None,
                     ports="Lightning", warranty="12 tháng")
        p2 = Product(name="IPhone 15 Pro Max", price=28990000,  brand_id=brand.id,cost_price=22000000,stock=100,
                     category_id=phone.id, cpu="Apple A17 Pro 6 nhân", ram="8GB", storage="256GB",
                     screen="6.7 inch Super Retina XDR OLED, 2796 x 1290 pixels, 120Hz", battery="4422mAh", os="iOS 17",
                     camera_front="12MP", camera_rear="48MP + 12MP + 12MP", weight="221g", color="Titan Xanh",
                     dimensions="159.9 x 76.7 x 8.25 mm", release_date=datetime(2023, 9, 16), graphics_card=None,
                     ports="USB Type-C", warranty="12 tháng")
        p3 = Product(name="IPhone 16 Pro Max", price=30590000,  brand_id=brand.id,cost_price=24300000,stock=100,
                     category_id=phone.id, cpu="Apple A18 Pro 6 nhân", ram="8GB", storage="256GB",
                     screen="6.9 Super Retina XDR OLED, 1320 x 2868 Pixels, 120Hz", battery="4676mAh", os="iOS 18",
                     camera_front="12MP", camera_rear="48MP + 48MP + 12MP", weight="227g", color="Titan Sa Mạc",
                     dimensions="163 x 77.6 x 8.25 mm", release_date=datetime(2024, 9, 16), graphics_card=None,
                     ports="Type-C", warranty="12 tháng")
        p4 = Product(name="IPhone X", price=4590000,  brand_id=brand.id,cost_price=3520000,stock=100,
                     category_id=phone.id, cpu="Apple A11 Bionic", ram="3GB", storage="64GB",
                     screen="5.8 inch, 1125 x 2436 pixels, 60Hz", battery="2716mAh", os="iOS 12",
                     camera_front="7MP", camera_rear="12MP + 12MP", weight="144g", color="Bạc",
                     dimensions="143.6 x 70.9 x 7.7 mm", release_date=datetime(2017, 9, 16), graphics_card=None,
                     ports="Lightning", warranty="12 tháng")
        p5 = Product(name="IPhone 8", price=3200000,  brand_id=brand.id,cost_price=2700000,stock=100,
                     category_id=phone.id, cpu="Apple A11 Bionic", ram="2GB", storage="64GB",
                     screen="4.7 inch , 750 x 1334 pixels, 60Hz", battery="1821mAh", os="iOS 14",
                     camera_front="7MP", camera_rear="12MP", weight="148g", color="Đỏ",
                     dimensions="Không rõ", release_date=datetime(2017, 9, 16), graphics_card=None,
                     ports="Lightning", warranty="12 tháng")
        p6 = Product(name="Samsung Galaxy Z Fold7", price=43990000,  brand_id=brand1.id,cost_price=39900000,stock=100,
                     category_id=phone.id, cpu="Qualcomm Snapdragon 8 Elite For Galaxy 8 nhân", ram="12GB", storage="256GB",
                     screen="Chính 7.3 & Phụ 4.6 inch, 2152 x 1536 Pixels, 120Hz", battery="4400mAh", os="Android 9 (Pie)",
                     camera_front="10MP + 10MP", camera_rear="200MP + 12MP + 10MP", weight="215g", color="Đen",
                     dimensions="158.4 x 143.2 x 72.8 mm", release_date=datetime(2025, 7, 16), graphics_card=None,
                     ports="Type-C", warranty="12 tháng")
        p7 = Product(name="OPPO Reno14 F 5G", price=11290000,  brand_id=brand2.id,cost_price=9370000,stock=100,
                     category_id=phone.id, cpu="Snapdragon 6 Gen 1 5G 8 nhân", ram="12GB", storage="256GB",
                     screen="6.57 inch AMOLED, 1080 x 2372 Pixels, 120Hz", battery="6000mAh", os="Android 15",
                     camera_front="32MP", camera_rear="50MP + 8MP + 2MP", weight="180g", color="Xanh dương",
                     dimensions="158.12 x 74.97 x 7.69 mm", release_date=datetime(2025, 7, 16), graphics_card=None,
                     ports="Type-C", warranty="12 tháng")
        p8 = Product(name="Xiaomi 15 Ultra 5G", price=32360000,  brand_id=brand3.id,cost_price=28160000,stock=100,
                     category_id=phone.id, cpu="Qualcomm Snapdragon 8 Elite 8 nhân", ram="16GB", storage="512GB",
                     screen="6.73 inch AMOLED, 1440 x 3200 pixels, 120Hz", battery="5410mAh", os="Xiaomi HyperOS 2",
                     camera_front="32MP", camera_rear="50MP + 200MP + 50MP + 50MP", weight="226g", color="Trắng",
                     dimensions="161.3 x 75.3 x 9.35 mm", release_date=datetime(2025, 3, 16), graphics_card=None,
                     ports="Type-C", warranty="12 tháng")
        p9 = Product(name="GIGABYTE Gaming A16 GA6H", price=26290000,  brand_id=brand5.id,cost_price=22210000,stock=100,
                     category_id=laptop.id, cpu="Intel Core i5 Raptor Lake - 13420H", ram="16GB DDR5", storage="512GB SSD",
                     screen="16 inch WUXGA (1920 x 1200), 60Hz", battery="76Wh", os="Windows 11 Home SL",
                     camera_front="720p HD", camera_rear=None, weight="2.227kg", color="Platinum Silver",
                     dimensions="358.3 x 262.5 x 22.99 mm", release_date=datetime(2024, 10, 1),
                     graphics_card="Intel Iris Xe Graphics", ports="1 x USB Type-C 3.2 (hỗ trợ DisplayPort 1.4 và Power delivery 3.0)",
                     warranty="24 tháng")
        p10 = Product(name="GIGABYTE Gaming AERO X16", price=35990000,  brand_id=brand5.id,cost_price=30010000,stock=100,
                      category_id=laptop.id, cpu="AMD Ryzen AI 7 - 350", ram="32GB DDR5", storage="1TB SSD",
                      screen="16 inch WQXGA (2560 x 1600), 165Hz", battery="76Wh", os="Windows 11 Home SL",
                      camera_front="720p HD", camera_rear=None, weight="1.99kg", color="Xám",
                      dimensions="355 x 250.7 x 19.99 mm", release_date=datetime(2025, 10, 1),
                      graphics_card="Card rời - NVIDIA GeForce RTX 5060, 8 GB", ports="1 x USB Type-C (hỗ trợ USB 4, DisplayPort 1.4 và Power Delivery 3.0)",
                      warranty="24 tháng")
        p11 = Product(name="Acer Gaming Nitro V 15 ProPanel", price=30490000,  brand_id=brand6.id,cost_price=25800000,stock=100,
                      category_id=laptop.id, cpu="Intel Core i7 Raptor Lake - 13620H", ram="16GB DDR4", storage="512GB SSD",
                      screen="15.6 inch FHD+ (1920 x 1080), 165Hz", battery="52Wh", os="Windows 11 Home SL",
                      camera_front="720p HD", camera_rear=None, weight="2.1kg", color="Đen",
                      dimensions="362.3 x 239.89 x 23.5 mm", release_date=datetime(2021, 10, 1),
                      graphics_card="Card rời - NVIDIA GeForce RTX 5050, 8 GB", ports="1 x USB Type-C (hỗ trợ USB, DisplayPort, Thunderbolt 4)",
                      warranty="24 tháng")
        p12 = Product(name="Lenovo XPS 13 9310", price=34990000,  brand_id=brand7.id,cost_price=28050000,stock=100,
                      category_id=laptop.id, cpu="Intel Core i7-1185G7", ram="16GB LPDDR4x", storage="512GB SSD",
                      screen="13.4 inch FHD+ (1920 x 1200), 60Hz", battery="76Wh", os="Windows 11",
                      camera_front="720p HD", camera_rear=None, weight="1.2kg", color="Đen",
                      dimensions="295.7 x 198.7 x 14.8 mm", release_date=datetime(2025, 10, 1),
                      graphics_card="Intel Iris Xe Graphics", ports="2 x Thunderbolt 4, 1 x 3.5mm Audio",
                      warranty="24 tháng")
        p13 = Product(name="MacBook Pro", price=44090000,  brand_id=brand8.id,cost_price=37090000,stock=100,
                      category_id=laptop.id, cpu="Apple M4", ram="16GB ", storage="1 TB SSD",
                      screen="14.2 inch Liquid Retina XDR display (3024 x 1964), 120Hz", battery="72.4Wh", os="macOS Sequoia",
                      camera_front="720p HD", camera_rear=None, weight="1.55kg", color="Bạc",
                      dimensions="312.6 x 221.2 x 15.5 mm", release_date=datetime(2024, 10, 1),
                      graphics_card="Card tích hợp - 10 nhân GPU", ports="3 x Thunderbolt 4 ( hỗ trợ DisplayPort, Thunderbolt 4 (up to 40Gb/s), USB 4 (up to 40Gb/s))",
                      warranty="24 tháng")
        p14 = Product(name="HP Pavilion X360 14", price=21490000,  brand_id=brand9.id,cost_price=15600000,stock=100,
                      category_id=laptop.id, cpu="Intel Core 5 Raptor Lake - 120U", ram="16GB DDR4", storage="512GB SSD",
                      screen="14 inch Full HD (1920 x 1080), 60Hz", battery="43Wh", os="Windows 11 Home SL",
                      camera_front="720p HD", camera_rear=None, weight="1.51kg", color="Vàng",
                      dimensions="322 x 210 x 18.9 mm", release_date=datetime(2024, 10, 1),
                      graphics_card="Card tích hợp - Intel Graphics", ports="1 x USB Type-C (hỗ trợ USB Power Delivery, DisplayPort 1.4)",
                      warranty="24 tháng")
        p15 = Product(name="Acer Gaming Nitro V", price=23590000,  brand_id=brand6.id,cost_price=15700000,stock=100,
                      category_id=laptop.id, cpu="Intel Core i5 Raptor Lake - 13420H", ram="16GB DDR5", storage="512GB SSD",
                      screen="15.6 inch Full HD (1920 x 1080), 144Hz", battery="57Wh", os="Windows 11 Home SL",
                      camera_front="720p HD", camera_rear=None, weight="2.1kg", color="Đen",
                      dimensions="362.3 x 239.89 x 26.9 mm", release_date=datetime(2023, 10, 1),
                      graphics_card="Card rời - NVIDIA GeForce RTX 4050, 6 GB", ports="1 x USB Type-C (hỗ trợ USB, DisplayPort, Thunderbolt 4)",
                      warranty="24 tháng")
        p16 = Product(name="Asus TUF Gaming F16", price=22190000,  brand_id=brand11.id,cost_price=17700000,stock=100,
                      category_id=laptop.id, cpu="Intel Core 5 Raptor Lake - 210H", ram="16GB LPDDR4x", storage="512GB SSD",
                      screen="16 inch Full HD+, 144Hz", battery="56Wh", os="Windows 11",
                      camera_front="720p HD", camera_rear=None, weight="2.2kg", color="Xám",
                      dimensions="354 x 251 x 26.7 mm", release_date=datetime(2025, 10, 1),
                      graphics_card="Card rời - NVIDIA GeForce RTX 3050, 6 GB", ports="1 x USB Type-C 3.2 (hỗ trợ Power Delivery và DisplayPort)",
                      warranty="24 tháng")
        p17 = Product(name="IPhone 17 Pro", price=34990000, brand_id=brand.id, cost_price=29100000, stock=100,
                     category_id=phone.id, cpu="Apple A19 Pro 6 nhân", ram="12GB", storage="256GB",
                     screen="6.3 inch , 1206 x 2622 pixels, 120Hz", battery="4252mAh", os="iOS 26",
                     camera_front="18MP", camera_rear="48MP + 48MP + 48MP", weight="204g", color="Cam vũ trụ",
                     dimensions="150 x 71.9 x 8.75 mm", release_date=datetime(2025, 9, 16), graphics_card=None,
                     ports="Type-C", warranty="12 tháng")
        p18 = Product(name="Xiaomi 14T Pro 5G", price=15190000, brand_id=brand3.id, cost_price=10100000, stock=100,
                     category_id=phone.id, cpu="MediaTek Dimensity 9300+ 8 nhân", ram="12GB", storage="256GB",
                     screen="6.67 inch AMOLED, 1220 x 2712 Pixels, 144Hz", battery="5000mAh", os="Xiaomi HyperOS (Android 14)",
                     camera_front="32MP", camera_rear="50MP + 50MP + 12MP", weight="209g", color="Trắng",
                     dimensions="160.4 x 75.1 x 8.39 mm", release_date=datetime(2024, 9, 16), graphics_card=None,
                     ports="Type-C", warranty="12 tháng")
        p19 = Product(name="Xiaomi Redmi Note 14 Pro+ 5G", price=11860000, brand_id=brand3.id, cost_price=7300000, stock=100,
                      category_id=phone.id, cpu="Snapdragon 7s Gen 3 5G 8 nhân", ram="12GB", storage="512GB",
                      screen="6.67 inch AMOLED, 1220 x 2712 Pixels, 120Hz", battery="5110mAh",
                      os="Android 14",
                      camera_front="20MP", camera_rear="200MP + 8MP + 2MP", weight="210.14g", color="Vàng",
                      dimensions="162.53 x 74.67 x 8.75 mm", release_date=datetime(2025, 1, 16), graphics_card=None,
                      ports="Type-C", warranty="12 tháng")
        p20 = Product(name="Xiaomi Redmi 15", price=4990000, brand_id=brand3.id, cost_price=3800000,
                      stock=100,
                      category_id=phone.id, cpu="Snapdragon 685 8 nhân", ram="6GB", storage="128GB",
                      screen="6.9 inch Full HD+ 1080 x 2340 Pixels, 144Hz", battery="7000mAh",
                      os="Android 15",
                      camera_front="8MP", camera_rear="50MP + QVGA", weight="214g", color="Xám",
                      dimensions="169.48 x 80.45 x 8.4 mm", release_date=datetime(2025, 8, 16), graphics_card=None,
                      ports="Type-C", warranty="12 tháng")
        p21 = Product(name="OPPO Find N5 5G", price=44180000, brand_id=brand2.id, cost_price=39990000, stock=100,
                     category_id=phone.id, cpu="Qualcomm Snapdragon 8 Elite 8 nhân", ram="16GB", storage="512GB",
                     screen="Chính 8.12 Phụ 6.62 inch LTPO AMOLED, Chính: QXGA+ (2248 x 2480 Pixels) & Phụ: FHD+ (1140x 2616 Pixels), 120Hz", battery="5600mAh", os="Android 15",
                     camera_front="8MP", camera_rear="50MP + 50MP + 8MP", weight="229g", color="Đen",
                     dimensions="160.87 x 146.58 x 4.21 mm", release_date=datetime(2025, 4, 16), graphics_card=None,
                     ports="Type-C", warranty="12 tháng")
        p22 = Product(name="OPPO Find X8 Pro 5G", price=26450000, brand_id=brand2.id, cost_price=22000000, stock=100,
                      category_id=phone.id, cpu="MediaTek Dimensity 9400 8 nhân", ram="16GB", storage="512GB",
                      screen="6.78 inch AMOLED 1264 x 2780 Pixels, 120Hz",
                      battery="5910mAh", os="Android 15",
                      camera_front="32MP", camera_rear="50MP + 50MP + 50MP + 50MP", weight="215g", color="Trắng",
                      dimensions="162.27 x 76.67 x 8.24 mm", release_date=datetime(2024, 11, 16), graphics_card=None,
                      ports="Type-C", warranty="12 tháng")
        p23 = Product(name="OPPO A58", price=5400000, brand_id=brand2.id, cost_price=3200000, stock=100,
                      category_id=phone.id, cpu="MediaTek Helio G85", ram="8GB", storage="128GB",
                      screen="6.72 inch Full HD+ 1080 x 2412 Pixels, 60Hz",
                      battery="5000mAh", os="Android 13",
                      camera_front="8MP", camera_rear="50MP + 2MP", weight="192g", color="Xanh ngọc",
                      dimensions="165.65 x 75.98 x 7.99 mm", release_date=datetime(2023, 8, 16), graphics_card=None,
                      ports="Type-C", warranty="12 tháng")
        p24 = Product(name="OPPO A5i", price=3090000, brand_id=brand2.id, cost_price=2610000, stock=100,
                      category_id=phone.id, cpu="Snapdragon 6s Gen 1 8 nhân", ram="4GB", storage="64GB",
                      screen="6.67 inch IPS LCD HD+ 720 x 1604 Pixels, 90Hz",
                      battery="5100mAh", os="Android 14",
                      camera_front="5MP", camera_rear="8MP", weight="186g", color="Tím",
                      dimensions="165.77 x 76.08 x 7.68 mm", release_date=datetime(2025, 7, 16), graphics_card=None,
                      ports="Type-C", warranty="12 tháng")
        p25 = Product(name="Samsung Galaxy S25 Ultra 5G", price=28280000, brand_id=brand1.id, cost_price=23320000, stock=100,
                     category_id=phone.id, cpu="Qualcomm Snapdragon 8 Elite For Galaxy 8 nhân", ram="12GB",
                     storage="256GB",
                     screen="6.9 inch Dynamic AMOLED 2X 2K+, 1440 x 3120 Pixels, 120Hz", battery="5000mAh",
                     os="Android 15",
                     camera_front="12MP", camera_rear="200MP + 50MP + 50MP + 10MP", weight="218g", color="Xanh dương",
                     dimensions="162.8 x 77.6 x 8.2 mm", release_date=datetime(2025, 1, 16), graphics_card=None,
                     ports="Type-C", warranty="12 tháng")
        p26 = Product(name="Vivo V60 5G", price=15990000, brand_id=brand12.id, cost_price=11110000,
                      stock=100,
                      category_id=phone.id, cpu="Snapdragon 7 Gen 4 8 nhân", ram="12GB",
                      storage="256GB",
                      screen="6.77 inch AMOLED Full HD+, 1080 x 2392 Pixels, 120Hz", battery="6500mAh",
                      os="Android 15",
                      camera_front="50MP", camera_rear="50MP + 50MP + 8MP", weight="213g", color="Xám",
                      dimensions="163.53 x 76.96 x 7.53 mm", release_date=datetime(2025, 8, 16), graphics_card=None,
                      ports="Type-C", warranty="12 tháng")
        p27 = Product(name="Vivo Y19s", price=3920000, brand_id=brand12.id, cost_price=2820000,
                      stock=100,
                      category_id=phone.id, cpu="Unisoc Tiger T612", ram="4GB",
                      storage="128GB",
                      screen="6.68 inch IPS LCD HD+, 720 x 1608 Pixels, 90Hz", battery="5500mAh",
                      os="Android 14",
                      camera_front="5MP", camera_rear="50MP + 0.08MP", weight="198g", color="Đen",
                      dimensions="165.75 x 76.1 x 8.1 mm", release_date=datetime(2024, 11, 16), graphics_card=None,
                      ports="Type-C", warranty="12 tháng")
        p28 = Product(name="Vivo V30 5G", price=13740000, brand_id=brand12.id, cost_price=10000000,
                      stock=100,
                      category_id=phone.id, cpu="Snapdragon 7 Gen 3 8 nhân", ram="12GB",
                      storage="512GB",
                      screen="6.78 inch AMOLED 1.5K, 1260 x 2800 Pixels, 120Hz", battery="5000mAh",
                      os="Android 14",
                      camera_front="50MP", camera_rear="50MP + 50MP", weight="186g", color="Đen",
                      dimensions="164.36 x 75.1 x 7.45 mm", release_date=datetime(2024, 5, 16), graphics_card=None,
                      ports="Type-C", warranty="12 tháng")
        p29 = Product(name="Vivo V50 Lite", price=8830000, brand_id=brand12.id, cost_price=6830000,
                      stock=100,
                      category_id=phone.id, cpu="Snapdragon 685 8 nhân", ram="8GB",
                      storage="256GB",
                      screen="6.77 inch AMOLED Full HD+, 1080 x 2392 Pixels, 120Hz", battery="6500mAh",
                      os="Android 15",
                      camera_front="32MP", camera_rear="50MP + 2MP", weight="196g", color="Tím",
                      dimensions="163.77 x 76.28 x 7.79 mm", release_date=datetime(2025, 5, 16), graphics_card=None,
                      ports="Type-C", warranty="12 tháng")
        p30 = Product(name="Realme 14 5G", price=9400000, brand_id=brand13.id, cost_price=7200000,
                      stock=100,
                      category_id=phone.id, cpu="Snapdragon 6 Gen 4 5G 8 nhân", ram="12GB",
                      storage="256GB",
                      screen="6.67 inch AMOLED Full HD+, 1080 x 2400 Pixels, 120Hz", battery="6000mAh",
                      os="Android 15",
                      camera_front="16MP", camera_rear="50MP + 2MP", weight="196g", color="Xám",
                      dimensions="163.15 x 75.65 x 7.97 mm", release_date=datetime(2025, 5, 16), graphics_card=None,
                      ports="Type-C", warranty="12 tháng")
        p31 = Product(name="Realme C75x", price=5200000, brand_id=brand13.id, cost_price=3100000,
                      stock=100,
                      category_id=phone.id, cpu="MediaTek Helio G81-Ultra 8 nhân", ram="8GB",
                      storage="128GB",
                      screen="6.67 inch IPS LCD HD+, 720 x 1604 Pixels, 120Hz", battery="5600mAh",
                      os="Android 15",
                      camera_front="5MP", camera_rear="50MP + Flicker", weight="196g", color="Hồng",
                      dimensions="165.69 x 76.22 x 7.99 mm", release_date=datetime(2025, 4, 16), graphics_card=None,
                      ports="Type-C", warranty="12 tháng")
        p32 = Product(name="Realme Note 70", price=2940000, brand_id=brand13.id, cost_price=2350000,
                      stock=100,
                      category_id=phone.id, cpu="Unisoc T7250 8 nhân", ram="4GB",
                      storage="64GB",
                      screen="6.74 inch TFT LCD HD+, 720 x 1600 Pixels, 120Hz", battery="6300mAh",
                      os="Android 15",
                      camera_front="5MP", camera_rear="13MP", weight="201g", color="Xanh lá nhạt",
                      dimensions="167.2 x 76.6 x 7.94 mm", release_date=datetime(2025, 8, 16), graphics_card=None,
                      ports="Type-C", warranty="12 tháng")
        p33 = Product(name="Realme Note 60x", price=3090000, brand_id=brand13.id, cost_price=2650000,
                      stock=100,
                      category_id=phone.id, cpu="Unisoc Tiger T612", ram="4GB",
                      storage="64GB",
                      screen="6.74 inch IPS LCD HD+, 720 x 1600 Pixels, 90Hz", battery="5000mAh",
                      os="Android 14",
                      camera_front="5MP", camera_rear="8MP", weight="187g", color="Đen",
                      dimensions="167.26 x 76.67 x 7.84 mm", release_date=datetime(2025, 1, 16), graphics_card=None,
                      ports="Type-C", warranty="12 tháng")
        p34 = Product(name="GIGABYTE Gaming AORUS MASTER 16", price=84890000, brand_id=brand5.id, cost_price=62830000,
                     stock=100,
                     category_id=laptop.id, cpu="Intel Core Ultra 9 Arrow Lake - 275HX", ram="32GB DDR5",
                     storage="1TB SSD",
                     screen="16 inch WQXGA (2560 x 1600) OLED, 240Hz", battery="99Wh", os="Windows 11 Home SL",
                     camera_front="720p HD", camera_rear=None, weight="2.5kg", color="Đen",
                     dimensions="357 x 254 x 29 mm", release_date=datetime(2025, 10, 1),
                     graphics_card="Card rời - NVIDIA GeForce RTX 5080, 16 GB",
                     ports="1 x USB Type-C with Thunderbolt 5 (hỗ trợ USB 4, DisplayPort 2.1 và Power Delivery 3.0)",
                     warranty="24 tháng")
        p35 = Product(name="GIGABYTE Gaming G5 MF5 RC555", price=20790000, brand_id=brand5.id, cost_price=16710000,
                      stock=100,
                      category_id=laptop.id, cpu="Intel Core i5 Raptor Lake - 13500H", ram="16GB DDR5",
                      storage="512GB SSD",
                      screen="15.6 inch Full HD (1920 x 1080), 144Hz", battery="54Wh", os="Windows 11 Home SL",
                      camera_front="720p HD", camera_rear=None, weight="2.115kg", color="Đen",
                      dimensions="360 x 238 x 22.7 mm", release_date=datetime(2023, 10, 1),
                      graphics_card="Card rời - NVIDIA GeForce RTX 4050, 6 GB",
                      ports="1 x Headphone/microphone combo LAN (RJ45)",
                      warranty="24 tháng")
        p36 = Product(name="GIGABYTE Gaming G6 MF RC56", price=23390000, brand_id=brand5.id, cost_price=19990000,
                      stock=100,
                      category_id=laptop.id, cpu="Intel Core i7 Raptor Lake - 13620H", ram="16GB DDR5",
                      storage="512GB SSD",
                      screen="16 inch WUXGA (1920 x 1200), 144Hz", battery="54Wh", os="Windows 11 Home SL",
                      camera_front="720p HD", camera_rear=None, weight="2.292kg", color="Đen",
                      dimensions="359.5 x 263.8 x 26 mm", release_date=datetime(2024, 10, 1),
                      graphics_card="Card rời - NVIDIA GeForce RTX 4050, 6 GB",
                      ports="1 x Headphone/microphone combo LAN (RJ45)",
                      warranty="24 tháng")
        p37 = Product(name="GIGABYTE Gaming G6X", price=31390000, brand_id=brand5.id, cost_price=24540000,
                      stock=100,
                      category_id=laptop.id, cpu="Intel Core i7 Raptor Lake - 13650HX", ram="16GB DDR5",
                      storage="1TB SSD",
                      screen="16 inch WUXGA (1920 x 1200), 165Hz", battery="73Wh", os="Windows 11 Home SL",
                      camera_front="720p HD", camera_rear=None, weight="2.533kg", color="Đen",
                      dimensions="361 x 259 x 28.9 mm", release_date=datetime(2024, 10, 1),
                      graphics_card="Card rời - NVIDIA GeForce RTX 4060, 8 GB",
                      ports="1 x Headphone/microphone combo LAN (RJ45)",
                      warranty="24 tháng")
        p38 = Product(name="MacBook Air M4", price=25590000, brand_id=brand8.id, cost_price=21910000, stock=100,
                      category_id=laptop.id, cpu="Apple M4", ram="16GB ", storage="256GB SSD",
                      screen="13.6 inch Liquid Retina XDR display (3024 x 1964), 120Hz", battery="53.8Wh",
                      os="macOS Sequoia",
                      camera_front="720p HD", camera_rear=None, weight="1.24kg", color="Vàng",
                      dimensions="304.1 x 215 x 11.3 mm", release_date=datetime(2025, 3, 1),
                      graphics_card="Card tích hợp - 8 nhân GPU",
                      ports="2 x Thunderbolt 4.0 (hỗ trợ USB 4, USB Type-C, DisplayPort và Power Delivery)",
                      warranty="24 tháng")
        p39 = Product(name="MacBook Air M2", price=19990000, brand_id=brand8.id, cost_price=14230000, stock=100,
                      category_id=laptop.id, cpu="Apple M2", ram="16GB ", storage="256GB SSD",
                      screen="13.6 inch Liquid Retina (2560 x 1664), 120Hz", battery="53.8Wh",
                      os="macOS Sequoia",
                      camera_front="720p HD", camera_rear=None, weight="1.24kg", color="Vàng đồng",
                      dimensions="304.1 x 215 x 11.3 mm", release_date=datetime(2022, 6, 1),
                      graphics_card="Card tích hợp - 8 nhân GPU",
                      ports="2 x Thunderbolt 3",
                      warranty="24 tháng")
        p40 = Product(name="MacBook Pro Nano M4 Max", price=79790000, brand_id=brand8.id, cost_price=72210000, stock=100,
                      category_id=laptop.id, cpu="Apple M4 Max", ram="36GB ", storage="1TB SSD",
                      screen="14.2 inch Liquid Retina XDR display (3024 x 1964), 120Hz", battery="72.4Wh",
                      os="macOS Sequoia",
                      camera_front="720p HD", camera_rear=None, weight="1.62kg", color="Vàng đồng",
                      dimensions="312.6 x 221.2 x 15.5 mm", release_date=datetime(2024, 10, 1),
                      graphics_card="Card tích hợp - 32 nhân GPU",
                      ports="3 x Thunderbolt 5 (USB-C) (hỗ trợ Charging, DisplayPort, Thunderbolt 4 và USB 4 (up to 40Gb/s))",
                      warranty="24 tháng")
        p41 = Product(name="HP 15", price=13290000, brand_id=brand9.id, cost_price=9540000,
                      stock=100,
                      category_id=laptop.id, cpu="AMD Ryzen 5 - 7430U", ram="16GB DDR4",
                      storage="512GB SSD",
                      screen="15.6 inch Full HD (1920 x 1080), 60Hz", battery="41Wh", os="Windows 11 Home SL",
                      camera_front="720p HD", camera_rear=None, weight="1.59kg", color="Vàng",
                      dimensions="359.8 x 236 x 18.6 mm", release_date=datetime(2023, 10, 1),
                      graphics_card="Card tích hợp - AMD Radeon Graphics",
                      ports="1 x USB Type-C (chỉ hỗ trợ truyền dữ liệu)",
                      warranty="24 tháng")
        p42 = Product(name="HP 240 G10", price=16290000, brand_id=brand9.id, cost_price=12220000,
                      stock=100,
                      category_id=laptop.id, cpu="Intel Core i5 Raptor Lake - 1334U", ram="16GB DDR4",
                      storage="512GB SSD",
                      screen="14 inch Full HD (1920 x 1080), 60Hz", battery="41Wh", os="Windows 11 Home SL",
                      camera_front="720p HD", camera_rear=None, weight="1.36kg", color="Vàng",
                      dimensions="324 x 215 x 17.9 mm", release_date=datetime(2025, 10, 1),
                      graphics_card="Card tích hợp - Intel UHD Graphics",
                      ports="1 x Headphone/microphone combo",
                      warranty="24 tháng")
        p43 = Product(name="HP 15 fd0303TU", price=11490000, brand_id=brand9.id, cost_price=8120000,
                      stock=100,
                      category_id=laptop.id, cpu="Intel Core i3 Raptor Lake - 1315U", ram="8GB DDR4",
                      storage="512GB SSD",
                      screen="15.6 inch Full HD (1920 x 1080), 60Hz", battery="41Wh", os="Windows 11 Home SL",
                      camera_front="720p HD", camera_rear=None, weight="1.59kg", color="Vàng",
                      dimensions="359.8 x 236 x 18.6 mm", release_date=datetime(2024, 10, 1),
                      graphics_card="Card tích hợp - Intel UHD Graphics",
                      ports="1 x USB Type-C (chỉ hỗ trợ truyền dữ liệu)",
                      warranty="24 tháng")
        p44 = Product(name="Lenovo Gaming LOQ", price=20490000, brand_id=brand7.id, cost_price=15460000, stock=100,
                      category_id=laptop.id, cpu="Intel Core i5 Alder Lake - 12450HX", ram="16GB DDR5", storage="512GB SSD",
                      screen="15.6 inch Full HD (1920 x 1080), 144Hz", battery="57Wh", os="Windows 11 Home SL",
                      camera_front="720p HD", camera_rear=None, weight="1.77kg", color="Xám",
                      dimensions="359.3 x 236 x 22.95 mm", release_date=datetime(2025, 10, 1),
                      graphics_card="Card rời - NVIDIA GeForce RTX 3050, 6 GB", ports="1 x USB Type-C (chỉ hỗ trợ truyền dữ liệu)",
                      warranty="24 tháng")
        p45 = Product(name="Lenovo Gaming Legion Pro 7", price=94990000, brand_id=brand7.id, cost_price=45670000, stock=100,
                      category_id=laptop.id, cpu="Intel Core Ultra 9 Arrow Lake - 275HX", ram="32GB DDR5",
                      storage="1TB SSD",
                      screen="16 inch WQXGA (2560 x 1600) OLED, 240Hz", battery="80Wh", os="Windows 11 Home SL + Office Home 2024 vĩnh viễn",
                      camera_front="720p HD", camera_rear=None, weight="2.57kg", color="Đen",
                      dimensions="364.38 x 275.94 x 26.65 mm", release_date=datetime(2025, 10, 1),
                      graphics_card="Card rời - NVIDIA GeForce RTX 5080, 16 GB",
                      ports="1 x USB-C 3.2 (hỗ trợ USB Power Delivery 65-100W và DisplayPort 2.1)",
                      warranty="24 tháng")
        p46 = Product(name="Lenovo Gaming Legion 5 Pro", price=57990000, brand_id=brand7.id, cost_price=43210000,
                      stock=100,
                      category_id=laptop.id, cpu="Intel Core Ultra 9 Arrow Lake - 275HX", ram="32GB DDR5",
                      storage="1TB SSD",
                      screen="16 inch WQXGA (2560 x 1600) OLED, 240Hz", battery="80Wh",
                      os="Windows 11 Home SL + Office Home 2024 vĩnh viễn",
                      camera_front="720p HD", camera_rear=None, weight="2.43kg", color="Đen",
                      dimensions="364.38 x 268.06 x 25.95 mm", release_date=datetime(2025, 10, 1),
                      graphics_card="Card rời - NVIDIA GeForce RTX 5070, 8 GB",
                      ports="1 x USB-C 3.2 (hỗ trợ USB Power Delivery 65-100W và DisplayPort 2.1)",
                      warranty="24 tháng")
        p47 = Product(name="Asus Gaming ROG Zephyrus G16", price=59990000, brand_id=brand11.id, cost_price=53320000, stock=100,
                      category_id=laptop.id, cpu="Intel Core Ultra 9 Arrow Lake - 285H", ram="32GB LPDDR5X",
                      storage="1TB SSD",
                      screen="16 inch WQXGA (2560 x 1600) OLED, 240Hz", battery="90Wh", os="Windows 11 Home SL",
                      camera_front="720p HD", camera_rear=None, weight="1.85kg", color="Xám",
                      dimensions="354 x 246 x 16.4 mm", release_date=datetime(2025, 10, 1),
                      graphics_card="Card rời - NVIDIA GeForce RTX 5060, 8 GB",
                      ports="1 x USB Type-C 3.2 (hỗ trợ Power Delivery và DisplayPort)",
                      warranty="24 tháng")
        p48 = Product(name="Asus Gaming ROG Strix G6", price=43690000, brand_id=brand11.id, cost_price=39990000,
                      stock=100,
                      category_id=laptop.id, cpu="Intel Core i7 Raptor Lake - 14650HX", ram="32GB DDR5",
                      storage="1TB SSD",
                      screen="16 inch 2.5K, 240Hz", battery="90Wh", os="Windows 11 Home",
                      camera_front="720p HD", camera_rear=None, weight="2.65kg", color="Xám",
                      dimensions="354 x 268 x 30.8 mm", release_date=datetime(2025, 10, 1),
                      graphics_card="Card rời - NVIDIA GeForce RTX 5060, 8 GB",
                      ports="1 x USB Type-C 3.2 (hỗ trợ Power Delivery và DisplayPort)",
                      warranty="24 tháng")
        p49 = Product(name="Asus Zenbook 14", price=30490000, brand_id=brand11.id, cost_price=27120000,
                      stock=100,
                      category_id=laptop.id, cpu="AMD Ryzen AI 7 - 350", ram="32GB LPDDR5X",
                      storage="1TB SSD",
                      screen="14 inch 3K (2880 x 1800), 120Hz", battery="75Wh", os="Windows 11 Home + Office Home 2024 + Microsoft 365 Basic",
                      camera_front="720p HD", camera_rear=None, weight="1.2kg", color="Đen",
                      dimensions="312.4 x 220.1 x 14.9 mm", release_date=datetime(2025, 10, 1),
                      graphics_card="Card tích hợp - AMD Radeon Graphics",
                      ports="1 x USB 4.0 Gen 3 Type-C (Hỗ trợ power delivery)",
                      warranty="24 tháng")
        p50 = Product(name="Asus Vivobook S16", price=29490000, brand_id=brand11.id, cost_price=22110000,
                      stock=100,
                      category_id=laptop.id, cpu="Intel Core Ultra 7 Arrow Lake - 255H", ram="16GB LPDDR5X",
                      storage="512GB SSD",
                      screen="16 inch 3K (2880 x 1800), 120Hz", battery="75Wh",
                      os="Windows 11 Home",
                      camera_front="720p HD", camera_rear=None, weight="1.5kg", color="Xanh dương",
                      dimensions="353.6 x 246.9 x 15.9 mm", release_date=datetime(2025, 10, 1),
                      graphics_card="Card tích hợp - Intel Arc Graphics",
                      ports="2 x Thunderbolt 4 (hỗ trợ Power Delivery, DisplayPort)",
                      warranty="24 tháng")

        db.session.add_all([p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15, p16,p17, p18, p19, p20, p21, p22,p23, p24, p25, p26, p27, p28, p29, p30, p31,p32,p33,
                            p34,p35,p36,p37,p38,p39,p40,p41,p42,p43,p44,p45,p46,p47,p48,p49,p50])
        db.session.commit()
        image_urls = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907049/ip141_adz2px.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907050/ip145_syddme.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907049/ip142_uqnc7x.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907050/ip144_gw8o0m.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907050/ip143_ffigej.jpg"
        ]
        image_urls1 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907052/ip155_drdkii.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907051/ip152_ailpyy.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907051/ip151_lf1pvk.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907051/ip153_pef3il.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907052/ip154_c0tjym.jpg"
        ]
        image_urls2 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907053/ip161_kbisee.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907053/ip165_ejek3q.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907053/ip164_epsfs4.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907053/ip163_ymwn7w.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907052/ip162_sdzot2.jpg"
        ]
        image_urls4 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907055/ipx1_hjdl87.png",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907055/ipx2_s4payz.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907056/ipx5_vi0x3l.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907055/ipx3_cs6sxd.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907055/ipx4_rzdghh.jpg"
        ]
        image_urls5 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907054/ip82_gv3zgq.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907054/ip81_bjagfe.png",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907054/ip83_erqrnr.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907055/ip84_rsv5wq.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907055/ip85_pci3kg.jpg"
        ]
        image_urls6 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907059/ss1_jzxsez.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907058/ss2_zd1zr1.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907079/ss3_z69zb9.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907079/ss4_zw75sg.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907079/ss5_lvigih.jpg"
        ]
        image_urls7 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907057/op1_ru3jab.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907057/op2_u5pj9r.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907058/op5_vbldse.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907058/op4_tnoogs.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907057/op3_t4th9i.jpg"
        ]
        image_urls8 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907079/x1_utzi5i.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907079/x5_nqk5iq.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907079/x4_xxkqtk.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907079/x3_fk8fdo.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907079/x2_vpzuum.jpg"
        ]
        image_urls9 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907052/d1_fntktd.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907055/d4_r9oltt.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907053/d5_mfrb2r.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907053/d3_vet2jj.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907053/d2_fzrlzz.jpg"
        ]
        image_urls10 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907054/g1_uzgp7d.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907055/g5_jyd7o5.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907054/g3_d8t1h2.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907054/g4_ortdtn.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907054/g2_pzaapm.jpg"
        ]
        image_urls11 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907048/a1_s9ttsl.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907048/a3_l5fa4a.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907048/a2_bndyvc.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907048/a4_khor4p.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907049/a5_g15bwv.jpg"
        ]
        image_urls12 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907056/l1_ouhok7.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907056/l5_xxt9zg.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907056/l4_tk0fhn.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907056/l3_f81sha.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907056/l2_vgfeus.jpg"
        ]
        image_urls13= [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907056/m1_wruxe7.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907057/m5_pysq2w.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907057/m3_jirjg3.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907057/m2_qwum3t.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907057/m4_pjgkif.jpg"
        ]
        image_urls14 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907049/h5_bnvghd.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907049/h4_cujdzv.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907049/h3_jneq8h.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907049/h2_ru1ofj.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907048/h1_vhbu6i.jpg"
        ]
        image_urls15 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907049/a1_khoeix.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907050/a4_msopvw.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907050/a5_bwqksf.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907049/a3_u0ppys.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907049/a2_cnhfgo.jpg"
        ]

        image_urls3 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907051/a1_ci5v5a.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907052/a5_vrgbtg.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907051/a4_ek9nf9.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907051/a3_krpzox.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1756907051/a2_hcsbuo.jpg"
        ]
        image_urls17 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515933/h1_c3kvmd.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515934/h4_wbnkbp.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515934/h5_gwancs.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515933/h3_p3hih6.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515933/h2_ph0x0f.jpg"
        ]
        image_urls18 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515987/h1_yp5qwo.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515988/h3_chjhvt.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515987/h2_q0nukr.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515989/h5_oms0b7.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515988/h4_gffm09.jpg"
        ]
        image_urls19 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515984/h1_hytbbx.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515985/h2_hdyqb9.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515986/h3_qnctjv.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515986/h4_paqxtb.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515986/h5_bq4jpr.jpg"
        ]
        image_urls20 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515982/h1_mgeydz.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515983/h2_my35el.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515983/h3_eqodwb.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515984/h4_hcfjwz.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515984/h5_jkr8ym.jpg"
        ]
        image_urls21 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515955/h1_m4nyxe.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515956/h3_l6d207.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515955/h2_rvqvzg.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515957/h5_qz0pzo.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515956/h4_c7lcyo.jpg"
        ]
        image_urls22 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515957/h1_mqjlz6.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515958/h3_doyl30.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515958/h2_v2gr9l.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515959/h5_l2tsbf.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515959/h4_l13if7.jpg"
        ]
        image_urls23 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515950/h1_hl6g4c.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515951/h3_ae0hyu.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515951/h2_kcp4de.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515952/h5_coqbqw.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515952/h4_wrvnwk.jpg"
        ]
        image_urls24 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515952/h1_oqtjwk.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515953/h3_qr47sc.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515953/h2_lmdmx9.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515954/h5_gmaxfl.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515954/h4_voven7.jpg"
        ]
        image_urls25 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515970/h1_lgtaew.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515971/h3_wmbsrs.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515970/h2_uuckfo.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515971/h4_kuyryc.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515972/h5_r02zhr.jpg"
        ]
        image_urls26 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515977/h1_hpty1y.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515978/h3_aiivoa.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515978/h2_j5ugaz.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515979/h4_k1y0m9.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515979/h5_zeoxml.jpg"
        ]
        image_urls27 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515980/h1_aze0rf.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515981/h3_kdxjq8.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515980/h2_mff3o1.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515982/h5_lrspnf.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515981/h4_ril329.jpg"
        ]
        image_urls28 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515972/h1_mklhtr.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515973/h3_xmvr0h.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515973/h2_h9lt88.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515974/h5_mn79dh.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515974/h4_mrua4s.jpg"
        ]
        image_urls29 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515975/h1_jjlgv1.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515976/h3_b9bp7l.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515975/h2_tdqcqc.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515977/h5_xjjmca.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515977/h4_aoysmr.jpg"
        ]
        image_urls30 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515960/h1_o1leuj.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515961/h3_kyhbn1.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515960/h2_o5ybf7.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515962/h5_oaabhc.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515961/h4_xpwevs.jpg"
        ]
        image_urls31 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515962/h1_q1zjgi.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515963/h3_ivujko.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515963/h2_zeeroz.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515964/h5_tmgffs.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515964/h4_cphd1a.jpg"
        ]

        image_urls32 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515967/h1_fyttcz.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515968/h3_tqmh3m.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515968/h2_jjeqqf.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515969/h5_v2sqv2.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515969/h4_ldn52p.jpg"
        ]
        image_urls33 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515965/h1_avqzqh.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515966/h3_u5lvau.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515965/h2_o2lqpg.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515967/h5_ki6mz5.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515966/h4_of9e3i.jpg"
        ]
        image_urls34 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515317/h1_bjbztw.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515576/h3_ftjdsw.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515317/h2_in9ff0.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515577/h5_tkl2qx.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515576/h4_mx9vuj.jpg"
        ]
        image_urls35 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515577/h1_lbidpa.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515578/h3_ffo7vj.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515578/h2_nx6a56.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515579/h4_bjorns.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515579/h5_aj32im.jpg"
        ]
        image_urls36 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515580/h1_bk7i51.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515581/h3_ixoejx.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515580/h2_buxaof.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515582/h5_xjvgqx.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515582/h4_korijf.jpg"
        ]
        image_urls37 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515582/h1_gzklve.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515583/h3_epnhne.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515583/h2_woabu5.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515584/h5_rzjflc.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515584/h4_vbwn3o.jpg"
        ]
        image_urls38 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515945/h1_koxeud.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515946/h3_iad5ia.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515945/h2_m3nyt5.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515947/h5_z7evaz.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515946/h4_nkp5cz.jpg"
        ]
        image_urls39 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515942/h1_nls0kc.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515943/h3_tutvt6.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515944/h5_zw0lfx.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515944/h4_usqgoh.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515943/h2_y9sqpz.jpg"
        ]
        image_urls40 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515947/h1_ak5kxk.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515949/h4_c9j644.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515948/h2_viiqpf.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515949/h5_sisl0a.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515949/h3_wgrsfg.jpg"
        ]
        image_urls41 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515635/h1_wicmrj.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515638/h4_vrh6cb.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515637/h2_l3wat2.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515658/h5_amreuw.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515638/h3_ysdd2c.jpg"
        ]
        image_urls42 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515828/h1_azf5ik.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515860/h3_qqug0h.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515834/h2_nv8br7.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515891/h5_g1ddhe.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515861/h4_g8or8n.jpg"
        ]
        image_urls43 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515667/h1_csgqci.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515827/h3_ulwkbl.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515826/h2_g8f7yt.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515828/h5_akauvg.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515827/h4_reemrt.jpg"
        ]
        image_urls44 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515940/h1_wno4uk.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515941/h3_twqdtk.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515940/h2_spdbig.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515942/h5_mtcp95.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515941/h4_drftde.jpg"
        ]
        image_urls45 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515937/h1_r8vctc.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515938/h3_ftn6ik.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515938/h2_qotbom.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515939/h5_nd0la3.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515939/h4_snflgx.jpg"
        ]
        image_urls46 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515935/h1_v0vhj0.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515936/h4_kexpws.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515935/h2_efl2cu.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515937/h5_l0enlg.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515936/h3_nldoj1.jpg"
        ]
        image_urls47 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515142/h1_r4bhsn.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515310/h3_nw4nmu.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515151/h2_x5dn6i.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515311/h5_jknhjg.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515310/h4_hbar8x.jpg"
        ]
        image_urls48 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515139/h1_v0rhxl.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515141/h3_zute2x.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515140/h2_d3nbzt.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515142/h5_ogbjjd.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515141/h4_iuxi6u.jpg"
        ]

        image_urls49 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515314/h1_qde8sb.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515315/h4_zyuqzk.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515316/j5_vslfms.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515315/h3_tflybd.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515315/h2_ie6ous.jpg"
        ]
        image_urls50 = [
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515311/h1_l1px6s.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515312/h3_jmqfye.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515312/h2_ugeouy.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515314/h5_izzmsg.jpg",
            "https://res.cloudinary.com/dbnra16ca/image/upload/v1760515313/h4_ek0jis.jpg"
        ]


        for url in image_urls:
            img = ProductImage(url=url, product_id=p1.id)
            db.session.add(img)
        for url in image_urls1:
            img = ProductImage(url=url, product_id=p2.id)
            db.session.add(img)
        for url in image_urls3:
            img = ProductImage(url=url, product_id=p16.id)
            db.session.add(img)
        for url in image_urls4:
            img = ProductImage(url=url, product_id=p4.id)
            db.session.add(img)
        for url in image_urls5:
            img = ProductImage(url=url, product_id=p5.id)
            db.session.add(img)
        for url in image_urls6:
            img = ProductImage(url=url, product_id=p6.id)
            db.session.add(img)
        for url in image_urls7:
            img = ProductImage(url=url, product_id=p7.id)
            db.session.add(img)
        for url in image_urls8:
            img = ProductImage(url=url, product_id=p8.id)
            db.session.add(img)
        for url in image_urls9:
            img = ProductImage(url=url, product_id=p9.id)
            db.session.add(img)
        for url in image_urls10:
            img = ProductImage(url=url, product_id=p10.id)
            db.session.add(img)
        for url in image_urls11:
            img = ProductImage(url=url, product_id=p11.id)
            db.session.add(img)
        for url in image_urls12:
            img = ProductImage(url=url, product_id=p12.id)
            db.session.add(img)
        for url in image_urls13:
            img = ProductImage(url=url, product_id=p13.id)
            db.session.add(img)
        for url in image_urls14:
            img = ProductImage(url=url, product_id=p14.id)
            db.session.add(img)
        for url in image_urls15:
            img = ProductImage(url=url, product_id=p15.id)
            db.session.add(img)
        for url in image_urls2:
            img = ProductImage(url=url, product_id=p3.id)
            db.session.add(img)
        for url in image_urls17:
            img = ProductImage(url=url, product_id=p17.id)
            db.session.add(img)
        for url in image_urls18:
            img = ProductImage(url=url, product_id=p18.id)
            db.session.add(img)
        for url in image_urls19:
            img = ProductImage(url=url, product_id=p19.id)
            db.session.add(img)
        for url in image_urls20:
            img = ProductImage(url=url, product_id=p20.id)
            db.session.add(img)
        for url in image_urls21:
            img = ProductImage(url=url, product_id=p21.id)
            db.session.add(img)
        for url in image_urls22:
            img = ProductImage(url=url, product_id=p22.id)
            db.session.add(img)
        for url in image_urls23:
            img = ProductImage(url=url, product_id=p23.id)
            db.session.add(img)
        for url in image_urls24:
            img = ProductImage(url=url, product_id=p24.id)
            db.session.add(img)
        for url in image_urls25:
            img = ProductImage(url=url, product_id=p25.id)
            db.session.add(img)
        for url in image_urls26:
            img = ProductImage(url=url, product_id=p26.id)
            db.session.add(img)
        for url in image_urls27:
            img = ProductImage(url=url, product_id=p27.id)
            db.session.add(img)
        for url in image_urls28:
            img = ProductImage(url=url, product_id=p28.id)
            db.session.add(img)
        for url in image_urls29:
            img = ProductImage(url=url, product_id=p29.id)
            db.session.add(img)
        for url in image_urls30:
            img = ProductImage(url=url, product_id=p30.id)
            db.session.add(img)
        for url in image_urls31:
            img = ProductImage(url=url, product_id=p31.id)
            db.session.add(img)
        for url in image_urls32:
            img = ProductImage(url=url, product_id=p32.id)
            db.session.add(img)
        for url in image_urls33:
            img = ProductImage(url=url, product_id=p33.id)
            db.session.add(img)
        for url in image_urls34:
            img = ProductImage(url=url, product_id=p34.id)
            db.session.add(img)
        for url in image_urls35:
            img = ProductImage(url=url, product_id=p35.id)
            db.session.add(img)
        for url in image_urls36:
            img = ProductImage(url=url, product_id=p36.id)
            db.session.add(img)
        for url in image_urls37:
            img = ProductImage(url=url, product_id=p37.id)
            db.session.add(img)
        for url in image_urls38:
            img = ProductImage(url=url, product_id=p38.id)
            db.session.add(img)
        for url in image_urls39:
            img = ProductImage(url=url, product_id=p39.id)
            db.session.add(img)
        for url in image_urls40:
            img = ProductImage(url=url, product_id=p40.id)
            db.session.add(img)
        for url in image_urls41:
            img = ProductImage(url=url, product_id=p41.id)
            db.session.add(img)
        for url in image_urls42:
            img = ProductImage(url=url, product_id=p42.id)
            db.session.add(img)
        for url in image_urls43:
            img = ProductImage(url=url, product_id=p43.id)
            db.session.add(img)
        for url in image_urls44:
            img = ProductImage(url=url, product_id=p44.id)
            db.session.add(img)
        for url in image_urls45:
            img = ProductImage(url=url, product_id=p45.id)
            db.session.add(img)
        for url in image_urls46:
            img = ProductImage(url=url, product_id=p46.id)
            db.session.add(img)
        for url in image_urls47:
            img = ProductImage(url=url, product_id=p47.id)
            db.session.add(img)
        for url in image_urls48:
            img = ProductImage(url=url, product_id=p48.id)
            db.session.add(img)
        for url in image_urls50:
            img = ProductImage(url=url, product_id=p50.id)
            db.session.add(img)
        for url in image_urls49:
            img = ProductImage(url=url, product_id=p49.id)
            db.session.add(img)
        db.session.commit()
    admin_username = "admin"
    admin_email = "admin@example.com"
    admin = User(
        username=admin_username,
        email=admin_email,
        role=UserRole.ADMIN
    )
    admin.set_password("admin123")  # mật khẩu admin
    db.session.add(admin)
    db.session.commit()

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()  # tạo bảng
        seed_data(db)      # thêm dữ liệu test
        print("Database đã tạo và seed dữ liệu thành công!")