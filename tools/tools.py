import pyautogui
import time
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(BASE_DIR, "images")


def get_image_path(image_name):

    if os.path.isabs(image_name):
        return image_name
    return os.path.join(IMAGES_DIR, image_name)


def click_on_image(image_name, confidence=0.8, timeout=10, click_type='single', offset_x=0, offset_y=0):

    image_path = get_image_path(image_name)
    
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Arquivo de imagem não encontrado: {image_path}")
    
    valid_click_types = ('single', 'double', 'right')
    if click_type not in valid_click_types:
        raise ValueError(f"Tipo de clique inválido: '{click_type}'. Use: {valid_click_types}")
    
    click_functions = {
        'single': pyautogui.click,
        'double': pyautogui.doubleClick,
        'right': pyautogui.rightClick
    }
    
    start_time = time.time()
    attempts = 0
    
    while time.time() - start_time < timeout:
        attempts += 1
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            
            if location is not None:
                center_x, center_y = pyautogui.center(location)
                click_x = center_x + offset_x
                click_y = center_y + offset_y
                
                click_functions[click_type](click_x, click_y)
                
                elapsed = round(time.time() - start_time, 2)
                print(f"✓ Imagem '{image_name}' encontrada e clicada em ({click_x}, {click_y}) "
                    f"[{attempts} tentativas, {elapsed}s]")
                return True
                
        except pyautogui.ImageNotFoundException:
            pass
        except Exception as e:
            raise Exception(f"⚠ Erro ao procurar imagem '{image_name}': {type(e).__name__}: {e}")
        
        time.sleep(0.3)
    
    raise Exception(f"✗ Imagem '{image_name}' não encontrada após {timeout}s ({attempts} tentativas)")


def wait_and_click_image(image_name, confidence=0.8, timeout=30):

    return click_on_image(image_name, confidence, timeout, 'single')

def init_chrome(url):
    pyautogui.press('win')
    time.sleep(1)
    pyautogui.write('chrome')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(3)
    pyautogui.write(url)
    pyautogui.press('enter')
    time.sleep(5)