from config import USUARIO, SENHA
from pipeline import login
from utils import get_logger

logger = get_logger("main")

def main():
    try:
        logger.info("Iniciando o processo de automação...")
        login(USUARIO, SENHA)
        logger.info("Processo de automação concluído com sucesso.")
    except Exception as e:
        logger.error(f"Erro durante a execução: {e}")
    
if __name__ == "__main__":
    main()