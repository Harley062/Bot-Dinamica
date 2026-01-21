from config import USUARIO, SENHA
from pipeline import login
from utils import get_logger
from pipeline import exportar_xml
from pipeline.exportar_produtos import exportar_produtos_para_excel
from pipeline.vinculo_fornecedor_item import vinculo_fornecedor_item

logger = get_logger("main")

def main():
    try:
        logger.info("Iniciando o processo de automação...")

        logger.info("Exportando produtos da API...")
        exportar_produtos_para_excel()

        login(USUARIO, SENHA)
    
        exportar_xml()
        logger.info("Processo de automação concluído com sucesso.")
    except Exception as e:
        logger.error(f"Erro durante a execução: {e}")

if __name__ == "__main__":
    main()