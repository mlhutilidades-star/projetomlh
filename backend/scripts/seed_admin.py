import os
import asyncio

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.models.user import User

settings = get_settings()


def seed():
    db: Session = SessionLocal()
    try:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        tenant_name = os.getenv("ADMIN_TENANT", "Tenant Demo")

        existing_user = db.query(User).filter(User.email == admin_email).first()
        if existing_user:
            print("Admin user already exists")
            return

        tenant = Tenant(name=tenant_name, plan="trial", tenant_id=0)
        db.add(tenant)
        db.flush()
        tenant.tenant_id = tenant.id

        user = User(
            tenant_id=tenant.id,
            name="Admin",
            email=admin_email,
            password_hash=get_password_hash(admin_password),
            role="admin",
        )
        db.add(user)
        db.commit()
        print(f"Created tenant {tenant_name} with admin {admin_email}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
