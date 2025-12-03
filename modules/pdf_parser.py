"""PDF parsing with optional OCR fallback.

If Tesseract or Poppler (pdf2image) is not installed, we degrade gracefully
and attempt very lightweight extraction from raw bytes / filename so that the
Upload PDF page still works without crashing Streamlit.
"""

import re
import io
import logging

logger = logging.getLogger('pdf_parser')

_OCR_AVAILABLE = True
try:  # Try heavy deps
    import pytesseract  # type: ignore
    from pdf2image import convert_from_bytes  # type: ignore
    from PIL import Image  # type: ignore
    logger.info('OCR dependencies loaded successfully (pytesseract + pdf2image)')
except Exception as e:
    _OCR_AVAILABLE = False
    logger.warning(f'OCR dependencies not available: {e}. Using fallback.')

# Regex patterns (flexible for different formats)

CNJP_REGEX = re.compile(r"(\d{2})[\.\-\s]*(\d{3})[\.\-\s]*(\d{3})[\.\-\/\s]*(\d{4})[\.\-\s]*(\d{2})")
VALOR_REGEX = re.compile(r"R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2}))")
DATA_REGEX = re.compile(r"\b(\d{2}/\d{2}/\d{4})\b")
LINHA_REGEX = re.compile(r"\d{5}\.\d{5}\s+\d{5}\.\d{6}\s+\d{5}\.\d{6}\s+\d\s+\d{14}")

def _extract_text_ocr(pdf_bytes: bytes) -> str:
    """Full OCR path using pdf2image + pytesseract."""
    try:
        pages = convert_from_bytes(pdf_bytes, dpi=180)
        logger.debug(f'PDF converted to {len(pages)} page(s)')
        chunks = []
        for i, pg in enumerate(pages):
            try:
                txt = pytesseract.image_to_string(pg, lang='por')
            except Exception as e:
                logger.warning(f'Failed OCR with lang=por on page {i}: {e}, trying default')
                txt = pytesseract.image_to_string(pg)
            chunks.append(txt)
        result = "\n".join(chunks)
        logger.info(f'OCR extracted {len(result)} characters')
        return result
    except Exception as e:
        logger.error(f'OCR extraction failed: {e}', exc_info=True)
        raise


def _quick_guess_text(pdf_bytes: bytes) -> str:
    """Fallback: attempt to decode bytes as latin-1 and search numeric patterns."""
    try:
        raw = pdf_bytes.decode('latin-1', errors='ignore')
    except Exception:
        raw = ''
    return raw[:10000]  # limit size


def extract_from_pdf(pdf_bytes: bytes, filename: str = '') -> dict:
    """Public API used by page. Returns dict with extracted fields.

    If OCR dependencies are missing, returns minimal structure and attempts
    regex over raw content and filename.
    """
    logger.debug(f'Starting PDF extraction for file: {filename} ({len(pdf_bytes)} bytes)')
    dados = { 'cnpj': '', 'valor': '', 'vencimento': '', 'linha_digitavel': '' }

    if _OCR_AVAILABLE:
        try:
            joined = _extract_text_ocr(pdf_bytes)
            logger.debug('OCR extraction completed')
        except Exception as e:
            logger.warning(f'OCR failed, falling back to simple extraction: {e}')
            joined = _quick_guess_text(pdf_bytes)
    else:
        logger.debug('Using fallback extraction (no OCR)')
        joined = _quick_guess_text(pdf_bytes)

    # Try patterns in text
    cnpj_match = CNJP_REGEX.search(joined)
    if not cnpj_match and filename:
        logger.debug(f'CNPJ not found in text, searching filename: {filename}')
        cnpj_match = CNJP_REGEX.search(filename)
    if cnpj_match:
        dados['cnpj'] = cnpj_match.group(0)
        logger.info(f'CNPJ found: {dados["cnpj"]}')
    else:
        logger.debug('CNPJ not found in text or filename')

    valor_match = VALOR_REGEX.search(joined)
    if valor_match:
        dados['valor'] = valor_match.group(1).replace('.', '').replace(',', '.')
        logger.info(f'Valor found: {dados["valor"]}')

    data_match = DATA_REGEX.search(joined)
    if data_match:
        dados['vencimento'] = data_match.group(1)
        logger.info(f'Vencimento found: {dados["vencimento"]}')

    linha_match = LINHA_REGEX.search(joined)
    if linha_match:
        dados['linha_digitavel'] = linha_match.group(0)
        logger.info(f'Linha digitável found')

    # Add flag for UI (optional)
    dados['ocr_usado'] = _OCR_AVAILABLE
    logger.debug(f'Extraction complete: {dados}')
    return dados

def ocr_status() -> str:
    return "OCR completo ativo" if _OCR_AVAILABLE else "OCR indisponível (fallback simples)"
