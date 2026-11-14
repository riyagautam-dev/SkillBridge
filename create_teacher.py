
from database import SessionLocal
from models import User
from services.auth import password_hasher

db = SessionLocal()

try:
    email = "teacher@skillbridge.com"

    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:
        existing_user.role = "teacher"
        print("Existing account updated to teacher.")
    else:
        teacher = User(
            name="SkillBridge Teacher",
            email=email,
            password_hash=password_hasher.hash("Teacher@123"),
            role="teacher"
        )
        db.add(teacher)
        print("Teacher account created.")

    db.commit()

finally:
    db.close()
