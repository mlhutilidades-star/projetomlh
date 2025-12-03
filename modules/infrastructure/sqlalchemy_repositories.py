"""
Infrastructure layer - SQLAlchemy implementation of repositories
"""
from typing import List, Optional
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from ..database import ContaPagar, RegraM11
from ..domain.repositories import ContaRepository, RegraRepository
from ..domain.entities import Conta, Regra

class SQLAlchemyContaRepository(ContaRepository):
    """Implementação SQLAlchemy do repositório de contas"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def _to_entity(self, model: ContaPagar) -> Conta:
        """Converte model ORM para entity"""
        return Conta(
            id=model.id,
            mes=model.mes,
            vencimento=model.vencimento,
            fornecedor=model.fornecedor,
            cnpj=model.cnpj,
            categoria=model.categoria,
            descricao=model.descricao,
            valor=model.valor,
            status=model.status,
            data_pagamento=model.data_pagamento,
            linha_digitavel=model.linha_digitavel,
            pdf_url=model.pdf_url,
            observacoes=model.observacoes,
            data_cadastro=model.data_cadastro
        )
    
    def _to_model(self, entity: Conta) -> ContaPagar:
        """Converte entity para model ORM"""
        return ContaPagar(
            id=entity.id,
            mes=entity.mes,
            vencimento=entity.vencimento,
            fornecedor=entity.fornecedor,
            cnpj=entity.cnpj,
            categoria=entity.categoria,
            descricao=entity.descricao,
            valor=entity.valor,
            status=entity.status,
            data_pagamento=entity.data_pagamento,
            linha_digitavel=entity.linha_digitavel,
            pdf_url=entity.pdf_url,
            observacoes=entity.observacoes,
            data_cadastro=entity.data_cadastro
        )
    
    def add(self, conta: Conta) -> Conta:
        """Adiciona uma conta e retorna a entidade persistida."""
        model = self._to_model(conta)
        self.session.add(model)
        self.session.flush()
        return self._to_entity(model)
    
    def get_by_id(self, conta_id: int) -> Optional[Conta]:
        model = self.session.query(ContaPagar).filter(ContaPagar.id == conta_id).first()
        return self._to_entity(model) if model else None
    
    def get_all(self) -> List[Conta]:
        models = self.session.query(ContaPagar).all()
        return [self._to_entity(m) for m in models]

    # Compatibilidade com testes que chamam list_all()
    def list_all(self) -> List[Conta]:
        return self.get_all()
    
    def get_pending(self) -> List[Conta]:
        models = self.session.query(ContaPagar).filter(ContaPagar.status == 'Pendente').all()
        return [self._to_entity(m) for m in models]
    
    def get_overdue(self, reference_date: date = None) -> List[Conta]:
        ref = reference_date or date.today()
        models = self.session.query(ContaPagar).filter(
            ContaPagar.vencimento < ref,
            ContaPagar.status == 'Pendente'
        ).all()
        return [self._to_entity(m) for m in models]
    
    def find_duplicates(self, dedup_hash: str) -> List[Conta]:
        """Busca por duplicatas usando o hash armazenado em observacoes."""
        models = self.session.query(ContaPagar).filter(
            ContaPagar.observacoes.like(f"%HASH:{dedup_hash}%")
        ).all()
        return [self._to_entity(m) for m in models]

    def update(self, conta: Conta) -> Conta:
        """Atualiza uma conta existente e retorna a entidade atualizada."""
        model = self.session.query(ContaPagar).filter(ContaPagar.id == conta.id).first()
        if not model:
            raise ValueError(f"Conta id={conta.id} não encontrada para atualização")
        # Sincroniza campos
        model.mes = conta.mes
        model.vencimento = conta.vencimento
        model.fornecedor = conta.fornecedor
        model.cnpj = conta.cnpj
        model.categoria = conta.categoria
        model.descricao = conta.descricao
        model.valor = conta.valor
        model.status = conta.status
        model.data_pagamento = conta.data_pagamento
        model.linha_digitavel = conta.linha_digitavel
        model.pdf_url = conta.pdf_url
        model.observacoes = conta.observacoes
        model.data_cadastro = conta.data_cadastro
        self.session.flush()
        return self._to_entity(model)

    def delete(self, conta_id: int) -> None:
        """Remove uma conta pelo ID."""
        model = self.session.query(ContaPagar).filter(ContaPagar.id == conta_id).first()
        if model:
            self.session.delete(model)
            self.session.flush()

class SQLAlchemyRegraRepository(RegraRepository):
    """Implementação SQLAlchemy do repositório de regras"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def _to_entity(self, model: RegraM11) -> Regra:
        return Regra(
            id=model.id,
            cnpj=model.cnpj,
            fornecedor=model.fornecedor,
            categoria=model.categoria,
            contador_usos=model.contador_usos,
            ativo=model.ativo,
            ultima_atualizacao=model.ultima_atualizacao
        )
    
    def get_by_cnpj(self, cnpj: str) -> Optional[Regra]:
        model = self.session.query(RegraM11).filter(RegraM11.cnpj == cnpj).first()
        return self._to_entity(model) if model else None
    
    def add_or_update(self, cnpj: str, fornecedor: str, categoria: str) -> Regra:
        model = self.session.query(RegraM11).filter(RegraM11.cnpj == cnpj).first()
        if model:
            model.fornecedor = fornecedor
            model.categoria = categoria
            model.contador_usos += 1
            if model.contador_usos >= 3:
                model.ativo = True
            model.ultima_atualizacao = datetime.now()
        else:
            model = RegraM11(
                cnpj=cnpj,
                fornecedor=fornecedor,
                categoria=categoria,
                contador_usos=1,
                ativo=False
            )
            self.session.add(model)
        self.session.flush()
        return self._to_entity(model)
    
    def increment_usage(self, cnpj: str) -> None:
        model = self.session.query(RegraM11).filter(RegraM11.cnpj == cnpj).first()
        if model:
            model.contador_usos += 1
            if model.contador_usos >= 3:
                model.ativo = True
            model.ultima_atualizacao = datetime.now()
    
    def count_active(self) -> int:
        return self.session.query(RegraM11).filter(RegraM11.ativo == True).count()
