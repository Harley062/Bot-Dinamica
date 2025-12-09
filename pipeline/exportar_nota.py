from tools import click_on_image
import time
import pyautogui


def exportar_nota():
    click_on_image('exportar_xml/EpuPRI53T2.png', confidence=0.7, timeout=20)
    
    time.sleep(5)
    
    click_on_image('exportar_xml/todos_os_modulos.png', confidence=0.7, timeout=20)
    
    time.sleep(5)
    
    click_on_image('exportar_xml/fiscal.png', confidence=0.7, timeout=20)
    
    time.sleep(30)
    
    click_on_image('exportar_xml/fechar.png', confidence=0.7, timeout=20)
    
    time.sleep(5)
    
    click_on_image('exportar_xml/gerenciador_de_nf.png', confidence=0.7, timeout=20)
    
    
    
    return True