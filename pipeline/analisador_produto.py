"""
Serviço de Análise e Cadastro Automático de Produtos

Este módulo analisa produtos e retorna uma resposta estruturada indicando:
- Se o produto existe na base (com vínculo)
- Se é necessário cadastrar um novo produto
- Se é necessário fazer vínculo fornecedor-item

O GPT retorna de forma estruturada para que o sistema interprete e 
realize o cadastro/vínculo automaticamente.
"""

import os
import sys
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from enum import Enum
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Ajusta path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Imports do projeto
from pipeline.autenticacao import APIClient
from pre_filtro_inteligente import MatcherHibrido, ProviderOpenAI, ProviderAnthropic
import pandas as pd


class AcaoRequerida(Enum):
    """Ações que o sistema pode executar."""
    APENAS_VINCULO = "apenas_vinculo"           # Produto existe, só vincular
    CADASTRO_E_VINCULO = "cadastro_e_vinculo"   # Produto não existe, cadastrar e vincular
    NENHUMA = "nenhuma"                          # Produto já vinculado ou erro


@dataclass
class ResultadoAnalise:
    """Resultado estruturado da análise de produto."""
    
    # Identificação
    descricao_buscada: str
    codigo_fornecedor: Optional[str] = None
    
    # Resultado da busca
    produto_encontrado: bool = False
    similaridade: int = 0  # 0-100
    confianca: str = "BAIXA"  # ALTA, MEDIA, BAIXA
    
    # Dados do produto encontrado (se existir)
    produto_match: Optional[Dict] = None
    
    # Ação requerida
    acao: AcaoRequerida = AcaoRequerida.NENHUMA
    
    # Dados para cadastro (quando necessário)
    dados_cadastro: Optional[Dict] = None
    
    # Justificativa da decisão
    justificativa: str = ""
    
    # Status de execução
    cadastro_realizado: bool = False
    vinculo_realizado: bool = False
    erro: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Converte para dicionário serializável."""
        result = asdict(self)
        result['acao'] = self.acao.value
        return result
    
    def to_json(self) -> str:
        """Converte para JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass 
class DadosCadastroProduto:
    """Dados estruturados para cadastro de produto via API."""
    
    descricao: str
    descricaoNFe: str
    alternativo: Optional[str] = None
    
    # Classificação
    definicaoItem: str = "IS"  # IS = Item de Serviço/Insumo
    procedencia: str = "C"     # C = Comprado
    definicaoFiscal: str = "07"
    
    # Unidade (obrigatório)
    unidade: Optional[Dict] = None
    
    # Grupo (obrigatório)
    grupo: Optional[Dict] = None
    
    # NCM (opcional)
    ncm: Optional[Dict] = None
    
    # Controles
    padrao: int = 1
    controlaEstoque: bool = True
    controlaSerie: bool = False
    controlaLotes: bool = False
    controlaDataValidade: bool = False
    inativo: bool = False
    
    # Flags padrão
    comissionado: bool = True
    geraSolicitacao: int = 3
    quantidadeComprar: str = "1"
    definicaoIcms: str = "N"
    generico: str = "N"
    
    def to_api_payload(self) -> Dict:
        """Converte para payload da API."""
        payload = {
            "padrao": self.padrao,
            "descricao": self.descricao,
            "descricaoNFe": self.descricaoNFe,
            "definicaoItem": self.definicaoItem,
            "procedencia": self.procedencia,
            "definicaoFiscal": self.definicaoFiscal,
            "controlaEstoque": self.controlaEstoque,
            "controlaSerie": self.controlaSerie,
            "controlaLotes": self.controlaLotes,
            "controlaDataValidade": self.controlaDataValidade,
            "quantidadeCalculoValidade": 0,  # Campo obrigatório
            "inativo": self.inativo,
            "comissionado": self.comissionado,
            "geraSolicitacao": self.geraSolicitacao,
            "quantidadeComprar": self.quantidadeComprar,
            "definicaoIcms": self.definicaoIcms,
            "generico": self.generico,
        }
        
        # Campo alternativo é obrigatório - gera um baseado na descrição se não fornecido
        if self.alternativo:
            payload["alternativo"] = self.alternativo
        else:
            # Gera código alternativo baseado no timestamp
            import time
            payload["alternativo"] = f"AUTO-{int(time.time())}"
            
        # IMPORTANTE: A API exige id, codigo e padrao para unidade
        if self.unidade:
            payload["unidade"] = {
                "id": self.unidade.get("id"),
                "codigo": self.unidade.get("codigo"),
                "padrao": self.unidade.get("padrao", 1)
            }
            
        # IMPORTANTE: A API exige id, codigo, identificador e padrao para grupo
        if self.grupo:
            payload["grupo"] = {
                "id": self.grupo.get("id"),
                "codigo": self.grupo.get("codigo"),
                "padrao": self.grupo.get("padrao", 1),
                "identificador": self.grupo.get("identificador"),
                "descricao": self.grupo.get("descricao", "")
            }
            
        if self.ncm:
            payload["ncm"] = {"id": self.ncm.get("id")} if isinstance(self.ncm, dict) else self.ncm
            
        return payload


