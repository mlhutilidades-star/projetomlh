# modules/pdf_processor.py
import logging
import pdfplumber
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PDFBoletoProcessor:
    """
    Processador de boletos em PDF para extrair dados financeiros.
    Extrai informações como banco, agência, conta, valor, vencimento, etc.
    """
    
    # Padrões de busca comuns em boletos
    KEYWORDS = {
        "valor": ["valor", "montante", "total", "valor cobrado"],
        "vencimento": ["vencimento", "data de vencimento", "data venc"],
        "banco": ["banco", "código do banco"],
        "agencia": ["agência", "agencia"],
        "conta": ["conta", "nosso número"],
        "cedente": ["cedente", "beneficiário"],
        "sacado": ["sacado", "pagador"]
    }
    
    def __init__(self):
        """Inicializa o processador de boletos."""
        pass

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extrai texto de um arquivo PDF de boleto.
        
        Args:
            pdf_path: Caminho do arquivo PDF
            
        Returns:
            str: Texto extraído do PDF
        """
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            
            logging.info(f"Texto extraído do PDF: {pdf_path}")
            return text
        except FileNotFoundError:
            logging.error(f"Arquivo PDF não encontrado: {pdf_path}")
            return ""
        except Exception as e:
            logging.error(f"Erro ao extrair texto do PDF: {e}")
            return ""

    def extract_boleto_data(self, pdf_path: str) -> Dict:
        """
        Extrai dados de um boleto PDF.
        
        Args:
            pdf_path: Caminho do arquivo PDF do boleto
            
        Returns:
            dict: Dicionário com dados extraídos
        """
        try:
            text = self.extract_text_from_pdf(pdf_path)
            
            if not text:
                return {}
            
            # Inicializa dicionário de resultado
            boleto_data = {
                "arquivo": pdf_path,
                "status": "processado",
                "dados_extraidos": {}
            }
            
            # Busca por padrões no texto
            lines = text.lower().split('\n')
            
            for key, keywords in self.KEYWORDS.items():
                for keyword in keywords:
                    for line in lines:
                        if keyword in line:
                            boleto_data["dados_extraidos"][key] = line.strip()
                            break
            
            logging.info(f"Dados de boleto extraídos: {len(boleto_data['dados_extraidos'])} campos")
            return boleto_data
        
        except Exception as e:
            logging.error(f"Erro ao extrair dados de boleto: {e}")
            return {"status": "erro", "mensagem": str(e)}

    def extract_value_from_text(self, text: str) -> Optional[float]:
        """
        Tenta extrair valor monetário de um texto.
        
        Args:
            text: Texto contendo valor
            
        Returns:
            float: Valor extraído ou None
        """
        try:
            # Remove caracteres não numéricos exceto ponto e vírgula
            import re
            
            # Procura por padrões de valor (R$ 1.250,00 ou R$ 1250.00)
            pattern = r'R\$\s*([\d.,]+)'
            match = re.search(pattern, text)
            
            if match:
                valor_str = match.group(1)
                # Detecta formato: se tem ponto antes da vírgula, é europeu (1.250,00)
                # se tem vírgula antes do ponto, é americano (1,250.00)
                if ',' in valor_str and '.' in valor_str:
                    # Formato europeu: 1.250,00 -> remove ponto e troca vírgula por ponto
                    if valor_str.rfind(',') > valor_str.rfind('.'):
                        valor_str = valor_str.replace('.', '').replace(',', '.')
                    else:
                        # Formato americano: mantém como está
                        valor_str = valor_str.replace(',', '')
                elif ',' in valor_str:
                    # Apenas vírgula: pode ser decimal (1,50) ou milhar europeu
                    valor_str = valor_str.replace(',', '.')
                
                return float(valor_str)
            
            return None
        except Exception as e:
            logging.error(f"Erro ao extrair valor: {e}")
            return None

    def process_multiple_boletos(self, pdf_paths: List[str]) -> List[Dict]:
        """
        Processa múltiplos boletos PDF.
        
        Args:
            pdf_paths: Lista de caminhos de PDFs
            
        Returns:
            list: Lista de dicionários com dados extraídos
        """
        results = []
        
        for pdf_path in pdf_paths:
            logging.info(f"Processando boleto: {pdf_path}")
            result = self.extract_boleto_data(pdf_path)
            results.append(result)
        
        logging.info(f"Processamento de {len(pdf_paths)} boletos concluído")
        return results


if __name__ == '__main__':
    try:
        processor = PDFBoletoProcessor()
        
        # Exemplo de uso (comentado para não gerar erro se PDF não existir)
        # pdf_path = "data/boleto_exemplo.pdf"
        # dados = processor.extract_boleto_data(pdf_path)
        # print("Dados extraídos:")
        # print(dados)
        
        print("PDFBoletoProcessor inicializado com sucesso")
    
    except Exception as e:
        print(f"Erro: {e}")
