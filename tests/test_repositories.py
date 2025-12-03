"""
Testes de Integração - Repositories
------------------------------------
Testa implementações SQLAlchemy dos repositories.
"""
import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from modules.database import Base, ContaPagar as ContaPagarModel
from modules.domain.entities import Conta
from modules.infrastructure.sqlalchemy_repositories import SQLAlchemyContaRepository


@pytest.fixture
def db_session():
    """Cria sessão de banco em memória para testes."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def conta_repository(db_session):
    """Cria instância de repository com sessão de teste."""
    return SQLAlchemyContaRepository(db_session)


class TestSQLAlchemyContaRepository:
    """Testes para SQLAlchemyContaRepository."""
    
    def test_add_conta(self, conta_repository: SQLAlchemyContaRepository, db_session: Session):
        """Testa adição de conta."""
        conta = Conta(
            id=None,
            descricao="Teste Add",
            fornecedor="Fornecedor Teste",
            categoria="Despesa Teste",
            valor=100.0,
            vencimento=date.today(),
            mes=1,
            status="Pendente",
            observacoes="Teste de adição"
        )
        
        saved_conta = conta_repository.add(conta)
        
        assert saved_conta.id is not None
        assert saved_conta.descricao == "Teste Add"
        
        # Verifica persistência
        db_conta = db_session.query(ContaPagarModel).filter_by(id=saved_conta.id).first()
        assert db_conta is not None
        assert db_conta.descricao == "Teste Add"
    
    def test_get_by_id(self, conta_repository: SQLAlchemyContaRepository, db_session: Session):
        """Testa recuperação por ID."""
        # Cria conta diretamente no banco
        model = ContaPagarModel(
            descricao="Teste Get",
            fornecedor="Fornecedor",
            categoria="Categoria",
            valor=50.0,
            vencimento=date.today(),
            mes=2,
            status="Pago"
        )
        db_session.add(model)
        db_session.commit()
        
        # Recupera via repository
        conta = conta_repository.get_by_id(model.id)
        
        assert conta is not None
        assert conta.id == model.id
        assert conta.descricao == "Teste Get"
    
    def test_get_by_id_not_found(self, conta_repository: SQLAlchemyContaRepository):
        """Testa recuperação de ID inexistente."""
        conta = conta_repository.get_by_id(99999)
        assert conta is None
    
    def test_list_all(self, conta_repository: SQLAlchemyContaRepository, db_session: Session):
        """Testa listagem de todas as contas."""
        # Cria 3 contas
        for i in range(3):
            model = ContaPagarModel(
                descricao=f"Conta {i}",
                fornecedor="Fornecedor",
                categoria="Categoria",
                valor=i * 10.0,
                vencimento=date.today(),
                mes=1,
                status="Pendente"
            )
            db_session.add(model)
        db_session.commit()
        
        # Lista todas
        contas = conta_repository.list_all()
        
        assert len(contas) == 3
        assert all(isinstance(c, Conta) for c in contas)
    
    def test_find_duplicates_by_hash(self, conta_repository: SQLAlchemyContaRepository, db_session: Session):
        """Testa busca de duplicatas por hash."""
        hash_test = "abc123def456"
        
        # Cria conta com hash
        model = ContaPagarModel(
            descricao="Duplicata",
            fornecedor="Fornecedor",
            categoria="Categoria",
            valor=100.0,
            vencimento=date.today(),
            mes=1,
            status="Pendente",
            observacoes=f"Importado | HASH:{hash_test}"
        )
        db_session.add(model)
        db_session.commit()
        
        # Busca duplicatas
        duplicates = conta_repository.find_duplicates(dedup_hash=hash_test)
        
        assert len(duplicates) == 1
        assert duplicates[0].id == model.id
    
    def test_update_conta(self, conta_repository: SQLAlchemyContaRepository, db_session: Session):
        """Testa atualização de conta."""
        # Cria conta
        model = ContaPagarModel(
            descricao="Original",
            fornecedor="Fornecedor",
            categoria="Categoria",
            valor=100.0,
            vencimento=date.today(),
            mes=1,
            status="Pendente"
        )
        db_session.add(model)
        db_session.commit()
        
        # Atualiza via repository
        conta = conta_repository.get_by_id(model.id)
        conta.descricao = "Atualizado"
        conta.status = "Pago"
        
        updated = conta_repository.update(conta)
        
        assert updated.descricao == "Atualizado"
        assert updated.status == "Pago"
        
        # Verifica persistência
        db_session.refresh(model)
        assert model.descricao == "Atualizado"
        assert model.status == "Pago"
    
    def test_delete_conta(self, conta_repository: SQLAlchemyContaRepository, db_session: Session):
        """Testa remoção de conta."""
        # Cria conta
        model = ContaPagarModel(
            descricao="Para deletar",
            fornecedor="Fornecedor",
            categoria="Categoria",
            valor=100.0,
            vencimento=date.today(),
            mes=1,
            status="Pendente"
        )
        db_session.add(model)
        db_session.commit()
        conta_id = model.id
        
        # Remove via repository
        conta_repository.delete(conta_id)
        
        # Verifica remoção
        db_conta = db_session.query(ContaPagarModel).filter_by(id=conta_id).first()
        assert db_conta is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
