from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import DateTime, func, Column, Integer, ForeignKey


class Base(DeclarativeBase):
    id: int

    @declared_attr.directive
    def id(cls):  # type: ignore
        return Column(Integer, primary_key=True, index=True)

    @declared_attr.directive
    def __tablename__(cls) -> str:  # type: ignore
        return cls.__name__.lower()

    @declared_attr.directive
    def created_at(cls):  # type: ignore
        return Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @declared_attr.directive
    def updated_at(cls):  # type: ignore
        return Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class MultiTenantMixin:
    @declared_attr.directive
    def tenant_id(cls):  # type: ignore
        return Column(Integer, ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)


# Import models for Alembic's autogenerate to detect
# Commented to avoid circular imports at runtime
# from app.models.tenant import Tenant  # noqa: E402,F401
# from app.models.user import User  # noqa: E402,F401
# from app.models.store import Store  # noqa: E402,F401
# from app.models.product import Product  # noqa: E402,F401
# from app.models.order import Order  # noqa: E402,F401
# from app.models.payout import Payout  # noqa: E402,F401
# from app.models.payable import Payable  # noqa: E402,F401
# from app.models.receivable import Receivable  # noqa: E402,F401
# from app.models.bank_transaction import BankTransaction  # noqa: E402,F401
from app.models.boleto_rule import BoletoRule  # noqa: E402,F401
from app.models.boleto_upload import BoletoUpload  # noqa: E402,F401
