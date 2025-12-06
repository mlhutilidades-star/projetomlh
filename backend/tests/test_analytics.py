"""
Testes básicos para endpoints de analytics
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import get_settings

client = TestClient(app)
settings = get_settings()


def get_auth_token():
    """Helper para obter token de autenticação"""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_resumo_financeiro():
    """Testa endpoint de resumo financeiro"""
    token = get_auth_token()
    response = client.get(
        "/api/v1/analytics/resumo-financeiro",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "faturamento_30d" in data
    assert "lucro_estimado_30d" in data
    assert "contas_pagar_abertas" in data
    assert "contas_receber_abertas" in data
    assert "saldo_repasses_30d" in data
    assert "ticket_medio_30d" in data


def test_dre_mensal():
    """Testa endpoint de DRE mensal"""
    token = get_auth_token()
    response = client.get(
        "/api/v1/analytics/dre-mensal?ano=2025",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ano"] == 2025
    assert len(data["meses"]) == 12
    for mes in data["meses"]:
        assert "receitas_brutas" in mes
        assert "descontos_taxas" in mes
        assert "custos_produto" in mes
        assert "despesas" in mes
        assert "resultado_liquido" in mes


def test_margem_por_produto():
    """Testa endpoint de margem por produto"""
    token = get_auth_token()
    response = client.get(
        "/api/v1/analytics/margem-por-produto",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "itens" in data
    if len(data["itens"]) > 0:
        item = data["itens"][0]
        assert "sku" in item
        assert "nome" in item
        assert "vendas_qtd" in item
        assert "receita_liquida" in item
        assert "custo_total" in item
        assert "margem_valor" in item
        assert "margem_percentual" in item


def test_margem_por_canal():
    """Testa endpoint de margem por canal"""
    token = get_auth_token()
    response = client.get(
        "/api/v1/analytics/margem-por-canal",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "itens" in data


def test_curva_abc():
    """Testa endpoint de curva ABC"""
    token = get_auth_token()
    response = client.get(
        "/api/v1/analytics/curva-abc",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "itens" in data
    if len(data["itens"]) > 0:
        item = data["itens"][0]
        assert "sku" in item
        assert "classe" in item
        assert item["classe"] in ["A", "B", "C"]


def test_precificacao_sugerida():
    """Testa endpoint de precificação sugerida"""
    token = get_auth_token()
    response = client.get(
        "/api/v1/analytics/precificacao-sugerida",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "itens" in data
    if len(data["itens"]) > 0:
        item = data["itens"][0]
        assert "sku" in item
        assert "preco_sugerido_20" in item
        assert "preco_sugerido_30" in item


def test_analytics_require_auth():
    """Testa que endpoints exigem autenticação"""
    response = client.get("/api/v1/analytics/resumo-financeiro")
    assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
