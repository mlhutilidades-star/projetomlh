"""Atualização de custos no Tiny a partir de NF-e (XML preferível).

Fluxo:
1) Ler arquivo de NF-e (XML preferível; PDF só se não houver XML)
2) Extrair itens e calcular custo unitário sugerido
3) Escrever custos_propostos.csv para revisão
4) Pausar para você revisar/editar custo_unit_final
5) Ler o CSV ajustado e enviar atualização para o Tiny (preco_custo)

Uso:
    python atualiza_custos_tiny_via_pdf.py caminho\nota.xml
    python atualiza_custos_tiny_via_pdf.py caminho\nota.pdf   # menos preciso

Flags:
    --dry-run    : não envia nada para o Tiny, só gera o CSV
    --quick      : acelera prints e limitações de volume quando múltiplas notas forem adicionadas no futuro

Observação importante:
- Para refletir o custo atual no Tiny de forma rápida, usamos produto.alterar.php (campo preco_custo).
- A "aba de custos" do Tiny (histórico) requer endpoints específicos para exclusão/inclusão de custos,
  que não estão cobertos nesta primeira versão. Se desejar, expandimos depois.
"""
from __future__ import annotations
import sys, os, csv, time
from typing import List, Dict

from modules.nfe_parser import parse_nfe_xml, to_rows
from modules.pdf_parser import extract_from_pdf
from modules.tiny_api import atualizar_preco_custo
from modules.database import get_regra_custo, add_or_update_regra_custo, init_database
from modules.regras_custo import calcular_custo_item, adicionar_regra as cache_regra


