#!/usr/bin/env python
"""Seed admin user"""
import sys
sys.path.insert(0, '/app')

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.models.user import User

settings = get_settings()
session = SessionLocal()

try:
    admin = session.query(User).filter(User.email == settings.admin_email).first()
    if not admin:
        tenant = session.query(Tenant).filter(Tenant.name == settings.admin_tenant).first()
        if not tenant:
            tenant = Tenant(name=settings.admin_tenant, plan="professional", tenant_id=1)
            session.add(tenant)
            session.flush()
        admin = User(
            tenant_id=tenant.id,
            name="Admin",
            email=settings.admin_email,
            password_hash=get_password_hash(settings.admin_password),
            role="admin"
        )
        session.add(admin)
        session.commit()
        print("✅ Admin user created")
    else:
        print("✅ Admin user exists")
finally:
    session.close()
