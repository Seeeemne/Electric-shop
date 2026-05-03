from functools import wraps
from pathlib import Path
import uuid
import base64

from flask import Flask, render_template, abort, session, redirect, url_for, request, jsonify
from werkzeug.utils import secure_filename

from db import init_db
from extensions import db
from models import User, Product, Order, OrderItem

from models_products import (
    get_all_products,
    get_filtered_products,
    get_admin_filtered_products,
    get_product_by_id,
    add_product,
    update_product,
    delete_product,
)

from models_users import (
    get_user_by_email,
    get_user_by_id,
    get_all_users,
    create_user,
    verify_user_password,
)

from models_orders import (
    create_order,
    get_orders_by_user_id,
    get_all_orders,
    get_orders_stats,
    get_order_by_id,
    get_order_items,
    update_order_status,
)

from models_categories import (
    get_all_categories,
    get_category_by_id,
    get_category_by_name,
    add_category,
    update_category,
    delete_category,
    initialize_default_categories,
    get_category_with_product_count,
)


app = Flask(__name__)
app.config["SECRET_KEY"] = "kulon_secret_key"

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "shop.db"
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)

db.init_app(app)
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

with app.app_context():
    db.create_all()
    initialize_default_categories()

init_db()


def allowed_file(filename):
    if not filename or "." not in filename:
        return False

    ext = filename.rsplit(".", 1)[1].lower()
    return ext in {"png", "jpg", "jpeg", "webp", "gif"}


def save_uploaded_image(file_storage):
    if file_storage is None or not file_storage.filename:
        return ""

    if not allowed_file(file_storage.filename):
        return ""

    original_name = secure_filename(file_storage.filename)
    ext = original_name.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    save_path = UPLOAD_FOLDER / unique_name
    file_storage.save(save_path)

    return f"/static/uploads/{unique_name}"


def save_cropped_image(data_url):
    if not data_url:
        return ""

    if "," not in data_url:
        return ""

    header, encoded = data_url.split(",", 1)

    if "image" not in header:
        return ""

    try:
        image_data = base64.b64decode(encoded)
    except Exception:
        return ""

    unique_name = f"{uuid.uuid4().hex}.png"
    save_path = UPLOAD_FOLDER / unique_name

    with open(save_path, "wb") as file:
        file.write(image_data)

    return f"/static/uploads/{unique_name}"


def get_current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    return get_user_by_id(user_id)


@app.context_processor
def inject_current_user():
    return {
        "current_user": get_current_user()
    }


def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        current_user = get_current_user()

        if current_user is None:
            return redirect(url_for("login"))

        if not current_user.is_admin:
            return redirect(url_for("profile"))

        return view_func(*args, **kwargs)

    return wrapped_view


def normalize_cart(cart):
    if isinstance(cart, dict):
        normalized = {}

        for key, value in cart.items():
            try:
                product_key = str(int(key))
                quantity = int(value)

                if quantity > 0:
                    normalized[product_key] = quantity

            except (ValueError, TypeError):
                continue

        return normalized

    if isinstance(cart, list):
        normalized = {}

        for product_id in cart:
            try:
                product_key = str(int(product_id))
                normalized[product_key] = normalized.get(product_key, 0) + 1

            except (ValueError, TypeError):
                continue

        return normalized

    return {}


def get_user_cart_key():
    user_id = session.get("user_id")

    if user_id:
        return str(user_id)

    return "guest"


def get_current_cart():
    carts = session.get("carts", {})
    cart_key = get_user_cart_key()

    user_cart = carts.get(cart_key, {})
    user_cart = normalize_cart(user_cart)

    carts[cart_key] = user_cart
    session["carts"] = carts

    return user_cart


def save_current_cart(cart):
    carts = session.get("carts", {})
    cart_key = get_user_cart_key()

    carts[cart_key] = normalize_cart(cart)
    session["carts"] = carts


def get_cart_data():
    cart = get_current_cart()

    items = []
    total = 0
    total_quantity = 0

    for product_id_str, quantity in cart.items():
        try:
            product_id = int(product_id_str)
        except ValueError:
            continue

        product = get_product_by_id(product_id)

        if product and quantity > 0:
            subtotal = product.price * quantity

            items.append({
                "product": product,
                "quantity": quantity,
                "subtotal": subtotal,
            })

            total += subtotal
            total_quantity += quantity

    return items, total, total_quantity


