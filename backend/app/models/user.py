from sqlalchemy import Column, String, Integer, UniqueConstraint

from app.db.base import Base, MultiTenantMixin


class User(MultiTenantMixin, Base):
    __tablename__ = "user"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),
    )

    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="admin")
