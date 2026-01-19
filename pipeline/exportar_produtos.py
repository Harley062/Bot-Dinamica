import pandas as pd
from datetime import datetime
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

import autenticacao
APIClient = autenticacao.APIClient


def exportar_produtos_para_excel(nome_arquivo="produtos_api.xlsx", apenas_ativos=True):
    try:
        print("Iniciando exportação de produtos...")

        client = APIClient()

        print("Buscando produtos da API...")
        produtos = client.get_produtos()

        if not produtos:
            print("Nenhum produto encontrado.")
            return

        print(f"Total de produtos retornados pela API: {len(produtos) if isinstance(produtos, list) else 1}")

        df = pd.DataFrame(produtos if isinstance(produtos, list) else [produtos])

        if apenas_ativos and 'inativo' in df.columns:
            produtos_antes = len(df)
            df = df[(df['inativo'] == False) | (df['inativo'] == 0)]
            print(f"Filtrando apenas produtos ativos: {produtos_antes} -> {len(df)} produtos")

        df.to_excel(nome_arquivo, index=False, engine='openpyxl')

        print(f"\nProdutos exportados com sucesso para: {nome_arquivo}")
        print(f"Total de linhas: {len(df)}")
        print(f"Colunas: {', '.join(df.columns.tolist())}")

        return nome_arquivo

    except Exception as e:
        print(f"Erro ao exportar produtos: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    exportar_produtos_para_excel()
