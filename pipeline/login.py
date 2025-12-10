from tools import init_chrome, click_on_image
import time 
import pyautogui

def login(usuario, senha, usuario_mega="mega", senha_mega="a"):
    
    init_chrome("https://dev.megaerp.online/")
    time.sleep(5)
    click_on_image('login/login.png')
    pyautogui.press('tab')
    pyautogui.write(usuario)
    pyautogui.press('tab')
    pyautogui.write(senha)
    click_on_image('login/acessar.png', confidence=0.7, timeout=20)
    
    click_on_image('login/conection.png', confidence=0.7, timeout=320, click_type='double')
    time.sleep(10)
    click_on_image('login/minimizar.png', confidence=0.7, timeout=30)
    time.sleep(5)
    click_on_image('login/abrir_mega.png', confidence=0.7, timeout=30, click_type='double')
    time.sleep(10)
    click_on_image('login/logo.png', confidence=0.7, timeout=30)
    # pyautogui.press('tab')
    time.sleep(1)
    pyautogui.write(usuario_mega)
    time.sleep(1)
    pyautogui.press('tab')
    
    pyautogui.write(senha_mega)
    
    click_on_image('login/autenticar.png', confidence=0.7, timeout=30)
    time.sleep(15)
    
    click_on_image('login/fechar.png', confidence=0.7, timeout=30)
    time.sleep(5)
    
    print("Login realizado com sucesso.")
    return True
    
    