class AnalisadorProduto:
    """
    Serviço principal de análise e cadastro de produtos.
    
    Fluxo:
    1. Recebe descrição do produto (da nota fiscal)
    2. Busca na base usando IA híbrida
    3. Retorna resultado estruturado com ação requerida
    4. Executa cadastro/vínculo se solicitado
    """
    
    def __init__(
        self,
        api_client: Optional[APIClient] = None,
        openai_key: Optional[str] = None,
        anthropic_key: Optional[str] = None,
        limiar_match: int = 70,       # Score mínimo para considerar match
        limiar_cadastro: int = 50     # Score abaixo disso sugere cadastro
    ):
        self.api_client = api_client or APIClient()
        self.limiar_match = limiar_match
        self.limiar_cadastro = limiar_cadastro
        
        # Configura provider de IA
        self.provider_ia = None
        if openai_key or os.getenv('OPENAI_API_KEY'):
            self.provider_ia = ProviderOpenAI(openai_key or os.getenv('OPENAI_API_KEY'))
        elif anthropic_key or os.getenv('ANTHROPIC_API_KEY'):
            self.provider_ia = ProviderAnthropic(anthropic_key or os.getenv('ANTHROPIC_API_KEY'))
        
        # Cache de dados auxiliares
        self._grupos_cache = None
        self._unidades_cache = None
        self._matcher = None
    
    def _get_matcher(self) -> MatcherHibrido:
        """Obtém ou cria o matcher híbrido."""
        if self._matcher is None:
            # Carrega produtos da API
            produtos = self.api_client.get_produtos()
            
            # Converte para DataFrame
            df = pd.DataFrame(produtos)
            
            # Mapeia colunas para o formato esperado pelo matcher
            col_mapping = {
                'codigo': 'PRO_ST_CODREAL',
                'alternativo': 'PRO_ST_CODREAL',
                'descricao': 'PRO_ST_DESCRICAO',
                'id': 'PRO_IN_CODIGO'
            }
            
            for old, new in col_mapping.items():
                if old in df.columns and new not in df.columns:
                    df[new] = df[old]
            
            # Garante tipos
            if 'PRO_ST_CODREAL' in df.columns:
                df['PRO_ST_CODREAL'] = df['PRO_ST_CODREAL'].astype(str)
            if 'PRO_ST_DESCRICAO' in df.columns:
                df['PRO_ST_DESCRICAO'] = df['PRO_ST_DESCRICAO'].astype(str).fillna('')
            
            self._matcher = MatcherHibrido(df, provider_ia=self.provider_ia)
        
        return self._matcher
    
    def _get_grupos(self) -> List[Dict]:
        """Obtém lista de grupos."""
        if self._grupos_cache is None:
            try:
                self._grupos_cache = self.api_client.get_grupos()
            except:
                self._grupos_cache = []
        return self._grupos_cache
    
    def _get_unidades(self) -> List[Dict]:
        """Obtém lista de unidades."""
        if self._unidades_cache is None:
            try:
                self._unidades_cache = self.api_client.get_unidades()
            except:
                self._unidades_cache = []
        return self._unidades_cache
    
    def _selecionar_grupo_padrao(self) -> Optional[Dict]:
        """Seleciona grupo padrão para cadastro."""
        grupos = self._get_grupos()
        if grupos:
            # Retorna primeiro grupo ou um específico
            # IMPORTANTE: A API usa 'identificador' como código do grupo (GRU_IDE_ST_CODIGO)
            return {
                "id": grupos[0].get('id'),
                "codigo": grupos[0].get('codigo'),
                "identificador": grupos[0].get('identificador'),
                "descricao": grupos[0].get('descricao'),
                "padrao": grupos[0].get('padrao', 1)
            }
        return None
    
    def _selecionar_unidade_padrao(self) -> Optional[Dict]:
        """Seleciona unidade padrão para cadastro."""
        unidades = self._get_unidades()
        if unidades:
            # Procura por "UN" ou primeira disponível
            for u in unidades:
                descricao = str(u.get('descricao', '')).upper()
                codigo = str(u.get('codigo', '')).upper()
                if descricao in ['UN', 'UND', 'UNID', 'UNIDADE'] or codigo in ['UN', 'UND', 'UNID']:
                    return {
                        "id": u.get('id'),
                        "codigo": u.get('codigo'),
                        "padrao": u.get('padrao', 1)
                    }
            # Retorna primeira unidade disponível
            return {
                "id": unidades[0].get('id'),
                "codigo": unidades[0].get('codigo'),
                "padrao": unidades[0].get('padrao', 1)
            }
        return None
    
    def classificar_grupo_por_ia(self, descricao_produto: str) -> Optional[Dict]:
        """
        Usa IA para classificar o produto no grupo mais adequado.
        
        Args:
            descricao_produto: Descrição do produto a ser classificado
            
        Returns:
            Dict com dados do grupo selecionado ou None se falhar
        """
        grupos = self._get_grupos()
        if not grupos or not self.provider_ia:
            return self._selecionar_grupo_padrao()
        
        # Monta lista de grupos para a IA analisar
        grupos_texto = []
        for g in grupos:
            grupos_texto.append(f"- Código {g['codigo']}: {g['descricao']} (ID: {g['id']}, Identificador: {g['identificador']})")
        
        prompt = f"""Analise a descrição do produto e determine qual grupo é mais adequado para classificá-lo.

DESCRIÇÃO DO PRODUTO:
"{descricao_produto}"

GRUPOS DISPONÍVEIS:
{chr(10).join(grupos_texto[:100])}

REGRAS DE CLASSIFICAÇÃO:
1. Materiais de construção (cimento, areia, tijolo, etc.) → Grupos com identificador "1" (Materiais)
2. Serviços → Grupos com identificador "2" (Serviços)
3. Mão de obra → Grupos com identificador "3" (Mão de Obra)
4. Produtos agrícolas/fazenda → Grupos com identificador "4" (Fazenda)
5. Se não souber, use o grupo mais genérico de materiais

IMPORTANTE: Analise o produto e escolha o grupo mais específico possível.

Responda APENAS em JSON com a estrutura:
{{
    "codigo_grupo": <número do código do grupo>,
    "justificativa": "<breve explicação da escolha>"
}}"""

        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um especialista em classificação de produtos para construção civil e materiais. Responda sempre em JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            resultado = json.loads(response.choices[0].message.content)
            codigo_escolhido = resultado.get('codigo_grupo')
            
            # Busca o grupo pelo código
            for g in grupos:
                if g['codigo'] == codigo_escolhido:
                    print(f"  🏷️  IA classificou no grupo: {g['descricao']} (código {codigo_escolhido})")
                    print(f"     Justificativa: {resultado.get('justificativa', 'N/A')}")
                    return {
                        "id": g.get('id'),
                        "codigo": g.get('codigo'),
                        "identificador": g.get('identificador'),
                        "descricao": g.get('descricao'),
                        "padrao": g.get('padrao', 1)
                    }
            
            # Se não encontrou, retorna o padrão
            print(f"  ⚠️ Grupo {codigo_escolhido} não encontrado, usando padrão")
            return self._selecionar_grupo_padrao()
            
        except Exception as e:
            print(f"  ⚠️ Erro na classificação por IA: {e}")
            return self._selecionar_grupo_padrao()
    
    def classificar_unidade_por_ia(self, descricao_produto: str) -> Optional[Dict]:
        """
        Usa IA para classificar a unidade mais adequada para o produto.
        
        Args:
            descricao_produto: Descrição do produto a ser classificado
            
        Returns:
            Dict com dados da unidade selecionada ou None se falhar
        """
        unidades = self._get_unidades()
        if not unidades or not self.provider_ia:
            return self._selecionar_unidade_padrao()
        
        # Monta lista de unidades para a IA analisar
        unidades_texto = []
        for u in unidades:
            unidades_texto.append(f"- {u['codigo']}: {u.get('descricao', u['codigo'])}")
        
        prompt = f"""Analise a descrição do produto e determine qual unidade de medida é mais adequada.

DESCRIÇÃO DO PRODUTO:
"{descricao_produto}"

UNIDADES DISPONÍVEIS:
{chr(10).join(unidades_texto)}

REGRAS DE CLASSIFICAÇÃO:
1. Produtos vendidos por peso (areia, brita, cimento a granel) → KG ou TON
2. Produtos em sacos (cimento, argamassa, cal) → SC (saco) ou UN
3. Produtos lineares (tubos, cabos, fios, barras) → M (metro) ou BR (barra)
4. Produtos de área (pisos, azulejos, telhas) → M2 (metro quadrado) ou UN
5. Produtos de volume (concreto, terra) → M3 (metro cúbico)
6. Líquidos (tintas, solventes, combustível) → L ou LT (litro) ou GL (galão)
7. Produtos contáveis individuais (parafusos, pregos, conexões) → UN (unidade) ou PCT/CX
8. Produtos em pares (luvas, botas) → PAR
9. Produtos em rolos (lonas, telas, fitas) → RL (rolo) ou M
10. Serviços → SV, H (hora), DIA (diária)
11. Se a descrição mencionar a unidade explicitamente, use essa
12. Na dúvida, use UN (unidade)

DICAS:
- "50KG" ou "SC 50KG" na descrição → SC ou KG
- "BARRA" ou "BR" na descrição → BR ou M
- "ROLO" na descrição → RL
- "LITRO" ou "L" na descrição → L ou LT
- "METRO" ou "M" na descrição → M
- "CAIXA" ou "CX" na descrição → CX
- "PACOTE" ou "PCT" na descrição → PCT

Responda APENAS em JSON com a estrutura:
{{
    "codigo_unidade": "<código da unidade>",
    "justificativa": "<breve explicação da escolha>"
}}"""

        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um especialista em classificação de produtos para construção civil e materiais. Responda sempre em JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            resultado = json.loads(response.choices[0].message.content)
            codigo_escolhido = str(resultado.get('codigo_unidade', '')).upper()
            
            # Busca a unidade pelo código
            for u in unidades:
                if str(u['codigo']).upper() == codigo_escolhido:
                    print(f"  📏 IA classificou unidade: {u.get('descricao', u['codigo'])} ({codigo_escolhido})")
                    print(f"     Justificativa: {resultado.get('justificativa', 'N/A')}")
                    return {
                        "id": u.get('id'),
                        "codigo": u.get('codigo'),
                        "padrao": u.get('padrao', 1)
                    }
            
            # Se não encontrou, retorna o padrão
            print(f"  ⚠️ Unidade '{codigo_escolhido}' não encontrada, usando UN")
            return self._selecionar_unidade_padrao()
            
        except Exception as e:
            print(f"  ⚠️ Erro na classificação de unidade por IA: {e}")
            return self._selecionar_unidade_padrao()
    
    def analisar(
        self,
        descricao_produto: str,
        codigo_fornecedor: Optional[str] = None,
        contexto: Optional[str] = None,
        auto_cadastrar: bool = False,
        debug: bool = False
    ) -> ResultadoAnalise:
        """
        Analisa um produto e retorna resultado estruturado.
        
        Args:
            descricao_produto: Descrição do produto (da nota fiscal)
            codigo_fornecedor: Código do produto no fornecedor
            contexto: Contexto adicional para IA
            auto_cadastrar: Se True, cadastra automaticamente quando necessário
            debug: Se True, imprime informações de debug
            
        Returns:
            ResultadoAnalise com ação requerida e dados
        """
        resultado = ResultadoAnalise(
            descricao_buscada=descricao_produto,
            codigo_fornecedor=codigo_fornecedor
        )
        
        try:
            # Busca no matcher híbrido
            matcher = self._get_matcher()
            busca = matcher.buscar(
                descricao_produto,
                limite=5,
                usar_ia=self.provider_ia is not None,
                contexto=contexto,
                debug=debug
            )
            
            # Analisa resultado
            if busca['melhor_match']:
                match = busca['melhor_match']
                score = match.get('score_final', match.get('score', 0))
                confianca = match.get('confianca', 'MEDIA')
                
                resultado.produto_encontrado = True
                resultado.similaridade = score
                resultado.confianca = confianca
                resultado.produto_match = match
                resultado.justificativa = match.get('justificativa', 
                    f"Match encontrado com score {score}%")
                
                # Se score for abaixo de 75%, cadastrar novo produto
                if score < 75:
                    resultado.acao = AcaoRequerida.CADASTRO_E_VINCULO
                    resultado.justificativa = f"Score {score}% abaixo de 75% - cadastrando novo produto"
                else:
                    # Match com boa confiança - apenas vincular
                    resultado.acao = AcaoRequerida.APENAS_VINCULO
                    resultado.justificativa = f"Match encontrado com score {score}% (≥75%)"
                    
            elif busca['sugestao_cadastro'] or not busca['resultados']:
                # Nenhum match - cadastrar novo
                resultado.produto_encontrado = False
                resultado.acao = AcaoRequerida.CADASTRO_E_VINCULO
                resultado.justificativa = "Produto não encontrado na base de dados"
                
            else:
                # Resultados com baixo score
                melhor = busca['resultados'][0] if busca['resultados'] else None
                if melhor:
                    score = melhor.get('score_final', melhor.get('score', 0))
                    resultado.similaridade = score
                    resultado.produto_match = melhor
                    
                    # Aplica mesma regra: abaixo de 75% cadastra novo
                    if score < 75:
                        resultado.acao = AcaoRequerida.CADASTRO_E_VINCULO
                        resultado.justificativa = f"Score {score}% abaixo de 75% - cadastrando novo produto"
                    else:
                        resultado.acao = AcaoRequerida.APENAS_VINCULO
                        resultado.justificativa = f"Match encontrado com score {score}% (≥75%)"
            
            # Prepara dados para cadastro se necessário
            if resultado.acao == AcaoRequerida.CADASTRO_E_VINCULO:
                # Usa IA para classificar o grupo adequado
                grupo_classificado = self.classificar_grupo_por_ia(descricao_produto)
                
                # Usa IA para classificar a unidade adequada
                unidade_classificada = self.classificar_unidade_por_ia(descricao_produto)
                
                dados = DadosCadastroProduto(
                    descricao=descricao_produto.upper().strip(),
                    descricaoNFe=descricao_produto.upper().strip(),
                    alternativo=codigo_fornecedor,
                    unidade=unidade_classificada,
                    grupo=grupo_classificado
                )
                resultado.dados_cadastro = dados.to_api_payload()
            
            # Auto cadastrar se solicitado
            if auto_cadastrar and resultado.acao == AcaoRequerida.CADASTRO_E_VINCULO:
                try:
                    novo_produto = self.api_client.post_produtos(resultado.dados_cadastro)
                    resultado.cadastro_realizado = True
                    resultado.produto_match = novo_produto
                    resultado.justificativa += " | Cadastro realizado com sucesso"
                except Exception as e:
                    resultado.erro = f"Erro no cadastro: {str(e)}"
                    resultado.cadastro_realizado = False
                    
        except Exception as e:
            resultado.erro = str(e)
            resultado.acao = AcaoRequerida.NENHUMA
            
        return resultado
    
    def analisar_lote(
        self,
        produtos: List[Dict],
        auto_cadastrar: bool = False,
        debug: bool = False
    ) -> List[ResultadoAnalise]:
        """
        Analisa um lote de produtos.
        
        Args:
            produtos: Lista de dicts com 'descricao' e opcionalmente 'codigo_fornecedor'
            auto_cadastrar: Se True, cadastra automaticamente
            debug: Se True, imprime informações de debug
            
        Returns:
            Lista de ResultadoAnalise
        """
        resultados = []
        
        for item in produtos:
            descricao = item.get('descricao', '')
            codigo = item.get('codigo_fornecedor')
            
            resultado = self.analisar(
                descricao_produto=descricao,
                codigo_fornecedor=codigo,
                auto_cadastrar=auto_cadastrar,
                debug=debug
            )
            resultados.append(resultado)
            
        return resultados


