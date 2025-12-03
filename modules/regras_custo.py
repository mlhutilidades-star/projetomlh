"""Regras de cálculo de custo por fornecedor.

Permite criar fórmulas customizadas por fornecedor para calcular o custo unitário
a partir dos valores extraídos da NF-e.

Variáveis disponíveis na fórmula:
- vUnCom: valor unitário comercial
- quantidade: quantidade
- vProd: valor total do produto
- ipi_total: IPI total do item
- ipi_aliq: alíquota IPI em % (extraída do XML pIPI, ou calculada como fallback)
- st_total: ICMS ST total
- icms_total: ICMS total
- pis_total: PIS total
- cofins_total: COFINS total
- rateio_frete: frete rateado para o item
- rateio_seguro: seguro rateado para o item
- rateio_outros: outros rateado para o item
- rateio_desconto: desconto rateado para o item

Exemplo de regra:
    GGB BRINQUEDOS: (vUnCom / 7) + (ipi_aliq * 0.7)
    
Nota: ipi_aliq é preferencialmente extraído do campo pIPI do XML. Se não disponível, 
é calculado como (ipi_total / vProd * 100) como fallback.
"""
from __future__ import annotations
import re
from typing import Dict, Optional


class RegraFornecedorCusto:
    def __init__(self, fornecedor: str, formula: str, ativo: bool = True):
        self.fornecedor = fornecedor.strip().upper()
        self.formula = formula.strip()
        self.ativo = ativo

    def calcular_custo(self, vars: Dict[str, float]) -> float:
        """Calcula o custo usando a fórmula com as variáveis fornecidas."""
        if not self.ativo:
            raise ValueError("Regra inativa")
        
        # Sanitize e validação básica
        formula_safe = self.formula
        # Permitir apenas caracteres seguros: números, letras, operadores, parênteses, ponto decimal
        if not re.match(r'^[\d\w\s\+\-\*/\(\)\.]+$', formula_safe):
            raise ValueError(f"Fórmula contém caracteres não permitidos: {formula_safe}")
        
        # Preparar contexto de variáveis
        context = {k: float(v) for k, v in vars.items()}
        
        # Calcular ipi_aliq se não fornecido OU se vier como 0 e houver dados para calcular
        vProd = context.get('vProd', 0.0)
        ipi_total = context.get('ipi_total', 0.0)
        if ('ipi_aliq' not in context) or (float(context.get('ipi_aliq', 0.0)) == 0.0 and ipi_total > 0 and vProd > 0):
            context['ipi_aliq'] = (ipi_total / vProd * 100.0) if vProd > 0 else 0.0
        
        try:
            result = eval(formula_safe, {"__builtins__": {}}, context)
            return float(result)
        except Exception as e:
            raise ValueError(f"Erro ao avaliar fórmula: {e}")

    def to_dict(self) -> Dict:
        return {
            'fornecedor': self.fornecedor,
            'formula': self.formula,
            'ativo': self.ativo
        }

    @staticmethod
    def from_dict(data: Dict) -> 'RegraFornecedorCusto':
        return RegraFornecedorCusto(
            fornecedor=data['fornecedor'],
            formula=data['formula'],
            ativo=data.get('ativo', True)
        )


# Singleton para gerenciar regras em memória (persistência via DB)
_regras_cache: Dict[str, RegraFornecedorCusto] = {}


def adicionar_regra(fornecedor: str, formula: str, ativo: bool = True):
    """Adiciona ou atualiza regra de custo para um fornecedor."""
    regra = RegraFornecedorCusto(fornecedor, formula, ativo)
    _regras_cache[regra.fornecedor] = regra


def obter_regra(fornecedor: str) -> Optional[RegraFornecedorCusto]:
    """Obtém regra de custo para fornecedor (case-insensitive)."""
    key = fornecedor.strip().upper()
    return _regras_cache.get(key)


def listar_regras() -> list[RegraFornecedorCusto]:
    """Lista todas as regras cadastradas."""
    return list(_regras_cache.values())


def remover_regra(fornecedor: str):
    """Remove regra de custo para fornecedor."""
    key = fornecedor.strip().upper()
    if key in _regras_cache:
        del _regras_cache[key]


def calcular_custo_item(item_vars: Dict[str, float], fornecedor: str) -> tuple[float, Optional[str]]:
    """Calcula custo de um item usando regra do fornecedor se existir.
    
    Returns:
        (custo_calculado, nome_regra_aplicada ou None)
    """
    regra = obter_regra(fornecedor)
    if regra and regra.ativo:
        try:
            custo = regra.calcular_custo(item_vars)
            return (custo, regra.fornecedor)
        except Exception as e:
            # Fallback para cálculo padrão se regra falhar
            pass
    
    # Cálculo padrão: vUnCom + rateios + impostos agregados
    custo_default = (
        item_vars.get('vUnCom', 0.0) +
        (item_vars.get('rateio_frete', 0.0) / item_vars.get('quantidade', 1.0)) +
        (item_vars.get('rateio_seguro', 0.0) / item_vars.get('quantidade', 1.0)) +
        (item_vars.get('rateio_outros', 0.0) / item_vars.get('quantidade', 1.0)) -
        (item_vars.get('rateio_desconto', 0.0) / item_vars.get('quantidade', 1.0)) +
        (item_vars.get('ipi_total', 0.0) / item_vars.get('quantidade', 1.0)) +
        (item_vars.get('st_total', 0.0) / item_vars.get('quantidade', 1.0))
    )
    return (custo_default, None)
