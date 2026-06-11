"""
Módulo 02 — Analista de Conteúdo
Cálculo determinístico do Índice de Qualidade Didática e Veredito.

PRINCÍPIO: A IA (Agente E) atribui notas; este módulo faz a conta.
           Aritmética pura, auditável e testável — sem IA.
"""

# =============================================================================
# PESOS — DECISÃO INSTITUCIONAL (não empírica)
# =============================================================================
# Os pesos refletem a prioridade pedagógica da UNIGRAN EAD.
# B3 (Estrutura) tem maior peso porque o alinhamento entre objetivos,
# conteúdo e avaliação é o fator que mais impacta a aprendizagem (Biggs, 1996).

PESOS = {
    "B1": 0.20,  # Dialogicidade — peso 20%
    "B2": 0.15,  # Densidade — peso 15%
    "B3": 0.30,  # Estrutura — peso 30%
    "B4": 0.15,  # Engajamento — peso 15%
    "B5": 0.20,  # Legibilidade — peso 20%
}

INDICADORES_OBRIGATORIOS = frozenset(PESOS.keys())  # {"B1", "B2", "B3", "B4", "B5"}

# =============================================================================
# CONSTANTES DE SEVERIDADE
# =============================================================================
SEVERIDADE_VALIDAS = frozenset({"SEM_RESSALVA", "RESSALVA", "CRITICO"})

# =============================================================================
# TABELA DE VEREDITOS (4 faixas)
# =============================================================================
# Regra em cascata: usa >= para definir faixas, sem teto fixo.
# Override: qualquer CRÍTICO em A1 ou A2 → RECRIAR, independente do índice.

VEREDITOS = [
    {
        "faixa": "APROVAR",
        "emoji": "🟢",
        "minimo": 8.0,
        "rotulo": "Aprovar",
        "acao_coordenador": "Libera para diagramação",
    },
    {
        "faixa": "APROVAR_COM_RESSALVA",
        "emoji": "🟡",
        "minimo": 6.5,
        "rotulo": "Aprovar com ressalva",
        "acao_coordenador": "Libera com relatório de ajustes",
    },
    {
        "faixa": "INTERVENCAO_EDITORIAL",
        "emoji": "🟠",
        "minimo": 5.0,
        "rotulo": "Intervenção editorial",
        "acao_coordenador": "Decide: edita ou devolve ao autor",
    },
    {
        "faixa": "RECRIAR",
        "emoji": "🔴",
        "minimo": 0.0,
        "rotulo": "Recriar",
        "acao_coordenador": "Retorna ao autor com parecer",
    },
]


def validar_notas(notas: dict) -> list:
    """
    Valida estrutura e valores das notas B1–B5.

    Regras:
    - Exatamente 5 indicadores: B1, B2, B3, B4, B5 (nem mais, nem menos)
    - Cada nota deve ser número (int ou float) entre 0 e 10

    Parameters
    ----------
    notas : dict
        Dicionário com as notas dos indicadores.

    Returns
    -------
    list
        Lista de erros (vazia se válido).
    """
    erros = []

    # Verifica indicadores obrigatórios
    indicadores_recebidos = set(notas.keys())
    faltantes = INDICADORES_OBRIGATORIOS - indicadores_recebidos
    extras = indicadores_recebidos - INDICADORES_OBRIGATORIOS

    if faltantes:
        erros.append(f"Indicadores faltando: {', '.join(sorted(faltantes))}")
    if extras:
        erros.append(f"Indicadores extras não permitidos: {', '.join(sorted(extras))}")

    # Verifica valores das notas
    for indicador, nota in notas.items():
        if indicador not in INDICADORES_OBRIGATORIOS:
            continue  # já reportado acima
        if not isinstance(nota, (int, float)):
            erros.append(f"{indicador}: nota deve ser número, recebido {type(nota).__name__}")
        elif not (0 <= nota <= 10):
            erros.append(f"{indicador}: nota deve estar entre 0 e 10, recebido {nota}")

    return erros


def validar_severidade(a1: str, a2: str) -> list:
    """
    Valida valores de severidade de A1 e A2.

    Valores válidos: SEM_RESSALVA | RESSALVA | CRITICO

    Parameters
    ----------
    a1 : str
        Severidade de A1.
    a2 : str
        Severidade de A2.

    Returns
    -------
    list
        Lista de erros (vazia se válido).
    """
    erros = []

    if a1 not in SEVERIDADE_VALIDAS:
        erros.append(f"A1: severidade inválida '{a1}' — válido: {SEVERIDADE_VALIDAS}")
    if a2 not in SEVERIDADE_VALIDAS:
        erros.append(f"A2: severidade inválida '{a2}' — válido: {SEVERIDADE_VALIDAS}")

    return erros


def calcular_indice(notas: dict) -> dict:
    """
    Calcula o Índice de Qualidade Didática (0–10).

    Aritmética pura: cada nota B1–B5 é multiplicada pelo seu peso.
    O índice é a soma das contribuições, arredondado para 2 casas.

    Parameters
    ----------
    notas : dict
        Dicionário com as notas dos 5 indicadores.
        Ex: {"B1": 8.0, "B2": 7.0, "B3": 6.0, "B4": 8.0, "B5": 7.5}

    Returns
    -------
    dict
        Dicionário com:
        - contribuicoes: contribuição de cada indicador (nota × peso)
        - indice: soma das contribuições (arredondado 2 casas)

    Raises
    ------
    ValueError
        Se as notas não passarem na validação.
    """
    # Validação estrita antes de calcular
    erros = validar_notas(notas)
    if erros:
        raise ValueError(f"Notas inválidas: {'; '.join(erros)}")

    contribuicoes = {}
    indice = 0.0

    for indicador, nota in notas.items():
        peso = PESOS.get(indicador, 0.0)
        contribuicao = nota * peso
        contribuicoes[indicador] = round(contribuicao, 2)
        indice += contribuicao

    return {
        "contribuicoes": contribuicoes,
        "indice": round(indice, 2),
    }