def validate_cart_stock(cart_items):
    for item in cart_items:
        product = item["product"]
        quantity = item["quantity"]

        if product.stock <= 0:
            return f"Товар «{product.name}» закончился на складе."

        if quantity > product.stock:
            return (
                f"Недостаточно товара «{product.name}» на складе. "
                f"Доступно: {product.stock} шт., в корзине: {quantity} шт."
            )

    return ""


@app.route("/")
def index():
    products = get_all_products()
    return render_template("index.html", products=products[:4])


@app.route("/catalog")
def catalog():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "default").strip()
    in_stock = request.args.get("in_stock", "").strip() == "1"

    min_price_raw = request.args.get("min_price", "").strip()
    max_price_raw = request.args.get("max_price", "").strip()

    min_price = None
    max_price = None

    try:
        if min_price_raw:
            min_price = int(min_price_raw)
    except ValueError:
        min_price = None

    try:
        if max_price_raw:
            max_price = int(max_price_raw)
    except ValueError:
        max_price = None

    products = get_filtered_products(
        search=search,
        category=category,
        in_stock=in_stock,
        min_price=min_price,
        max_price=max_price,
        sort=sort,
    )

    all_categories = get_all_categories()

    return render_template(
        "catalog.html",
        products=products,
        search=search,
        category=category,
        sort=sort,
        in_stock=in_stock,
        min_price=min_price_raw,
        max_price=max_price_raw,
        all_categories=all_categories,
    )

@app.route("/product/<int:product_id>")
def product(product_id):
    product_item = get_product_by_id(product_id)

    if product_item is None:
        abort(404)

    return render_template("product.html", product=product_item)


@app.route("/add-to-cart/<int:product_id>")
def add_to_cart(product_id):
    product_item = get_product_by_id(product_id)

    if product_item is None:
        abort(404)

    if product_item.stock <= 0:
        return redirect(url_for("product", product_id=product_id))

    cart = get_current_cart()

    product_key = str(product_id)
    current_quantity = cart.get(product_key, 0)

    if current_quantity < product_item.stock:
        cart[product_key] = current_quantity + 1

    save_current_cart(cart)

    return redirect(url_for("cart"))


@app.route("/cart")
def cart():
    cart_items, total, total_quantity = get_cart_data()

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total,
        total_quantity=total_quantity,
    )


@app.route("/cart/increase/<int:product_id>")
def increase_cart_item(product_id):
    product_item = get_product_by_id(product_id)

    if product_item is None:
        abort(404)

    cart = get_current_cart()

    product_key = str(product_id)
    current_quantity = cart.get(product_key, 0)

    if current_quantity < product_item.stock:
        cart[product_key] = current_quantity + 1

    save_current_cart(cart)

    return redirect(url_for("cart"))


@app.route("/cart/decrease/<int:product_id>")
def decrease_cart_item(product_id):
    cart = get_current_cart()

    product_key = str(product_id)

    if product_key in cart:
        cart[product_key] -= 1

        if cart[product_key] <= 0:
            del cart[product_key]

    save_current_cart(cart)

    return redirect(url_for("cart"))


@app.route("/remove-from-cart/<int:product_id>")
def remove_from_cart(product_id):
    cart = get_current_cart()

    product_key = str(product_id)

    if product_key in cart:
        del cart[product_key]

    save_current_cart(cart)

    return redirect(url_for("cart"))


