#!/usr/bin/env python3
"""
03-agente-e.py — Avalia qualidade didática do material e gera laudo.

Módulo 02 — Analista de Conteúdo (Agente E)
Modelo: claude-opus-4-7

Recebe:
  - 02_markdown/{ID}.md (texto bruto da aula)
  - Contexto: curso, disciplina, aula

Gera:
  - 03_avaliacao/avaliacao_v01.md (laudo completo)
  - 03_avaliacao/score_v01.json (dados estruturados)
  - _incubadora/ (se veredito = RECRIAR)

Uso:
  python3 scripts/03-agente-e.py \\
      --codigo ADM \\
      --disciplina "Fundamentos de Administração" \\
      --aula 1 \\
      --curso "administracao"
"""
import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from lib import pastas, logger

# Importa módulo de cálculo (aritmética pura)
sys.path.insert(0, str(Path(__file__).parent.parent / "modulo02"))
from calculo import avaliar as calcular_score


def carregar_config() -> dict:
    cfg_path = Path(__file__).parent / "config.yml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def carregar_markdown_aula(pasta_aula: Path) -> str:
    """Carrega o markdown extraído pelo M01."""
    md_dir = pasta_aula / "02_markdown"
    if not md_dir.exists():
        raise FileNotFoundError(f"Pasta 02_markdown não encontrada em {pasta_aula}")

    md_files = list(md_dir.glob("*.md"))
    if not md_files:
        raise FileNotFoundError(f"Nenhum arquivo .md em {md_dir}")

    return md_files[0].read_text(encoding="utf-8")


def avaliar_com_ia(texto: str, aula_id: str) -> dict:
    """
    Chama o Agente E (claude-opus-4-7) para avaliar o material.

    Retorna o JSON de notas com fundamentos (A1, A2) e indicadores (B1-B5).
    """
    # Esta função será implementada com a chamada real à API
    # Por enquanto, retorna estrutura placeholder para desenvolvimento

    print("\n🔍 Agente E — Avaliando material...")
    print(f"   Aula: {aula_id}")
    print(f"   Texto: {len(texto)} caracteres")
    print("\n   ⚠️  Implementação da chamada API pendente")
    print("   Usando dados de exemplo para demonstração...\n")

    # Placeholder - será substituído pela chamada real
    return {
        "fundamentos": {
            "A1": {
                "severidade": "SEM_RESSALVA",
                "justificativa": "Conceitos corretos e atualizados.",
                "trecho": "Exemplo de trecho..."
            },
            "A2": {
                "severidade": "SEM_RESSALVA",
                "justificativa": "Referências localizáveis.",
                "fontes_verificadas": []
            }
        },
        "indicadores": {
            "B1": {"nota": 7.0, "justificativa": "Tom adequado, mas poderia interpelar mais o aluno."},
            "B2": {"nota": 6.5, "justificativa": "Densidade aceitável, alguns trechos concentrados."},
            "B3": {"nota": 7.5, "justificativa": "Estrutura pedagógica clara com objetivos e fechamento."},
            "B4": {"nota": 6.0, "justificativa": "Exemplos presentes, mas genéricos."},
            "B5": {"nota": 8.0, "justificativa": "Hierarquia clara, parágrafos bem dimensionados."}
        }
    }


