import pyautogui
import time
import os
import cv2
import numpy as np
from PIL import ImageGrab

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

def houver_on_image(image_name, confidence=0.8, timeout=10):

    image_path = get_image_path(image_name)
    
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Arquivo de imagem não encontrado: {image_path}")
    
    start_time = time.time()
    attempts = 0
    
    while time.time() - start_time < timeout:
        attempts += 1
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            
            if location is not None:
                center_x, center_y = pyautogui.center(location)
                
                pyautogui.moveTo(center_x, center_y)
                
                elapsed = round(time.time() - start_time, 2)
                print(f"✓ Imagem '{image_name}' encontrada e hover em ({center_x}, {center_y}) "
                    f"[{attempts} tentativas, {elapsed}s]")
                return True
                
        except pyautogui.ImageNotFoundException:
            pass
        except Exception as e:
            raise Exception(f"⚠ Erro ao procurar imagem '{image_name}': {type(e).__name__}: {e}")
        
        time.sleep(0.3)
    
    Exception(f"✗ Imagem '{image_name}' não encontrada após {timeout}s ({attempts} tentativas)")
    return False

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


def apagar_xml_downloads(target_dir: str = None):
    import glob

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if target_dir is None:
        candidates = [
            os.path.join(repo_root, 'download'),
            os.path.join(repo_root, 'downloads'),
            os.path.join(os.path.expanduser('~'), 'Downloads'),
        ]
        for c in candidates:
            if os.path.isdir(c):
                target_dir = c
                break

    if target_dir is None:
        raise FileNotFoundError('Pasta de downloads não encontrada.')

    if not os.path.isdir(target_dir):
        raise FileNotFoundError(f'Pasta inválida: {target_dir}')

    pattern = os.path.join(target_dir, '*.xml')
    files = glob.glob(pattern)
    removed = []
    for f in files:
        try:
            os.remove(f)
            removed.append(f)
        except Exception as e:
            raise Exception(f'Erro ao remover {f}: {e}')

    print(f"Removidos {len(removed)} arquivos .xml em {target_dir}")
    return removed
import cv2
import numpy as np
import pyautogui
from PIL import ImageGrab
import time
import os


