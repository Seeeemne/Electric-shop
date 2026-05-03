from sqlalchemy import func

from extensions import db
from models import Category, Product


def get_all_categories():
    """Получить все категории, отсортированные по названию."""
    return Category.query.order_by(Category.name.asc()).all()


def get_category_by_id(category_id):
    """Получить категорию по ID."""
    return db.session.get(Category, category_id)


def get_category_by_name(name):
    """Получить категорию по названию."""
    return Category.query.filter(Category.name == name).first()


def add_category(name, description=""):
    """Добавить новую категорию."""
    existing = get_category_by_name(name)

    if existing:
        return None

    category = Category(
        name=name,
        description=description,
    )

    db.session.add(category)
    db.session.commit()

    return category.id


def update_category(category_id, name, description=""):
    """Обновить категорию."""
    category = get_category_by_id(category_id)

    if category is None:
        return False

    existing = Category.query.filter(
        Category.name == name,
        Category.id != category_id
    ).first()

    if existing:
        return False

    category.name = name
    category.description = description

    db.session.commit()
    return True


def delete_category(category_id):
    """Удалить категорию, если в ней нет товаров."""
    category = get_category_by_id(category_id)

    if category is None:
        return False

    if category.products:
        return False

    db.session.delete(category)
    db.session.commit()

    return True


def initialize_default_categories():
    """Создать стандартные категории, если их ещё нет."""
    default_categories = [
        {
            "name": "Клавиатуры",
            "description": "Механические, мембранные и игровые клавиатуры.",
        },
        {
            "name": "Мыши",
            "description": "Проводные, беспроводные и игровые мыши.",
        },
        {
            "name": "Наушники",
            "description": "Наушники для игр, работы и музыки.",
        },
        {
            "name": "Мониторы",
            "description": "Мониторы для работы, учебы и игр.",
        },
        {
            "name": "Аксессуары",
            "description": "Полезные аксессуары для компьютера и рабочего места.",
        },
    ]

    for item in default_categories:
        existing = get_category_by_name(item["name"])

        if existing is None:
            category = Category(
                name=item["name"],
                description=item["description"],
            )

            db.session.add(category)

    db.session.commit()


def get_category_with_product_count():
    """Получить категории вместе с количеством товаров."""
    categories = (
        db.session.query(
            Category.id,
            Category.name,
            Category.description,
            Category.created_at,
            func.count(Product.id).label("product_count"),
        )
        .outerjoin(Product, Category.id == Product.category_id)
        .group_by(
            Category.id,
            Category.name,
            Category.description,
            Category.created_at,
        )
        .order_by(Category.name.asc())
        .all()
    )

    result = []

    for category in categories:
        result.append({
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "created_at": category.created_at,
            "product_count": category.product_count,
        })

    return result