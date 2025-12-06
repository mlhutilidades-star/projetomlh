#!/usr/bin/env python3
"""Script para testar endpoints de analytics"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_analytics():
    # 1. Login
    print("🔐 Fazendo login...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "admin@example.com", "password": "admin123"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Erro no login: {login_response.status_code}")
        print(login_response.text)
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Login OK! Token: {token[:20]}...")
    
    # 2. Testar endpoints
    endpoints = [
        "/analytics/resumo-financeiro",
        "/analytics/dre-mensal",
        "/analytics/margem-por-produto",
        "/analytics/margem-por-canal",
        "/analytics/curva-abc",
        "/analytics/precificacao-sugerida"
    ]
    
    print("\n📊 Testando endpoints de analytics:")
    print("=" * 60)
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ {endpoint}")
                print(f"   Status: {response.status_code}")
                
                # Mostrar resumo dos dados
                if isinstance(data, dict):
                    print(f"   Campos: {list(data.keys())}")
                    # Mostrar alguns valores
                    for key, value in list(data.items())[:3]:
                        if isinstance(value, list):
                            print(f"   {key}: {len(value)} itens")
                        else:
                            print(f"   {key}: {value}")
                elif isinstance(data, list):
                    print(f"   Total de itens: {len(data)}")
                    if data:
                        print(f"   Primeiro item: {list(data[0].keys())}")
            else:
                print(f"\n❌ {endpoint}")
                print(f"   Status: {response.status_code}")
                print(f"   Erro: {response.text[:200]}")
        
        except Exception as e:
            print(f"\n❌ {endpoint}")
            print(f"   Erro: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎉 Testes concluídos!")

if __name__ == "__main__":
    test_analytics()