def determinar_veredito(indice: float, a1: str, a2: str) -> dict:
    """
    Aplica a regra das 4 faixas + override por CRÍTICO.

    Regra em cascata (usa >=, sem teto fixo):
      - Índice >= 8,0 → APROVAR
      - Índice >= 6,5 → APROVAR_COM_RESSALVA (cobre 6,5 a 7,99)
      - Índice >= 5,0 → INTERVENCAO_EDITORIAL (cobre 5,0 a 6,49)
      - Índice <  5,0 → RECRIAR

    Override: Se A1 == CRITICO ou A2 == CRITICO → RECRIAR (independe do índice)

    Parameters
    ----------
    indice : float
        Índice de Qualidade Didática calculado (0–10).
    a1 : str
        Severidade de A1 (Precisão Conceitual): SEM_RESSALVA | RESSALVA | CRITICO
    a2 : str
        Severidade de A2 (Validade Bibliográfica): SEM_RESSALVA | RESSALVA | CRITICO

    Returns
    -------
    dict
        Dicionário com:
        - faixa: identificador interno (ex: "APROVAR_COM_RESSALVA")
        - emoji: símbolo visual (🟢 🟡 🟠 🔴)
        - rotulo: nome legível da faixa
        - acao_coordenador: ação recomendada
    """
    # Override: qualquer CRÍTICO nos fundamentos → RECRIAR
    if a1 == "CRITICO" or a2 == "CRITICO":
        return {
            "faixa": "RECRIAR",
            "emoji": "🔴",
            "rotulo": "Recriar",
            "acao_coordenador": "Retorna ao autor com parecer (fundamento crítico)",
        }

    # Regra em cascata: usa >= para definir faixas
    for veredito in VEREDITOS:
        if indice >= veredito["minimo"]:
            return {
                "faixa": veredito["faixa"],
                "emoji": veredito["emoji"],
                "rotulo": veredito["rotulo"],
                "acao_coordenador": veredito["acao_coordenador"],
            }

    # Fallback (não deve ocorrer, pois a última faixa tem minimo=0.0)
    return VEREDITOS[-1]


def avaliar(notas: dict, a1: str, a2: str) -> dict:
    """
    Combina índice + veredito num laudo estruturado completo.

    Esta é a função principal do módulo — chama as duas anteriores
    e monta um laudo legível para o coordenador.

    Parameters
    ----------
    notas : dict
        Dicionário com as notas dos 5 indicadores (B1–B5).
    a1 : str
        Severidade de A1 (Precisão Conceitual).
    a2 : str
        Severidade de A2 (Validade Bibliográfica).

    Returns
    -------
    dict
        Laudo estruturado com:
        - indice: resultado de calcular_indice()
        - veredito: resultado de determinar_veredito()
        - laudo: texto formatado para leitura humana
        - valido: True se avaliação é válida, False caso contrário
        - erros: lista de erros de validação (vazia se válido)

    Raises
    ------
    ValueError
        Se as notas ou severidades não passarem na validação.
    """
    # Validação estrita de entradas
    erros_notas = validar_notas(notas)
    erros_severidade = validar_severidade(a1, a2)
    todos_erros = erros_notas + erros_severidade

    if todos_erros:
        return {
            "valido": False,
            "erros": todos_erros,
            "indice": None,
            "veredito": None,
            "laudo": f" Avaliação inválida: {'; '.join(todos_erros)}",
        }

    resultado_indice = calcular_indice(notas)
    veredito = determinar_veredito(
        indice=resultado_indice["indice"], a1=a1, a2=a2
    )

    # Monta laudo legível
    laudo = []
    laudo.append("=" * 60)
    laudo.append("RELATÓRIO DE AVALIAÇÃO — MÓDULO 02 (ANALISTA DE CONTEÚDO)")
    laudo.append("=" * 60)
    laudo.append("")
    laudo.append("FUNDAMENTOS (verificação de integridade)")
    laudo.append(f"  A1 — Precisão Conceitual: {a1}")
    laudo.append(f"  A2 — Validade Bibliográfica: {a2}")
    laudo.append("")
    laudo.append("ÍNDICE DE QUALIDADE DIDÁTICA (0–10)")
    for indicador, contribuicao in resultado_indice["contribuicoes"].items():
        nota = notas.get(indicador, 0)
        peso = PESOS.get(indicador, 0)
        laudo.append(f"  {indicador} = {nota} × {peso:.2f} = {contribuicao:.2f}")
    laudo.append(f"  ÍNDICE TOTAL: {resultado_indice['indice']:.2f}")
    laudo.append("")
    laudo.append("VEREDITO")
    laudo.append(f"  {veredito['emoji']} {veredito['rotulo']}")
    laudo.append(f"  Ação: {veredito['acao_coordenador']}")
    laudo.append("")
    laudo.append("=" * 60)

    return {
        "valido": True,
        "erros": [],
        "indice": resultado_indice,
        "veredito": veredito,
        "laudo": "\n".join(laudo),
    }


# =============================================================================
# CLI — execução direta para testes rápidos
# =============================================================================
if __name__ == "__main__":
    # Exemplo de uso
    notas_exemplo = {
        "B1": 8.0,
        "B2": 7.0,
        "B3": 6.0,
        "B4": 8.0,
        "B5": 7.5,
    }
    a1_exemplo = "SEM_RESSALVA"
    a2_exemplo = "SEM_RESSALVA"

    resultado = avaliar(notas_exemplo, a1_exemplo, a2_exemplo)
    print(resultado["laudo"])
