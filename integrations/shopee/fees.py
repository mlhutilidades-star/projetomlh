# integrations/shopee/fees.py
import logging
from decimal import Decimal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ShopeeFees:
    """
    Calcula taxas e comissões da Shopee baseado em valores e tipos de transação.
    """
    
    # Taxa padrão de comissão Shopee (em porcentagem)
    DEFAULT_COMMISSION_RATE = Decimal('5.0')  # 5%
    
    # Taxa de processamento de pagamento (em porcentagem)
    PAYMENT_PROCESSING_RATE = Decimal('2.0')  # 2%
    
    # Taxa de logística (pode variar)
    DEFAULT_LOGISTICS_RATE = Decimal('0.0')  # Deve ser definido por tipo de envio
    
    def __init__(self):
        """Inicializa o calculador de taxas."""
        self.commission_rate = self.DEFAULT_COMMISSION_RATE
        self.payment_processing_rate = self.PAYMENT_PROCESSING_RATE

    def calculate_commission(self, order_amount: float, category: str = "general") -> dict:
        """
        Calcula comissão baseada no valor do pedido e categoria.
        
        Args:
            order_amount: Valor bruto do pedido
            category: Categoria do produto (general, fashion, electronics, etc.)
            
        Returns:
            dict: Dicionário com comissão calculada e taxa aplicada
        """
        try:
            amount = Decimal(str(order_amount))
            
            # Ajusta taxa por categoria (exemplo)
            category_multiplier = self._get_category_multiplier(category)
            commission_rate = self.commission_rate * category_multiplier
            
            commission = amount * (commission_rate / 100)
            
            logging.info(f"Comissão calculada: R$ {commission:.2f} ({commission_rate}% sobre R$ {amount:.2f})")
            
            return {
                "order_amount": float(amount),
                "commission_rate": float(commission_rate),
                "commission_value": float(commission)
            }
        except Exception as e:
            logging.error(f"Erro ao calcular comissão: {e}")
            return {}

    def calculate_payment_processing_fee(self, order_amount: float, payment_method: str = "card") -> dict:
        """
        Calcula taxa de processamento de pagamento.
        
        Args:
            order_amount: Valor bruto do pedido
            payment_method: Método de pagamento (card, wallet, transfer, etc.)
            
        Returns:
            dict: Dicionário com taxa calculada
        """
        try:
            amount = Decimal(str(order_amount))
            
            # Ajusta taxa por método de pagamento
            processing_rate = self._get_payment_processing_rate(payment_method)
            
            processing_fee = amount * (processing_rate / 100)
            
            logging.info(f"Taxa de processamento: R$ {processing_fee:.2f} ({processing_rate}% sobre R$ {amount:.2f})")
            
            return {
                "order_amount": float(amount),
                "payment_method": payment_method,
                "processing_rate": float(processing_rate),
                "processing_fee": float(processing_fee)
            }
        except Exception as e:
            logging.error(f"Erro ao calcular taxa de processamento: {e}")
            return {}

    def calculate_total_fees(self, order_amount: float, category: str = "general", payment_method: str = "card") -> dict:
        """
        Calcula total de todas as taxas e retorna dados consolidados.
        
        Args:
            order_amount: Valor bruto do pedido
            category: Categoria do produto
            payment_method: Método de pagamento
            
        Returns:
            dict: Dicionário com todas as taxas e valor líquido
        """
        try:
            commission_data = self.calculate_commission(order_amount, category)
            processing_data = self.calculate_payment_processing_fee(order_amount, payment_method)
            
            if not commission_data or not processing_data:
                return {}
            
            total_fees = commission_data["commission_value"] + processing_data["processing_fee"]
            net_amount = order_amount - total_fees
            
            result = {
                "gross_amount": order_amount,
                "commission": commission_data,
                "payment_processing": processing_data,
                "total_fees": total_fees,
                "net_amount": net_amount,
                "fee_percentage": (total_fees / order_amount * 100) if order_amount > 0 else 0
            }
            
            logging.info(f"Taxas totais: R$ {total_fees:.2f} | Valor líquido: R$ {net_amount:.2f}")
            
            return result
        except Exception as e:
            logging.error(f"Erro ao calcular taxas totais: {e}")
            return {}

    def _get_category_multiplier(self, category: str) -> Decimal:
        """Retorna multiplicador de taxa por categoria."""
        multipliers = {
            "fashion": Decimal('1.1'),  # 5.5%
            "electronics": Decimal('1.2'),  # 6%
            "home": Decimal('1.0'),  # 5%
            "general": Decimal('1.0')  # 5%
        }
        return multipliers.get(category.lower(), Decimal('1.0'))

    def _get_payment_processing_rate(self, payment_method: str) -> Decimal:
        """Retorna taxa de processamento por método de pagamento."""
        rates = {
            "card": Decimal('2.0'),  # 2%
            "wallet": Decimal('1.5'),  # 1.5%
            "transfer": Decimal('1.0'),  # 1%
            "voucher": Decimal('1.0')  # 1%
        }
        return rates.get(payment_method.lower(), Decimal('2.0'))


if __name__ == '__main__':
    try:
        fees_calculator = ShopeeFees()
        
        # Exemplo de cálculo
        order_value = 100.00
        fees_result = fees_calculator.calculate_total_fees(order_value, category="electronics", payment_method="card")
        
        print("\n--- Exemplo de Cálculo de Taxas ---")
        print(f"Valor do pedido: R$ {fees_result['gross_amount']:.2f}")
        print(f"Comissão: R$ {fees_result['commission']['commission_value']:.2f}")
        print(f"Taxa de processamento: R$ {fees_result['payment_processing']['processing_fee']:.2f}")
        print(f"Total de taxas: R$ {fees_result['total_fees']:.2f}")
        print(f"Valor líquido: R$ {fees_result['net_amount']:.2f}")
        
    except Exception as e:
        print(f"Erro: {e}")
