import pytesseract
from pdf2image import convert_from_path
from typing import List

def extrair_dados_boleto(caminho_pdf: str) -> List[str]:
    """
    Extrai dados de um boleto a partir de um arquivo PDF.

    :param caminho_pdf: Caminho para o arquivo PDF do boleto.
    :return: Lista de strings com os dados extraídos.
    """
    imagens = convert_from_path(caminho_pdf)
    dados_extraidos = []

    for imagem in imagens:
        texto = pytesseract.image_to_string(imagem)
        dados_extraidos.append(texto)

    return dados_extraidos
