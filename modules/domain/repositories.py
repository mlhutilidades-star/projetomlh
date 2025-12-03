"""
Domain layer - Repository interfaces (contracts)
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date
from .entities import Conta, Regra

class ContaRepository(ABC):
    """Interface para repositório de contas"""
    
    @abstractmethod
    def add(self, conta: Conta) -> int:
        """Adiciona conta e retorna ID"""
        pass
    
    @abstractmethod
    def get_by_id(self, conta_id: int) -> Optional[Conta]:
        """Busca conta por ID"""
        pass
    
    @abstractmethod
    def get_all(self) -> List[Conta]:
        """Retorna todas as contas"""
        pass
    
    @abstractmethod
    def get_pending(self) -> List[Conta]:
        """Retorna contas pendentes"""
        pass
    
    @abstractmethod
    def get_overdue(self, reference_date: date = None) -> List[Conta]:
        """Retorna contas vencidas"""
        pass
    
    @abstractmethod
    def find_duplicates(self, fornecedor: str, valor: float, vencimento: date, tolerance_days: int = 3) -> Optional[Conta]:
        """Busca duplicatas baseado em fornecedor, valor e vencimento"""
        pass

class RegraRepository(ABC):
    """Interface para repositório de regras M11"""
    
    @abstractmethod
    def get_by_cnpj(self, cnpj: str) -> Optional[Regra]:
        """Busca regra por CNPJ"""
        pass
    
    @abstractmethod
    def add_or_update(self, cnpj: str, fornecedor: str, categoria: str) -> Regra:
        """Cria ou atualiza regra"""
        pass
    
    @abstractmethod
    def increment_usage(self, cnpj: str) -> None:
        """Incrementa contador de uso"""
        pass
    
    @abstractmethod
    def count_active(self) -> int:
        """Conta regras ativas"""
        pass
