import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "shop.db"


SEED_PRODUCTS = [
    {
        "name": "Redragon Kumara K552",
        "category": "Клавиатуры",
        "brand": "Redragon",
        "price": 8990,
        "old_price": 10490,
        "stock": 24,
        "article": "KB-1001",
        "description": "Компактная механическая клавиатура с подсветкой, удобная для игр, учебы и повседневной работы.",
        "full_description": "Redragon Kumara K552 — компактная механическая клавиатура с подсветкой и прочной конструкцией. Подходит для игр, учебы, работы с текстом и ежедневного использования.",
        "image": "https://images.unsplash.com/photo-1541140532154-b024d705b90a?auto=format&fit=crop&w=900&q=80"
    },
    {
        "name": "Logitech G305",
        "category": "Мыши",
        "brand": "Logitech",
        "price": 5490,
        "old_price": 6490,
        "stock": 18,
        "article": "MS-1002",
        "description": "Легкая беспроводная мышь с точным сенсором, удобной формой и хорошим временем автономной работы.",
        "full_description": "Logitech G305 — удобная беспроводная мышь с качественным сенсором и компактным корпусом. Хорошо подходит для учебы, работы и игр.",
        "image": "https://images.unsplash.com/photo-1527814050087-3793815479db?auto=format&fit=crop&w=900&q=80"
    },
    {
        "name": "Sony WH-CH720N",
        "category": "Наушники",
        "brand": "Sony",
        "price": 24990,
        "old_price": 27990,
        "stock": 7,
        "article": "HP-1003",
        "description": "Беспроводные наушники с чистым звуком, активным шумоподавлением и удобной посадкой.",
        "full_description": "Sony WH-CH720N — удобные наушники для музыки, фильмов, звонков и повседневного использования. Есть шумоподавление и длительное время работы.",
        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80"
    },
    {
        "name": "Studio Display XDR",
        "category": "Мониторы",
        "brand": "Studio",
        "price": 29990,
        "old_price": 33990,
        "stock": 11,
        "article": "MN-1004",
        "description": "27-дюймовый монитор с высокой частотой обновления, тонкими рамками и четкой картинкой.",
        "full_description": "Монитор Studio Display XDR подходит для работы, учебы, просмотра видео и повседневных задач. Отличается хорошей цветопередачей и современным дизайном.",
        "image": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=900&q=80"
    },
    {
        "name": "ASUS VivoBook 15",
        "category": "Ноутбуки",
        "brand": "ASUS",
        "price": 54990,
        "old_price": 56990,
        "stock": 6,
        "article": "NB-1005",
        "description": "Универсальный ноутбук для учебы, работы с документами, просмотра видео и повседневных задач.",
        "full_description": "ASUS VivoBook 15 — это удобный ноутбук для учебы, браузера, офисных программ, фильмов, видеосвязи и ежедневной работы.",
        "image": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=80"
    },
    {
        "name": "Logitech MK270",
        "category": "Аксессуары",
        "brand": "Logitech",
        "price": 6990,
        "old_price": 7990,
        "stock": 13,
        "article": "AC-1006",
        "description": "Практичный комплект из клавиатуры и мыши для домашнего рабочего места и комфортной учебы.",
        "full_description": "Logitech MK270 — удобный комплект клавиатуры и мыши для учебы, офиса и домашнего использования.",
        "image": "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?auto=format&fit=crop&w=900&q=80"
    }
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_users_is_admin_column(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    columns = [row["name"] for row in cursor.fetchall()]
    if "is_admin" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
        conn.commit()


def seed_admin_if_missing(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", ("admin@kulon.local",))
    admin = cursor.fetchone()

    if admin is None:
        cursor.execute(
            """
            INSERT INTO users (name, email, password, is_admin)
            VALUES (?, ?, ?, ?)
            """,
            (
                "Администратор",
                "admin@kulon.local",
                generate_password_hash("admin123"),
                1,
            ),
        )
        conn.commit()


def seed_products_if_empty(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS count FROM products")
    count = cursor.fetchone()["count"]

    if count > 0:
        return

    for product in SEED_PRODUCTS:
        cursor.execute(
            """
            INSERT INTO products (
                name, category, brand, price, old_price, stock,
                article, description, full_description, image
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product["name"],
                product["category"],
                product["brand"],
                product["price"],
                product["old_price"],
                product["stock"],
                product["article"],
                product["description"],
                product["full_description"],
                product["image"],
            ),
        )

    conn.commit()


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)

    ensure_users_is_admin_column(conn)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            brand TEXT NOT NULL,
            price INTEGER NOT NULL,
            old_price INTEGER,
            stock INTEGER NOT NULL DEFAULT 0,
            article TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL,
            full_description TEXT NOT NULL,
            image TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            phone TEXT,
            address TEXT NOT NULL,
            comment TEXT,
            delivery_type TEXT NOT NULL,
            payment_type TEXT NOT NULL,
            total_amount INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    conn.commit()
    seed_admin_if_missing(conn)
    seed_products_if_empty(conn)
    conn.close()