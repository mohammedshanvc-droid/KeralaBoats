
from getpass import getpass
from sqlalchemy import select

from app.database import SessionLocal
from app.models import User
from app.security import hash_password

database = SessionLocal()

try:
    name = input("Enter admin name: ").strip()
    email = input("Enter admin email: ").strip().lower()

    password = getpass("Enter admin password: ")
    confirm = getpass("Confirm password: ")

    if not name or not email:
        print("Name and email are required.")

    elif len(password) < 6:
        print("Password must be at least 6 characters.")

    elif len(password.encode("utf-8")) > 72:
        print("Password must not exceed 72 bytes.")

    elif password != confirm:
        print("Passwords do not match.")

    elif database.scalar(select(User).where(User.email == email)):
        print("This email already exists.")

    else:
        admin = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role="admin"
        )

        database.add(admin)
        database.commit()

        print("Admin account created successfully!")

except Exception as e:
    database.rollback()
    print("Error:", e)

finally:
    database.close()
