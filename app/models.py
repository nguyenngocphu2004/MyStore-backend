from backend.app import create_app, db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import Enum
import enum


class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"

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


class Product(BaseModel):
    __tablename__ = "products"

    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    brand = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
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


class Order(BaseModel):
    __tablename__ = "orders"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # có thể là None
    guest_name = db.Column(db.String(100), nullable=True)   # tên khách vãng lai
    guest_phone = db.Column(db.String(20), nullable=True)   # SĐT khách vãng lai
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_price = db.Column(db.Float, nullable=False)
    delivery_method = db.Column(db.String(20), default="store")
    address = db.Column(db.String(255), nullable=True)
    items = db.relationship("OrderItem", backref="order", lazy=True)

    def __str__(self):
        return self.name

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


def seed_data(db):
    if not Category.query.first():
        phone = Category(name="Điện thoại")
        laptop = Category(name="Laptop")

        db.session.add_all([phone, laptop])
        db.session.commit()

        p1 = Product(name="iPhone 14 Pro Max", price=32990000, brand="Apple",
                     category_id=phone.id, cpu="Apple A16 Bionic", ram="6GB", storage="256GB",
                     screen="6.7 inch OLED, 2796 x 1290 pixels, 120Hz", battery="4323mAh", os="iOS 16",
                     camera_front="12MP", camera_rear="48MP + 12MP + 12MP", weight="240g", color="Deep Purple",
                     dimensions="160.7 x 77.6 x 7.9 mm", release_date=datetime(2022, 9, 16), graphics_card=None,
                     ports="Lightning", warranty="12 tháng")
        p2 = Product(name="iPhone 15 Pro Max", price=35990000,  brand="Apple",
                     category_id=phone.id, cpu="Apple A16 Bionic", ram="6GB", storage="256GB",
                     screen="6.7 inch OLED, 2796 x 1290 pixels, 120Hz", battery="4323mAh", os="iOS 16",
                     camera_front="12MP", camera_rear="48MP + 12MP + 12MP", weight="240g", color="Deep Purple",
                     dimensions="160.7 x 77.6 x 7.9 mm", release_date=datetime(2022, 9, 16), graphics_card=None,
                     ports="Lightning", warranty="12 tháng")
        p3 = Product(name="iPhone 16 Pro Max", price=38990000,  brand="Apple",
                     category_id=phone.id, cpu="Apple A16 Bionic", ram="6GB", storage="256GB",
                     screen="6.7 inch OLED, 2796 x 1290 pixels, 120Hz", battery="4323mAh", os="iOS 16",
                     camera_front="12MP", camera_rear="48MP + 12MP + 12MP", weight="240g", color="Deep Purple",
                     dimensions="160.7 x 77.6 x 7.9 mm", release_date=datetime(2022, 9, 16), graphics_card=None,
                     ports="Lightning", warranty="12 tháng")
        p4 = Product(name="iPhone X", price=30990000,  brand="Apple",
                     category_id=phone.id, cpu="Apple A16 Bionic", ram="6GB", storage="256GB",
                     screen="6.7 inch OLED, 2796 x 1290 pixels, 120Hz", battery="4323mAh", os="iOS 16",
                     camera_front="12MP", camera_rear="48MP + 12MP + 12MP", weight="240g", color="Deep Purple",
                     dimensions="160.7 x 77.6 x 7.9 mm", release_date=datetime(2022, 9, 16), graphics_card=None,
                     ports="Lightning", warranty="12 tháng")
        p5 = Product(name="iPhone 8", price=21990000,  brand="Apple",
                     category_id=phone.id, cpu="Apple A16 Bionic", ram="6GB", storage="256GB",
                     screen="6.7 inch OLED, 2796 x 1290 pixels, 120Hz", battery="4323mAh", os="iOS 16",
                     camera_front="12MP", camera_rear="48MP + 12MP + 12MP", weight="240g", color="Deep Purple",
                     dimensions="160.7 x 77.6 x 7.9 mm", release_date=datetime(2022, 9, 16), graphics_card=None,
                     ports="Lightning", warranty="12 tháng")
        p6 = Product(name="Samsung Fold", price=3590000,  brand="Samsung",
                     category_id=phone.id, cpu="Apple A16 Bionic", ram="6GB", storage="256GB",
                     screen="6.7 inch OLED, 2796 x 1290 pixels, 120Hz", battery="4323mAh", os="iOS 16",
                     camera_front="12MP", camera_rear="48MP + 12MP + 12MP", weight="240g", color="Deep Purple",
                     dimensions="160.7 x 77.6 x 7.9 mm", release_date=datetime(2022, 9, 16), graphics_card=None,
                     ports="Lightning", warranty="12 tháng")
        p7 = Product(name="Oppo 14 Pro Max", price=32990000,  brand="Oppo",
                     category_id=phone.id, cpu="Apple A16 Bionic", ram="6GB", storage="256GB",
                     screen="6.7 inch OLED, 2796 x 1290 pixels, 120Hz", battery="4323mAh", os="iOS 16",
                     camera_front="12MP", camera_rear="48MP + 12MP + 12MP", weight="240g", color="Deep Purple",
                     dimensions="160.7 x 77.6 x 7.9 mm", release_date=datetime(2022, 9, 16), graphics_card=None,
                     ports="Lightning", warranty="12 tháng")
        p8 = Product(name="Xiaomi 14 Pro Max", price=32990000,  brand="Xiaomi",
                     category_id=phone.id, cpu="Apple A16 Bionic", ram="6GB", storage="256GB",
                     screen="6.7 inch OLED, 2796 x 1290 pixels, 120Hz", battery="4323mAh", os="iOS 16",
                     camera_front="12MP", camera_rear="48MP + 12MP + 12MP", weight="240g", color="Deep Purple",
                     dimensions="160.7 x 77.6 x 7.9 mm", release_date=datetime(2022, 9, 16), graphics_card=None,
                     ports="Lightning", warranty="12 tháng")
        p9 = Product(name="Dell XPS 13 9310", price=34990000,  brand="Dell",
                     category_id=laptop.id, cpu="Intel Core i7-1185G7", ram="16GB LPDDR4x", storage="512GB SSD",
                     screen="13.4 inch FHD+ (1920 x 1200), 60Hz", battery="52Wh", os="Windows 11",
                     camera_front="720p HD", camera_rear=None, weight="1.2kg", color="Platinum Silver",
                     dimensions="295.7 x 198.7 x 14.8 mm", release_date=datetime(2021, 10, 1),
                     graphics_card="Intel Iris Xe Graphics", ports="2 x Thunderbolt 4, 1 x 3.5mm Audio",
                     warranty="24 tháng")
        p10 = Product(name="Gigabyte XPS 13 9310", price=34990000,  brand="Gigabyte",
                      category_id=laptop.id, cpu="Intel Core i7-1185G7", ram="16GB LPDDR4x", storage="512GB SSD",
                      screen="13.4 inch FHD+ (1920 x 1200), 60Hz", battery="52Wh", os="Windows 11",
                      camera_front="720p HD", camera_rear=None, weight="1.2kg", color="Platinum Silver",
                      dimensions="295.7 x 198.7 x 14.8 mm", release_date=datetime(2021, 10, 1),
                      graphics_card="Intel Iris Xe Graphics", ports="2 x Thunderbolt 4, 1 x 3.5mm Audio",
                      warranty="24 tháng")
        p11 = Product(name="Acer XPS 13 9310", price=34990000,  brand="Acer",
                      category_id=laptop.id, cpu="Intel Core i7-1185G7", ram="16GB LPDDR4x", storage="512GB SSD",
                      screen="13.4 inch FHD+ (1920 x 1200), 60Hz", battery="52Wh", os="Windows 11",
                      camera_front="720p HD", camera_rear=None, weight="1.2kg", color="Platinum Silver",
                      dimensions="295.7 x 198.7 x 14.8 mm", release_date=datetime(2021, 10, 1),
                      graphics_card="Intel Iris Xe Graphics", ports="2 x Thunderbolt 4, 1 x 3.5mm Audio",
                      warranty="24 tháng")
        p12 = Product(name="Lenovo XPS 13 9310", price=34990000,  brand="Lenovo",
                      category_id=laptop.id, cpu="Intel Core i7-1185G7", ram="16GB LPDDR4x", storage="512GB SSD",
                      screen="13.4 inch FHD+ (1920 x 1200), 60Hz", battery="52Wh", os="Windows 11",
                      camera_front="720p HD", camera_rear=None, weight="1.2kg", color="Platinum Silver",
                      dimensions="295.7 x 198.7 x 14.8 mm", release_date=datetime(2021, 10, 1),
                      graphics_card="Intel Iris Xe Graphics", ports="2 x Thunderbolt 4, 1 x 3.5mm Audio",
                      warranty="24 tháng")
        p13 = Product(name="Macbook XPS 13 9310", price=34990000,  brand="Macbook",
                      category_id=laptop.id, cpu="Intel Core i7-1185G7", ram="16GB LPDDR4x", storage="512GB SSD",
                      screen="13.4 inch FHD+ (1920 x 1200), 60Hz", battery="52Wh", os="Windows 11",
                      camera_front="720p HD", camera_rear=None, weight="1.2kg", color="Platinum Silver",
                      dimensions="295.7 x 198.7 x 14.8 mm", release_date=datetime(2021, 10, 1),
                      graphics_card="Intel Iris Xe Graphics", ports="2 x Thunderbolt 4, 1 x 3.5mm Audio",
                      warranty="24 tháng")
        p14 = Product(name="Hp XPS 13 9310", price=34990000,  brand="Hp",
                      category_id=laptop.id, cpu="Intel Core i7-1185G7", ram="16GB LPDDR4x", storage="512GB SSD",
                      screen="13.4 inch FHD+ (1920 x 1200), 60Hz", battery="52Wh", os="Windows 11",
                      camera_front="720p HD", camera_rear=None, weight="1.2kg", color="Platinum Silver",
                      dimensions="295.7 x 198.7 x 14.8 mm", release_date=datetime(2021, 10, 1),
                      graphics_card="Intel Iris Xe Graphics", ports="2 x Thunderbolt 4, 1 x 3.5mm Audio",
                      warranty="24 tháng")
        p15 = Product(name="Acer XPS 13 9310", price=34990000,  brand="Acer",
                      category_id=laptop.id, cpu="Intel Core i7-1185G7", ram="16GB LPDDR4x", storage="512GB SSD",
                      screen="13.4 inch FHD+ (1920 x 1200), 60Hz", battery="52Wh", os="Windows 11",
                      camera_front="720p HD", camera_rear=None, weight="1.2kg", color="Platinum Silver",
                      dimensions="295.7 x 198.7 x 14.8 mm", release_date=datetime(2021, 10, 1),
                      graphics_card="Intel Iris Xe Graphics", ports="2 x Thunderbolt 4, 1 x 3.5mm Audio",
                      warranty="24 tháng")
        p16 = Product(name="Asus XPS 14 9310", price=36990000,  brand="Asus",
                      category_id=laptop.id, cpu="Intel Core i7-1185G7", ram="16GB LPDDR4x", storage="512GB SSD",
                      screen="13.4 inch FHD+ (1920 x 1200), 60Hz", battery="52Wh", os="Windows 11",
                      camera_front="720p HD", camera_rear=None, weight="1.2kg", color="Platinum Silver",
                      dimensions="295.7 x 198.7 x 14.8 mm", release_date=datetime(2021, 10, 1),
                      graphics_card="Intel Iris Xe Graphics", ports="2 x Thunderbolt 4, 1 x 3.5mm Audio",
                      warranty="24 tháng")


        db.session.add_all([p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15, p16])
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
        print("✅ Database đã tạo và seed dữ liệu thành công!")