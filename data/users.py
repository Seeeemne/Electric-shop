users = [
    {
        "id": 1,
        "name": "Иван Иванович",
        "email": "ivan@example.com",
        "password": "12345"
    }
]


def get_all_users():
    return users


def get_user_by_email(email):
    for user in users:
        if user["email"] == email:
            return user
    return None


def get_user_by_id(user_id):
    for user in users:
        if user["id"] == user_id:
            return user
    return None


def create_user(name, email, password):
    new_user = {
        "id": len(users) + 1,
        "name": name,
        "email": email,
        "password": password
    }
    users.append(new_user)
    return new_user