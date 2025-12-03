"""
Módulo de banco de dados
Gerencia conexão e operações com SQLite
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import os

# Base para modelos
Base = declarative_base()

# Engine do banco
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///hub_financeiro.db")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

# Modelos

class ContaPagar(Base):
    """Modelo para contas a pagar"""
    __tablename__ = "contas_pagar"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    mes = Column(Integer, nullable=False)  # 1-12
    vencimento = Column(Date, nullable=False)
    fornecedor = Column(String(200), nullable=False)
    cnpj = Column(String(18))
    categoria = Column(String(100))
    descricao = Column(String(500))
    valor = Column(Float, nullable=False)
    status = Column(String(20), default="Pendente")
    data_pagamento = Column(Date)
    linha_digitavel = Column(String(100))
    pdf_url = Column(String(500))
    observacoes = Column(String(1000))
    data_cadastro = Column(DateTime, default=datetime.now)

class RegraM11(Base):
    """Modelo para regras de aprendizado M11"""
    __tablename__ = "regras_m11"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cnpj = Column(String(18), unique=True, nullable=False)
    fornecedor = Column(String(200), nullable=False)
    categoria = Column(String(100), nullable=False)
    contador_usos = Column(Integer, default=1)
    ativo = Column(Boolean, default=False)
    ultima_atualizacao = Column(DateTime, default=datetime.now)

class PedidoShopee(Base):
    """Modelo para pedidos do Shopee"""
    __tablename__ = "pedidos_shopee"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_sn = Column(String(100), unique=True, nullable=False)
    order_status = Column(String(50))
    create_time = Column(DateTime)
    update_time = Column(DateTime)
    total_amount = Column(Float)
    buyer_username = Column(String(200))
    data_sincronizacao = Column(DateTime, default=datetime.now)

class ProdutoTiny(Base):
    """Modelo para produtos do Tiny ERP"""
    __tablename__ = "produtos_tiny"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    produto_id = Column(String(100), unique=True, nullable=False)
    nome = Column(String(500))
    preco = Column(Float)
    estoque = Column(Integer)
    ativo = Column(Boolean, default=True)
    data_sincronizacao = Column(DateTime, default=datetime.now)

class ContaReceber(Base):
    """Modelo para contas a receber"""
    __tablename__ = "contas_receber"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    mes = Column(Integer, nullable=False)
    vencimento = Column(Date, nullable=False)
    cliente = Column(String(200), nullable=False)
    descricao = Column(String(500))
    valor = Column(Float, nullable=False)
    status = Column(String(20), default="Pendente")
    data_recebimento = Column(Date)
    observacoes = Column(String(1000))
    data_cadastro = Column(DateTime, default=datetime.now)

class RegraFornecedorCusto(Base):
    """Modelo para regras de cálculo de custo por fornecedor"""
    __tablename__ = "regras_fornecedor_custo"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fornecedor = Column(String(200), unique=True, nullable=False)
    formula = Column(String(500), nullable=False)
    ativo = Column(Boolean, default=True)
    contador_usos = Column(Integer, default=0)
    ultima_atualizacao = Column(DateTime, default=datetime.now)
    observacoes = Column(String(1000))

def init_database():
    """Inicializa o banco de dados criando todas as tabelas"""
    Base.metadata.create_all(engine)
    ensure_indexes()

def init_db():
    """Alias de compatibilidade"""
    init_database()

def get_db():
    """Retorna uma sessão do banco de dados (caller deve fechar manualmente)"""
    return SessionLocal()

def ensure_indexes():
    """Cria índices úteis para performance se não existirem."""
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_contas_vencimento ON contas_pagar (vencimento)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_contas_categoria ON contas_pagar (categoria)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_contas_fornecedor ON contas_pagar (fornecedor)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_contas_mes ON contas_pagar (mes)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_contas_status ON contas_pagar (status)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_contas_descricao ON contas_pagar (descricao)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_regras_cnpj ON regras_m11 (cnpj)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_regras_ativo ON regras_m11 (ativo)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_shopee_order_sn ON pedidos_shopee (order_sn)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_shopee_status ON pedidos_shopee (order_status)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_tiny_produto_id ON produtos_tiny (produto_id)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_regras_custo_fornecedor ON regras_fornecedor_custo (fornecedor)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_regras_custo_ativo ON regras_fornecedor_custo (ativo)")
            conn.commit()
    except Exception as e:
        # Logging leve para evitar dependência circular
        print(f"[DB] Falha ao criar índices: {e}")

# --- Funções de Regras (M11) ---
def get_regra(cnpj: str):
    """Obtém regra por CNPJ, retorna dict ou None"""
    db = get_db()
    try:
        regra = db.query(RegraM11).filter(RegraM11.cnpj == cnpj).first()
        if not regra:
            return None
        return {
            'id': regra.id,
            'cnpj': regra.cnpj,
            'fornecedor': regra.fornecedor,
            'categoria': regra.categoria,
            'contador_usos': regra.contador_usos,
            'ativo': regra.ativo,
            'ultima_atualizacao': regra.ultima_atualizacao
        }
    finally:
        db.close()

def registrar_uso_cnpj(cnpj: str):
    """Incrementa contador de uso de uma regra; ativa se >=3"""
    db = get_db()
    try:
        regra = db.query(RegraM11).filter(RegraM11.cnpj == cnpj).first()
        if regra:
            regra.contador_usos += 1
            if regra.contador_usos >= 3:
                regra.ativo = True
            regra.ultima_atualizacao = datetime.now()
            db.commit()
    finally:
        db.close()

def add_or_update_regra(cnpj: str, fornecedor: str, categoria: str):
    """Cria ou atualiza regra para CNPJ; ativa após 3 usos.
    Sempre incrementa contador quando chamada em contexto de criação de conta.
    """
    if not cnpj or not fornecedor or not categoria:
        return None
    db = get_db()
    try:
        regra = db.query(RegraM11).filter(RegraM11.cnpj == cnpj).first()
        if regra:
            # Atualiza campos se vieram diferentes e fazem sentido
            if fornecedor and fornecedor != regra.fornecedor:
                regra.fornecedor = fornecedor
            if categoria and categoria != regra.categoria:
                regra.categoria = categoria
            regra.contador_usos += 1
            if regra.contador_usos >= 3:
                regra.ativo = True
            regra.ultima_atualizacao = datetime.now()
        else:
            regra = RegraM11(
                cnpj=cnpj,
                fornecedor=fornecedor,
                categoria=categoria,
                contador_usos=1,
                ativo=False
            )
            db.add(regra)
        db.commit()
        return regra
    finally:
        db.close()

def count_regras_ativas():
    """Retorna quantidade de regras ativas"""
    db = get_db()
    try:
        return db.query(RegraM11).filter(RegraM11.ativo == True).count()
    finally:
        db.close()

# --- Funções de ContaPagar helper ---
from datetime import datetime as _dt
def add_conta(dados: dict = None, **kwargs):
    """Adiciona uma conta a pagar a partir de dict ou kwargs.
    Campos esperados: vencimento (DD/MM/AAAA, YYYY-MM-DD ou date), fornecedor, cnpj, categoria,
    descricao, valor (float), status, linha_digitavel, pdf_path/ pdf_url, observacoes, observacao.
    """
    # Aceitar tanto dict quanto kwargs
    if dados is None:
        dados = kwargs
    else:
        dados = {**dados, **kwargs}
    
    db = get_db()
    try:
        venc = dados.get('vencimento')
        if isinstance(venc, str):
            try:
                # Tentar DD/MM/YYYY
                venc_date = _dt.strptime(venc, '%d/%m/%Y').date()
            except:
                try:
                    # Tentar YYYY-MM-DD
                    venc_date = _dt.strptime(venc, '%Y-%m-%d').date()
                except:
                    # fallback para hoje
                    venc_date = _dt.now().date()
        else:
            venc_date = venc if venc else _dt.now().date()
        
        conta = ContaPagar(
            mes=venc_date.month,
            vencimento=venc_date,
            fornecedor=dados.get('fornecedor','').strip(),
            cnpj=dados.get('cnpj') or None,
            categoria=dados.get('categoria') or None,
            descricao=dados.get('descricao') or None,
            valor=float(dados.get('valor',0.0)),
            status=dados.get('status','Pendente'),
            linha_digitavel=dados.get('linha_digitavel') or None,
            pdf_url=dados.get('pdf_path') or dados.get('pdf_url') or None,
            observacoes=dados.get('observacoes') or dados.get('observacao') or None
        )
        db.add(conta)
        db.commit()
        return conta.id
    finally:
        db.close()

def get_all_contas():
    """Retorna todas as contas como lista de dicts"""
    db = get_db()
    try:
        contas = db.query(ContaPagar).all()
        return [{
            'id': c.id,
            'mes': c.mes,
            'vencimento': c.vencimento.strftime('%Y-%m-%d') if c.vencimento else '',
            'fornecedor': c.fornecedor,
            'cnpj': c.cnpj or '',
            'categoria': c.categoria or '',
            'descricao': c.descricao or '',
            'valor': c.valor,
            'status': c.status,
            'data_pagamento': c.data_pagamento.strftime('%Y-%m-%d') if c.data_pagamento else '',
            'linha_digitavel': c.linha_digitavel or '',
            'pdf_url': c.pdf_url or '',
            'observacoes': c.observacoes or '',
            'data_cadastro': c.data_cadastro.strftime('%Y-%m-%d %H:%M:%S') if c.data_cadastro else ''
        } for c in contas]
    finally:
        db.close()

# Alias para compatibilidade
Conta = ContaPagar

# --- Funções de RegraFornecedorCusto helper ---
def get_regra_custo(fornecedor: str):
    """Obtém regra de custo por fornecedor, retorna dict ou None"""
    db = get_db()
    try:
        fornecedor_upper = fornecedor.strip().upper()
        regra = db.query(RegraFornecedorCusto).filter(
            RegraFornecedorCusto.fornecedor == fornecedor_upper
        ).first()
        if not regra:
            return None
        return {
            'id': regra.id,
            'fornecedor': regra.fornecedor,
            'formula': regra.formula,
            'ativo': regra.ativo,
            'contador_usos': regra.contador_usos,
            'ultima_atualizacao': regra.ultima_atualizacao,
            'observacoes': regra.observacoes
        }
    finally:
        db.close()

def add_or_update_regra_custo(fornecedor: str, formula: str, ativo: bool = True, observacoes: str = None):
    """Cria ou atualiza regra de custo para fornecedor"""
    if not fornecedor or not formula:
        return None
    db = get_db()
    try:
        fornecedor_upper = fornecedor.strip().upper()
        regra = db.query(RegraFornecedorCusto).filter(
            RegraFornecedorCusto.fornecedor == fornecedor_upper
        ).first()
        if regra:
            regra.formula = formula
            regra.ativo = ativo
            regra.contador_usos += 1
            regra.ultima_atualizacao = datetime.now()
            if observacoes:
                regra.observacoes = observacoes
        else:
            regra = RegraFornecedorCusto(
                fornecedor=fornecedor_upper,
                formula=formula,
                ativo=ativo,
                contador_usos=1,
                observacoes=observacoes
            )
            db.add(regra)
        db.commit()
        return regra
    finally:
        db.close()

def list_regras_custo(apenas_ativas: bool = False):
    """Lista todas as regras de custo"""
    db = get_db()
    try:
        query = db.query(RegraFornecedorCusto)
        if apenas_ativas:
            query = query.filter(RegraFornecedorCusto.ativo == True)
        regras = query.all()
        return [{
            'id': r.id,
            'fornecedor': r.fornecedor,
            'formula': r.formula,
            'ativo': r.ativo,
            'contador_usos': r.contador_usos,
            'ultima_atualizacao': r.ultima_atualizacao,
            'observacoes': r.observacoes or ''
        } for r in regras]
    finally:
        db.close()

def delete_regra_custo(fornecedor: str):
    """Remove regra de custo por fornecedor"""
    db = get_db()
    try:
        fornecedor_upper = fornecedor.strip().upper()
        regra = db.query(RegraFornecedorCusto).filter(
            RegraFornecedorCusto.fornecedor == fornecedor_upper
        ).first()
        if regra:
            db.delete(regra)
            db.commit()
            return True
        return False
    finally:
        db.close()
