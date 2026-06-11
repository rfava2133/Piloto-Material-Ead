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
  - 07_incubadora/ (se veredito = RECRIAR)

Uso:
  python3 scripts/03-agente-e.py \\
      --codigo ADM \\
      --disciplina "Fundamentos de Administração" \\
      --aula 1 \\
      --curso "administracao"
"""
import argparse
import json
import os
import shutil
import subprocess
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


def avaliar_com_ollama(texto: str, aula_id: str, disciplina: str, curso: str, modelo: str = "codex") -> tuple:
    """
    Fallback local: chama modelo Ollama para avaliação quando skill está indisponível.

    Returns
    -------
    tuple
        (sucesso: bool, resultado: dict ou erro: str)
    """
    print(f"\n   🤖 Usando Ollama ({modelo}) como fallback...")

    prompt = f"""Você é o Agente E — Analista de Conteúdo para material EAD.
Avalie o material didático abaixo e retorne APENAS JSON válido com esta estrutura:

{{
  "fundamentos": {{
    "A1": {{"severidade": "SEM_RESSALVA|RESSALVA|CRITICO", "justificativa": "...", "trecho": "..."}},
    "A2": {{"severidade": "SEM_RESSALVA|RESSALVA|CRITICO", "justificativa": "...", "fontes_verificadas": []}}
  }},
  "indicadores": {{
    "B1": {{"nota": 0-10, "justificativa": "..."}},
    "B2": {{"nota": 0-10, "justificativa": "..."}},
    "B3": {{"nota": 0-10, "justificativa": "..."}},
    "B4": {{"nota": 0-10, "justificativa": "..."}},
    "B5": {{"nota": 0-10, "justificativa": "..."}}
  }}
}}

Critérios:
- B1 (Dialogicidade): Tom conversacional, perguntas ao aluno, conexão com realidade EAD
- B2 (Densidade): Conceitos sem empilhamento, exemplos intercalados
- B3 (Estrutura): Objetivos claros, progressão lógica, fechamento
- B4 (Engajamento): Exemplos atuais, estudos de caso, analogias
- B5 (Legibilidade): Hierarquia visual, parágrafos curtos, figuras legendadas

A1: Precisão conceitual e científica
A2: Validade bibliográfica e fontes

Material para avaliação:
Curso: {curso}
Disciplina: {disciplina}
Aula: {aula_id}

---
{texto[:30000]}
---

