def log_upload(user_id: str, filename: str):
    # In production, log to a database or persistent store
    print(f"User {user_id} uploaded {filename}")