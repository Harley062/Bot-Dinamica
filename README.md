# Bot Dinâmica - Automação MegaERP

Bot de automação RPA (Robotic Process Automation) para integração com o sistema MegaERP. Automatiza processos de importação de notas fiscais XML, análise inteligente de produtos usando IA e cadastro automático.

## Funcionalidades

- **Login Automático**: Autenticação com suporte a 2FA no MegaERP
- **Exportação de XML**: Processamento automatizado de notas fiscais eletrônicas
- **Análise Inteligente de Produtos**: Matching híbrido de produtos usando IA (GPT-4/Claude)
  - Pré-filtro tradicional com fuzzy matching
  - Análise semântica profunda com IA
  - Cadastro automático de produtos novos
- **Integração com API**: Cliente REST completo para MegaERP
- **Extração de Dados**: Detecção automática de tipo de frete (CIF/FOB/RED) de XMLs

## Requisitos

- Python 3.8+
- Windows (automação visual com PyAutoGUI)
- Navegador Chrome
- Acesso ao sistema MegaERP

## Instalação

1. Clone o repositório:
```bash
git clone <repository-url>
cd Bot-Dinamica
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas credenciais:
```bash
USUARIO=seu_usuario
SENHA=sua_senha
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
```

5. Crie a estrutura de pastas necessária:
```bash
mkdir -p data/cache logs
```

## Estrutura do Projeto

```
Bot-Dinamica/
├── config/              # Configurações centralizadas
│   └── settings.py      # URLs, timeouts, paths
├── pipeline/            # Módulos de automação principal
│   ├── login.py         # Autenticação no sistema
│   ├── exportar_xml.py  # Processamento de NFe
│   ├── analisador_produto.py  # IA para análise de produtos
│   ├── pre_filtro_inteligente.py  # Matching híbrido
│   ├── exportar_produtos.py  # Exportação para Excel
│   └── autenticacao.py  # Cliente REST API
├── tools/               # Utilitários de automação RPA
│   └── tools.py         # Funções de clique, OCR, etc.
├── utils/               # Utilitários gerais
│   └── logger.py        # Sistema de logging
├── scripts/             # Scripts utilitários CLI
│   ├── listar_grupos.py
│   └── run_exportar_produtos.py
├── images/              # Recursos visuais para RPA
│   ├── login/
│   ├── exportar_xml/
│   └── vinculo_forn_item/
├── data/                # Dados e cache (não versionado)
│   └── cache/
│       └── produtos_api.xlsx
├── logs/                # Logs de execução
└── main.py              # Entry point principal
```

## Uso

### Execução Principal

Execute o fluxo completo de automação:
```bash
python main.py
```

### Scripts Individuais

Listar grupos de produtos da API:
```bash
python scripts/listar_grupos.py
```

Exportar produtos para Excel:
```bash
python scripts/run_exportar_produtos.py
```

## Fluxo de Automação

1. **Login**: Autentica no MegaERP
2. **Exportar XML**:
   - Filtra notas fiscais abertas
   - Baixa XML das NFe
   - Extrai tipo de frete (CIF/FOB/RED)
   - Vincula itens
3. **Análise de Produtos**:
   - Verifica produtos sem código (código = 0)
   - Busca match na base usando IA
   - Cadastra automaticamente se necessário
   - Vincula produto ao item da nota
4. **Processamento Final**:
   - Confirma vinculações
   - Gera pedido de compra
   - Atualiza estoque

## Configurações

### Paths Customizados

Por padrão, o sistema usa a pasta Downloads do usuário. Para customizar:

1. Edite `.env`:
```bash
DOWNLOADS_PATH=/custom/path/downloads
```

2. Ou modifique `config/settings.py`:
```python
DOWNLOADS_PATH = "C:/custom/path"
```

### Providers de IA

O sistema suporta OpenAI e Anthropic. Configure no `.env`:
- `OPENAI_API_KEY`: Para usar GPT-4
- `ANTHROPIC_API_KEY`: Para usar Claude

## Logs

Logs são salvos diariamente em `logs/bot_YYYYMMDD.log` com:
- Timestamps detalhados
- Níveis de log (INFO, ERROR, DEBUG)
- Rastreamento de erros completo

Visualizar logs em tempo real:
```bash
tail -f logs/bot_20260120.log
```

## Troubleshooting

### Erro de Import
```
ImportError: cannot import name 'MatcherHibrido'
```
**Solução**: Certifique-se de que todos os arquivos estão nos locais corretos após reorganização.

### Arquivo XML não encontrado
```
Nenhum arquivo XML encontrado
```
**Solução**: Verifique se os XMLs foram baixados na pasta Downloads configurada.

### Erro de Autenticação API
```
401 Unauthorized
```
**Solução**: Verifique as credenciais no arquivo `.env`.

### Produtos não encontrados
```
Nenhum produto encontrado
```
**Solução**: Execute `python scripts/run_exportar_produtos.py` para atualizar cache local.

## Desenvolvimento

### Adicionar Novo Módulo

1. Crie em `pipeline/novo_modulo.py`
2. Adicione ao `pipeline/__init__.py`:
```python
from .novo_modulo import funcao_principal
```

### Adicionar Novas Imagens RPA

1. Capture screenshot da região desejada
2. Salve em `images/categoria/nome_descritivo.png`
3. Use no código:
```python
click_on_image('categoria/nome_descritivo.png')
```

## Tecnologias

- **PyAutoGUI**: Automação de GUI
- **OpenCV**: Reconhecimento de imagens
- **Pandas**: Manipulação de dados
- **OpenAI/Anthropic**: APIs de IA
- **Requests**: Cliente HTTP
- **FuzzyWuzzy**: Matching fuzzy de strings
- **Python-dotenv**: Gerenciamento de variáveis de ambiente

## Contribuindo

1. Faça fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Licença

Este projeto é proprietário e confidencial.

## Suporte

Para dúvidas ou problemas:
1. Verifique os logs em `logs/`
2. Consulte a seção Troubleshooting acima
3. Entre em contato com o time de desenvolvimento
