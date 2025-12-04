# 🔒 Notas de Segurança - Hub Financeiro

---

## 📋 Arquivos Sensíveis (Nunca Commitar)

Os seguintes arquivos devem existir **APENAS localmente** e NUNCA devem ser adicionados ao Git:

### Variáveis de Ambiente
- `.env` - **PRINCIPAL**: Contém todas as credenciais
- `.env.local` - Variáveis de ambiente locais
- `.env.*.local` - Variáveis específicas por ambiente

### Tokens & Credenciais
- `oauth_tokens.json` - Tokens OAuth de APIs
- `shopee_credentials.json` - Credenciais do Shopee
- `tiny_credentials.json` - Credenciais do Tiny ERP
- Qualquer arquivo contendo padrão `*token*`, `*oauth*`, `*credential*`, `*api_key*`

### Configuração Local
- `config_local.py` - Configurações locais
- `secrets/` - Pasta para segredos locais

---

## 🛠️ Como Configurar Localmente

### 1. Criar seu `.env` local (não será commitado)

```bash
cp .env.example .env
# Editar .env com suas credenciais LOCAIS
```

### 2. Estrutura do `.env` local

```env
# ===== Tiny ERP =====
TINY_API_TOKEN=your_actual_token_here

# ===== Shopee =====
SHOPEE_PARTNER_ID=your_partner_id
SHOPEE_PARTNER_KEY=your_partner_key
SHOPEE_SHOP_ID=your_shop_id
SHOPEE_ACCESS_TOKEN=your_access_token
SHOPEE_REFRESH_TOKEN=your_refresh_token
SHOPEE_REDIRECT_URL=your_redirect_url

# ===== Database =====
DATABASE_URL=sqlite:///hub_financeiro.db

# ===== Outros =====
DEBUG=False
```

### 3. Carregar variáveis localmente

Em Python (exemplo):
```python
from dotenv import load_dotenv
import os

load_dotenv('.env')  # Carrega de .env local
api_token = os.getenv('TINY_API_TOKEN')
```

---

## 🔐 Regras de Segurança

| Regra | O que fazer | O que NÃO fazer |
|-------|-----------|----------------|
| **Credenciais** | Guardar APENAS em `.env` local | ❌ Commitar credenciais reais |
| **Tokens** | Usar variáveis de ambiente | ❌ Hardcoded em código |
| **Secrets** | Colocar em `secrets/` local | ❌ Publicar em repositório |
| **API Keys** | Usar `os.getenv()` | ❌ Exibir em logs |

---

## ✅ Checklist de Segurança

- [ ] Troquei as credenciais Tiny ERP expostas
- [ ] Regenerei tokens Shopee (Partner Key + Access/Refresh)
- [ ] Criei `.env` local com novas credenciais
- [ ] Adicionei `.env` ao `.gitignore` ✓ (já feito)
- [ ] Testei conexões com novas credenciais
- [ ] Removi credenciais de qualquer histórico local antigo
- [ ] Comuniquei o incident para a segurança interna

---

## 📚 Referências

- [OWASP: Environment Variables](https://cheatsheetseries.owasp.org/cheatsheets/Nodejs_Security_Cheat_Sheet.html#environment-variables)
- [GitHub: Removing Sensitive Data from a Repository](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [python-dotenv Documentation](https://github.com/theskumar/python-dotenv)

---

**Data da última atualização**: 04 de dezembro de 2025  
**Responsável**: Security Review
