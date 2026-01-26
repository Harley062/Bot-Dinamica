from tools import click_on_image, houver_on_image, apagar_xml_downloads, click_on_all_images
import time
import pyautogui
import pandas as pd
from typing import Optional, Dict
import os
from datetime import datetime,timedelta
import xml.etree.ElementTree as ET
import glob

# Import do analisador de produtos com IA
from pipeline.analisador_produto import AnalisadorProduto, AcaoRequerida
from config import DOWNLOADS_PATH

read_path = os.path.join(DOWNLOADS_PATH, 'gd_ItensXML.xls')
xml_download_path = DOWNLOADS_PATH



# Instância global do analisador (reutilizada para performance)
_analisador_produto: Optional[AnalisadorProduto] = None


def extrair_tipo_frete_xml() -> str:
    """
    Extrai o tipo de frete do XML da NF-e baixado.

    Mapeia o valor de <modFrete> para o código usado no sistema:
    - 0 (CIF): Frete por conta do Remetente/Emitente = 'CIF'
    - 1 (FOB): Frete por conta do Destinatário/Remetente = 'FOB'
    - 2 (Por conta de terceiros): 'RED' (ou outro código conforme sistema)
    - 9 (Sem frete): 'RED' (padrão)

    Returns:
        str: Código do tipo de frete ('CIF', 'FOB' ou 'RED')
    """
    try:
        # Busca o arquivo XML mais recente na pasta de downloads
        xml_files = glob.glob(os.path.join(xml_download_path, '*.xml'))

        if not xml_files:
            print("Nenhum arquivo XML encontrado. Usando CIF como padrão.")
            return 'CIF'

        # Pega o arquivo XML mais recente
        xml_mais_recente = max(xml_files, key=os.path.getctime)
        print(f"Lendo XML: {os.path.basename(xml_mais_recente)}")

        # Parse do XML
        tree = ET.parse(xml_mais_recente)
        root = tree.getroot()

        # Namespace da NF-e (necessário para buscar elementos)
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

        # Busca o elemento modFrete
        mod_frete_elem = root.find('.//nfe:transp/nfe:modFrete', ns)

        if mod_frete_elem is None:
            # Tenta sem namespace (alguns XMLs podem não ter)
            mod_frete_elem = root.find('.//transp/modFrete')

        if mod_frete_elem is not None:
            mod_frete = mod_frete_elem.text.strip()
            print(f"modFrete encontrado no XML: {mod_frete}")

            # Mapeamento conforme documentação da NF-e
            mapeamento = {
                '0': 'CIF',  # Emitente
                '1': 'FOB',  # Destinatário
                '2': 'RED',  # Terceiros (Redespacho)
                '3': 'RED',  # Próprio por conta do Remetente
                '4': 'RED',  # Próprio por conta do Destinatário
                '9': 'RED'   # Sem frete
            }

            tipo_frete = mapeamento.get(mod_frete, 'CIF')
            print(f"Tipo de frete mapeado: {tipo_frete}")
            return tipo_frete
        else:
            print("Campo modFrete não encontrado no XML. Usando CIF como padrão.")
            return 'CIF'

    except Exception as e:
        print(f"Erro ao extrair tipo de frete do XML: {e}")
        print("Usando CIF como padrão.")
        return 'CIF'


