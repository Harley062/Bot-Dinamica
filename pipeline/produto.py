import pandas as pd
from pathlib import Path


def ler_est_produtos(caminho_arquivo: str = None) -> pd.DataFrame:
    """
    Lê o arquivo EST_PRODUTOS.csv e retorna um DataFrame do pandas.

    Args:
        caminho_arquivo (str, optional): Caminho completo para o arquivo CSV.
                                         Se não fornecido, usa o caminho padrão.

    Returns:
        pd.DataFrame: DataFrame contendo os dados do arquivo EST_PRODUTOS.csv

    Raises:
        FileNotFoundError: Se o arquivo não for encontrado
        Exception: Para outros erros na leitura do arquivo
    """
    if caminho_arquivo is None:
        # Caminho padrão relativo à raiz do projeto
        caminho_arquivo = Path(__file__).parent.parent / "EST_PRODUTOS.csv"

    try:
        # Lê o CSV com delimitador de ponto e vírgula
        df = pd.read_csv(
            caminho_arquivo,
            sep=';',
            encoding='latin1',  # Encoding comum para arquivos exportados de sistemas brasileiros
            low_memory=False,  # Evita warnings com arquivos grandes
            #dtype=str  # Lê todas as colunas como string para evitar conversões automáticas
        )

        print(f"Arquivo lido com sucesso: {len(df)} registros encontrados")
        print(f"Colunas: {len(df.columns)}")

        return df

    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
    except Exception as e:
        raise Exception(f"Erro ao ler o arquivo: {str(e)}")


if __name__ == "__main__":
    # Teste da função
    df = ler_est_produtos()
    print("\nPrimeiras 5 linhas:")
    print(df.head())
    print("\nInformações do DataFrame:")
    print(df.info())
