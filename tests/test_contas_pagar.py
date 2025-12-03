import pytest
from fastapi.testclient import TestClient
from api.contas_pagar import app
from datetime import date

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
    data = response.json()
    assert data["descricao"] == "Conta de Teste"
    assert data["valor"] == 100.0
    assert data["status"] == "pendente"
    assert "id" in data

def test_editar_conta():
    # Criar conta primeiro
    nova_conta = {
        "descricao": "Conta Original",
        "valor": 200.0,
        "data_vencimento": "2025-12-31"
    }
    create_resp = client.post("/contas_pagar/", json=nova_conta)
    conta_id = create_resp.json()["id"]
    
    # Editar
    conta_atualizada = {
        "descricao": "Conta Atualizada",
        "valor": 250.0,
        "data_vencimento": "2026-01-15",
        "fornecedor": "Fornecedor ABC"
    }
    response = client.put(f"/contas_pagar/{conta_id}", json=conta_atualizada)
    assert response.status_code == 200
    data = response.json()
    assert data["descricao"] == "Conta Atualizada"
    assert data["valor"] == 250.0
    assert data["fornecedor"] == "Fornecedor ABC"

def test_marcar_como_paga():
    # Criar conta
    nova_conta = {
        "descricao": "Conta para Pagar",
        "valor": 150.0,
        "data_vencimento": "2025-12-20"
    }
    create_resp = client.post("/contas_pagar/", json=nova_conta)
    conta_id = create_resp.json()["id"]
    
    # Marcar como paga
    response = client.patch(f"/contas_pagar/{conta_id}/pagar")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "paga"
    assert data["data_pagamento"] is not None

def test_excluir_conta():
    # Criar conta
    nova_conta = {
        "descricao": "Conta para Excluir",
        "valor": 50.0,
        "data_vencimento": "2025-12-10"
    }
    create_resp = client.post("/contas_pagar/", json=nova_conta)
    conta_id = create_resp.json()["id"]
    
    # Excluir
    response = client.delete(f"/contas_pagar/{conta_id}")
    assert response.status_code == 200
    
    # Verificar que foi excluída (tentar editar deve retornar 404)
    edit_resp = client.put(f"/contas_pagar/{conta_id}", json=nova_conta)
    assert edit_resp.status_code == 404

def test_conta_nao_encontrada():
    response = client.get("/contas_pagar/99999")
    # Assumindo que 99999 não existe; ajustar se rota GET individual existir
    # Por enquanto, apenas testamos que edição de ID inexistente retorna 404
    edit_resp = client.put("/contas_pagar/99999", json={
        "descricao": "Teste",
        "valor": 10.0,
        "data_vencimento": "2025-12-31"
    })
    assert edit_resp.status_code == 404