def extrair_vencimentos_xml() -> list:
    """
    Extrai as datas de vencimento das duplicatas do XML da NF-e.

    Retorna uma lista de dicionários contendo informações de cada duplicata:
    - numero: Número da duplicata
    - vencimento: Data de vencimento (formato YYYY-MM-DD)
    - valor: Valor da duplicata

    Returns:
        list: Lista de dicionários com dados das duplicatas
    """
    try:
        xml_files = glob.glob(os.path.join(xml_download_path, '*.xml'))

        if not xml_files:
            print("Nenhum arquivo XML encontrado para extrair vencimentos.")
            return []

        xml_mais_recente = max(xml_files, key=os.path.getctime)
        print(f"Lendo XML para vencimentos: {os.path.basename(xml_mais_recente)}")

        tree = ET.parse(xml_mais_recente)
        root = tree.getroot()

        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

        duplicatas = root.findall('.//nfe:cobr/nfe:dup', ns)

        if not duplicatas:
            duplicatas = root.findall('.//cobr/dup')

        vencimentos = []
        for dup in duplicatas:
            # Tenta com namespace primeiro
            n_dup = dup.find('nfe:nDup', ns)
            d_venc = dup.find('nfe:dVenc', ns)
            v_dup = dup.find('nfe:vDup', ns)

            # Se não encontrar, tenta sem namespace
            if n_dup is None:
                n_dup = dup.find('nDup')
            if d_venc is None:
                d_venc = dup.find('dVenc')
            if v_dup is None:
                v_dup = dup.find('vDup')

            vencimento_info = {
                'numero': n_dup.text.strip() if n_dup is not None else None,
                'vencimento': d_venc.text.strip() if d_venc is not None else None,
                'valor': float(v_dup.text.strip()) if v_dup is not None else None
            }
            vencimentos.append(vencimento_info)

        print(f"Vencimentos encontrados: {len(vencimentos)}")
        for v in vencimentos:
            print(f"  Parcela {v['numero']}: {v['vencimento']} - R$ {v['valor']:.2f}" if v['valor'] else f"  Parcela {v['numero']}: {v['vencimento']}")

        return vencimentos

    except Exception as e:
        print(f"Erro ao extrair vencimentos do XML: {e}")
        return []


def extrair_parcelas_xml() -> str:
    """
    Extrai a quantidade de parcelas do XML da NF-e e retorna o código de condição de pagamento.

    A quantidade de parcelas é determinada pelo número de elementos <dup> (duplicatas)
    dentro do elemento <cobr> (cobrança) do XML.

    Mapeamento:
    - 1 parcela = '30D'
    - 2 parcelas = '30/60'
    - 3 parcelas = '30/60/90'
    - 4 parcelas = '30/60/90/120'
    - etc.

    Returns:
        str: Código da condição de pagamento
    """
    try:
        # Busca o arquivo XML mais recente na pasta de downloads
        xml_files = glob.glob(os.path.join(xml_download_path, '*.xml'))

        if not xml_files:
            print("Nenhum arquivo XML encontrado. Usando 30D como padrão.")
            return '30D'

        # Pega o arquivo XML mais recente
        xml_mais_recente = max(xml_files, key=os.path.getctime)
        print(f"Lendo XML para parcelas: {os.path.basename(xml_mais_recente)}")

        # Parse do XML
        tree = ET.parse(xml_mais_recente)
        root = tree.getroot()

        # Namespace da NF-e
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

        # Busca todos os elementos <dup> (duplicatas) dentro de <cobr>
        duplicatas = root.findall('.//nfe:cobr/nfe:dup', ns)

        if not duplicatas:
            # Tenta sem namespace
            duplicatas = root.findall('.//cobr/dup')

        quantidade_parcelas = len(duplicatas)
        print(f"Quantidade de parcelas encontradas: {quantidade_parcelas}")

        if quantidade_parcelas == 0:
            print("Nenhuma duplicata encontrada. Usando 30D como padrão.")
            return '30D'

        # Monta o código de condição de pagamento
        if quantidade_parcelas == 1:
            condicao = '30D'
        else:
            # Gera sequência: 30/60/90/120...
            dias = [str(30 * i) for i in range(1, quantidade_parcelas + 1)]
            condicao = '/'.join(dias)

        print(f"Condição de pagamento: {condicao}")
        return condicao

    except Exception as e:
        print(f"Erro ao extrair parcelas do XML: {e}")
        print("Usando 30D como padrão.")
        return '30D'


def get_analisador() -> AnalisadorProduto:
    """Obtém instância do analisador de produtos (singleton)."""
    global _analisador_produto
    if _analisador_produto is None:
        _analisador_produto = AnalisadorProduto()
    return _analisador_produto


