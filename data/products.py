products = [
    {
        "id": 1,
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
        "id": 2,
        "name": "Logitech G305",
        "category": "Мыши",
        "brand": "Logitech",
        "price": 5490,
        "old_price": 6490,
        "stock": 18,
        "article": "MS-1002",
        "description": "Легкая беспроводная мышь с точным сенсором и удобной формой.",
        "full_description": "Logitech G305 — удобная беспроводная мышь с качественным сенсором и компактным корпусом. Хорошо подходит для учебы, работы и игр.",
        "image": "https://images.unsplash.com/photo-1527814050087-3793815479db?auto=format&fit=crop&w=900&q=80"
    },
    {
        "id": 3,
        "name": "Sony WH-CH720N",
        "category": "Наушники",
        "brand": "Sony",
        "price": 24990,
        "old_price": 27990,
        "stock": 7,
        "article": "HP-1003",
        "description": "Беспроводные наушники с чистым звуком и шумоподавлением.",
        "full_description": "Sony WH-CH720N — удобные наушники для музыки, фильмов, звонков и повседневного использования.",
        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80"
    },
    {
        "id": 4,
        "name": "Studio Display XDR",
        "category": "Мониторы",
        "brand": "Studio",
        "price": 29990,
        "old_price": 33990,
        "stock": 11,
        "article": "MN-1004",
        "description": "27-дюймовый монитор с четкой картинкой и современным дизайном.",
        "full_description": "Монитор Studio Display XDR подходит для работы, учебы, просмотра видео и повседневных задач.",
        "image": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=900&q=80"
    },
    {
        "id": 5,
        "name": "ASUS VivoBook 15",
        "category": "Ноутбуки",
        "brand": "ASUS",
        "price": 54990,
        "old_price": 56990,
        "stock": 6,
        "article": "NB-1005",
        "description": "Универсальный ноутбук для учебы, работы и повседневных задач.",
        "full_description": "ASUS VivoBook 15 — удобный ноутбук для браузера, офисных программ, фильмов, видеосвязи и ежедневной работы.",
        "image": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=80"
    },
    {
        "id": 6,
        "name": "Logitech MK270",
        "category": "Аксессуары",
        "brand": "Logitech",
        "price": 6990,
        "old_price": 7990,
        "stock": 13,
        "article": "AC-1006",
        "description": "Комплект клавиатуры и мыши для дома, учебы и офиса.",
        "full_description": "Logitech MK270 — удобный комплект клавиатуры и мыши для учебы, офиса и домашнего использования.",
        "image": "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?auto=format&fit=crop&w=900&q=80"
    }
]


def get_all_products():
    return products


def get_product_by_id(product_id):
    for product in products:
        if product["id"] == product_id:
            return product
    return None