def click_on_all_images(image_name, target_color=None, color_tolerance=30, 
                        confidence=0.7, click_type='single', 
                        offset_x=0, offset_y=0, color_region='center',
                        delay_between_clicks=0.5, max_clicks=None,
                        multi_scale=True, min_scale=0.5, max_scale=1.5,
                        debug=False):
    
    image_path = get_image_path(image_name)
    
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Arquivo de imagem não encontrado: {image_path}")
    
    valid_click_types = ('single', 'double', 'right')
    if click_type not in valid_click_types:
        raise ValueError(f"Tipo de clique inválido: '{click_type}'. Use: {valid_click_types}")
    
    valid_color_regions = ('center', 'full', 'top', 'bottom', 'left', 'right')
    if color_region not in valid_color_regions:
        raise ValueError(f"Região de cor inválida: '{color_region}'. Use: {valid_color_regions}")
    
    click_functions = {
        'single': pyautogui.click,
        'double': pyautogui.doubleClick,
        'right': pyautogui.rightClick
    }
    
    template = cv2.imread(image_path)
    if template is None:
        raise ValueError(f"Não foi possível carregar a imagem: {image_path}")
    
    screenshot = ImageGrab.grab()
    screenshot_np = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    
    all_matches = []
    
    if multi_scale:
        scales = np.linspace(min_scale, max_scale, 15)
    else:
        scales = [1.0]
    
    print(f"🔍 Procurando '{image_name}' com {len(scales)} escalas...")
    
    for scale in scales:
        resized_template = cv2.resize(template, None, fx=scale, fy=scale, 
                                     interpolation=cv2.INTER_CUBIC)
        
        if resized_template.shape[0] > screenshot_bgr.shape[0] or \
           resized_template.shape[1] > screenshot_bgr.shape[1]:
            continue
        
        template_gray = cv2.cvtColor(resized_template, cv2.COLOR_BGR2GRAY)
        screenshot_gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)
        w, h = template_gray.shape[::-1]
        
        methods = [
            cv2.TM_CCOEFF_NORMED,
            cv2.TM_CCORR_NORMED,
            cv2.TM_SQDIFF_NORMED
        ]
        
        for method in methods:
            result = cv2.matchTemplate(screenshot_gray, template_gray, method)
            
            if method == cv2.TM_SQDIFF_NORMED:
                locations = np.where(result <= (1 - confidence))
            else:
                locations = np.where(result >= confidence)
            
            for pt in zip(*locations[::-1]):
                all_matches.append({
                    'position': pt,
                    'width': w,
                    'height': h,
                    'scale': scale,
                    'method': method
                })
    
    if not all_matches:
        print(f"✗ Nenhuma ocorrência da imagem '{image_name}' encontrada")
        if debug:
            cv2.imwrite('debug_screenshot.png', screenshot_bgr)
            print("  Screenshot salvo em 'debug_screenshot.png'")
        return 0
    
    print(f"  Encontradas {len(all_matches)} correspondências brutas")
    
    filtered_matches = _remove_overlapping_matches_advanced(all_matches)
    
    print(f"  Após filtro: {len(filtered_matches)} correspondências únicas")
    
    if debug:
        debug_img = screenshot_bgr.copy()
        for match in filtered_matches:
            pt = match['position']
            w, h = match['width'], match['height']
            cv2.rectangle(debug_img, pt, (pt[0] + w, pt[1] + h), (0, 255, 0), 2)
        cv2.imwrite('debug_matches.png', debug_img)
        print("  Matches destacados em 'debug_matches.png'")
    
    clicked_count = 0
    for i, match in enumerate(filtered_matches):
        if max_clicks is not None and clicked_count >= max_clicks:
            break
        
        pt = match['position']
        w, h = match['width'], match['height']
        
        top_left = pt
        bottom_right = (top_left[0] + w, top_left[1] + h)
        
        if target_color is not None:
            region = screenshot_bgr[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
            
            if region.size == 0:
                continue
            
            if color_region == 'center':
                cy, cx = region.shape[0] // 2, region.shape[1] // 2
                check_region = region[max(0, cy-2):cy+2, max(0, cx-2):cx+2]
            elif color_region == 'full':
                check_region = region
            elif color_region == 'top':
                check_region = region[:max(1, region.shape[0]//4), :]
            elif color_region == 'bottom':
                check_region = region[3*region.shape[0]//4:, :]
            elif color_region == 'left':
                check_region = region[:, :max(1, region.shape[1]//4)]
            elif color_region == 'right':
                check_region = region[:, 3*region.shape[1]//4:]
            
            if check_region.size == 0:
                continue
            
            avg_color = check_region.mean(axis=(0, 1))
            target_bgr = (target_color[2], target_color[1], target_color[0])
            
            color_diff = np.abs(avg_color - target_bgr)
            if not np.all(color_diff <= color_tolerance):
                if debug:
                    print(f"    Match rejeitado por cor: {tuple(map(int, avg_color[::-1]))} vs {target_color}")
                continue
        
        center_x = top_left[0] + w // 2
        center_y = top_left[1] + h // 2
        click_x = center_x + offset_x
        click_y = center_y + offset_y
        
        click_functions[click_type](click_x, click_y)
        clicked_count += 1
        
        scale_info = f" [escala: {match['scale']:.2f}]" if multi_scale else ""
        print(f"  [{clicked_count}] ✓ Clicado em ({click_x}, {click_y}){scale_info}")
        
        if i < len(filtered_matches) - 1:
            time.sleep(delay_between_clicks)
            
        pyautogui.press('right', presses=8, interval=0.5)
        if houver_on_image('exportar_xml/cod.png', confidence=0.7, timeout=20):
            number = 2553 + 1
            pyautogui.write(str(number))
            pyautogui.press('down')
        else:
            pyautogui.press('left', presses=15, interval=0.5)
    
    color_info = " com cor validada" if target_color else ""
    print(f"✓ Total de {clicked_count} imagem(ns) '{image_name}'{color_info} clicada(s)")
    return clicked_count


def _remove_overlapping_matches_advanced(matches, overlap_threshold=0.3):
    if not matches:
        return []
    
    matches_with_score = []
    for match in matches:
        score = match.get('score', 1.0)
        matches_with_score.append((match, score))
    
    matches_with_score.sort(key=lambda x: x[1], reverse=True)
    
    filtered = []
    for match, score in matches_with_score:
        is_overlapping = False
        for existing in filtered:
            overlap = _calculate_overlap_advanced(match, existing)
            if overlap > overlap_threshold:
                is_overlapping = True
                break
        
        if not is_overlapping:
            filtered.append(match)
    
    return filtered


def _calculate_overlap_advanced(match1, match2):
    x1_min, y1_min = match1['position']
    w1, h1 = match1['width'], match1['height']
    x1_max, y1_max = x1_min + w1, y1_min + h1
    
    x2_min, y2_min = match2['position']
    w2, h2 = match2['width'], match2['height']
    x2_max, y2_max = x2_min + w2, y2_min + h2
    
    x_overlap = max(0, min(x1_max, x2_max) - max(x1_min, x2_min))
    y_overlap = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
    
    overlap_area = x_overlap * y_overlap
    area1 = w1 * h1
    area2 = w2 * h2
    min_area = min(area1, area2)
    
    return overlap_area / min_area if min_area > 0 else 0