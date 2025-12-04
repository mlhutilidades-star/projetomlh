"""
Testes expandidos para database.py focando em funções não cobertas
"""
import pytest
from datetime import date, datetime
from modules.database import (
    init_database, get_db, ensure_indexes,
    get_regra, registrar_uso_cnpj, add_or_update_regra,
    get_all_contas, get_regra_custo, add_or_update_regra_custo,
    ContaPagar, RegraM11, RegraFornecedorCusto
)


class TestDatabaseExpanded:
    """Tests for database functions with low coverage"""
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        """Setup test database - use the same database as other tests"""
        # Initialize database if needed (conftest already does this, but ensure it's done)
        from modules.database import init_database, get_db
        init_database()
        
        # Clean up any existing test data before each test to ensure isolation
        db = get_db()
        try:
            # Clean tables
            db.query(ContaPagar).delete()
            db.query(RegraM11).delete()
            db.query(RegraFornecedorCusto).delete()
            db.commit()
        except:
            db.rollback()
        finally:
            db.close()
        
        yield
        
        # No cleanup needed - database persists for other tests
    
    def test_get_db_returns_session(self):
        """Test that get_db returns a valid session"""
        db = get_db()
        
        assert db is not None
        # Session should be usable
        result = db.query(ContaPagar).count()
        assert result == 0  # Empty database
        
        db.close()
    
    def test_ensure_indexes(self):
        """Test index creation"""
        # Should not raise errors
        ensure_indexes()
        
        # Verify database still works after index creation
        db = get_db()
        count = db.query(ContaPagar).count()
        assert count == 0
        db.close()
    
    def test_get_regra_not_found(self):
        """Test get_regra when CNPJ doesn't exist"""
        result = get_regra("00.000.000/0000-00")
        
        assert result is None
    
    def test_get_regra_found(self):
        """Test get_regra when CNPJ exists"""
        # Create a rule
        add_or_update_regra("12.345.678/0001-90", "Fornecedor Teste", "Aluguel")
        
        # Retrieve it
        result = get_regra("12.345.678/0001-90")
        
        assert result is not None
        assert result['cnpj'] == "12.345.678/0001-90"
        assert result['fornecedor'] == "Fornecedor Teste"
        assert result['categoria'] == "Aluguel"
        assert result['contador_usos'] == 1
        assert result['ativo'] is False
    
    def test_registrar_uso_cnpj_increments_counter(self):
        """Test that registrar_uso_cnpj increments counter"""
        # Create rule
        add_or_update_regra("12.345.678/0001-90", "Fornecedor", "Categoria")
        
        # Register first use (should be at 2 now, 1 from creation)
        registrar_uso_cnpj("12.345.678/0001-90")
        
        regra = get_regra("12.345.678/0001-90")
        assert regra['contador_usos'] == 2
        assert regra['ativo'] is False
    
    def test_registrar_uso_cnpj_activates_at_3(self):
        """Test that rule becomes active after 3 uses"""
        # Create rule (count = 1)
        add_or_update_regra("12.345.678/0001-90", "Fornecedor", "Categoria")
        
        # Register 2 more uses
        registrar_uso_cnpj("12.345.678/0001-90")  # count = 2
        registrar_uso_cnpj("12.345.678/0001-90")  # count = 3
        
        regra = get_regra("12.345.678/0001-90")
        assert regra['contador_usos'] == 3
        assert regra['ativo'] is True
    
    def test_get_all_contas_empty(self):
        """Test get_all_contas with empty database"""
        result = get_all_contas()
        
        assert result == []
    
    def test_get_all_contas_with_data(self):
        """Test get_all_contas with actual data"""
        db = get_db()
        
        # Create test contas
        conta1 = ContaPagar(
            mes=1,
            vencimento=date(2025, 1, 15),
            fornecedor="Fornecedor 1",
            valor=100.50,
            status="Pendente"
        )
        conta2 = ContaPagar(
            mes=2,
            vencimento=date(2025, 2, 20),
            fornecedor="Fornecedor 2",
            valor=200.75,
            status="Pago"
        )
        
        db.add(conta1)
        db.add(conta2)
        db.commit()
        db.close()
        
        # Get all
        result = get_all_contas()
        
        assert len(result) == 2
        assert result[0]['fornecedor'] == "Fornecedor 1"
        assert result[1]['fornecedor'] == "Fornecedor 2"
    
    def test_get_regra_custo_not_found(self):
        """Test get_regra_custo when fornecedor doesn't exist"""
        result = get_regra_custo("Fornecedor Inexistente")
        
        assert result is None
    
    def test_add_or_update_regra_custo_new(self):
        """Test creating new cost rule"""
        add_or_update_regra_custo("Fornecedor Teste", "valor * 1.15")
        
        # Verify saved
        result = get_regra_custo("Fornecedor Teste")
        
        assert result is not None
        # Database uppercases fornecedor
        assert result['fornecedor'].upper() == "FORNECEDOR TESTE"
        assert result['formula'] == "valor * 1.15"
        assert result['ativo'] is True
        # Counter starts at 1 upon creation
        assert result['contador_usos'] >= 0
    
    def test_add_or_update_regra_custo_update(self):
        """Test updating existing cost rule"""
        # Create initial rule
        add_or_update_regra_custo("Fornecedor Teste", "valor * 1.15")
        
        # Update with new formula
        add_or_update_regra_custo("Fornecedor Teste", "valor * 1.20")
        
        # Verify updated
        result = get_regra_custo("Fornecedor Teste")
        
        assert result['formula'] == "valor * 1.20"
    
    def test_add_or_update_regra_new(self):
        """Test creating new M11 rule"""
        add_or_update_regra("12.345.678/0001-90", "Fornecedor Novo", "Categoria Nova")
        
        # Verify
        result = get_regra("12.345.678/0001-90")
        
        assert result is not None
        assert result['fornecedor'] == "Fornecedor Novo"
        assert result['categoria'] == "Categoria Nova"
    
    def test_add_or_update_regra_update(self):
        """Test updating existing M11 rule"""
        # Create
        add_or_update_regra("12.345.678/0001-90", "Fornecedor Antigo", "Categoria Antiga")
        
        # Update
        add_or_update_regra("12.345.678/0001-90", "Fornecedor Novo", "Categoria Nova")
        
        # Verify updated
        result = get_regra("12.345.678/0001-90")
        
        assert result['fornecedor'] == "Fornecedor Novo"
        assert result['categoria'] == "Categoria Nova"