def write_csv(path: str, rows: List[Dict]):
    if not rows:
        return
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def read_csv(path: str) -> List[Dict]:
    with open(path, 'r', newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        return [dict(row) for row in r]


def parse_invoice(file_path: str) -> tuple[List[Dict], str]:
    """Parse invoice and return (rows, supplier_name)"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.xml':
        nfe = parse_nfe_xml(file_path)
        rows = to_rows(nfe)
        return (rows, nfe.emitente)
    elif ext == '.pdf':
        # Atenção: PDF é muito menos preciso para itens. Aqui, apenas tentamos extrair
        # texto básico e gerar uma linha placeholder para orientar o processo manual.
        with open(file_path, 'rb') as f:
            data = f.read()
        meta = extract_from_pdf(data, os.path.basename(file_path))
        # Sem XML, não temos itens. Cria planilha modelo para preenchimento manual.
        return ([{
            'codigo': '', 'descricao': '', 'ncm': '', 'cfop': '', 'quantidade': 0,
            'vUnCom': 0.0, 'vProd': 0.0, 'ipi_total': 0.0, 'st_total': 0.0,
            'icms_total': 0.0, 'pis_total': 0.0, 'cofins_total': 0.0,
            'rateio_frete': 0.0, 'rateio_seguro': 0.0, 'rateio_outros': 0.0,
            'rateio_desconto': 0.0, 'custo_unit_sugerido': 0.0, 'custo_unit_final': 0.0
        }], 'FORNECEDOR_DESCONHECIDO')
    else:
        raise ValueError('Formato não suportado. Use XML (preferível) ou PDF.')


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    file_path = sys.argv[1]
    dry = '--dry-run' in sys.argv

    if not os.path.exists(file_path):
        print(f"Arquivo não encontrado: {file_path}")
        sys.exit(2)

    # Inicializar DB e carregar regras
    init_database()
    
    print(f"Lendo nota: {file_path}")
    rows, fornecedor = parse_invoice(file_path)
    if not rows:
        print('Nenhum item encontrado. (Para PDF, prefira usar o XML da NF-e)')
        sys.exit(0)

    # Verificar se existe regra cadastrada para o fornecedor
    regra_db = get_regra_custo(fornecedor)
    if regra_db and regra_db['ativo']:
        print(f"\n✅ Regra de custo encontrada para fornecedor: {fornecedor}")
        print(f"   Fórmula: {regra_db['formula']}")
        print(f"   Aplicando automaticamente...\n")
        # Carregar regra no cache para uso
        cache_regra(fornecedor, regra_db['formula'], True)
        # Aplicar regra a cada item
        for r in rows:
            item_vars = {
                'vUnCom': r.get('vUnCom', 0.0),
                'quantidade': r.get('quantidade', 1.0),
                'vProd': r.get('vProd', 0.0),
                'ipi_total': r.get('ipi_total', 0.0),
                'st_total': r.get('st_total', 0.0),
                'icms_total': r.get('icms_total', 0.0),
                'pis_total': r.get('pis_total', 0.0),
                'cofins_total': r.get('cofins_total', 0.0),
                'rateio_frete': r.get('rateio_frete', 0.0),
                'rateio_seguro': r.get('rateio_seguro', 0.0),
                'rateio_outros': r.get('rateio_outros', 0.0),
                'rateio_desconto': r.get('rateio_desconto', 0.0),
            }
            custo_calc, _ = calcular_custo_item(item_vars, fornecedor)
            r['custo_unit_sugerido'] = custo_calc
            r['custo_unit_final'] = custo_calc
    else:
        print(f"\n⚠️  Nenhuma regra de custo cadastrada para: {fornecedor}")
        print("   Usando cálculo padrão. Você pode criar uma regra customizada após revisar.")

    out_csv = 'custos_propostos.csv'
    write_csv(out_csv, rows)
    print(f"\nPlanilha gerada para revisão: {out_csv}")
    print("Edite a coluna 'custo_unit_final' conforme sua formação de preço.")
    
    # Oferecer criação de regra se não existir
    if not regra_db or not regra_db['ativo']:
        criar = input(f"\nDeseja criar uma regra de custo para '{fornecedor}'? (s/N): ").strip().lower()
        if criar == 's':
            print("\nVariáveis disponíveis na fórmula:")
            print("  vUnCom, quantidade, vProd, ipi_total, ipi_aliq, st_total,")
            print("  icms_total, pis_total, cofins_total, rateio_frete,")
            print("  rateio_seguro, rateio_outros, rateio_desconto")
            print("\nExemplo: (vUnCom / 7) + (ipi_aliq * 0.7)")
            formula = input("Digite a fórmula: ").strip()
            if formula:
                add_or_update_regra_custo(fornecedor, formula, ativo=True, observacoes=f"Criada via CLI em {file_path}")
                print(f"✅ Regra salva para '{fornecedor}'. Próximas notas deste fornecedor aplicarão automaticamente.")
                # Recalcular com a nova regra
                cache_regra(fornecedor, formula, True)
                for r in rows:
                    item_vars = {
                        'vUnCom': r.get('vUnCom', 0.0),
                        'quantidade': r.get('quantidade', 1.0),
                        'vProd': r.get('vProd', 0.0),
                        'ipi_total': r.get('ipi_total', 0.0),
                        'st_total': r.get('st_total', 0.0),
                        'icms_total': r.get('icms_total', 0.0),
                        'pis_total': r.get('pis_total', 0.0),
                        'cofins_total': r.get('cofins_total', 0.0),
                        'rateio_frete': r.get('rateio_frete', 0.0),
                        'rateio_seguro': r.get('rateio_seguro', 0.0),
                        'rateio_outros': r.get('rateio_outros', 0.0),
                        'rateio_desconto': r.get('rateio_desconto', 0.0),
                    }
                    custo_calc, _ = calcular_custo_item(item_vars, fornecedor)
                    r['custo_unit_sugerido'] = custo_calc
                    r['custo_unit_final'] = custo_calc
                write_csv(out_csv, rows)
                print(f"Planilha atualizada com nova regra: {out_csv}")
    
    input("\nPressione Enter após revisar e salvar o CSV...")

    # Recarregar planilha com ajustes
    rows2 = read_csv(out_csv)

    # Validação básica
    for r in rows2:
        try:
            r['custo_unit_final'] = float(str(r.get('custo_unit_final', '0')).replace(',', '.'))
        except Exception:
            r['custo_unit_final'] = 0.0

    if dry:
        print("--dry-run: não enviaremos nada para o Tiny. Exemplo dos primeiros itens:")
        for r in rows2[:10]:
            print(r['codigo'], r['descricao'][:50], '=>', r['custo_unit_final'])
        sys.exit(0)

    print("\nEnviando atualização de custo para o Tiny (preco_custo):")
    ok = 0
    fail = 0
    for r in rows2:
        codigo = (r.get('codigo') or '').strip()
        custo = float(r.get('custo_unit_final') or 0.0)
        if not codigo or custo <= 0:
            print(f"  Ignorando item sem código/custo válido: {codigo} -> {custo}")
            continue
        resp = atualizar_preco_custo(codigo, custo)
        if isinstance(resp, dict) and resp.get('error'):
            print(f"  ERRO ao atualizar {codigo}: {resp['error']}")
            fail += 1
        else:
            print(f"  OK  {codigo}: custo atualizado para {custo:.2f}")
            ok += 1
        time.sleep(0.2)  # rate limit simples
    print(f"\nConcluído. Sucesso: {ok}, Erros: {fail}")

if __name__ == '__main__':
    main()
