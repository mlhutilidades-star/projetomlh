# modules/pdf_payables_integration.py
import logging
from typing import Dict, List
from modules.pdf_processor import PDFBoletoProcessor
from integrations.tiny_erp.payables import TinyERPPayables
from integrations.tiny_erp.auth import TinyERPAuth

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PDFPayablesIntegration:
    """
    Integra processamento de PDF com criação automática de contas a pagar.
    Extrai dados de boletos PDF e pré-preenche contas a pagar no Tiny ERP.
    """
    
    def __init__(self, tiny_auth: TinyERPAuth = None):
        """
        Inicializa integrador de PDF com Contas a Pagar.
        
        Args:
            tiny_auth: Cliente de autenticação do Tiny ERP
        """
        self.pdf_processor = PDFBoletoProcessor()
        self.tiny_auth = tiny_auth or TinyERPAuth()
        self.payables_manager = TinyERPPayables(self.tiny_auth)

    def extract_and_prefill(self, pdf_path: str) -> Dict:
        """
        Extrai dados de um boleto PDF e cria conta a pagar pré-preenchida.
        
        Args:
            pdf_path: Caminho do arquivo PDF do boleto
            
        Returns:
            dict: Resultado da operação com dados extraídos e status
        """
        try:
            # Extrai dados do boleto
            boleto_data = self.pdf_processor.extract_boleto_data(pdf_path)
            
            if not boleto_data.get("dados_extraidos"):
                return {
                    "status": "erro",
                    "mensagem": "Não foi possível extrair dados do PDF",
                    "arquivo": pdf_path
                }
            
            # Monta dados para conta a pagar
            payable_data = self._map_boleto_to_payable(boleto_data)
            
            # Cria conta a pagar no Tiny ERP
            result = self.payables_manager.create_payable(payable_data)
            
            logging.info(f"Conta a pagar criada com sucesso a partir de {pdf_path}")
            
            return {
                "status": "sucesso",
                "arquivo": pdf_path,
                "dados_extraidos": boleto_data["dados_extraidos"],
                "payable_criada": result,
                "payable_data": payable_data
            }
        
        except Exception as e:
            logging.error(f"Erro ao processar boleto {pdf_path}: {e}")
            return {
                "status": "erro",
                "mensagem": str(e),
                "arquivo": pdf_path
            }

    def extract_and_prefill_batch(self, pdf_paths: List[str]) -> List[Dict]:
        """
        Processa múltiplos boletos PDFs e cria contas a pagar.
        
        Args:
            pdf_paths: Lista de caminhos de PDFs
            
        Returns:
            list: Lista com resultados de cada processamento
        """
        results = []
        
        for pdf_path in pdf_paths:
            logging.info(f"Processando boleto em lote: {pdf_path}")
            result = self.extract_and_prefill(pdf_path)
            results.append(result)
        
        # Resumo de processamento
        success_count = sum(1 for r in results if r.get("status") == "sucesso")
        error_count = len(results) - success_count
        
        logging.info(f"Processamento de lote concluído: {success_count} sucessos, {error_count} erros")
        
        return results

    def _map_boleto_to_payable(self, boleto_data: Dict) -> Dict:
        """
        Mapeia dados de boleto para formato de conta a pagar Tiny ERP.
        
        Args:
            boleto_data: Dados extraídos do boleto
            
        Returns:
            dict: Dados formatados para API Tiny ERP
        """
        extracted = boleto_data.get("dados_extraidos", {})
        
        payable_data = {
            "descricao": f"Boleto - {extracted.get('cedente', 'Cedente desconhecido')}",
            "valor": self._parse_valor(extracted.get("valor", "0")),
            "data_vencimento": self._parse_data_vencimento(extracted.get("vencimento", "")),
            "fornecedor_nome": extracted.get("cedente", ""),
            "numero_documento": self._extract_numero_boleto(extracted),
            "banco": extracted.get("banco", ""),
            "agencia": extracted.get("agencia", ""),
            "conta": extracted.get("conta", ""),
            "status": "A vencer"  # Padrão: contas criadas aguardam pagamento
        }
        
        return payable_data

    def _parse_valor(self, valor_str: str) -> float:
        """Extrai valor numérico de string."""
        try:
            # Tenta extrair valor usando o processador de PDF
            valor = self.pdf_processor.extract_value_from_text(f"R$ {valor_str}")
            return valor if valor else 0.0
        except:
            return 0.0

    def _parse_data_vencimento(self, data_str: str) -> str:
        """Converte string de data para formato DD/MM/YYYY."""
        try:
            import re
            # Tenta encontrar padrão DD/MM/YYYY
            match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', data_str)
            if match:
                return f"{match.group(1).zfill(2)}/{match.group(2).zfill(2)}/{match.group(3)}"
            return ""
        except:
            return ""

    def _extract_numero_boleto(self, extracted_data: Dict) -> str:
        """Extrai número do boleto dos dados extraídos."""
        # Prioridade: nosso número > conta > cedente número
        return (extracted_data.get("nosso_numero") or 
                extracted_data.get("conta") or 
                "").split()[-1] if extracted_data else ""


if __name__ == '__main__':
    try:
        # Inicializa integrador
        integrador = PDFPayablesIntegration()
        
        # Exemplo de uso (comentado para não gerar erro se PDF não existir)
        # resultado = integrador.extract_and_prefill("data/boleto_exemplo.pdf")
        # print("Resultado:")
        # print(resultado)
        
        print("PDFPayablesIntegration inicializado com sucesso")
    
    except Exception as e:
        print(f"Erro: {e}")
