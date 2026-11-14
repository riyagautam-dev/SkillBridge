from database import SessionLocal
from models import User
from pwdlib import PasswordHash

password_hasher = PasswordHash.recommended()

db = SessionLocal()

try:
    new_user = User(
        name="Rahul Sharma",
        email="rahul.demo@example.com",
        password_hash=password_hasher.hash("DemoPass123!"),
        role="student"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    print("User created successfully!")
    print("User ID:", new_user.id)
    print("Name:", new_user.name)
    print("Email:", new_user.email)

except Exception as e:
    db.rollback()
    print("Error:", e)

finally:
    db.close()