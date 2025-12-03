"""
Testes de Serviços - Service Layer
-----------------------------------
Testa lógica de negócios em ContaService e RegraService.
"""
import pytest
from datetime import date
from unittest.mock import Mock, MagicMock

from modules.domain.entities import Conta, Regra
from modules.services import ContaService, RegraService


@pytest.fixture
def mock_conta_repository():
    """Cria mock do repository de contas."""
    return Mock()


@pytest.fixture
def mock_regra_repository():
    """Cria mock do repository de regras."""
    return Mock()


@pytest.fixture
def conta_service(mock_conta_repository, mock_regra_repository):
    """Cria instância de ContaService com mocks."""
    return ContaService(mock_conta_repository, mock_regra_repository)


@pytest.fixture
def regra_service(mock_regra_repository):
    """Cria instância de RegraService com mock."""
    return RegraService(mock_regra_repository)


class TestContaService:
    """Testes para ContaService."""
    
    def test_generate_dedup_hash(self, conta_service: ContaService):
        """Testa geração de hash determinístico."""
        hash1 = conta_service.generate_dedup_hash("ID123", 100.50, date(2024, 1, 15))
        hash2 = conta_service.generate_dedup_hash("ID123", 100.50, date(2024, 1, 15))
        hash3 = conta_service.generate_dedup_hash("ID124", 100.50, date(2024, 1, 15))
        
        assert hash1 == hash2  # Mesmo input = mesmo hash
        assert hash1 != hash3  # Input diferente = hash diferente
        assert len(hash1) == 16  # Hash truncado
    
    def test_create_conta_without_duplicate(self, conta_service: ContaService, mock_conta_repository: Mock, mock_regra_repository: Mock):
        """Testa criação de conta nova (sem duplicata)."""
        # Mock não encontra duplicata
        mock_conta_repository.find_duplicates.return_value = []
        mock_regra_repository.find_by_cnpj.return_value = None
        
        # Mock retorna conta salva
        saved_conta = Conta(
            id=1,
            descricao="Nova Conta",
            fornecedor="Fornecedor X",
            categoria="Categoria Padrão",
            valor=150.0,
            vencimento=date.today(),
            mes=1,
            status="Pendente",
            observacoes="HASH:abc123"
        )
        mock_conta_repository.add.return_value = saved_conta
        
        # Cria conta
        result = conta_service.create_conta(
            descricao="Nova Conta",
            fornecedor="Fornecedor X",
            valor=150.0,
            vencimento=date.today(),
            external_id="EXT123"
        )
        
        assert result is not None
        assert result.id == 1
        mock_conta_repository.add.assert_called_once()
    
    def test_create_conta_with_duplicate(self, conta_service: ContaService, mock_conta_repository: Mock):
        """Testa criação com duplicata existente."""
        # Mock encontra duplicata
        existing = Conta(
            id=99,
            descricao="Duplicata",
            fornecedor="Fornecedor X",
            categoria="Categoria",
            valor=150.0,
            vencimento=date.today(),
            mes=1,
            status="Pago",
            observacoes="HASH:same_hash"
        )
        mock_conta_repository.find_duplicates.return_value = [existing]
        
        # Tenta criar conta
        result = conta_service.create_conta(
            descricao="Duplicata",
            fornecedor="Fornecedor X",
            valor=150.0,
            vencimento=date.today(),
            external_id="EXT123"
        )
        
        assert result is None  # Não criou duplicata
        mock_conta_repository.add.assert_not_called()
    
    def test_create_conta_applies_rule(self, conta_service: ContaService, mock_conta_repository: Mock, mock_regra_repository: Mock):
        """Testa aplicação de regra M11 na criação."""
        # Mock não encontra duplicata
        mock_conta_repository.find_duplicates.return_value = []
        
        # Mock encontra regra ativa
        regra = Regra(
            id=1,
            cnpj="12345678000199",
            razao_social="Fornecedor Teste",
            categoria="Categoria da Regra",
            uso=10,
            min_ocorrencias=3,
            ativo=True
        )
        mock_regra_repository.find_by_cnpj.return_value = regra
        
        # Mock retorna conta salva
        saved_conta = Conta(
            id=1,
            descricao="Com Regra",
            fornecedor="Fornecedor Teste",
            categoria="Categoria da Regra",  # Aplicou regra
            valor=100.0,
            vencimento=date.today(),
            mes=1,
            status="Pendente",
            cnpj="12345678000199",
            observacoes="HASH:xyz789"
        )
        mock_conta_repository.add.return_value = saved_conta
        
        # Cria conta com CNPJ
        result = conta_service.create_conta(
            descricao="Com Regra",
            fornecedor="Fornecedor Teste",
            valor=100.0,
            vencimento=date.today(),
            external_id="EXT456",
            cnpj="12345678000199"
        )
        
        assert result is not None
        # Verifica que incrementou uso da regra
        mock_regra_repository.update.assert_called_once()


class TestRegraService:
    """Testes para RegraService."""
    
    def test_train_rule_creates_new(self, regra_service: RegraService, mock_regra_repository: Mock):
        """Testa criação de nova regra."""
        # Mock não encontra regra existente
        mock_regra_repository.find_by_cnpj.return_value = None
        
        # Mock retorna regra salva
        saved_regra = Regra(
            id=1,
            cnpj="12345678000199",
            razao_social="Nova Empresa",
            categoria="Categoria Nova",
            uso=1,
            min_ocorrencias=3,
            ativo=False
        )
        mock_regra_repository.add.return_value = saved_regra
        
        # Treina regra
        result = regra_service.train_rule(
            cnpj="12345678000199",
            razao_social="Nova Empresa",
            categoria="Categoria Nova"
        )
        
        assert result is not None
        assert result.id == 1
        assert result.uso == 1
        mock_regra_repository.add.assert_called_once()
    
    def test_train_rule_increments_existing(self, regra_service: RegraService, mock_regra_repository: Mock):
        """Testa incremento de regra existente."""
        # Mock encontra regra existente
        existing = Regra(
            id=2,
            cnpj="12345678000199",
            razao_social="Empresa Existente",
            categoria="Categoria Existente",
            uso=2,
            min_ocorrencias=3,
            ativo=False
        )
        mock_regra_repository.find_by_cnpj.return_value = existing
        
        # Mock retorna regra atualizada
        updated = Regra(
            id=2,
            cnpj="12345678000199",
            razao_social="Empresa Existente",
            categoria="Categoria Existente",
            uso=3,  # Incrementado
            min_ocorrencias=3,
            ativo=True  # Ativado automaticamente
        )
        mock_regra_repository.update.return_value = updated
        
        # Treina regra
        result = regra_service.train_rule(
            cnpj="12345678000199",
            razao_social="Empresa Existente",
            categoria="Categoria Existente"
        )
        
        assert result is not None
        assert result.uso == 3
        assert result.ativo is True
        mock_regra_repository.update.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
