"""
Pré-Filtro Híbrido de Produtos v3.0

Arquitetura em 2 estágios:
1. PRÉ-FILTRO TRADICIONAL (v2.1) - Rápido, reduz universo para ~20 candidatos
2. ANÁLISE POR IA - Refina ranking com compreensão semântica profunda

Vantagens:
- Custo otimizado (IA só analisa candidatos pré-filtrados)
- Alta acurácia (IA entende contexto e variações)
- Fallback robusto (funciona mesmo sem IA)
"""

import re
import json
import pandas as pd
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from fuzzywuzzy import fuzz
from abc import ABC, abstractmethod
import os
import sys

# Adiciona diretório pai ao path para imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import PRODUTOS_CACHE


# ============================================================================
# CONFIGURAÇÃO DE PROVIDERS DE IA
# ============================================================================

@dataclass
class AnaliseIA:
    """Resultado da análise por IA."""
    codigo: str
    descricao: str
    score_ia: int  # 0-100
    confianca: str  # ALTA, MEDIA, BAIXA
    justificativa: str
    match_exato: bool
    sugestao_cadastro: bool


class ProviderIA(ABC):
    """Interface para providers de IA."""
    
    @abstractmethod
    def analisar_produtos(
        self,
        query: str,
        candidatos: List[Dict],
        contexto: Optional[str] = None
    ) -> List[AnaliseIA]:
        pass


