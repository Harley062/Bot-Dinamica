from tools import click_on_image, houver_on_image, apagar_xml_downloads, click_on_all_images
import time
import pyautogui


def exportar_xml():
    apagar_xml_downloads()
    
    click_on_image('exportar_xml/EpuPRI53T2.png', confidence=0.7, timeout=20)
    
    time.sleep(5)
    
    click_on_image('exportar_xml/todos_os_modulos.png', confidence=0.7, timeout=20)
    
    time.sleep(5)
    
    click_on_image('exportar_xml/fiscal.png', confidence=0.7, timeout=20)
    
    time.sleep(20)
    
    click_on_image('exportar_xml/fechar.png', confidence=0.7, timeout=30)
    
    time.sleep(5)
    
    click_on_image('exportar_xml/gerenciador_de_nf.png', confidence=0.7, timeout=20)
    
    time.sleep(5)
    
    click_on_image('exportar_xml/calendario.png', confidence=0.7, timeout=20)
    
    time.sleep(2)
    
    click_on_image('exportar_xml/limpar.png', confidence=0.7, timeout=20)
    
    time.sleep(2)
    
    pyautogui.write('01012025')
    
    time.sleep(2)
    
    click_on_image('exportar_xml/status_xml.png', confidence=0.7, timeout=20)
    
    time.sleep(2)
    
    pyautogui.press('down', presses=2, interval=1)
    
    time.sleep(2)
    
    click_on_image('exportar_xml/aberto.png', confidence=0.7, timeout=20)
    
    time.sleep(2)
    
    click_on_image('exportar_xml/filtrar.png', confidence=0.7, timeout=20)
    
    time.sleep(10)
    
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
    
    click_on_image('exportar_xml/ok.png', confidence=0.7, timeout=20)
    
    time.sleep(5)
    
    houver_on_image('exportar_xml/lYW5IFXKAw.png', confidence=0.7, timeout=20)
    
    click_on_image('exportar_xml/fechar.png', confidence=0.7, timeout=30)
    
    time.sleep(10)
    
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
    
    #retorna dado do xml
    pyautogui.write('CIF')
    
    pyautogui.press('tab')
    
    pyautogui.write('06 DIAS')
    
    click_on_image('exportar_xml/vincular_itens.png', confidence=0.7, timeout=20)
    
    time.sleep(2)
    pyautogui.press('tab', presses=2, interval=0.5)
    pyautogui.press('right')
    
    total = click_on_all_images(
    'exportar_xml/cadastro_produto.png',
    confidence=0.9,
)
    time.sleep(2)
    click_on_image('exportar_xml/confirmar.png', confidence=0.7, timeout=20)    
    time.sleep(10)
    click_on_image('exportar_xml/editar_item.png', confidence=0.7, timeout=30)
    time.sleep(2)
    click_on_image('exportar_xml/editar.png', confidence=0.7, timeout=30)
    time.sleep(2)
    click_on_image('exportar_xml/estoque.png', confidence=0.7, timeout=30)
    time.sleep(2)
    pyautogui.press('tab', presses=2, interval=0.5)
    pyautogui.write('29')
    click_on_image('exportar_xml/estoque2.png', confidence=0.7, timeout=30)
    pyautogui.press('tab', presses=3, interval=0.5)
    pyautogui.write('1')
    
    click_on_image('exportar_xml/confirmar3.png.png', confidence=0.7, timeout=30)
    
    try:
        click_on_image('exportar_xml/confirmar2.png', confidence=0.7, timeout=30)
    except Exception as e:
        click_on_image('exportar_xml/confirmar.png', confidence=0.7, timeout=20) 
    
    click_on_image('exportar_xml/ok2.png', confidence=0.7, timeout=30)
    
    time.sleep(5)
    click_on_image('exportar_xml/confirmar.png', confidence=0.7, timeout=20) 
    
    return True
