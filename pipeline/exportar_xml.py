from tools import click_on_image, houver_on_image, apagar_xml_downloads, click_on_all_images
import time
import pyautogui
import pandas as pd
from typing import Optional, Dict
import os

# Import do analisador de produtos com IA
from pipeline.analisador_produto import AnalisadorProduto, AcaoRequerida


# Instância global do analisador (reutilizada para performance)
_analisador_produto: Optional[AnalisadorProduto] = None


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
    
    # apagar_xml_downloads()
    read_path = r'C:\Users\harley.goncalves\Downloads\gd_ItensXML.xls'
    
    if os.path.exists(read_path):
        os.remove(read_path)
    
    # apagar_xml_downloads()
    # click_on_image('exportar_xml/EpuPRI53T2.png', confidence=0.7, timeout=20)
    
    # time.sleep(5)
    
    # click_on_image('exportar_xml/todos_os_modulos.png', confidence=0.7, timeout=20)
    
    # time.sleep(5)
    
    # click_on_image('exportar_xml/fiscal.png', confidence=0.7, timeout=20)
    
    # time.sleep(20)
    
    # click_on_image('exportar_xml/fechar.png', confidence=0.7, timeout=30)
    
    # time.sleep(5)
    
    # click_on_image('exportar_xml/gerenciador_de_nf.png', confidence=0.7, timeout=20)
    
    # time.sleep(5)
    
    # click_on_image('exportar_xml/calendario.png', confidence=0.7, timeout=20)
    
    # time.sleep(2)
    
    # click_on_image('exportar_xml/limpar.png', confidence=0.7, timeout=20)
    
    # time.sleep(2)
    
    # pyautogui.write('01012025')
    
    # time.sleep(2)
    
    # click_on_image('exportar_xml/status_xml.png', confidence=0.7, timeout=20)
    
    # time.sleep(2)
    
    # pyautogui.press('down', presses=2, interval=1)
    
    # time.sleep(2)
    
    # click_on_image('exportar_xml/aberto.png', confidence=0.7, timeout=20)
    
    # time.sleep(2)
    
    # click_on_image('exportar_xml/filtrar.png', confidence=0.7, timeout=20)
    
    # time.sleep(10)
    
    # click_on_image('exportar_xml/status_aberto.png', click_type='double', confidence=0.7, timeout=20)
    
    # time.sleep(2)
    
    # click_on_image('exportar_xml/outros.png', confidence=0.7, timeout=20)
    
    # time.sleep(2)
    
    # houver_on_image('exportar_xml/exportar.png', confidence=0.7, timeout=20)
    
    # time.sleep(2)
    
    # pyautogui.press('down', presses=3, interval=1)
    
    # time.sleep(1)
    
    # pyautogui.press('enter')
    
    # time.sleep(2)
    
    # click_on_image('exportar_xml/webfile.png', confidence=0.7, timeout=20)
    
    # time.sleep(2)
    
    # click_on_image('exportar_xml/ok.png', confidence=0.7, timeout=20)
    
    # time.sleep(5)
    
    # houver_on_image('exportar_xml/lYW5IFXKAw.png', confidence=0.7, timeout=20)
    
    # click_on_image('exportar_xml/fechar.png', confidence=0.7, timeout=30)
    
    # time.sleep(10)
    
    
    # #Aqui ja tem o xml baixado
    
    
    # click_on_image('exportar_xml/receber.png', confidence=0.7, timeout=20)
    
    # time.sleep(2)
    
    # pyautogui.press('down', presses=2, interval=1)
    
    # pyautogui.press('enter')
    
    # time.sleep(15)
    
    # pyautogui.write('864')
    
    # time.sleep(2)
    
    # pyautogui.press('tab')
    
    # time.sleep(2)
    
    # # pyautogui.write('NFS')
    
    # pyautogui.press('tab', presses=3, interval=1)
    
    # #retorna dado do xml
    
    # pyautogui.write('CIF')
    
    # pyautogui.press('tab')
    
    # pyautogui.write('06 DIAS')
    
    # click_on_image('exportar_xml/vincular_itens.png', confidence=0.7, timeout=20)
    
    # time.sleep(2)

    # click_on_image('exportar_xml/bPCGyi572k.png', confidence=0.7, timeout=20)

    # time.sleep(5)
    
    # pyautogui.rightClick(842,474)
    # time.sleep(2)
    
    # click_on_image('exportar_xml/exportar_xls.png', confidence=0.7, timeout=20)
    
    # time.sleep(2)
    
    # click_on_image('exportar_xml/ok3.png', confidence=0.7, timeout=20, continue_after_fail=True)
    
    # time.sleep(5)
    
    # click_on_image('exportar_xml/salvar.png', confidence=0.7, timeout=30)
    
    # time.sleep(10)
    
    # df = pd.read_excel(read_path)
    
    # print(f'Total de linhas no excel: {df.shape[0]}')
    # pyautogui.press('up', presses=df.shape[0], interval=0.5)
    # time.sleep(2)
    # pyautogui.press('right', presses=4, interval=0.5) 
    # time.sleep(2)
    
    # for row, values in df.iterrows():
    #     codigo_produto = int(values['Cód.Produto'])
    #     descricao_item = str(values['Descrição XML']).strip()
        
    #     if codigo_produto == 0:
    #         print(f'Produto sem código: {descricao_item}')
            
    #         resultado_ia = analisar_e_obter_id_produto(descricao_item, auto_cadastrar=True)
            
    #         if resultado_ia['erro']:
    #             print(f'Erro na análise: {resultado_ia["erro"]}')
    #             continue
            
    #         if resultado_ia['produto_codigo']:
    #             if resultado_ia['produto_novo']:
    #                 print(f'Produto CADASTRADO com código: {resultado_ia["produto_codigo"]}')
    #             else:
    #                 print(f'Produto ENCONTRADO com código: {resultado_ia["produto_codigo"]}')
    #             print(f'Descrição: {resultado_ia["descricao_match"]}')
    #             print(f'Confiança: {resultado_ia["confianca"]} ({resultado_ia["similaridade"]}%)')
    #             print(f'Justificativa: {resultado_ia["justificativa"]}')
                
                
    #             if resultado_ia.get('dados_cadastro'):
    #                 dados = resultado_ia['dados_cadastro']
    #                 if dados.get('grupo'):
    #                     grupo = dados['grupo']
    #                     print(f'     Grupo: {grupo.get("codigo")} - {grupo.get("descricao", "N/A")}')
    #                 if dados.get('unidade'):
    #                     unidade = dados['unidade']
    #                     print(f'     Unidade: {unidade.get("codigo")}')
                
    #             codigo_produto = resultado_ia['produto_codigo']
                
    #             print(f'Vinculando produto no sistema...')
                
    #             pyautogui.write(str(codigo_produto))
    #         else:
    #             print(f'Não foi possível identificar/cadastrar o produto')
    #             print(f'Justificativa: {resultado_ia["justificativa"]}')
                
                        
    #     pyautogui.press('down')
        
            
    # print('---')
    # print('Processo de exportação e vinculação finalizado.')
    # time.sleep(5)
    # click_on_image('exportar_xml/confirmar.png', confidence=0.7, timeout=30)
    
    # print('Função exportar_xml executada.')
    
    # time.sleep(10)
    
    # click_on_image('exportar_xml/serie_ap.png', confidence=0.7, timeout=30)
    # time.sleep(2)
    
    # pyautogui.write('AP')
    # pyautogui.press('tab', presses=3, interval=0.5)
    # time.sleep(2)
    
    # pyautogui.write('92')
    # time.sleep(2)
    
    # pyautogui.press('tab')
    # time.sleep(2)
    
    # click_on_image('exportar_xml/editar_item.png', confidence=0.7, timeout=30)
    # time.sleep(2)
    
    # click_on_image('exportar_xml/editar.png', confidence=0.7, timeout=30)
    
    # time.sleep(2)
    
    # click_on_image('exportar_xml/estoque.png', confidence=0.7, timeout=30)
    
    # time.sleep(2)
    
    # click_on_image('exportar_xml/almoxarifado.png', confidence=0.7, timeout=30)
    # time.sleep(2)
    
    # pyautogui.write('29')
    
    # time.sleep(2)
    
    # pyautogui.press('tab')
    
    # time.sleep(2)
    
    # pyautogui.write('1')
    
    # time.sleep(2)
    
    # pyautogui.press('tab')
    
    # time.sleep(2)
    
    # pyautogui.write('DP')
    
    # time.sleep(2)
    
    # pyautogui.press('tab')
    
    # time.sleep(2)
    
    # pyautogui.press('enter')
    
    # click_on_image('exportar_xml/confirmar.png', confidence=0.7, timeout=30)
    # time.sleep(2)
    
    # click_on_image('exportar_xml/ok2.png.png', confidence=0.7, timeout=30)
    
    # time.sleep(5)
    
    # click_on_image('exportar_xml/confirmar.png', confidence=0.7, timeout=30)
    
    # time.sleep(20)