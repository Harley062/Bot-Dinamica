"""Lista todos os grupos disponíveis."""
from pipeline.autenticacao import APIClient

api = APIClient()
grupos = api.get_grupos()

print(f"Total de grupos: {len(grupos)}\n")

# Agrupa por identificador
identificadores = {}
for g in grupos:
    ident = g.get('identificador', 'N/A')
    if ident not in identificadores:
        identificadores[ident] = []
    identificadores[ident].append(g)

print("=" * 60)
print("GRUPOS AGRUPADOS POR IDENTIFICADOR (CATEGORIA BASE)")
print("=" * 60)

for ident, lista in sorted(identificadores.items()):
    print(f"\n📁 Identificador: {ident}")
    print("-" * 40)
    for g in lista[:10]:  # Mostra até 10 de cada
        print(f"   {g['codigo']:>5} - {g['descricao']}")
    if len(lista) > 10:
        print(f"   ... e mais {len(lista) - 10} grupos")