def analisar_e_obter_id_produto(descricao_item: str, auto_cadastrar: bool = True) -> Dict:
    """
    Analisa a descrição do item usando IA e retorna o código do produto.
    
    A IA irá:
    1. Buscar na base de produtos existentes
    2. Se encontrar match confiável: retorna código do produto existente
    3. Se não encontrar: cadastra novo produto e retorna o novo código
    4. Classifica automaticamente o grupo e unidade mais adequados para o produto
    
    Args:
        descricao_item: Descrição do item da nota fiscal
        auto_cadastrar: Se True, cadastra automaticamente quando produto não existe
        
    Returns:
        Dict com:
            - 'produto_codigo': Código do produto (cadastrado ou encontrado)
            - 'acao': 'apenas_vinculo' ou 'cadastro_e_vinculo'
            - 'produto_novo': True se foi cadastrado agora
            - 'confianca': 'ALTA', 'MEDIA' ou 'BAIXA'
            - 'similaridade': Score de similaridade (0-100)
            - 'descricao_match': Descrição do produto encontrado/cadastrado
            - 'justificativa': Explicação da decisão da IA
            - 'grupo_classificado': Grupo sugerido pela IA (quando cadastro)
            - 'dados_cadastro': Dados completos para cadastro
            - 'erro': Mensagem de erro se houver
    """
    analisador = get_analisador()
    
    # Realiza análise com IA
    resultado = analisador.analisar(
        descricao_produto=descricao_item,
        auto_cadastrar=auto_cadastrar,
        debug=True
    )
    
    # Monta resposta estruturada
    resposta = {
        'produto_codigo': None,
        'acao': resultado.acao.value,
        'produto_novo': resultado.cadastro_realizado,
        'confianca': resultado.confianca,
        'similaridade': resultado.similaridade,
        'descricao_match': None,
        'justificativa': resultado.justificativa,
        'grupo_classificado': None,
        'dados_cadastro': resultado.dados_cadastro,
        'erro': resultado.erro
    }
    
    # Extrai código do produto
    if resultado.produto_match:
        # Tenta diferentes campos possíveis para o código
        resposta['produto_codigo'] = (
            resultado.produto_match.get('codigo') or 
            resultado.produto_match.get('PRO_ST_CODREAL') or
            resultado.produto_match.get('alternativo')
        )
        resposta['descricao_match'] = (
            resultado.produto_match.get('descricao') or 
            resultado.produto_match.get('PRO_ST_DESCRICAO') or
            resultado.produto_match.get('DESCRICAO')
        )
    
    # Extrai informações do grupo classificado
    if resultado.dados_cadastro and resultado.dados_cadastro.get('grupo'):
        resposta['grupo_classificado'] = resultado.dados_cadastro['grupo']
    
    return resposta