# ============================================================================
# FUNÇÕES AUXILIARES PARA INTEGRAÇÃO COM O FLUXO PRINCIPAL
# ============================================================================

def analisar_produto_para_vinculo(
    descricao: str,
    codigo_fornecedor: Optional[str] = None,
    auto_cadastrar: bool = False
) -> Dict:
    """
    Função simplificada para uso no fluxo principal.
    
    Retorna dict estruturado que pode ser interpretado pelo sistema.
    """
    analisador = AnalisadorProduto()
    resultado = analisador.analisar(
        descricao_produto=descricao,
        codigo_fornecedor=codigo_fornecedor,
        auto_cadastrar=auto_cadastrar
    )
    return resultado.to_dict()


def processar_itens_nota(
    itens: List[Dict],
    auto_cadastrar: bool = False
) -> Dict[str, Any]:
    """
    Processa todos os itens de uma nota fiscal.
    
    Args:
        itens: Lista de itens com 'descricao' e 'codigo_fornecedor'
        auto_cadastrar: Se True, cadastra produtos automaticamente
        
    Returns:
        {
            'resumo': {
                'total': int,
                'apenas_vinculo': int,
                'cadastro_e_vinculo': int,
                'erros': int
            },
            'itens': List[ResultadoAnalise como dict]
        }
    """
    analisador = AnalisadorProduto()
    resultados = analisador.analisar_lote(itens, auto_cadastrar=auto_cadastrar)
    
    resumo = {
        'total': len(resultados),
        'apenas_vinculo': sum(1 for r in resultados if r.acao == AcaoRequerida.APENAS_VINCULO),
        'cadastro_e_vinculo': sum(1 for r in resultados if r.acao == AcaoRequerida.CADASTRO_E_VINCULO),
        'erros': sum(1 for r in resultados if r.erro is not None)
    }
    
    return {
        'resumo': resumo,
        'itens': [r.to_dict() for r in resultados]
    }


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("TESTE DO ANALISADOR DE PRODUTOS")
    print("="*60)
    
    # Testa análise de um produto
    resultado = analisar_produto_para_vinculo(
        descricao="CERA ACRILICA RENKO 5L",
        codigo_fornecedor="FORN-001"
    )
    
    print("\nResultado da análise:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    print("\n" + "="*60)
    print(f"Ação requerida: {resultado['acao']}")
    print(f"Justificativa: {resultado['justificativa']}")
    
    if resultado['acao'] == 'cadastro_e_vinculo':
        print("\nDados para cadastro:")
        print(json.dumps(resultado['dados_cadastro'], indent=2, ensure_ascii=False))
