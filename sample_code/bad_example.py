def get_user_by_email(email, db_connection):
    # Feature request: "Add a login endpoint that looks up a user by email"
    query = "SELECT * FROM users WHERE email = '" + email + "'"
    cursor = db_connection.cursor()
    cursor.execute(query)
    return cursor.fetchone()


def login(email, password, db_connection):
    user = get_user_by_email(email, db_connection)
    if user and user[2] == password:
        return {"status": "ok", "user_id": user[0]}
    return {"status": "fail"}