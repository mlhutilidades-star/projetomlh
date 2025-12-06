from sqlalchemy import Column, String, Integer

from app.db.base import Base


class Tenant(Base):
    __tablename__ = "tenant"

    name = Column(String(255), nullable=False)
    plan = Column(String(50), nullable=True)
    tenant_id = Column(Integer, nullable=False, unique=True, index=True)
