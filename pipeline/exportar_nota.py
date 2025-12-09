from tools import click_on_image
import time
import pyautogui


def exportar_nota():
    click_on_image('exportar_xml/EpuPRI53T2.png', confidence=0.7, timeout=20)
    
    return True