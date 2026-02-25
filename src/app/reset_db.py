from sqlalchemy.orm import Session
from src.app.core.database import engine, Base, SessionLocal
from src.app.core.security import get_password_hash
import src.app.models.user
import src.app.models.partner
import src.app.models.product
import src.app.models.geography
import src.app.models.inventory
import src.app.models.sales_primary
import src.app.models.sales_secondary
import src.app.models.sales_tertiary
import src.app.models.finance
import src.app.models.logistics
import src.app.models.pricing
from src.app.models.user import User, Role


def reset_and_seed_database():
    print("🧨 WARNING: Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)

    print("🏗️ Recreating clean tables from latest schema...")
    Base.metadata.create_all(bind=engine)

    print("🌱 Seeding default Admin user...")
    db = SessionLocal()
    try:
        admin_role = Role(name="Admin", description="Super Administrator with full access")
        db.add(admin_role)
        db.flush()
        admin_user = User(
            username="admin",
            # email="manan@houseofmalhotra.com",
            password_hash=get_password_hash("admin123"),
            is_active=True,
            role_id=admin_role.id
        )
        db.add(admin_user)
        db.commit()

        print("✅ Database reset complete!")
        print("🔐 You can now log into the frontend with:")
        print("   Username: admin")
        print("   Password: admin123")

    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    confirm = input("This will DESTROY ALL DATA in the database. Are you sure? (type 'yes'): ")
    if confirm.lower() == 'yes':
        reset_and_seed_database()
    else:
        print("Aborted.")