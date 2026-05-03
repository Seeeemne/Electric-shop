from datetime import datetime

from extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    products = db.relationship(
        "Product",
        backref="category_obj",
        lazy=True,
    )

    def __repr__(self):
        return f"<Category {self.name}>"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Integer, nullable=False, default=0)

    orders = db.relationship(
        "Order",
        backref="user",
        lazy=True,
    )

    def __repr__(self):
        return f"<User {self.email}>"


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(255), nullable=False)

    # Новая связь с таблицей categories
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id"),
        nullable=True,
    )

    # Старое текстовое поле категории оставляем,
    # чтобы не ломались старые товары и фильтры.
    category = db.Column(db.String(255), nullable=True)

    brand = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    old_price = db.Column(db.Integer, nullable=True)
    stock = db.Column(db.Integer, nullable=False, default=0)

    article = db.Column(db.String(255), unique=True, nullable=False)

    description = db.Column(db.Text, nullable=False)
    full_description = db.Column(db.Text, nullable=False)
    image = db.Column(db.Text, nullable=False)

    order_items = db.relationship(
        "OrderItem",
        backref="product",
        lazy=True,
    )

    def __repr__(self):
        return f"<Product {self.name}>"


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )

    customer_name = db.Column(db.String(255), nullable=False)
    customer_email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(255), nullable=True)
    address = db.Column(db.Text, nullable=False)
    comment = db.Column(db.Text, nullable=True)

    delivery_type = db.Column(db.String(100), nullable=False)
    payment_type = db.Column(db.String(100), nullable=False)

    total_amount = db.Column(db.Integer, nullable=False)

    # new, processing, done
    status = db.Column(db.String(100), nullable=False, default="new")

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    items = db.relationship(
        "OrderItem",
        backref="order",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Order {self.id}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id"),
        nullable=False,
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False,
    )

    # Сохраняем название и цену на момент заказа,
    # чтобы старые заказы не менялись после редактирования товара.
    product_name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    def __repr__(self):
        return f"<OrderItem order={self.order_id} product={self.product_id}>"