class ProviderOpenAI(ProviderIA):
    """Provider usando OpenAI GPT."""
    
    def __init__(self, api_key: str, modelo: str = "gpt-4o-mini"):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.modelo = modelo
        except ImportError:
            raise ImportError("Instale: pip install openai")
    
    def analisar_produtos(
        self,
        query: str,
        candidatos: List[Dict],
        contexto: Optional[str] = None
    ) -> List[AnaliseIA]:
        prompt = self._montar_prompt(query, candidatos, contexto)
        
        response = self.client.chat.completions.create(
            model=self.modelo,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        return self._parse_response(response.choices[0].message.content)
    
    def _get_system_prompt(self) -> str:
        return """Você é um especialista em matching de produtos para construção civil, EPIs, materiais e insumos.

Sua tarefa é analisar uma descrição de produto buscada e uma lista de candidatos, retornando um ranking preciso.

REGRAS CRÍTICAS DE EQUIVALÊNCIA:
1. FOQUE NO PRODUTO ESSENCIAL, IGNORE DETALHES:
   - Marcas (MARLUVAS, VONDER, TRAMONTINA) → IGNORAR na comparação
   - Certificados (C.A 13808, INMETRO) → IGNORAR
   - Códigos de modelo (50B26, XYZ123) → IGNORAR  
   - Tamanhos/Numerações (N.42, TAM G, Nº 10) → IGNORAR (a menos que mude categoria)
   - Cores específicas → IGNORAR (a menos que seja essencial)

2. PRODUTOS EQUIVALENTES (DEVEM TER SCORE ALTO 80-95):
   - "BOTINA NOBUCK MARLUVAS C.A 13808 50B26 N.42" = "BOTINA DE COURO" = "BOTINA SEGURANÇA"
   - "LUVA NITRÍLICA DANNY TAMANHO M" = "LUVA DE PROTEÇÃO" = "LUVA SEGURANÇA"
   - "CAPACETE 3M H-700 BRANCO" = "CAPACETE DE SEGURANÇA" = "CAPACETE EPI"
   - "CIMENTO CP II 50KG VOTORAN" = "CIMENTO" = "CIMENTO PORTLAND"
   - "DISCO CORTE 7" BOSCH" = "DISCO DE CORTE" = "DISCO ESMERILHADEIRA"
   - "PARAFUSO SEXTAVADO GALV 3/8X1.1/2" = "PARAFUSO SEXTAVADO 3/8" = "PARAFUSO 3/8"
   - "FIO FLEXÍVEL 2,5MM VERMELHO 100M" = "FIO 2,5MM" = "CABO 2,5MM"

3. CATEGORIAS QUE DEVEM CASAR:
   - EPIs: botina/bota, luva, capacete, óculos, protetor auricular → mesmo tipo = equivalente
   - Fixadores: parafuso, prego, bucha → mesmo tipo/medida base = equivalente
   - Elétricos: fio, cabo, disjuntor → mesmo tipo/amperagem = equivalente
   - Construção: cimento, areia, tijolo, bloco → mesmo material = equivalente

4. MEDIDAS IMPORTANTES (afetam score):
   - Parafusos: 3/8 x 1" ≠ 1/4 x 2" (medidas diferentes = produtos diferentes)
   - Fios: 2,5mm ≠ 4mm (bitola diferente = produto diferente)
   - Volume: 5L ≈ 5LT, mas considere 18L se não houver 5L disponível

5. NUNCA CONFUNDIR CATEGORIAS DIFERENTES:
   - CERA ≠ TINTA (mesmo que tenha "cor giz de cera")
   - SABÃO ≠ DETERGENTE
   - BOTINA ≠ SAPATO SOCIAL

SCORES:
- 90-100: Match exato ou muito próximo (mesmo produto, pode variar marca/tamanho)
- 80-89: Equivalente funcional (mesmo tipo de produto, especificações similares)
- 70-79: Possível equivalente (mesmo categoria, especificações podem diferir)
- 50-69: Match parcial (relacionado mas pode não servir)
- 0-49: Não é o produto buscado

Responda SEMPRE em JSON com a estrutura:
{
  "analise": [
    {
      "codigo": "string",
      "score": 0-100,
      "confianca": "ALTA|MEDIA|BAIXA",
      "justificativa": "string curta",
      "match_exato": true|false
    }
  ],
  "sugestao_cadastro": true|false,
  "observacao": "string opcional"
}"""

    def _montar_prompt(self, query: str, candidatos: List[Dict], contexto: str) -> str:
        lista = "\n".join([
            f"- [{c['codigo']}] {c['descricao']} (score_pre: {c.get('score', 0)})"
            for c in candidatos
        ])
        
        prompt = f"""PRODUTO BUSCADO: "{query}"

CANDIDATOS PRÉ-FILTRADOS:
{lista}

Analise cada candidato e retorne o ranking ordenado por relevância."""
        
        if contexto:
            prompt += f"\n\nCONTEXTO ADICIONAL: {contexto}"
        
        return prompt
    
    def _parse_response(self, content: str) -> List[AnaliseIA]:
        try:
            data = json.loads(content)
            resultados = []
            
            for item in data.get("analise", []):
                resultados.append(AnaliseIA(
                    codigo=item["codigo"],
                    descricao="",  # Será preenchido depois
                    score_ia=item["score"],
                    confianca=item["confianca"],
                    justificativa=item["justificativa"],
                    match_exato=item.get("match_exato", False),
                    sugestao_cadastro=data.get("sugestao_cadastro", False)
                ))
            
            return resultados
        except Exception as e:
            print(f"[ERRO] Parse IA: {e}")
            return []


class ProviderAnthropic(ProviderIA):
    """Provider usando Anthropic Claude."""
    
    def __init__(self, api_key: str, modelo: str = "claude-sonnet-4-20250514"):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            self.modelo = modelo
        except ImportError:
            raise ImportError("Instale: pip install anthropic")
    
    def analisar_produtos(
        self,
        query: str,
        candidatos: List[Dict],
        contexto: Optional[str] = None
    ) -> List[AnaliseIA]:
        prompt = self._montar_prompt(query, candidatos, contexto)
        
        response = self.client.messages.create(
            model=self.modelo,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
            system=self._get_system_prompt()
        )
        
        # Extrai JSON da resposta
        content = response.content[0].text
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            return self._parse_response(json_match.group())
        return []
    
    def _get_system_prompt(self) -> str:
        return """Você é um especialista em matching de produtos para construção civil, EPIs e materiais.

REGRAS CRÍTICAS - FOQUE NO PRODUTO ESSENCIAL:
1. IGNORE: marcas, certificados (C.A), códigos, tamanhos, numerações, cores
2. "BOTINA NOBUCK MARLUVAS C.A 13808 N.42" = "BOTINA DE COURO" (score 85+)
3. "LUVA NITRÍLICA DANNY TAM M" = "LUVA DE PROTEÇÃO" (score 85+)
4. EPIs do mesmo tipo = equivalentes (botina=botina, luva=luva, capacete=capacete)
5. Parafusos: foque na medida base (3/8, 1/4), ignore detalhes
6. Fios/Cabos: foque na bitola (2,5mm, 4mm)

SCORES: 90-100=exato, 80-89=equivalente, 70-79=possível, <70=diferente

Responda APENAS com JSON válido:
{"analise":[{"codigo":"X","score":0-100,"confianca":"ALTA|MEDIA|BAIXA","justificativa":"...","match_exato":bool}],"sugestao_cadastro":bool}"""

    def _montar_prompt(self, query: str, candidatos: List[Dict], contexto: str) -> str:
        lista = "\n".join([
            f"[{c['codigo']}] {c['descricao']}"
            for c in candidatos[:15]  # Limita para economizar tokens
        ])
        return f'BUSCA: "{query}"\n\nCANDIDATOS:\n{lista}\n\nRetorne JSON com análise.'
    
    def _parse_response(self, content: str) -> List[AnaliseIA]:
        try:
            data = json.loads(content)
            return [
                AnaliseIA(
                    codigo=item["codigo"],
                    descricao="",
                    score_ia=item["score"],
                    confianca=item["confianca"],
                    justificativa=item["justificativa"],
                    match_exato=item.get("match_exato", False),
                    sugestao_cadastro=data.get("sugestao_cadastro", False)
                )
                for item in data.get("analise", [])
            ]
        except:
            return []


# ============================================================================
# PRÉ-FILTRO TRADICIONAL (mantido da v2.1)
# ============================================================================

class PreFiltroTradicional:
    """Pré-filtro rápido usando técnicas tradicionais."""
    
    PRODUTOS_PRINCIPAIS = {
        'CERA', 'SABAO', 'DETERGENTE', 'DESINFETANTE', 'LIMPA', 'LIMPADOR',
        'ALVEJANTE', 'AMACIANTE', 'SABONETE', 'SHAMPOO', 'ESPONJA', 'PANO',
        'VASSOURA', 'RODO', 'BALDE', 'ESCOVA', 'LUVA', 'SACO', 'LIXO',
        'MASSA', 'TINTA', 'VERNIZ', 'SELADOR', 'PRIMER', 'FUNDO', 'ESMALTE',
        'TEXTURA', 'REJUNTE', 'ARGAMASSA', 'CIMENTO', 'CAL', 'GESSO',
        'COLA', 'SILICONE', 'VEDANTE', 'IMPERMEABILIZANTE',
        'TUBO', 'CANO', 'CONEXAO', 'REGISTRO', 'TORNEIRA', 'VALVULA',
        'PAPEL', 'CANETA', 'LAPIS', 'BORRACHA', 'FITA', 'TESOURA',
        'OLEO', 'GRAXA', 'LUBRIFICANTE',
    }
    
    MODIFICADORES = {
        'ACRILICA', 'ACRILICO', 'SINTETICA', 'SINTETICO', 'LATEX',
        'LIQUIDO', 'LIQUIDA', 'PASTOSO', 'PASTOSA', 'PO', 'GEL', 'SPRAY',
        'PROFISSIONAL', 'PREMIUM', 'ECONOMICO', 'SUPER', 'MULTIUSO',
        'BRILHANTE', 'FOSCO', 'FOSCA', 'ACETINADO', 'TRANSPARENTE',
    }
    
    PREFIXOS_SECUNDARIOS = {'COR', 'TIPO', 'MODELO', 'LINHA', 'GIZ', 'TONS', 'TOM'}
    
    def __init__(self, df_produtos: pd.DataFrame):
        self.df = df_produtos.copy()
        self._preparar_indices()
    
    def _preparar_indices(self):
        # Garante que colunas são string
        self.df['PRO_ST_CODREAL'] = self.df['PRO_ST_CODREAL'].astype(str).str.strip()
        self.df['PRO_ST_DESCRICAO'] = self.df['PRO_ST_DESCRICAO'].astype(str).fillna('')
        
        self.df['_norm'] = (
            self.df['PRO_ST_DESCRICAO']
            .str.upper()
            .str.replace(r'[^\w\s]', ' ', regex=True)
            .str.replace(r'\s+', ' ', regex=True)
            .str.strip()
        )
        
        self.indice_tipo = {}
        self.tipo_cache = {}
        
        for idx, row in self.df.iterrows():
            tipo = self._identificar_tipo(row['_norm'])
            if tipo:
                self.tipo_cache[idx] = tipo
                self.indice_tipo.setdefault(tipo, []).append(idx)
    
    def _identificar_tipo(self, desc: str) -> Optional[str]:
        palavras = desc.split()
        for i, p in enumerate(palavras):
            p_limpa = re.sub(r'[^\w]', '', p)
            if p_limpa in self.PRODUTOS_PRINCIPAIS:
                if i >= 1 and re.sub(r'[^\w]', '', palavras[i-1]) in self.PREFIXOS_SECUNDARIOS:
                    continue
                if i >= 2 and palavras[i-1] == 'DE':
                    if re.sub(r'[^\w]', '', palavras[i-2]) in self.PREFIXOS_SECUNDARIOS:
                        continue
                return p_limpa
        return None
    
    def filtrar(self, query: str, limite: int = 20) -> List[Dict]:
        query_norm = query.upper().strip()
        
        # Match exato por código (coluna já é string após _preparar_indices)
        match_cod = self.df[self.df['PRO_ST_CODREAL'].str.upper().str.strip() == query_norm]
        if not match_cod.empty:
            return [self._to_dict(row, 100, 'codigo') for _, row in match_cod.iterrows()]
        
        # Identifica tipo da query
        tipo_query = self._identificar_tipo(query_norm)
        
        # Busca por tipo
        candidatos = pd.DataFrame()
        if tipo_query and tipo_query in self.indice_tipo:
            indices = self.indice_tipo[tipo_query]
            candidatos = self.df.loc[indices]
        
        # Expande se necessário
        if len(candidatos) < limite:
            palavras = [p for p in query_norm.split() if len(p) > 2]
            for p in palavras[:3]:
                mask = self.df['_norm'].str.contains(re.escape(p), na=False)
                extras = self.df[mask & ~self.df.index.isin(candidatos.index)]
                candidatos = pd.concat([candidatos, extras.head(limite)])
                if len(candidatos) >= limite * 2:
                    break
        
        # Scoring
        scores = []
        for idx, row in candidatos.iterrows():
            score = self._calcular_score(query_norm, row['_norm'], idx, tipo_query)
            scores.append((idx, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return [
            self._to_dict(self.df.loc[idx], score, 'fuzzy')
            for idx, score in scores[:limite]
            if score >= 30
        ]
    
    def _calcular_score(self, q: str, p: str, idx: int, tipo_q: str) -> int:
        base = (
            fuzz.token_sort_ratio(q, p) * 0.4 +
            fuzz.token_set_ratio(q, p) * 0.3 +
            fuzz.partial_ratio(q, p) * 0.3
        )
        
        tipo_p = self.tipo_cache.get(idx)
        if tipo_q and tipo_p:
            if tipo_p == tipo_q:
                base += 30
            else:
                base -= 50
        
        return int(min(100, max(0, base)))
    
    def _to_dict(self, row, score: int, metodo: str) -> Dict:
        return {
            'codigo': row['PRO_ST_CODREAL'],
            'descricao': row['PRO_ST_DESCRICAO'],
            'id': row.get('PRO_IN_CODIGO', ''),
            'grupo': row.get('GRU_IN_CODIGO', ''),
            'score': score,
            'metodo': metodo
        }


# ============================================================================
# ORQUESTRADOR HÍBRIDO
# ============================================================================

class MatcherHibrido:
    """
    Combina pré-filtro tradicional + análise por IA.
    
    Fluxo:
    1. Pré-filtro reduz universo para ~20 candidatos (rápido, grátis)
    2. IA analisa candidatos com compreensão semântica (preciso)
    3. Combina scores para ranking final
    """
    
    def __init__(
        self,
        df_produtos: pd.DataFrame,
        provider_ia: Optional[ProviderIA] = None,
        peso_prefiltro: float = 0.3,
        peso_ia: float = 0.7
    ):
        self.pre_filtro = PreFiltroTradicional(df_produtos)
        self.provider_ia = provider_ia
        self.peso_pre = peso_prefiltro
        self.peso_ia = peso_ia
        self.df = df_produtos
    
    def buscar(
        self,
        query: str,
        limite: int = 10,
        usar_ia: bool = True,
        contexto: Optional[str] = None,
        debug: bool = False
    ) -> Dict:
        """
        Busca produtos com matching híbrido.
        
        Returns:
            {
                'query': str,
                'resultados': List[Dict],
                'melhor_match': Dict or None,
                'sugestao_cadastro': bool,
                'metricas': Dict
            }
        """
        resultado = {
            'query': query,
            'resultados': [],
            'melhor_match': None,
            'sugestao_cadastro': False,
            'metricas': {}
        }
        
        # ESTÁGIO 1: Pré-filtro tradicional
        if debug:
            print(f"\n[ESTÁGIO 1] Pré-filtro para: '{query}'")
        
        candidatos = self.pre_filtro.filtrar(query, limite=20)
        resultado['metricas']['candidatos_prefiltro'] = len(candidatos)
        
        if not candidatos:
            resultado['sugestao_cadastro'] = True
            return resultado
        
        if debug:
            print(f"  -> {len(candidatos)} candidatos")
        
        # ESTÁGIO 2: Análise por IA (opcional)
        if usar_ia and self.provider_ia and len(candidatos) > 0:
            if debug:
                print(f"\n[ESTÁGIO 2] Análise por IA...")
            
            try:
                analises = self.provider_ia.analisar_produtos(
                    query, candidatos, contexto
                )
                
                # Mescla scores
                analise_map = {a.codigo: a for a in analises}
                
                for cand in candidatos:
                    cod = cand['codigo']
                    if cod in analise_map:
                        a = analise_map[cod]
                        cand['score_ia'] = a.score_ia
                        cand['confianca'] = a.confianca
                        cand['justificativa'] = a.justificativa
                        cand['match_exato'] = a.match_exato
                        
                        # Score combinado
                        cand['score_final'] = int(
                            cand['score'] * self.peso_pre +
                            a.score_ia * self.peso_ia
                        )
                    else:
                        cand['score_final'] = cand['score']
                
                # Verifica sugestão de cadastro
                if analises and analises[0].sugestao_cadastro:
                    resultado['sugestao_cadastro'] = True
                
                resultado['metricas']['ia_utilizada'] = True
                
            except Exception as e:
                if debug:
                    print(f"  [ERRO IA] {e} - usando apenas pré-filtro")
                for c in candidatos:
                    c['score_final'] = c['score']
                resultado['metricas']['ia_utilizada'] = False
        else:
            for c in candidatos:
                c['score_final'] = c['score']
            resultado['metricas']['ia_utilizada'] = False
        
        # Ordena por score final
        candidatos.sort(key=lambda x: x.get('score_final', 0), reverse=True)
        
        # Prepara resultado
        resultado['resultados'] = candidatos[:limite]
        
        if candidatos:
            melhor = candidatos[0]
            if melhor.get('score_final', 0) >= 70:
                resultado['melhor_match'] = melhor
            elif melhor.get('score_final', 0) < 50:
                resultado['sugestao_cadastro'] = True
        
        return resultado
    
    def buscar_batch(
        self,
        queries: List[str],
        usar_ia: bool = True
    ) -> List[Dict]:
        """Busca múltiplos produtos."""
        return [self.buscar(q, usar_ia=usar_ia) for q in queries]


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

def exemplo_uso():
    """Demonstração do sistema híbrido."""
    import os
    
    # Carrega produtos (exemplo)
    try:
        df = pd.read_excel(PRODUTOS_CACHE)
        
        # Mapeia colunas (flexível para diferentes formatos)
        col_map = {
            'codigo': 'PRO_ST_CODREAL',
            'descricao': 'PRO_ST_DESCRICAO',
            'id': 'PRO_IN_CODIGO'
        }
        
        for old, new in col_map.items():
            if old in df.columns and new not in df.columns:
                df[new] = df[old]
        
        # Garante tipos corretos
        df['PRO_ST_CODREAL'] = df['PRO_ST_CODREAL'].astype(str).str.strip()
        df['PRO_ST_DESCRICAO'] = df['PRO_ST_DESCRICAO'].astype(str).fillna('')
        
        if 'PRO_IN_CODIGO' not in df.columns:
            df['PRO_IN_CODIGO'] = range(len(df))
        
        print(f"[OK] Carregados {len(df)} produtos do Excel")
        
    except Exception as e:
        print(f"[INFO] Erro ao carregar Excel ({e}), usando dados de exemplo")
        # Dados de exemplo
        df = pd.DataFrame({
            'PRO_ST_CODREAL': ['001', '002', '003', '004', '005'],
            'PRO_ST_DESCRICAO': [
                'CERA ACRILICA RENKO 5L',
                'TINTA ACRILICA COR GIZ DE CERA 18L',
                'CERA LIQUIDA PREMIUM 5 LITROS',
                'SABAO EM BARRA YPE 5X1',
                'MASSA ACRILICA SUVINIL 18L'
            ],
            'PRO_IN_CODIGO': [1, 2, 3, 4, 5]
        })
    
    # Configura provider (escolha um)
    provider = None
    
    # OpenAI
    if os.getenv('OPENAI_API_KEY'):
        provider = ProviderOpenAI(os.getenv('OPENAI_API_KEY'))
        print("[OK] Usando OpenAI GPT-4o-mini")
    
    # Anthropic
    elif os.getenv('ANTHROPIC_API_KEY'):
        provider = ProviderAnthropic(os.getenv('ANTHROPIC_API_KEY'))
        print("[OK] Usando Anthropic Claude")
    
    else:
        print("[INFO] Sem API key - usando apenas pré-filtro")
    
    # Inicializa matcher
    matcher = MatcherHibrido(df, provider_ia=provider)
    
    # Testes
    queries = [
        "CERA ACRILICA RENKO 5 LITROS",
        "TINTA COR CERA",
        "SABAO BARRA YPE",
    ]
    
    for q in queries:
        print(f"\n{'='*60}")
        print(f"BUSCA: {q}")
        print('='*60)
        
        resultado = matcher.buscar(q, limite=5, debug=True)
        
        print(f"\nRESULTADOS:")
        for i, r in enumerate(resultado['resultados'], 1):
            score_info = f"Pre:{r['score']}"
            if 'score_ia' in r:
                score_info += f" IA:{r['score_ia']} Final:{r['score_final']}"
            print(f"  {i}. [{score_info}] {r['codigo']} - {r['descricao']}")
            if 'justificativa' in r:
                print(f"      └─ {r['justificativa']}")
        
        if resultado['melhor_match']:
            print(f"\n✓ MELHOR MATCH: {resultado['melhor_match']['codigo']}")
        elif resultado['sugestao_cadastro']:
            print(f"\n⚠ SUGESTÃO: Cadastrar novo produto")


if __name__ == "__main__":
    exemplo_uso()