Retorne apenas o JSON, sem markdown ou explicações."""

    try:
        result = subprocess.run(
            ["ollama", "run", modelo, prompt],
            capture_output=True,
            text=True,
            timeout=180,
        )

        if result.returncode != 0:
            return (False, f"Ollama falhou: {result.stderr}")

        output = result.stdout.strip()

        # Extrai JSON do output
        import re
        json_match = re.search(r'\{.*\}', output, re.DOTALL)
        if not json_match:
            return (False, f"Ollama não retornou JSON: {output[:200]}")

        dados = json.loads(json_match.group(0))

        # Valida estrutura mínima
        if "fundamentos" not in dados or "indicadores" not in dados:
            return (False, "JSON sem estrutura required")

        # Normaliza severidades
        for key in ["A1", "A2"]:
            sev = dados["fundamentos"][key].get("severidade", "SEM_RESSALVA").upper()
            dados["fundamentos"][key]["severidade"] = sev.replace(" ", "_")

        return (True, dados)

    except FileNotFoundError:
        return (False, "Ollama não encontrado — instale com 'brew install ollama'")
    except subprocess.TimeoutExpired:
        return (False, "Timeout no Ollama (3 min)")
    except json.JSONDecodeError as e:
        return (False, f"JSON inválido do Ollama: {e}")
    except Exception as e:
        return (False, f"Erro Ollama: {type(e).__name__}: {e}")


def avaliar_com_ia(texto: str, aula_id: str, disciplina: str, curso: str) -> tuple:
    """
    Chama o Agente E via Skill 'analista-conteudo' com fallback para Ollama.

    A skill deve gravar diretamente o JSON estruturado em:
    {pasta_aula}/03_avaliacao/score_vNN.json

    Returns
    -------
    tuple
        (sucesso: bool, resultado: dict ou erro: str)
        - Se sucesso: (True, dict_com_dados)
        - Se falha: (False, "mensagem_de_erro")
    """
    print("\n🔍 Agente E — Avaliando material...")
    print(f"   Aula: {aula_id}")
    print(f"   Disciplina: {disciplina}")
    print(f"   Curso: {curso}")
    print(f"   Texto: {len(texto)} caracteres")

    # Salva texto em arquivo temporário
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    texto_file = tmp / "aula.md"
    texto_file.write_text(texto[:50000], encoding="utf-8")  # limita a 50k chars

    # Tenta 1: Skill /analista-conteudo (Claude Opus)
    print("\n   📡 Tentando skill /analista-conteudo (claude-opus-4-7)...")

    try:
        # Chama a skill analista-conteudo
        result = subprocess.run(
            ["claude", "/analista-conteudo", str(texto_file)],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutos timeout
            cwd=str(Path(__file__).parent.parent),  # roda do root do projeto
        )

        shutil.rmtree(tmp, ignore_errors=True)

        if result.returncode != 0:
            return (False, f"Skill falhou com código {result.returncode}: {result.stderr}")

        output = result.stdout + result.stderr

        # Tenta extrair JSON do output (a skill deve gravar JSON estruturado)
        import re
        json_match = re.search(r'\{[^{}]*"aula_id"[^{}]*\}', output, re.DOTALL)

        if json_match:
            try:
                dados = json.loads(json_match.group(0))
                # Valida estrutura mínima
                if "fundamentos" not in dados or "indicadores" not in dados:
                    return (False, "JSON sem estrutura required: 'fundamentos' e 'indicadores'")
                return (True, dados)
            except json.JSONDecodeError as e:
                return (False, f"JSON inválido: {e}")

        # Fallback: tenta parsing do rodapé machine-readable (legado)
        match = re.search(r"VEREDITO=(\w+)\s+INDICE=([\d.]+)\s+A1=(\w+)\s+A2=(\w+)", output)

        if match:
            veredito_str, indice_str, a1_str, a2_str = match.groups()

            veredito_map = {
                "VERDE": "APROVAR",
                "AMARELO": "APROVAR_COM_RESSALVA",
                "LARANJA": "INTERVENCAO_EDITORIAL",
                "VERMELHO": "RECRIAR",
            }

            a1_map = {"SR": "SEM_RESSALVA", "R": "RESSALVA", "C": "CRITICO"}
            a2_map = {"SR": "SEM_RESSALVA", "R": "RESSALVA", "C": "CRITICO"}

            # Extrai notas do laudo (procura padrão "B1 Dialogicidade | X/10 | 20%")
            notas = {}
            for ind in ["B1", "B2", "B3", "B4", "B5"]:
                match_ind = re.search(rf"{ind}\s+[^\|]+\|\s*(\d+)/10", output)
                if match_ind:
                    notas[ind] = float(match_ind.group(1))
                else:
                    # NOTA FALTANTE → falha, não fallback
                    return (False, f"Nota de {ind} não encontrada no laudo")

            return (True, {
                "fundamentos": {
                    "A1": {
                        "severidade": a1_map.get(a1_str, "SEM_RESSALVA"),
                        "justificativa": "Verificado via skill analista-conteudo.",
                        "trecho": ""
                    },
                    "A2": {
                        "severidade": a2_map.get(a2_str, "SEM_RESSALVA"),
                        "justificativa": "Verificado via skill analista-conteudo.",
                        "fontes_verificadas": []
                    }
                },
                "indicadores": {
                    ind: {"nota": nota, "justificativa": "Atribuído pela skill analista-conteudo."}
                    for ind, nota in notas.items()
                },
            })

        # Sem JSON e sem rodapé → falha explícita
        return (False, "Skill não retornou JSON estruturado nem rodapé machine-readable")

    except FileNotFoundError:
        print("   ⚠️  Claude CLI não encontrado. Tentando fallback com Ollama...")
    except subprocess.TimeoutExpired:
        print("   ⚠️  Timeout na skill. Tentando fallback com Ollama...")
    except Exception as e:
        print(f"   ⚠️  Erro na skill: {type(e).__name__}. Tentando fallback com Ollama...")

    # Fallback: Ollama (modelo local)
    print("\n   🔄 Fallback: Usando Ollama (modelo local)...")
    shutil.rmtree(tmp, ignore_errors=True)

    # Tenta com 'codex' primeiro, depois 'llama3' se falhar
    for modelo in ["codex", "llama3"]:
        sucesso, resultado = avaliar_com_ollama(texto, aula_id, disciplina, curso, modelo)
        if sucesso:
            print(f"   ✅ Ollama ({modelo}) retornou avaliação válida")
            return (True, resultado)
        print(f"   ⚠️  Ollama ({modelo}) falhou: {resultado}")

    return (False, "Skill e Ollama indisponíveis. Verifique conexão ou instale ollama 'brew install ollama'")


def gerar_laudo_markdown(aula_id: str, resultado_ia: dict, score: dict) -> str:
    """Gera o laudo em formato Markdown para leitura humana."""
    linhas = []

    linhas.append("# Relatório de Avaliação — Módulo 02")
    linhas.append(f"**Aula:** {aula_id}")
    linhas.append(f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    linhas.append("")

    # Veredito em destaque
    emoji = score["veredito"]["emoji"]
    rotulo = score["veredito"]["rotulo"]
    indice_valor = score["indice"]["indice"] if isinstance(score["indice"], dict) else score["indice"]
    linhas.append(f"## {emoji} Veredito: {rotulo}")
    linhas.append(f"**Índice de Qualidade Didática:** {indice_valor:.2f}")
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

    linhas.append(f"| **TOTAL** | — | **1.00** | **{indice_valor:.2f}** |")
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


def proxima_versao(pasta_avaliacao: Path) -> str:
    """
    Retorna próxima versão disponível para score/laudo.

    Ex: v01, v02, v03...

    Parameters
    ----------
    pasta_avaliacao : Path
        Pasta 03_avaliacao onde os arquivos serão gravados.

    Returns
    -------
    str
        Versão no formato 'v01', 'v02', etc.
    """
    existentes = sorted(pasta_avaliacao.glob("score_v*.json"))
    if not existentes:
        return "v01"

    ultimo = existentes[-1].stem  # ex: score_v01
    try:
        num = int(ultimo.replace("score_v", "").replace("v", ""))
        return f"v{num + 1:02d}"
    except ValueError:
        return "v01"


def criar_incubadora(pasta_aula: Path, score: dict, laudo_md: str):
    """Cria pasta 07_incubadora/ quando veredito = RECRIAR."""
    incubadora = pasta_aula / "07_incubadora"
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
        "motivo": "Material enviado para incubadora devido ao veredito RECRIAR."
    }
    (incubadora / "motivo.json").write_text(
        json.dumps(motivo, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"   📁 07_incubadora/ criada em {incubadora}")


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
    sucesso, resultado_ia_ou_erro = avaliar_com_ia(texto, aula_id, disciplina, curso)

    if not sucesso:
        # Falha explícita do Agente E — NÃO gera score
        print(f"\n   ❌ Erro no Agente E: {resultado_ia_ou_erro}")
        return {
            "ok": False,
            "erro": "erro_agente_e",
            "mensagem": resultado_ia_ou_erro,
            "sugestao": "Verifique se o Claude CLI está instalado e tente novamente."
        }

    resultado_ia = resultado_ia_ou_erro

    # Valida estrutura do resultado
    if "fundamentos" not in resultado_ia or "indicadores" not in resultado_ia:
        return {
            "ok": False,
            "erro": "score_invalido",
            "mensagem": "Resultado da IA não tem estrutura required (fundamentos, indicadores)",
            "sugestao": "Verifique se a skill está retornando JSON estruturado."
        }

    # Extrai notas para cálculo
    notas = {
        ind: dados["nota"]
        for ind, dados in resultado_ia["indicadores"].items()
    }
    a1 = resultado_ia["fundamentos"]["A1"]["severidade"]
    a2 = resultado_ia["fundamentos"]["A2"]["severidade"]

    # Valida notas antes de calcular (defesa em profundidade)
    from modulo02.calculo import validar_notas, validar_severidade
    erros_notas = validar_notas(notas)
    erros_severidade = validar_severidade(a1, a2)

    if erros_notas or erros_severidade:
        todos_erros = erros_notas + erros_severidade
        return {
            "ok": False,
            "erro": "score_invalido",
            "mensagem": f"Notas ou severidades inválidas: {'; '.join(todos_erros)}",
            "sugestao": "A skill deve retornar B1-B5 com notas 0-10 e A1/A2 com SEM_RESSALVA/RESSALVA/CRITICO"
        }

    # Calcula índice e veredito (aritmética pura)
    score = calcular_score(notas, a1, a2)

    # Verifica se o cálculo foi válido
    if not score.get("valido", True):
        return {
            "ok": False,
            "erro": "score_invalido",
            "mensagem": f"Cálculo falhou: {'; '.join(score.get('erros', []))}",
            "sugestao": "Verifique as notas e severidades retornadas pela skill."
        }

    # Gera laudo Markdown
    laudo_md = gerar_laudo_markdown(aula_id, resultado_ia, score)

    # Monta score JSON completo (formato compatível com laudo.html)
    indice_valor = score["indice"]["indice"] if isinstance(score["indice"], dict) else score["indice"]

    # Bibliografia: se a skill não retornou fontes, extrai do markdown da aula
    a2_block = resultado_ia["fundamentos"]["A2"]
    if not a2_block.get("fontes_verificadas"):
        from referencias import extrair_referencias_markdown
        fontes_md = extrair_referencias_markdown(texto, numero_aula=aula)
        if fontes_md:
            a2_block["fontes_verificadas"] = fontes_md
            if a2_block.get("justificativa") in (
                "Verificado via skill analista-conteudo.",
                "Referências localizáveis.",
                "",
            ):
                a2_block["justificativa"] = (
                    f"{len(fontes_md)} referência(s) citada(s) no material — "
                    "validação externa pendente (Agente E)."
                )

    # Adiciona peso e contribuicao em cada indicador (esperado pelo laudo.html)
    pesos = {"B1": 0.20, "B2": 0.15, "B3": 0.30, "B4": 0.15, "B5": 0.20}
    indicadores_formatados = {}
    for ind, dados in resultado_ia["indicadores"].items():
        nota = dados["nota"]
        peso = pesos[ind]
        indicadores_formatados[ind] = {
            "nota": nota,
            "peso": peso,
            "contribuicao": round(nota * peso, 2),
            "justificativa": dados["justificativa"],
        }

    score_json = {
        "aula_id": aula_id,
        "disciplina": disciplina,
        "curso": curso,
        "data_avaliacao": datetime.now().isoformat(),
        "indice": indice_valor,  # valor float direto (esperado pelo laudo.html)
        "veredito": score["veredito"]["faixa"],  # string direta (esperado pelo laudo.html)
        "emoji": score["veredito"]["emoji"],
        "acao": score["veredito"]["acao_coordenador"],
        "fundamentos": resultado_ia["fundamentos"],
        "indicadores": indicadores_formatados,
    }

    # Salva arquivos (versionamento automático)
    versao = proxima_versao(pasta_avaliacao)
    (pasta_avaliacao / f"avaliacao_{versao}.md").write_text(laudo_md, encoding="utf-8")
    (pasta_avaliacao / f"score_{versao}.json").write_text(
        json.dumps(score_json, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"\n   ✅ Laudo gerado: {pasta_avaliacao / f'avaliacao_{versao}.md'}")
    print(f"   ✅ Score JSON: {pasta_avaliacao / f'score_{versao}.json'}")
    print(f"\n   📊 Índice: {indice_valor:.2f}")
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
        "indice": indice_valor,
        "veredito": score["veredito"]["faixa"],
        "score_path": str(pasta_avaliacao / f"score_{versao}.json"),
        "laudo_path": str(pasta_avaliacao / f"avaliacao_{versao}.md"),
    })

    return {
        "ok": True,
        "aula_id": aula_id,
        "indice": indice_valor,
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
