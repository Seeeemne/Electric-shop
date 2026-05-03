from extensions import db
from models import Product, Category


def get_all_products():
    return Product.query.order_by(Product.id.asc()).all()


def get_filtered_products(search="", category="", in_stock=False, min_price=None, max_price=None, sort="default"):
    query = Product.query

    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    if category:
        query = query.filter(Product.category == category)

    if in_stock:
        query = query.filter(Product.stock > 0)

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort == "name_asc":
        query = query.order_by(Product.name.asc())
    else:
        query = query.order_by(Product.id.asc())

    return query.all()


def get_admin_filtered_products(search="", category="", in_stock=False, sort="default"):
    query = Product.query

    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    if category:
        query = query.filter(Product.category == category)

    if in_stock:
        query = query.filter(Product.stock > 0)

    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort == "name_asc":
        query = query.order_by(Product.name.asc())
    elif sort == "stock_desc":
        query = query.order_by(Product.stock.desc())
    else:
        query = query.order_by(Product.id.desc())

    return query.all()


def get_product_by_id(product_id):
    return db.session.get(Product, product_id)


def add_product(name, category, brand, price, old_price, stock, article, description, full_description, image):
    category_obj = Category.query.filter(Category.name == category).first()

    product = Product(
        name=name,
        category=category,
        category_id=category_obj.id if category_obj else None,
        brand=brand,
        price=price,
        old_price=old_price,
        stock=stock,
        article=article,
        description=description,
        full_description=full_description,
        image=image,
    )

    db.session.add(product)
    db.session.commit()

    return product.id


def update_product(product_id, name, category, brand, price, old_price, stock, article, description, full_description, image):
    product = db.session.get(Product, product_id)
    if product is None:
        return

    category_obj = Category.query.filter(Category.name == category).first()

    product.name = name
    product.category = category
    product.category_id = category_obj.id if category_obj else None
    product.brand = brand
    product.price = price
    product.old_price = old_price
    product.stock = stock
    product.article = article
    product.description = description
    product.full_description = full_description
    product.image = image

    db.session.commit()


def delete_product(product_id):
    product = db.session.get(Product, product_id)
    if product is None:
        return

    db.session.delete(product)
    db.session.commit()