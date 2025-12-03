"""
Utility functions for data export
"""
import pandas as pd
from io import BytesIO
from datetime import datetime
import logging

logger = logging.getLogger('export')

def export_to_excel(contas_list, regras_list=None):
    """Export contas and optionally regras to Excel with multiple sheets"""
    logger.info(f'Exporting {len(contas_list)} contas to Excel')
    
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Contas sheet
        if contas_list:
            df_contas = pd.DataFrame([{
                'ID': c.id,
                'Mês': c.mes,
                'Vencimento': c.vencimento.strftime('%d/%m/%Y') if c.vencimento else '',
                'Fornecedor': c.fornecedor,
                'CNPJ': c.cnpj or '',
                'Categoria': c.categoria or '',
                'Descrição': c.descricao or '',
                'Valor': c.valor,
                'Status': c.status,
                'Data Pagamento': c.data_pagamento.strftime('%d/%m/%Y') if c.data_pagamento else '',
                'Linha Digitável': c.linha_digitavel or '',
                'PDF URL': c.pdf_url or '',
                'Observações': c.observacoes or '',
                'Data Cadastro': c.data_cadastro.strftime('%d/%m/%Y %H:%M') if c.data_cadastro else ''
            } for c in contas_list])
            
            df_contas.to_excel(writer, sheet_name='Contas a Pagar', index=False)
            logger.info(f'Contas sheet created with {len(df_contas)} rows')
        
        # Regras sheet
        if regras_list:
            df_regras = pd.DataFrame([{
                'ID': r.id,
                'CNPJ': r.cnpj,
                'Fornecedor': r.fornecedor,
                'Categoria': r.categoria,
                'Contador Usos': r.contador_usos,
                'Ativo': 'Sim' if r.ativo else 'Não',
                'Última Atualização': r.ultima_atualizacao.strftime('%d/%m/%Y %H:%M') if r.ultima_atualizacao else ''
            } for r in regras_list])
            
            df_regras.to_excel(writer, sheet_name='Regras M11', index=False)
            logger.info(f'Regras sheet created with {len(df_regras)} rows')
    
    output.seek(0)
    return output

def export_to_csv(data_list, columns):
    """Export list to CSV"""
    logger.info(f'Exporting {len(data_list)} records to CSV')
    
    df = pd.DataFrame(data_list)
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    csv_buffer.seek(0)
    
    return csv_buffer

def get_export_filename(prefix='export'):
    """Generate timestamped filename"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{prefix}_{timestamp}"