def exportar_xml():
    primeiro_loop = True
    
    while True:
    
        apagar_xml_downloads()
        if os.path.exists(read_path):
            os.remove(read_path)
            
        time.sleep(5)
        if primeiro_loop:
            click_on_image('exportar_xml/EpuPRI53T2.png', confidence=0.7, timeout=20)
            
            time.sleep(5)
            
            click_on_image('exportar_xml/todos_os_modulos.png', confidence=0.7, timeout=20)
            
            time.sleep(5)
            
            click_on_image('exportar_xml/fiscal.png', confidence=0.7, timeout=20)
            
            time.sleep(20)
            
            click_on_image('exportar_xml/fechar.png', confidence=0.7, timeout=30)
            
            time.sleep(5)
            
            click_on_image('exportar_xml/KgFh1LwTzB.png', confidence=0.7, timeout=30, continue_after_fail=True)
            time.sleep(2)
            click_on_image('exportar_xml/KgFh1LwTzB.png', confidence=0.7, timeout=30, continue_after_fail=True)
        
            time.sleep(5)
        
            click_on_image('exportar_xml/gerenciador_de_nf.png', confidence=0.7, timeout=20)
        
            time.sleep(5)
        
            click_on_image('exportar_xml/calendario.png', confidence=0.7, timeout=20)
        
            time.sleep(2)
        
            click_on_image('exportar_xml/limpar.png', confidence=0.7, timeout=20)
        
            time.sleep(2)
        
            pyautogui.write((datetime.now() - timedelta(days=365)).strftime('%d%m%Y'))

            time.sleep(2)
            pyautogui.press('tab')
            time.sleep(2)
            pyautogui.write((datetime.now() - timedelta(days=1)).strftime('%d%m%Y'))
        
            click_on_image('exportar_xml/status_xml.png', confidence=0.7, timeout=20)
        
            time.sleep(2)
        
            pyautogui.press('down', presses=2, interval=1)
        
            time.sleep(2)
        
            click_on_image('exportar_xml/aberto.png', confidence=0.7, timeout=20)
        
            time.sleep(2)
        
            click_on_image('exportar_xml/filtrar.png', confidence=0.7, timeout=20)
        
            time.sleep(10)
            
            click_on_image('exportar_xml/status_aberto.png', confidence=0.7, timeout=20)
            
            pyautogui.press('right', presses=30, interval=0.2)
            
            time.sleep(2)
            
            houver_on_image('exportar_xml/data_venc.png', confidence=0.7, timeout=20)
            
            time.sleep(2)
            
            click_on_image('exportar_xml/filtro.png', confidence=0.7, timeout=20)
            
            time.sleep(2)
            
            click_on_image('exportar_xml/nao_vazio.png', confidence=0.7, timeout=20)
            
            time.sleep(2)
            
            click_on_image('exportar_xml/data_venc.png', confidence=0.7, timeout=20)
            
            time.sleep(2)
            
            pyautogui.press('left', presses=30, interval=0.2)
    
            primeiro_loop = False
        
        click_on_image('exportar_xml/status_aberto.png', click_type='double', confidence=0.7, timeout=20)
        
        time.sleep(2)
        
        click_on_image('exportar_xml/outros.png', confidence=0.7, timeout=20)
        
        time.sleep(2)
        
        houver_on_image('exportar_xml/exportar.png', confidence=0.7, timeout=20)
        
        time.sleep(2)
        
        pyautogui.press('down', presses=3, interval=1)
        
        time.sleep(1)
        
        pyautogui.press('enter')
        
        time.sleep(2)
        
        click_on_image('exportar_xml/webfile.png', confidence=0.7, timeout=20)
        
        time.sleep(2)
        
        pyautogui.press('enter')
        
        time.sleep(2)
        
        click_on_image('exportar_xml/ok.png', confidence=0.7, timeout=20, continue_after_fail=True)
        
        time.sleep(5)
        
        houver_on_image('exportar_xml/lYW5IFXKAw.png', confidence=0.7, timeout=20)
        
        time.sleep(10)
        click_on_image('exportar_xml/fechar2.png', confidence=0.7, timeout=30)
        
        time.sleep(2)
        
        click_on_image('exportar_xml/receber.png', confidence=0.7, timeout=20)
        
        time.sleep(2)
        
        pyautogui.press('down', presses=2, interval=1)
        
        pyautogui.press('enter')
        
        time.sleep(15)
        
        pyautogui.write('864')
        
        time.sleep(2)
        
        pyautogui.press('tab')
        
        time.sleep(2)
        
        pyautogui.write('NFS')
        
        pyautogui.press('tab', presses=3, interval=1)

        # Extrai o tipo de frete do XML e usa no sistema
        tipo_frete = extrair_tipo_frete_xml()

        pyautogui.write(tipo_frete)

        pyautogui.press('tab')

        condicao_pagamento = extrair_parcelas_xml()
        pyautogui.write(condicao_pagamento)

        
        time.sleep(2)
        
        click_on_image('exportar_xml/vincular_itens.png', confidence=0.7, timeout=20)

        time.sleep(2)
        
        click_on_image('exportar_xml/descricao.png', click_type='right', confidence=0.7, timeout=20)
        
        time.sleep(2)
        
        click_on_image('exportar_xml/exportar_xls.png', confidence=0.7, timeout=20)
        
        time.sleep(2)
        
        click_on_image('exportar_xml/ok3.png', confidence=0.7, timeout=20, continue_after_fail=True)
        
        time.sleep(2)
        
        click_on_image('exportar_xml/acesso.png', confidence=0.9, timeout=30)
        
        time.sleep(2)
        
        pyautogui.press('tab')
        
        pyautogui.press('down', presses=6, interval=0.5)
        
        time.sleep(2)
        
        click_on_image('exportar_xml/webfile2.png',click_type='double', confidence=0.7, timeout=30)
        
        time.sleep(2)
        
        click_on_image('exportar_xml/salvar.png', confidence=0.7, timeout=30)
        
        time.sleep(2)
        
        pyautogui.press('enter')
        
        time.sleep(10)
        
        df = pd.read_excel(read_path)
        
        print(f'Total de linhas no excel: {df.shape[0]}')
        
        pyautogui.press('up', presses=df.shape[0], interval=0.5)
        
        time.sleep(2)
        
        pyautogui.press('right', presses=4, interval=0.2)
        
        time.sleep(2)
        pyautogui.press('right', presses=4, interval=0.5) 
        time.sleep(2)
        
        for row, values in df.iterrows():
            codigo_produto = int(values['Cód.Produto'])
            descricao_item = str(values['Descrição XML']).strip()
            
            if codigo_produto == 0:
                print(f'Produto sem código: {descricao_item}')
                
                resultado_ia = analisar_e_obter_id_produto(descricao_item, auto_cadastrar=True)
                
                if resultado_ia['erro']:
                    print(f'Erro na análise: {resultado_ia["erro"]}')
                    continue
                
                if resultado_ia['produto_codigo']:
                    if resultado_ia['produto_novo']:
                        print(f'Produto CADASTRADO com código: {resultado_ia["produto_codigo"]}')
                    else:
                        print(f'Produto ENCONTRADO com código: {resultado_ia["produto_codigo"]}')
                    print(f'Descrição: {resultado_ia["descricao_match"]}')
                    print(f'Confiança: {resultado_ia["confianca"]} ({resultado_ia["similaridade"]}%)')
                    print(f'Justificativa: {resultado_ia["justificativa"]}')
                    
                    
                    if resultado_ia.get('dados_cadastro'):
                        dados = resultado_ia['dados_cadastro']
                        if dados.get('grupo'):
                            grupo = dados['grupo']
                            print(f'     Grupo: {grupo.get("codigo")} - {grupo.get("descricao", "N/A")}')
                        if dados.get('unidade'):
                            unidade = dados['unidade']
                            print(f'     Unidade: {unidade.get("codigo")}')
                    
                    codigo_produto = resultado_ia['produto_codigo']
                    
                    print(f'Vinculando produto no sistema...')
                    
                    pyautogui.write(str(codigo_produto))
                else:
                    print(f'Não foi possível identificar/cadastrar o produto')
                    print(f'Justificativa: {resultado_ia["justificativa"]}')
                    
                            
            pyautogui.press('down')
            
                
        print('---')
        print('Processo de exportação e vinculação finalizado.')
        time.sleep(5)
        
        click_on_image('exportar_xml/vincular_pedidos.png', confidence=0.7, timeout=30)
        
        time.sleep(2)
        
        pyautogui.press('enter')
        
        time.sleep(2)
        
        click_on_image('exportar_xml/confirmar.png', confidence=0.7, timeout=30, continue_after_fail=True)
        time.sleep(2)
        click_on_image('exportar_xml/sim.png', confidence=0.7, timeout=30, continue_after_fail=True)
        time.sleep(2)
        click_on_image('exportar_xml/confirmar.png', confidence=0.7, timeout=10, continue_after_fail=True)
        
        time.sleep(10)

        
        click_on_image('exportar_xml/serie_ap.png', confidence=0.7, timeout=30)
        time.sleep(2)
        
        pyautogui.write('AP')
        
        pyautogui.press('tab', presses=4, interval=1)
        
        time.sleep(2)
        
        pyautogui.write('2')
        time.sleep(2)
        
        pyautogui.press('tab')
        time.sleep(2)
    
        click_on_image('exportar_xml/confirmar.png', confidence=0.7, timeout=30)
        
        time.sleep(20)

        vencimentos = extrair_vencimentos_xml()
        for v in vencimentos:
            print(f"Parcela {v['numero']}: Vencimento {v['vencimento']} - Valor R$ {v['valor']:.2f}" if v['valor'] else f"Parcela {v['numero']}: Vencimento {v['vencimento']}")
            click_on_image('exportar_xml/parcelas.png', confidence=0.7, timeout=30)
            time.sleep(2)
            pyautogui.press('tab')
            time.sleep(2)     
            vencimento_dt = datetime.strptime(v['vencimento'], '%Y-%m-%d')
            pyautogui.write(vencimento_dt.strftime('%d%m%Y'))
            time.sleep(2)
            pyautogui.press('tab')
            time.sleep(2)
            pyautogui.write(vencimento_dt.strftime('%d%m%Y'))
            click_on_all_images('exportar_xml/down.png', confidence=0.7)
            click_on_image('exportar_xml/KgFh1LwTzB.png', confidence=0.7, timeout=30, continue_after_fail=True)
            time.sleep(2)
            click_on_image('exportar_xml/KgFh1LwTzB.png', confidence=0.7, timeout=30, continue_after_fail=True)
        
        click_on_image('exportar_xml/confirmar.png', confidence=0.7, timeout=30)
        time.sleep(5)
        
        
