import os
from dotenv import load_dotenv

load_dotenv()

USUARIO = os.getenv("USUARIO")
SENHA = os.getenv("SENHA")

URL_LOGIN = "https://dev.megaerp.online/"

DEFAULT_TIMEOUT = 20       
DEFAULT_CONFIDENCE = 0.7    
CLICK_DELAY = 0.5           
PAGE_LOAD_DELAY = 5         

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Paths de dados
DATA_DIR = os.path.join(BASE_DIR, "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
DOWNLOADS_PATH = os.path.join(os.path.expanduser("~"), "Downloads")

# Arquivos de cache
PRODUTOS_CACHE = os.path.join(CACHE_DIR, "produtos_api.xlsx")
