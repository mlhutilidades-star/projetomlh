"""initial

Revision ID: 0001_init
Revises: 
Create Date: 2025-12-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import enum

# revision identifiers, used by Alembic.
revision: str = '0001_init'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class BoletoStatus(str, enum.Enum):
    pendente = "pendente"
    processado = "processado"
    erro = "erro"


def upgrade() -> None:
    op.create_table(
        'tenant',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('plan', sa.String(length=50), nullable=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id'),
    )
    op.create_index(op.f('ix_tenant_id'), 'tenant', ['id'], unique=False)

    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'email', name='uq_user_tenant_email')
    )
    op.create_index(op.f('ix_user_id'), 'user', ['id'], unique=False)
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=False)
    op.create_index(op.f('ix_user_tenant_id'), 'user', ['tenant_id'], unique=False)

    op.create_table(
        'store',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('tipo_canal', sa.String(length=50), nullable=False),
        sa.Column('credenciais', sa.JSON(), nullable=True),
        sa.Column('ativo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_store_id'), 'store', ['id'], unique=False)
    op.create_index(op.f('ix_store_tenant_id'), 'store', ['tenant_id'], unique=False)

    op.create_table(
        'boletorule',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('cnpj', sa.String(length=20), nullable=False),
        sa.Column('fornecedor_sugerido', sa.String(length=255), nullable=True),
        sa.Column('categoria_sugerida', sa.String(length=100), nullable=True),
        sa.Column('ativo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_boletorule_id'), 'boletorule', ['id'], unique=False)
    op.create_index(op.f('ix_boletorule_tenant_id'), 'boletorule', ['tenant_id'], unique=False)

    op.create_table(
        'boletoupload',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('arquivo_path', sa.String(length=255), nullable=True),
        sa.Column('cnpj', sa.String(length=20), nullable=True),
        sa.Column('vencimento', sa.Date(), nullable=True),
        sa.Column('valor', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('linha_digitavel', sa.String(length=255), nullable=True),
        sa.Column('status', sa.Enum(BoletoStatus), nullable=False, server_default=BoletoStatus.pendente.value),
        sa.Column('mensagem_erro', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_boletoupload_id'), 'boletoupload', ['id'], unique=False)
    op.create_index(op.f('ix_boletoupload_tenant_id'), 'boletoupload', ['tenant_id'], unique=False)

    op.create_table(
        'product',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('store_id', sa.Integer(), nullable=True),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('canal', sa.String(length=50), nullable=True),
        sa.Column('custo_atual', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('preco_venda', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('ativo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.ForeignKeyConstraint(['store_id'], ['store.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_product_id'), 'product', ['id'], unique=False)
    op.create_index(op.f('ix_product_sku'), 'product', ['sku'], unique=False)
    op.create_index(op.f('ix_product_tenant_id'), 'product', ['tenant_id'], unique=False)

    op.create_table(
        'order',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('store_id', sa.Integer(), nullable=True),
        sa.Column('codigo_externo', sa.String(length=100), nullable=False),
        sa.Column('canal', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('total_bruto', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('taxas', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('frete', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('liquido', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('data_pedido', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['store_id'], ['store.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_order_id'), 'order', ['id'], unique=False)
    op.create_index(op.f('ix_order_codigo_externo'), 'order', ['codigo_externo'], unique=False)
    op.create_index(op.f('ix_order_tenant_id'), 'order', ['tenant_id'], unique=False)

    op.create_table(
        'payout',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('store_id', sa.Integer(), nullable=True),
        sa.Column('referencia_periodo', sa.String(length=100), nullable=False),
        sa.Column('valor_bruto', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('taxas', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('frete', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('liquido', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('data_repassado', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['store_id'], ['store.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payout_id'), 'payout', ['id'], unique=False)
    op.create_index(op.f('ix_payout_tenant_id'), 'payout', ['tenant_id'], unique=False)

    op.create_table(
        'payable',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('fornecedor', sa.String(length=255), nullable=False),
        sa.Column('categoria', sa.String(length=100), nullable=True),
        sa.Column('vencimento', sa.Date(), nullable=False),
        sa.Column('valor_previsto', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('origem', sa.String(length=50), nullable=True),
        sa.Column('boleto_upload_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['boleto_upload_id'], ['boletoupload.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payable_id'), 'payable', ['id'], unique=False)
    op.create_index(op.f('ix_payable_tenant_id'), 'payable', ['tenant_id'], unique=False)

    op.create_table(
        'receivable',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('origem', sa.String(length=50), nullable=True),
        sa.Column('referencia', sa.String(length=255), nullable=False),
        sa.Column('previsao', sa.Date(), nullable=True),
        sa.Column('valor_previsto', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_receivable_id'), 'receivable', ['id'], unique=False)
    op.create_index(op.f('ix_receivable_tenant_id'), 'receivable', ['tenant_id'], unique=False)

    op.create_table(
        'banktransaction',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('banco', sa.String(length=100), nullable=False),
        sa.Column('data', sa.Date(), nullable=False),
        sa.Column('valor', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('tipo', sa.String(length=10), nullable=False),
        sa.Column('descricao', sa.String(length=255), nullable=True),
        sa.Column('conciliado', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_banktransaction_id'), 'banktransaction', ['id'], unique=False)
    op.create_index(op.f('ix_banktransaction_tenant_id'), 'banktransaction', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_table('banktransaction')
    op.drop_table('receivable')
    op.drop_table('payable')
    op.drop_table('payout')
    op.drop_table('order')
    op.drop_table('product')
    op.drop_table('boletoupload')
    op.drop_table('boletorule')
    op.drop_table('store')
    op.drop_table('user')
    op.drop_table('tenant')
