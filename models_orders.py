from sqlalchemy import func

from extensions import db
from models import Order, OrderItem, Product


def create_order(user_id, customer_name, customer_email, phone, address, comment,
                 delivery_type, payment_type, cart_items, total_amount):
    """
    Создаёт заказ и сохраняет товары заказа.
    Количество товаров на складе здесь НЕ уменьшается.
    Остаток уменьшается только когда админ меняет статус заказа на done.
    """
    order = Order(
        user_id=user_id,
        customer_name=customer_name,
        customer_email=customer_email,
        phone=phone,
        address=address,
        comment=comment,
        delivery_type=delivery_type,
        payment_type=payment_type,
        total_amount=total_amount,
        status="new",
    )

    db.session.add(order)
    db.session.flush()

    for item in cart_items:
        product = item["product"]
        quantity = item["quantity"]

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            price=product.price,
            quantity=quantity,
        )
        db.session.add(order_item)

    db.session.commit()
    return order.id


def get_orders_by_user_id(user_id):
    rows = (
        db.session.query(
            Order.id,
            Order.customer_name,
            Order.customer_email,
            Order.total_amount,
            Order.status,
            Order.created_at,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("items_count"),
        )
        .outerjoin(OrderItem, Order.id == OrderItem.order_id)
        .filter(Order.user_id == user_id)
        .group_by(
            Order.id,
            Order.customer_name,
            Order.customer_email,
            Order.total_amount,
            Order.status,
            Order.created_at,
        )
        .order_by(Order.id.desc())
        .all()
    )

    result = []
    for row in rows:
        result.append({
            "id": row.id,
            "customer_name": row.customer_name,
            "customer_email": row.customer_email,
            "total_amount": row.total_amount,
            "status": row.status,
            "created_at": row.created_at,
            "items_count": row.items_count,
        })

    return result


def get_all_orders():
    rows = (
        db.session.query(
            Order.id,
            Order.customer_name,
            Order.customer_email,
            Order.total_amount,
            Order.payment_type,
            Order.status,
            Order.created_at,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("items_count"),
        )
        .outerjoin(OrderItem, Order.id == OrderItem.order_id)
        .group_by(
            Order.id,
            Order.customer_name,
            Order.customer_email,
            Order.total_amount,
            Order.payment_type,
            Order.status,
            Order.created_at,
        )
        .order_by(Order.id.desc())
        .all()
    )

    result = []
    for row in rows:
        result.append({
            "id": row.id,
            "customer_name": row.customer_name,
            "customer_email": row.customer_email,
            "total_amount": row.total_amount,
            "payment_type": row.payment_type,
            "status": row.status,
            "created_at": row.created_at,
            "items_count": row.items_count,
        })

    return result


def get_orders_stats():
    total_orders = db.session.query(func.count(Order.id)).scalar() or 0
    new_orders = db.session.query(func.count(Order.id)).filter(Order.status == "new").scalar() or 0
    processing_orders = db.session.query(func.count(Order.id)).filter(Order.status == "processing").scalar() or 0
    done_orders = db.session.query(func.count(Order.id)).filter(Order.status == "done").scalar() or 0

    return {
        "total_orders": total_orders,
        "new_orders": new_orders,
        "processing_orders": processing_orders,
        "done_orders": done_orders,
    }


def get_order_by_id(order_id):
    order = db.session.get(Order, order_id)
    if order is None:
        return None

    return {
        "id": order.id,
        "user_id": order.user_id,
        "customer_name": order.customer_name,
        "customer_email": order.customer_email,
        "phone": order.phone,
        "address": order.address,
        "comment": order.comment,
        "delivery_type": order.delivery_type,
        "payment_type": order.payment_type,
        "total_amount": order.total_amount,
        "status": order.status,
        "created_at": order.created_at,
    }


def get_order_items(order_id):
    items = (
        db.session.query(
            OrderItem.id,
            OrderItem.order_id,
            OrderItem.product_id,
            OrderItem.product_name,
            OrderItem.price,
            OrderItem.quantity,
            (OrderItem.price * OrderItem.quantity).label("subtotal"),
        )
        .filter(OrderItem.order_id == order_id)
        .order_by(OrderItem.id.asc())
        .all()
    )

    result = []
    for item in items:
        result.append({
            "id": item.id,
            "order_id": item.order_id,
            "product_id": item.product_id,
            "product_name": item.product_name,
            "price": item.price,
            "quantity": item.quantity,
            "subtotal": item.subtotal,
        })

    return result


def update_order_status(order_id, status):
    """
    Меняет статус заказа.

    Если заказ впервые переводится в статус done,
    количество товаров на складе уменьшается.

    Защита от двойного списания:
    если заказ уже был done, повторно товары не списываются.
    """
    order = db.session.get(Order, order_id)
    if order is None:
        return False

    old_status = order.status

    if old_status == status:
        return True

    allowed_statuses = ["new", "processing", "done"]
    if status not in allowed_statuses:
        return False

    # Списываем товары только при переходе В статус done
    if status == "done" and old_status != "done":
        order_items = OrderItem.query.filter_by(order_id=order_id).all()

        # Сначала проверяем, хватает ли товаров на складе
        for item in order_items:
            product = db.session.get(Product, item.product_id)

            if product is None:
                continue

            if product.stock < item.quantity:
                db.session.rollback()
                return False

        # Если всего хватает — списываем
        for item in order_items:
            product = db.session.get(Product, item.product_id)

            if product is None:
                continue

            product.stock -= item.quantity

    order.status = status
    db.session.commit()
    return True