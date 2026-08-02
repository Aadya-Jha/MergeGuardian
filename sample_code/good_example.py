from werkzeug.security import check_password_hash


def get_user_by_email(email: str, db_connection) -> dict | None:
    """Look up a user by email using a parameterized query."""
    query = "SELECT id, email, password_hash FROM users WHERE email = %s"
    cursor = db_connection.cursor()
    cursor.execute(query, (email,))
    row = cursor.fetchone()
    if row is None:
        return None
    return {"id": row[0], "email": row[1], "password_hash": row[2]}


def login(email: str, password: str, db_connection) -> dict:
    """Authenticate a user by email and password."""
    user = get_user_by_email(email, db_connection)
    if user is None:
        return {"status": "fail", "reason": "user not found"}

    if check_password_hash(user["password_hash"], password):
        return {"status": "ok", "user_id": user["id"]}

    return {"status": "fail", "reason": "invalid credentials"}