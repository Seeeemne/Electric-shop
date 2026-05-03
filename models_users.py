from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from models import User


def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


def get_user_by_id(user_id):
    return User.query.get(user_id)


def get_all_users():
    return User.query.order_by(User.id.desc()).all()


def create_user(name, email, password):
    password_hash = generate_password_hash(password)

    user = User(
        name=name,
        email=email,
        password=password_hash,
        is_admin=0,
    )

    db.session.add(user)
    db.session.commit()

    return user


def verify_user_password(user, password):
    if user is None:
        return False

    return check_password_hash(user.password, password)