@app.route("/clear-cart")
def clear_cart():
    save_current_cart({})
    return redirect(url_for("cart"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        user = get_user_by_email(email)

        if user is None:
            error = "Пользователь с такой почтой не найден."
        elif not verify_user_password(user, password):
            error = "Неверный пароль."
        else:
            session.pop("cart", None)
            session["user_id"] = user.id
            return redirect(url_for("profile"))

    return render_template("login.html", error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = ""

    if request.method == "POST":
        name = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        password_repeat = request.form.get("password_repeat", "").strip()

        if not name or not email or not password:
            error = "Заполните все обязательные поля."
        elif password != password_repeat:
            error = "Пароли не совпадают."
        elif get_user_by_email(email) is not None:
            error = "Пользователь с такой почтой уже существует."
        else:
            new_user = create_user(name, email, password)
            session["user_id"] = new_user.id
            return redirect(url_for("profile"))

    return render_template("register.html", error=error)


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("cart", None)
    return redirect(url_for("login"))


@app.route("/profile")
def profile():
    current_user = get_current_user()

    if current_user is None:
        return redirect(url_for("login"))

    orders = get_orders_by_user_id(current_user.id)

    return render_template(
        "profile.html",
        user=current_user,
        orders=orders,
    )


@app.route("/order/<int:order_id>")
def order_detail(order_id):
    current_user = get_current_user()

    if current_user is None:
        return redirect(url_for("login"))

    order = get_order_by_id(order_id)

    if order is None:
        abort(404)

    if not current_user.is_admin and order["user_id"] != current_user.id:
        return redirect(url_for("profile"))

    items = get_order_items(order_id)

    return render_template(
        "order_detail.html",
        order=order,
        items=items,
    )


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart_items, total, total_quantity = get_cart_data()
    current_user = get_current_user()

    if request.method == "POST":
        if not current_user:
            return redirect(url_for("login"))

        if not cart_items:
            return redirect(url_for("cart"))

        stock_error = validate_cart_stock(cart_items)

        if stock_error:
            return render_template(
                "checkout.html",
                cart_items=cart_items,
                total=total,
                total_quantity=total_quantity,
                error=stock_error,
            )

        name = request.form.get("name", "").strip()
        surname = request.form.get("surname", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        comment = request.form.get("comment", "").strip()
        delivery_type = request.form.get("delivery", "courier").strip()
        payment_type = request.form.get("payment", "online").strip()

        customer_name = f"{name} {surname}".strip()

        if not customer_name or not email or not address:
            return render_template(
                "checkout.html",
                cart_items=cart_items,
                total=total,
                total_quantity=total_quantity,
                error="Заполните имя, фамилию, email и адрес.",
            )

        create_order(
            user_id=current_user.id,
            customer_name=customer_name,
            customer_email=email,
            phone=phone,
            address=address,
            comment=comment,
            delivery_type=delivery_type,
            payment_type=payment_type,
            cart_items=cart_items,
            total_amount=total,
        )

        save_current_cart({})
        return redirect(url_for("profile"))

    return render_template(
        "checkout.html",
        cart_items=cart_items,
        total=total,
        total_quantity=total_quantity,
        error="",
    )


@app.route("/admin/products")
@admin_required
def admin_products():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "default").strip()
    in_stock = request.args.get("in_stock", "").strip() == "1"

    products = get_admin_filtered_products(
        search=search,
        category=category,
        in_stock=in_stock,
        sort=sort,
    )

    all_categories = get_all_categories()

    return render_template(
        "admin_products.html",
        products=products,
        search=search,
        category=category,
        sort=sort,
        in_stock=in_stock,
        all_categories=all_categories,
    )


@app.route("/admin/products/add", methods=["GET", "POST"])
@admin_required
def add_product_page():
    error = ""
    categories = get_all_categories()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        brand = request.form.get("brand", "").strip()
        article = request.form.get("article", "").strip()
        description = request.form.get("description", "").strip()
        full_description = request.form.get("full_description", "").strip()

        image = request.form.get("image", "").strip()
        image_file = request.files.get("image_file")
        cropped_image_data = request.form.get("cropped_image_data", "").strip()

        if cropped_image_data:
            cropped_path = save_cropped_image(cropped_image_data)

            if cropped_path:
                image = cropped_path
            else:
                error = "Не удалось сохранить обрезанное изображение."
        elif image_file and image_file.filename:
            uploaded_path = save_uploaded_image(image_file)

            if uploaded_path:
                image = uploaded_path
            else:
                error = "Разрешены только изображения: png, jpg, jpeg, webp, gif."

        try:
            price = int(request.form.get("price", "0").strip() or 0)
            old_price = int(request.form.get("old_price", "0").strip() or 0)
            stock = int(request.form.get("stock", "0").strip() or 0)
        except ValueError:
            error = "Цена и количество должны быть числами."
            return render_template(
                "add_product.html",
                error=error,
                categories=categories,
            )

        if not name or not category or not brand or not article or not description or not full_description:
            error = "Заполните все обязательные поля."
        elif not image:
            error = "Укажите ссылку на изображение или загрузите файл."
        elif price <= 0:
            error = "Цена должна быть больше нуля."
        elif stock < 0:
            error = "Количество не может быть отрицательным."
        elif not error:
            try:
                new_id = add_product(
                    name=name,
                    category=category,
                    brand=brand,
                    price=price,
                    old_price=old_price,
                    stock=stock,
                    article=article,
                    description=description,
                    full_description=full_description,
                    image=image,
                )

                return redirect(url_for("edit_product", product_id=new_id))

            except Exception:
                error = "Не удалось добавить товар. Возможно, артикул уже используется."

    return render_template(
        "add_product.html",
        error=error,
        categories=categories,
    )


@app.route("/admin/products/edit/<int:product_id>", methods=["GET", "POST"])
@admin_required
def edit_product(product_id):
    product_item = get_product_by_id(product_id)

    if product_item is None:
        abort(404)

    error = ""
    success = ""
    categories = get_all_categories()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        brand = request.form.get("brand", "").strip()
        article = request.form.get("article", "").strip()
        description = request.form.get("description", "").strip()
        full_description = request.form.get("full_description", "").strip()

        image = request.form.get("image", "").strip()
        image_file = request.files.get("image_file")
        cropped_image_data = request.form.get("cropped_image_data", "").strip()

        if cropped_image_data:
            cropped_path = save_cropped_image(cropped_image_data)

            if cropped_path:
                image = cropped_path
            else:
                error = "Не удалось сохранить обрезанное изображение."
        elif image_file and image_file.filename:
            uploaded_path = save_uploaded_image(image_file)

            if uploaded_path:
                image = uploaded_path
            else:
                error = "Разрешены только изображения: png, jpg, jpeg, webp, gif."

        try:
            price = int(request.form.get("price", "0").strip() or 0)
            old_price = int(request.form.get("old_price", "0").strip() or 0)
            stock = int(request.form.get("stock", "0").strip() or 0)
        except ValueError:
            error = "Цена и количество должны быть числами."

            return render_template(
                "edit_product.html",
                product=product_item,
                error=error,
                success=success,
                categories=categories,
            )

        if not name or not category or not brand or not article or not description or not full_description:
            error = "Заполните все обязательные поля."
        elif not image:
            error = "Укажите ссылку на изображение или загрузите файл."
        elif price <= 0:
            error = "Цена должна быть больше нуля."
        elif stock < 0:
            error = "Количество не может быть отрицательным."
        elif not error:
            try:
                update_product(
                    product_id=product_id,
                    name=name,
                    category=category,
                    brand=brand,
                    price=price,
                    old_price=old_price,
                    stock=stock,
                    article=article,
                    description=description,
                    full_description=full_description,
                    image=image,
                )

                product_item = get_product_by_id(product_id)
                success = "Товар успешно обновлён."

            except Exception:
                error = "Не удалось сохранить изменения. Возможно, артикул уже используется."

    return render_template(
        "edit_product.html",
        product=product_item,
        error=error,
        success=success,
        categories=categories,
    )


@app.route("/admin/products/delete/<int:product_id>", methods=["POST"])
@admin_required
def delete_product_page(product_id):
    product_item = get_product_by_id(product_id)

    if product_item is None:
        abort(404)

    delete_product(product_id)
    return redirect(url_for("admin_products"))


@app.route("/admin/orders")
@admin_required
def admin_orders():
    orders = get_all_orders()
    stats = get_orders_stats()

    return render_template(
        "admin_orders.html",
        orders=orders,
        stats=stats,
    )


@app.route("/admin/orders/<int:order_id>")
@admin_required
def admin_order_detail(order_id):
    order = get_order_by_id(order_id)

    if order is None:
        abort(404)

    items = get_order_items(order_id)

    return render_template(
        "order_detail.html",
        order=order,
        items=items,
    )


@app.route("/admin/orders/status/<int:order_id>", methods=["POST"])
@admin_required
def change_order_status(order_id):
    order = get_order_by_id(order_id)

    if order is None:
        abort(404)

    new_status = request.form.get("status", "").strip()
    allowed_statuses = ["new", "processing", "done"]

    if new_status in allowed_statuses:
        update_order_status(order_id, new_status)

    return redirect(url_for("admin_orders"))


@app.route("/admin/users")
@admin_required
def admin_users():
    users = get_all_users()

    return render_template(
        "admin_users.html",
        users=users,
    )


@app.route("/admin/categories")
@admin_required
def admin_categories():
    categories = get_category_with_product_count()

    return render_template(
        "admin_categories.html",
        categories=categories,
    )


@app.route("/admin/categories/add", methods=["GET", "POST"])
@admin_required
def add_category_page():
    error = ""
    success = ""
    name = ""
    description = ""

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            error = "Название категории обязательно."
        elif get_category_by_name(name):
            error = "Категория с таким названием уже существует."
        else:
            try:
                add_category(name, description)
                success = "Категория успешно добавлена."
                name = ""
                description = ""

            except Exception:
                error = "Не удалось добавить категорию."

    return render_template(
        "add_category.html",
        error=error,
        success=success,
        name=name,
        description=description,
    )


@app.route("/admin/categories/edit/<int:category_id>", methods=["GET", "POST"])
@admin_required
def edit_category_page(category_id):
    category = get_category_by_id(category_id)

    if category is None:
        abort(404)

    error = ""
    success = ""

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            error = "Название категории обязательно."
        else:
            existing = get_category_by_name(name)

            if existing and existing.id != category_id:
                error = "Категория с таким названием уже существует."
            else:
                try:
                    if update_category(category_id, name, description):
                        category = get_category_by_id(category_id)
                        success = "Категория успешно обновлена."
                    else:
                        error = "Не удалось обновить категорию."

                except Exception:
                    error = "Не удалось обновить категорию."

    return render_template(
        "edit_category.html",
        category=category,
        error=error,
        success=success,
    )


@app.route("/admin/categories/delete/<int:category_id>", methods=["POST"])
@admin_required
def delete_category_page(category_id):
    category = get_category_by_id(category_id)

    if category is None:
        abort(404)

    if category.products:
        return redirect(url_for("admin_categories"))

    try:
        delete_category(category_id)
    except Exception:
        pass

    return redirect(url_for("admin_categories"))


@app.route("/api/products")
def api_products():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    in_stock = request.args.get("in_stock", "").strip() == "1"

    products = get_filtered_products(
        search=search,
        category=category,
        in_stock=in_stock,
        min_price=None,
        max_price=None,
        sort="default",
    )

    result = []

    for product in products:
        result.append({
            "id": product.id,
            "name": product.name,
            "category": product.category,
            "brand": product.brand,
            "price": product.price,
            "old_price": product.old_price,
            "stock": product.stock,
            "article": product.article,
            "description": product.description,
            "image": product.image,
        })

    return jsonify({
        "count": len(result),
        "products": result,
    })


@app.route("/api/products/<int:product_id>")
def api_product_detail(product_id):
    product = get_product_by_id(product_id)

    if product is None:
        return jsonify({
            "error": "Товар не найден"
        }), 404

    return jsonify({
        "id": product.id,
        "name": product.name,
        "category": product.category,
        "brand": product.brand,
        "price": product.price,
        "old_price": product.old_price,
        "stock": product.stock,
        "article": product.article,
        "description": product.description,
        "full_description": product.full_description,
        "image": product.image,
    })


@app.route("/api/categories")
def api_categories():
    categories = get_category_with_product_count()

    result = []

    for category in categories:
        result.append({
            "id": category["id"],
            "name": category["name"],
            "description": category["description"],
            "product_count": category["product_count"],
        })

    return jsonify({
        "count": len(result),
        "categories": result,
    })


@app.route("/api/cart")
def api_cart():
    cart_items, total, total_quantity = get_cart_data()

    result = []

    for item in cart_items:
        product = item["product"]

        result.append({
            "product_id": product.id,
            "name": product.name,
            "price": product.price,
            "quantity": item["quantity"],
            "subtotal": item["subtotal"],
        })

    return jsonify({
        "total": total,
        "total_quantity": total_quantity,
        "items": result,
    })


@app.route("/api/orders")
@admin_required
def api_orders():
    orders = get_all_orders()

    result = []

    for order in orders:
        result.append({
            "id": order["id"],
            "customer_name": order["customer_name"],
            "customer_email": order["customer_email"],
            "total_amount": order["total_amount"],
            "payment_type": order["payment_type"],
            "status": order["status"],
            "items_count": order["items_count"],
            "created_at": str(order["created_at"]),
        })

    return jsonify({
        "count": len(result),
        "orders": result,
    })


@app.route("/api/orders/<int:order_id>")
@admin_required
def api_order_detail(order_id):
    order = get_order_by_id(order_id)

    if order is None:
        return jsonify({
            "error": "Заказ не найден"
        }), 404

    items = get_order_items(order_id)

    return jsonify({
        "order": {
            "id": order["id"],
            "user_id": order["user_id"],
            "customer_name": order["customer_name"],
            "customer_email": order["customer_email"],
            "phone": order["phone"],
            "address": order["address"],
            "comment": order["comment"],
            "delivery_type": order["delivery_type"],
            "payment_type": order["payment_type"],
            "total_amount": order["total_amount"],
            "status": order["status"],
            "created_at": str(order["created_at"]),
        },
        "items": items,
    })


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)