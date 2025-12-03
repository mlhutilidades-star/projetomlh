"""
Testes Unitários - Domain Layer
--------------------------------
Testa entidades e value objects do domain layer.
"""
import pytest
from datetime import date, datetime
from modules.domain.entities import Conta, Regra


class TestConta:
    """Testes para value object Conta."""
    
    def test_is_revenue_positive(self):
        """Testa detecção de receita."""
        conta = Conta(
            id=1,
            descricao="Venda Shopee",
            fornecedor="Shopee",
            categoria="Receita Vendas",
            valor=100.0,
            vencimento=date.today(),
            mes=1,
            status="Pago"
        )
        assert conta.is_revenue() is True
    
    def test_is_revenue_negative(self):
        """Testa detecção de despesa."""
        conta = Conta(
            id=2,
            descricao="Fornecedor X",
            fornecedor="Fornecedor X",
            categoria="Despesa Operacional",
            valor=50.0,
            vencimento=date.today(),
            mes=1,
            status="Pendente"
        )
        assert conta.is_revenue() is False
    
    def test_is_revenue_none_category(self):
        """Testa detecção com categoria None."""
        conta = Conta(
            id=3,
            descricao="Sem categoria",
            fornecedor="Teste",
            categoria=None,
            valor=75.0,
            vencimento=date.today(),
            mes=1,
            status="Pendente"
        )
        assert conta.is_revenue() is False
    
    def test_is_overdue_true(self):
        """Testa conta vencida."""
        from datetime import timedelta
        past_date = date.today() - timedelta(days=10)
        conta = Conta(
            id=4,
            descricao="Vencida",
            fornecedor="Teste",
            categoria="Despesa",
            valor=100.0,
            vencimento=past_date,
            mes=1,
            status="Pendente"
        )
        assert conta.is_overdue() is True
    
    def test_is_overdue_false_paid(self):
        """Testa conta paga não é vencida."""
        from datetime import timedelta
        past_date = date.today() - timedelta(days=10)
        conta = Conta(
            id=5,
            descricao="Paga",
            fornecedor="Teste",
            categoria="Despesa",
            valor=100.0,
            vencimento=past_date,
            mes=1,
            status="Pago"
        )
        assert conta.is_overdue() is False
    
    def test_is_overdue_false_future(self):
        """Testa conta futura não é vencida."""
        from datetime import timedelta
        future_date = date.today() + timedelta(days=10)
        conta = Conta(
            id=6,
            descricao="Futura",
            fornecedor="Teste",
            categoria="Despesa",
            valor=100.0,
            vencimento=future_date,
            mes=1,
            status="Pendente"
        )
        assert conta.is_overdue() is False


class TestRegra:
    """Testes para value object Regra."""
    
    def test_should_activate_true(self):
        """Testa ativação quando uso >= 3 e não está ativo."""
        regra = Regra(
            id=1,
            cnpj="12345678000199",
            fornecedor="Fornecedor Teste",
            categoria="Fornecedor X",
            contador_usos=5,
            ativo=False
        )
        assert regra.should_activate() is True
    
    def test_should_activate_false(self):
        """Testa não ativação quando uso < 3."""
        regra = Regra(
            id=2,
            cnpj="12345678000199",
            fornecedor="Fornecedor Teste",
            categoria="Fornecedor Y",
            contador_usos=2,
            ativo=False
        )
        assert regra.should_activate() is False
    
    def test_should_activate_already_active(self):
        """Testa que regra já ativa retorna False."""
        regra = Regra(
            id=3,
            cnpj="12345678000199",
            fornecedor="Fornecedor Teste",
            categoria="Fornecedor Z",
            contador_usos=10,
            ativo=True
        )
        assert regra.should_activate() is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
