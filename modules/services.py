"""
Application layer - Business logic services
"""
import hashlib
import logging
from typing import Dict, Optional
from datetime import date, datetime
from .domain.entities import Conta, Regra
from .domain.repositories import ContaRepository, RegraRepository

logger = logging.getLogger('services')

class ContaService:
    """Serviço de lógica de negócio para contas"""
    
    def __init__(self, conta_repo: ContaRepository, regra_repo: RegraRepository):
        self.conta_repo = conta_repo
        self.regra_repo = regra_repo
    
    def create_conta(self, **dados) -> Optional[Conta]:
        """Cria uma conta aplicando regras M11 e deduplicação"""
        # Parsear dados
        vencimento = dados.get('vencimento')
        if isinstance(vencimento, str):
            try:
                vencimento = datetime.strptime(vencimento, '%d/%m/%Y').date()
            except:
                try:
                    vencimento = datetime.strptime(vencimento, '%Y-%m-%d').date()
                except:
                    vencimento = date.today()
        elif not vencimento:
            vencimento = date.today()
        
        fornecedor = (dados.get('fornecedor') or '').strip()
        cnpj = dados.get('cnpj')
        categoria = dados.get('categoria')
        valor = float(dados.get('valor', 0.0))
        
        # Aplicar regra M11 se CNPJ disponível e categoria não especificada
        if cnpj and not categoria:
            regra = self.regra_repo.get_by_cnpj(cnpj)
            if regra and regra.ativo:
                categoria = regra.categoria
                fornecedor = (regra.razao_social or regra.fornecedor or fornecedor)
                logger.info(f'Regra M11 aplicada para CNPJ {cnpj}: categoria={categoria}')
        
        # Registrar uso de regra M11
        if cnpj and fornecedor and categoria:
            # Incrementa uso/atualiza regra
            try:
                self.regra_repo.update(Regra(id=None, cnpj=cnpj, categoria=categoria, ativo=True, fornecedor=fornecedor, contador_usos=0))
            except Exception:
                # Fallback para add_or_update em implementações simples
                self.regra_repo.add_or_update(cnpj, fornecedor, categoria)
        
        # Verificar duplicata via hash determinístico
        if fornecedor and valor and vencimento:
            dedup_hash = self.generate_dedup_hash(dados.get('external_id') or fornecedor, valor, vencimento)
            duplicates = self.conta_repo.find_duplicates(dedup_hash)
            if duplicates:
                logger.warning('Conta duplicada detectada (hash=%s)', dedup_hash)
                return None
        
        # Criar conta
        conta = Conta(
            id=None,
            mes=vencimento.month,
            vencimento=vencimento,
            fornecedor=fornecedor,
            cnpj=cnpj,
            categoria=categoria,
            descricao=dados.get('descricao'),
            valor=valor,
            status=dados.get('status', 'Pendente'),
            data_pagamento=dados.get('data_pagamento'),
            linha_digitavel=dados.get('linha_digitavel'),
            pdf_url=dados.get('pdf_path') or dados.get('pdf_url'),
            observacoes=dados.get('observacoes') or dados.get('observacao'),
            data_cadastro=datetime.now()
        )
        
        saved = self.conta_repo.add(conta)
        logger.info(f'Conta criada: ID {saved.id}')
        return saved
    
    def generate_dedup_hash(self, order_sn: str, valor: float, vencimento: date) -> str:
        """Gera hash (SHA256 truncado em 16 chars) para deduplicação."""
        key = f"{order_sn}|{valor}|{vencimento.isoformat()}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

class RegraService:
    """Serviço de lógica de negócio para regras M11"""
    
    def __init__(self, regra_repo: RegraRepository):
        self.regra_repo = regra_repo
    
    def apply_rule(self, cnpj: str) -> Optional[Dict]:
        """Retorna regra ativa para CNPJ se disponível"""
        regra = self.regra_repo.get_by_cnpj(cnpj)
        if regra and regra.ativo:
            return {
                'fornecedor': regra.fornecedor,
                'categoria': regra.categoria
            }
        return None
    
    def train_rule(self, cnpj: str, razao_social: str, categoria: str) -> Regra:
        """Treina/Cria regra e retorna objeto atualizado/novo.
        Se a regra existir, incrementa uso e pode ativar; se não existir, cria.
        """
        if not (cnpj and razao_social and categoria):
            raise ValueError('Parâmetros inválidos para treinamento de regra')
        existente = self.regra_repo.find_by_cnpj(cnpj)
        if existente is None:
            # cria nova
            return self.regra_repo.add(cnpj=cnpj, razao_social=razao_social, categoria=categoria)
        else:
            # incrementa uso e atualiza possivelmente ativando
            existente.razao_social = razao_social
            existente.categoria = categoria
            existente.uso = (existente.uso or 0) + 1
            if existente.should_activate():
                existente.ativo = True
            return self.regra_repo.update(existente)
