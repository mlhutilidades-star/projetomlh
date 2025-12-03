"""
Domain layer - Core business entities and value objects
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

@dataclass
class Conta:
    """Conta a pagar/receber - Value Object"""
    id: Optional[int]
    mes: int
    vencimento: date
    fornecedor: str
    categoria: Optional[str]
    descricao: Optional[str]
    valor: float
    status: str
    cnpj: Optional[str] = None
    data_pagamento: Optional[date] = None
    linha_digitavel: Optional[str] = None
    pdf_url: Optional[str] = None
    observacoes: Optional[str] = None
    data_cadastro: datetime = field(default_factory=datetime.now)
    
    def is_revenue(self) -> bool:
        """Identifica se é receita baseado na categoria"""
        if not self.categoria:
            return False
        return self.categoria.strip().lower().startswith('receita')
    
    def is_overdue(self, reference_date: date = None) -> bool:
        """Verifica se está vencida"""
        ref = reference_date or date.today()
        return self.vencimento < ref and self.status == 'Pendente'

@dataclass
class Regra:
    """Regra M11 - Value Object"""
    id: Optional[int]
    cnpj: str
    categoria: str
    ativo: bool = False
    fornecedor: str = ''
    contador_usos: int = 0
    ultima_atualizacao: datetime = field(default_factory=datetime.now)
    # Campos de compatibilidade com testes
    razao_social: Optional[str] = None  # alias de fornecedor
    uso: int = 0                        # alias de contador_usos
    min_ocorrencias: int = 3            # threshold para ativação
    
    def should_activate(self) -> bool:
        """Verifica se deve ser ativada (>= min_ocorrencias usos)."""
        # Prioriza campos de compatibilidade se fornecidos
        contador = self.uso if self.uso else self.contador_usos
        threshold = self.min_ocorrencias if self.min_ocorrencias else 3
        return not self.ativo and contador >= threshold

