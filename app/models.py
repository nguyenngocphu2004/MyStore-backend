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
    image = db.Column(db.String(255), nullable=True)
    brand = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)

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
def seed_data(db):
    if not Category.query.first():
        phone = Category(name="Điện thoại")
        laptop = Category(name="Laptop")

        db.session.add_all([phone, laptop])
        db.session.commit()

        p1 = Product(name="iPhone 14 Pro Max", price=32990000, image="iphone14promax.jpg", brand="Apple",
                     category_id=phone.id, cpu="Apple A16 Bionic", ram="6GB", storage="256GB",
                     screen="6.7 inch OLED, 2796 x 1290 pixels, 120Hz", battery="4323mAh", os="iOS 16",
                     camera_front="12MP", camera_rear="48MP + 12MP + 12MP", weight="240g", color="Deep Purple",
                     dimensions="160.7 x 77.6 x 7.9 mm", release_date=datetime(2022, 9, 16), graphics_card=None,
                     ports="Lightning", warranty="12 tháng")
        p2 = Product(name="iPhone 14 Pro Max", price=32990000, image="iphone14promax.jpg", brand="Apple",
                     category_id=phone.id, cpu="Apple A16 Bionic", ram="6GB", storage="256GB",
                     screen="6.7 inch OLED, 2796 x 1290 pixels, 120Hz", battery="4323mAh", os="iOS 16",
                     camera_front="12MP", camera_rear="48MP + 12MP + 12MP", weight="240g", color="Deep Purple",
                     dimensions="160.7 x 77.6 x 7.9 mm", release_date=datetime(2022, 9, 16), graphics_card=None,
                     ports="Lightning", warranty="12 tháng")
        p3 = Product(name="iPhone 14 Pro Max", price=32990000, image="iphone14promax.jpg", brand="Apple",
                     category_id=phone.id, cpu="Apple A16 Bionic", ram="6GB", storage="256GB",
                     screen="6.7 inch OLED, 2796 x 1290 pixels, 120Hz", battery="4323mAh", os="iOS 16",
                     camera_front="12MP", camera_rear="48MP + 12MP + 12MP", weight="240g", color="Deep Purple",
                     dimensions="160.7 x 77.6 x 7.9 mm", release_date=datetime(2022, 9, 16), graphics_card=None,
                     ports="Lightning", warranty="12 tháng")
        p4 = Product(name="iPhone 14 Pro Max", price=32990000, image="iphone14promax.jpg", brand="Apple",
                     category_id=phone.id, cpu="Apple A16 Bionic", ram="6GB", storage="256GB",
                     screen="6.7 inch OLED, 2796 x 1290 pixels, 120Hz", battery="4323mAh", os="iOS 16",
                     camera_front="12MP", camera_rear="48MP + 12MP + 12MP", weight="240g", color="Deep Purple",
                     dimensions="160.7 x 77.6 x 7.9 mm", release_date=datetime(2022, 9, 16), graphics_card=None,
                     ports="Lightning", warranty="12 tháng")
        p5 = Product(name="iPhone 14 Pro Max", price=32990000, image="iphone14promax.jpg", brand="Apple",
                     category_id=phone.id, cpu="Apple A16 Bionic", ram="6GB", storage="256GB",
                     screen="6.7 inch OLED, 2796 x 1290 pixels, 120Hz", battery="4323mAh", os="iOS 16",
                     camera_front="12MP", camera_rear="48MP + 12MP + 12MP", weight="240g", color="Deep Purple",
                     dimensions="160.7 x 77.6 x 7.9 mm", release_date=datetime(2022, 9, 16), graphics_card=None,
                     ports="Lightning", warranty="12 tháng")
        p6 = Product(name="iPhone 14 Pro Max", price=32990000, image="iphone14promax.jpg", brand="Apple",
                     category_id=phone.id, cpu="Apple A16 Bionic", ram="6GB", storage="256GB",
                     screen="6.7 inch OLED, 2796 x 1290 pixels, 120Hz", battery="4323mAh", os="iOS 16",
                     camera_front="12MP", camera_rear="48MP + 12MP + 12MP", weight="240g", color="Deep Purple",
                     dimensions="160.7 x 77.6 x 7.9 mm", release_date=datetime(2022, 9, 16), graphics_card=None,
                     ports="Lightning", warranty="12 tháng")
        p7 = Product(name="iPhone 14 Pro Max", price=32990000, image="iphone14promax.jpg", brand="Apple",
                     category_id=phone.id, cpu="Apple A16 Bionic", ram="6GB", storage="256GB",
                     screen="6.7 inch OLED, 2796 x 1290 pixels, 120Hz", battery="4323mAh", os="iOS 16",
                     camera_front="12MP", camera_rear="48MP + 12MP + 12MP", weight="240g", color="Deep Purple",
                     dimensions="160.7 x 77.6 x 7.9 mm", release_date=datetime(2022, 9, 16), graphics_card=None,
                     ports="Lightning", warranty="12 tháng")
        p8 = Product(name="iPhone 14 Pro Max", price=32990000, image="iphone14promax.jpg", brand="Apple",
                     category_id=phone.id, cpu="Apple A16 Bionic", ram="6GB", storage="256GB",
                     screen="6.7 inch OLED, 2796 x 1290 pixels, 120Hz", battery="4323mAh", os="iOS 16",
                     camera_front="12MP", camera_rear="48MP + 12MP + 12MP", weight="240g", color="Deep Purple",
                     dimensions="160.7 x 77.6 x 7.9 mm", release_date=datetime(2022, 9, 16), graphics_card=None,
                     ports="Lightning", warranty="12 tháng")
        p9 = Product(name="Dell XPS 13 9310", price=34990000, image="dellxps13.jpg", brand="Dell",
                     category_id=laptop.id, cpu="Intel Core i7-1185G7", ram="16GB LPDDR4x", storage="512GB SSD",
                     screen="13.4 inch FHD+ (1920 x 1200), 60Hz", battery="52Wh", os="Windows 11",
                     camera_front="720p HD", camera_rear=None, weight="1.2kg", color="Platinum Silver",
                     dimensions="295.7 x 198.7 x 14.8 mm", release_date=datetime(2021, 10, 1),
                     graphics_card="Intel Iris Xe Graphics", ports="2 x Thunderbolt 4, 1 x 3.5mm Audio",
                     warranty="24 tháng")
        p10 = Product(name="Dell XPS 13 9310", price=34990000, image="dellxps13.jpg", brand="Dell",
                      category_id=laptop.id, cpu="Intel Core i7-1185G7", ram="16GB LPDDR4x", storage="512GB SSD",
                      screen="13.4 inch FHD+ (1920 x 1200), 60Hz", battery="52Wh", os="Windows 11",
                      camera_front="720p HD", camera_rear=None, weight="1.2kg", color="Platinum Silver",
                      dimensions="295.7 x 198.7 x 14.8 mm", release_date=datetime(2021, 10, 1),
                      graphics_card="Intel Iris Xe Graphics", ports="2 x Thunderbolt 4, 1 x 3.5mm Audio",
                      warranty="24 tháng")
        p11 = Product(name="Dell XPS 13 9310", price=34990000, image="dellxps13.jpg", brand="Dell",
                      category_id=laptop.id, cpu="Intel Core i7-1185G7", ram="16GB LPDDR4x", storage="512GB SSD",
                      screen="13.4 inch FHD+ (1920 x 1200), 60Hz", battery="52Wh", os="Windows 11",
                      camera_front="720p HD", camera_rear=None, weight="1.2kg", color="Platinum Silver",
                      dimensions="295.7 x 198.7 x 14.8 mm", release_date=datetime(2021, 10, 1),
                      graphics_card="Intel Iris Xe Graphics", ports="2 x Thunderbolt 4, 1 x 3.5mm Audio",
                      warranty="24 tháng")
        p12 = Product(name="Dell XPS 13 9310", price=34990000, image="dellxps13.jpg", brand="Dell",
                      category_id=laptop.id, cpu="Intel Core i7-1185G7", ram="16GB LPDDR4x", storage="512GB SSD",
                      screen="13.4 inch FHD+ (1920 x 1200), 60Hz", battery="52Wh", os="Windows 11",
                      camera_front="720p HD", camera_rear=None, weight="1.2kg", color="Platinum Silver",
                      dimensions="295.7 x 198.7 x 14.8 mm", release_date=datetime(2021, 10, 1),
                      graphics_card="Intel Iris Xe Graphics", ports="2 x Thunderbolt 4, 1 x 3.5mm Audio",
                      warranty="24 tháng")
        p13 = Product(name="Dell XPS 13 9310", price=34990000, image="dellxps13.jpg", brand="Dell",
                      category_id=laptop.id, cpu="Intel Core i7-1185G7", ram="16GB LPDDR4x", storage="512GB SSD",
                      screen="13.4 inch FHD+ (1920 x 1200), 60Hz", battery="52Wh", os="Windows 11",
                      camera_front="720p HD", camera_rear=None, weight="1.2kg", color="Platinum Silver",
                      dimensions="295.7 x 198.7 x 14.8 mm", release_date=datetime(2021, 10, 1),
                      graphics_card="Intel Iris Xe Graphics", ports="2 x Thunderbolt 4, 1 x 3.5mm Audio",
                      warranty="24 tháng")
        p14 = Product(name="Dell XPS 13 9310", price=34990000, image="dellxps13.jpg", brand="Dell",
                      category_id=laptop.id, cpu="Intel Core i7-1185G7", ram="16GB LPDDR4x", storage="512GB SSD",
                      screen="13.4 inch FHD+ (1920 x 1200), 60Hz", battery="52Wh", os="Windows 11",
                      camera_front="720p HD", camera_rear=None, weight="1.2kg", color="Platinum Silver",
                      dimensions="295.7 x 198.7 x 14.8 mm", release_date=datetime(2021, 10, 1),
                      graphics_card="Intel Iris Xe Graphics", ports="2 x Thunderbolt 4, 1 x 3.5mm Audio",
                      warranty="24 tháng")
        p15 = Product(name="Dell XPS 13 9310", price=34990000, image="dellxps13.jpg", brand="Dell",
                      category_id=laptop.id, cpu="Intel Core i7-1185G7", ram="16GB LPDDR4x", storage="512GB SSD",
                      screen="13.4 inch FHD+ (1920 x 1200), 60Hz", battery="52Wh", os="Windows 11",
                      camera_front="720p HD", camera_rear=None, weight="1.2kg", color="Platinum Silver",
                      dimensions="295.7 x 198.7 x 14.8 mm", release_date=datetime(2021, 10, 1),
                      graphics_card="Intel Iris Xe Graphics", ports="2 x Thunderbolt 4, 1 x 3.5mm Audio",
                      warranty="24 tháng")
        p16 = Product(name="Dell XPS 13 9310", price=34990000, image="dellxps13.jpg", brand="Dell",
                      category_id=laptop.id, cpu="Intel Core i7-1185G7", ram="16GB LPDDR4x", storage="512GB SSD",
                      screen="13.4 inch FHD+ (1920 x 1200), 60Hz", battery="52Wh", os="Windows 11",
                      camera_front="720p HD", camera_rear=None, weight="1.2kg", color="Platinum Silver",
                      dimensions="295.7 x 198.7 x 14.8 mm", release_date=datetime(2021, 10, 1),
                      graphics_card="Intel Iris Xe Graphics", ports="2 x Thunderbolt 4, 1 x 3.5mm Audio",
                      warranty="24 tháng")

        db.session.add_all([p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15, p16])
        db.session.commit()

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()  # tạo bảng
        seed_data(db)      # thêm dữ liệu test
        print("✅ Database đã tạo và seed dữ liệu thành công!")