def gerar_laudo_markdown(aula_id: str, resultado_ia: dict, score: dict) -> str:
    """Gera o laudo em formato Markdown para leitura humana."""
    linhas = []

    linhas.append("# Laudo de Avaliação — Módulo 02")
    linhas.append(f"**Aula:** {aula_id}")
    linhas.append(f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    linhas.append("")

    # Veredito em destaque
    emoji = score["veredito"]["emoji"]
    rotulo = score["veredito"]["rotulo"]
    linhas.append(f"## {emoji} Veredito: {rotulo}")
    linhas.append(f"**Índice de Qualidade Didática:** {score['indice']:.2f}")
    linhas.append("")
    linhas.append(f"**Ação recomendada:** {score['veredito']['acao_coordenador']}")
    linhas.append("")

    # Fundamentos
    linhas.append("## Fundamentos (Verificação de Integridade)")
    linhas.append("")
    linhas.append("### A1 — Precisão Conceitual e Científica")
    a1 = resultado_ia["fundamentos"]["A1"]
    linhas.append(f"**Severidade:** {a1['severidade']}")
    linhas.append(f"**Justificativa:** {a1['justificativa']}")
    if a1.get("trecho"):
        linhas.append(f"**Trecho relacionado:** `{a1['trecho'][:100]}...`")
    linhas.append("")

    linhas.append("### A2 — Validade Bibliográfica e Fontes")
    a2 = resultado_ia["fundamentos"]["A2"]
    linhas.append(f"**Severidade:** {a2['severidade']}")
    linhas.append(f"**Justificativa:** {a2['justificativa']}")
    if a2.get("fontes_verificadas"):
        linhas.append("**Fontes verificadas:**")
        for fonte in a2["fontes_verificadas"]:
            status = "✅" if fonte["status"] == "confirmada" else "⚠️"
            linhas.append(f"  {status} {fonte['autor']} ({fonte['ano']}) — {fonte['obra']} [{fonte['status']}]")
    linhas.append("")

    # Indicadores
    linhas.append("## Indicadores de Qualidade Didática")
    linhas.append("")
    linhas.append("| Indicador | Nota | Peso | Contribuição |")
    linhas.append("|-----------|------|------|--------------|")

    pesos = {"B1": 0.20, "B2": 0.15, "B3": 0.30, "B4": 0.15, "B5": 0.20}
    for ind in ["B1", "B2", "B3", "B4", "B5"]:
        dados = resultado_ia["indicadores"][ind]
        peso = pesos[ind]
        contribuicao = dados["nota"] * peso
        linhas.append(f"| {ind} | {dados['nota']:.1f} | {peso:.2f} | {contribuicao:.2f} |")

    linhas.append(f"| **TOTAL** | — | **1.00** | **{score['indice']:.2f}** |")
    linhas.append("")

    # Detalhamento por indicador
    for ind in ["B1", "B2", "B3", "B4", "B5"]:
        dados = resultado_ia["indicadores"][ind]
        nomes = {
            "B1": "Dialogicidade / Tom EAD",
            "B2": "Densidade Conceitual",
            "B3": "Estrutura Pedagógica",
            "B4": "Engajamento",
            "B5": "Legibilidade Autoral"
        }
        linhas.append(f"### {ind} — {nomes[ind]}")
        linhas.append(f"**Nota:** {dados['nota']:.1f}")
        linhas.append(f"**Justificativa:** {dados['justificativa']}")
        linhas.append("")

    # Rodapé
    linhas.append("---")
    linhas.append("")
    linhas.append("> **Nota:** O módulo recomenda. O coordenador decide.")
    linhas.append("> ")
    linhas.append("> Este laudo é gerado automaticamente pelo Agente E (claude-opus-4-7)")
    linhas.append("> com cálculo determinístico via `modulo02/calculo.py`.")

    return "\n".join(linhas)


def criar_incubadora(pasta_aula: Path, score: dict, laudo_md: str):
    """Cria pasta _incubadora/ quando veredito = RECRIAR."""
    incubadora = pasta_aula / "_incubadora"
    historico = incubadora / "historico"
    material_atualizado = incubadora / "material_atualizado"

    incubadora.mkdir(parents=True, exist_ok=True)
    historico.mkdir(exist_ok=True)
    material_atualizado.mkdir(exist_ok=True)

    # Registra laudo na incubadora
    (incubadora / "laudo_recuperacao.md").write_text(laudo_md, encoding="utf-8")

    # Registra motivo
    motivo = {
        "data": datetime.now().isoformat(),
        "veredito": score["veredito"]["faixa"],
        "indice": score["indice"],
        "fundamentos": score["fundamentos"],
        "motivo": "Material enviado para _incubadora devido ao veredito RECRIAR."
    }
    (incubadora / "motivo.json").write_text(
        json.dumps(motivo, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"   📁 _incubadora/ criada em {incubadora}")


def agente_e(
    codigo: str,
    disciplina: str,
    aula: int,
    curso: str = "EAD",
    forcar: bool = False,
) -> dict:
    """
    Executa o Agente E — avaliação de qualidade didática.

    Returns
    -------
    dict
        Resultado com status e caminhos dos arquivos gerados.
    """
    cfg = carregar_config()
    raiz = Path(cfg["raiz"]).expanduser()

    # Estrutura de pastas
    pasta_aula = pastas.criar_estrutura(
        raiz, codigo, disciplina, aula, cfg["subpastas"], curso
    )
    aula_id = pastas.id_aula(codigo, aula)

    print(f"\n{'='*60}")
    print(f"MÓDULO 02 — ANALISTA DE CONTEÚDO (Agente E)")
    print(f"{'='*60}")
    print(f"Aula: {aula_id}")
    print(f"Disciplina: {disciplina}")
    print(f"Curso: {curso}")
    print(f"Pasta: {pasta_aula}")

    # Verifica se já existe avaliação
    pasta_avaliacao = pasta_aula / "03_avaliacao"
    score_existente = sorted(pasta_avaliacao.glob("score_v*.json")) if pasta_avaliacao.exists() else []

    if score_existente and not forcar:
        print(f"\n   ⏭  {aula_id} já possui avaliação — pulando (use --forcar para reavaliar)")
        return {
            "ok": True,
            "aviso": "Aula já avaliada",
            "score_path": str(score_existente[-1]),
        }

    # Cria pasta de avaliação
    pasta_avaliacao.mkdir(parents=True, exist_ok=True)

    # Carrega markdown
    try:
        texto = carregar_markdown_aula(pasta_aula)
    except FileNotFoundError as e:
        print(f"\n   ⚠️  {e}")
        return {
            "ok": False,
            "erro": str(e),
            "sugestao": "Execute o Módulo 01 (Extrator) primeiro."
        }

    # Avalia com IA
    resultado_ia = avaliar_com_ia(texto, aula_id)

    # Extrai notas para cálculo
    notas = {
        ind: dados["nota"]
        for ind, dados in resultado_ia["indicadores"].items()
    }
    a1 = resultado_ia["fundamentos"]["A1"]["severidade"]
    a2 = resultado_ia["fundamentos"]["A2"]["severidade"]

    # Calcula índice e veredito (aritmética pura)
    score = calcular_score(notas, a1, a2)

    # Gera laudo Markdown
    laudo_md = gerar_laudo_markdown(aula_id, resultado_ia, score)

    # Monta score JSON completo
    score_json = {
        "aula_id": aula_id,
        "disciplina": disciplina,
        "curso": curso,
        "data_avaliacao": datetime.now().isoformat(),
        "indice": score["indice"],
        "veredito": {
            "faixa": score["veredito"]["faixa"],
            "emoji": score["veredito"]["emoji"],
            "rotulo": score["veredito"]["rotulo"],
            "acao_coordenador": score["veredito"]["acao_coordenador"],
        },
        "fundamentos": resultado_ia["fundamentos"],
        "indicadores": resultado_ia["indicadores"],
        "contribuicoes": score["indice"]["contribuicoes"],
    }

    # Salva arquivos
    versao = "v01"
    (pasta_avaliacao / f"avaliacao_{versao}.md").write_text(laudo_md, encoding="utf-8")
    (pasta_avaliacao / f"score_{versao}.json").write_text(
        json.dumps(score_json, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"\n   ✅ Laudo gerado: {pasta_avaliacao / f'avaliacao_{versao}.md'}")
    print(f"   ✅ Score JSON: {pasta_avaliacao / f'score_{versao}.json'}")
    print(f"\n   📊 Índice: {score['indice']:.2f}")
    print(f"   {'='*60}")
    print(f"   {score['veredito']['emoji']} {score['veredito']['rotulo']}")
    print(f"   {score['veredito']['acao_coordenador']}")
    print(f"   {'='*60}")

    # Cria incubadora se necessário
    if score["veredito"]["faixa"] == "RECRIAR":
        criar_incubadora(pasta_aula, score_json, laudo_md)

    # Registra no log
    logger.registrar(pasta_aula, {
        "modulo": "M02",
        "agente": "E",
        "modelo": "claude-opus-4-7",
        "indice": score["indice"],
        "veredito": score["veredito"]["faixa"],
        "score_path": str(pasta_avaliacao / f"score_{versao}.json"),
        "laudo_path": str(pasta_avaliacao / f"avaliacao_{versao}.md"),
    })

    return {
        "ok": True,
        "aula_id": aula_id,
        "indice": score["indice"],
        "veredito": score["veredito"]["faixa"],
        "emoji": score["veredito"]["emoji"],
        "score_path": str(pasta_avaliacao / f"score_{versao}.json"),
        "laudo_path": str(pasta_avaliacao / f"avaliacao_{versao}.md"),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Módulo 02 — Avalia qualidade didática do material"
    )
    parser.add_argument("--codigo", required=True, help="Código da disciplina (ex: ADM)")
    parser.add_argument("--disciplina", required=True, help="Nome da disciplina")
    parser.add_argument("--aula", required=True, type=int, help="Número da aula")
    parser.add_argument("--curso", default="EAD", help="Nome do curso")
    parser.add_argument("--forcar", action="store_true", help="Reavaliar se já existir score")

    args = parser.parse_args()

    resultado = agente_e(
        args.codigo,
        args.disciplina,
        args.aula,
        args.curso,
        args.forcar,
    )

    print()
    if resultado.get("ok"):
        if resultado.get("aviso"):
            print(f"⚠️  {resultado['aviso']}")
        else:
            print(f"✅ Avaliação concluída: {resultado['emoji']} {resultado['veredito']}")
            print(f"   Score: {resultado['score_path']}")
    else:
        print(f"⚠️  {resultado.get('erro', 'Erro desconhecido')}")
        if resultado.get("sugestao"):
            print(f"   Sugestão: {resultado['sugestao']}")


if __name__ == "__main__":
    main()
