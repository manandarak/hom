from src.app.core.database import SessionLocal
from src.app.models.user import User
from src.app.core.security import get_password_hash
# EXPLICITLY IMPORT ALL MODELS TO REGISTER THEM WITH BASE
from src.app.models.user import User, Role
from src.app.models.geography import Zone, State, Region, Area, Territory

db = SessionLocal()
user = db.query(User).filter(User.username == "admin").first()

if user:
    # Generate a fresh hash for 'admin123' (or whatever you want)
    new_password = "admin123"
    new_hash = get_password_hash(new_password)

    # Update the user in the database
    user.password_hash = new_hash
    user.is_active = True
    db.commit()

    print(f"✅ Success! Admin password updated to: {new_password}")
    print(f"✅ New Hash saved: {new_hash}")
else:
    print("❌ User 'admin' not found.")

db.close()