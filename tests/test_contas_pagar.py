import pytest
from fastapi.testclient import TestClient
from api.contas_pagar import app

client = TestClient(app)

def test_listar_contas():
    response = client.get("/contas_pagar/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_criar_conta():
    nova_conta = {
        "descricao": "Conta de Teste",
        "valor": 100.0,
        "data_vencimento": "2025-12-31"
    }
    response = client.post("/contas_pagar/", json=nova_conta)
    assert response.status_code == 200
    assert response.json()["descricao"] == "Conta de Teste"
