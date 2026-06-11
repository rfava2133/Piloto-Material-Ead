#!/usr/bin/env python3
"""
M03 — Agente A: Texto Display

Executa o Agente A para reformular markdown aprovado em versão display.

Uso:
    python3 scripts/04-agente-a.py \
        --curso "Administração" \
        --codigo ADM \
        --disciplina "Fundamentos de Administração" \
        --aula 1 \
        --forcar   # opcional: reprocessar se já existir
"""

import argparse
import json
import sys
import shutil
from datetime import datetime
from pathlib import Path

# Adiciona o projeto ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import condicional para funcionar tanto via CLI quanto via servidor
try:
    from scripts.config import carregar_config
except ImportError:
    carregar_config = None


def slugify(texto: str) -> str:
    """Converte texto em slug kebab-case."""
    import unicodedata
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = texto.lower().replace(" ", "-")
    texto = "".join(c if c.isalnum() or c == "-" else "" for c in texto)
    texto = "-".join(filter(None, texto.split("-")))
    return texto


def construir_caminhos(curso_slug: str, codigo: str, disciplina_slug: str, aula_num: int):
    """Constrói caminhos da pasta da aula."""
    raiz = Path(__file__).parent.parent / "cursos"
    pasta_aula = raiz / curso_slug / f"{codigo}-{disciplina_slug}" / "aulas" / f"{aula_num:02d}"
    return pasta_aula


def verificar_pre_condicoes(pasta_aula: Path) -> tuple[bool, str]:
    """
    Verifica pré-condições para rodar o M03.

    Returns:
        (sucesso, mensagem)
    """
    # Verifica se pasta existe
    if not pasta_aula.exists():
        return False, f"Pasta da aula não encontrada: {pasta_aula}"

    # Verifica se há markdown original
    markdown_dir = pasta_aula / "02_markdown"
    if not markdown_dir.exists() or not list(markdown_dir.glob("*.md")):
        return False, "Nenhum arquivo .md em 02_markdown/"

    # Verifica se M02 já aprovou
    avaliacao_dir = pasta_aula / "03_avaliacao"
    score_path = avaliacao_dir / "score_v01.json"

    if score_path.exists():
        with open(score_path, "r", encoding="utf-8") as f:
            score = json.load(f)
        # Suporta tanto string ("INTERVENCAO_EDITORIAL") quanto objeto ({"rotulo": "..."})
        veredito_raw = score.get("veredito", "")
        if isinstance(veredito_raw, dict):
            veredito = veredito_raw.get("rotulo", "")
        else:
            veredito = veredito_raw
        if veredito == "RECRIAR":
            return False, "Material com veredito RECRIAR — não avançar sem aprovação do coordenador"

    # Verifica se já existe display (sem --forcar)
    display_path = pasta_aula / "03_reformulado" / "texto-display.md"
    if display_path.exists():
        return False, "texto-display.md já existe — use --forcar para reprocessar"

    return True, "OK"


def criar_backup(pasta_aula: Path):
    """Cria backup do texto-display.md existente com timestamp."""
    display_path = pasta_aula / "03_reformulado" / "texto-display.md"
    meta_path = pasta_aula / "03_reformulado" / "display_meta.json"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if display_path.exists():
        backup_display = pasta_aula / "03_reformulado" / f"texto-display_v{timestamp}.md"
        shutil.copy2(display_path, backup_display)
        print(f"  Backup criado: {backup_display.name}")

    if meta_path.exists():
        backup_meta = pasta_aula / "03_reformulado" / f"display_meta_v{timestamp}.json"
        shutil.copy2(meta_path, backup_meta)
        print(f"  Backup criado: {backup_meta.name}")


def executar_agente_a_ollama(pasta_aula: Path, input_md: Path, modelo: str = "codex") -> tuple[bool, str]:
    """
    Executa M03 usando Ollama local como fallback.

    Returns:
        (sucesso, mensagem)
    """
    import subprocess
    import re

    output_dir = pasta_aula / "03_reformulado"
    output_md = output_dir / "texto-display.md"
    output_meta = output_dir / "display_meta.json"

    output_dir.mkdir(parents=True, exist_ok=True)

    texto_original = input_md.read_text(encoding="utf-8")

    prompt = f"""Você é o Agente A — Texto Display para material EAD UNIGRAN.
Reformule o material abaixo para versão DISPLAY DE TELA.

REGRAS:
1. Tom conversacional (2ª pessoa: "você", "seu")
2. Preserve todos os marcadores [IMG-NN] exatamente como estão
3. Volume mínimo: 80% do original
4. Adicione 3-6 marcadores [VIDEO-NN] em pontos estratégicos
5. Inclua callouts: conceito-chave, atenção, resumo, exercício, dica
6. Termine com seção "## Glossário" com 5-10 termos técnicos
7. Use markdown limpo, sem HTML

Retorne APENAS o markdown reformulado, sem explicações.

--- MATERIAL ORIGINAL ---
{texto_original[:25000]}
"""

    try:
        result = subprocess.run(
            ["ollama", "run", modelo, prompt],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            return (False, f"Ollama falhou: {result.stderr}")

        output = result.stdout.strip()

        if len(output) < len(texto_original) * 0.5:
            return (False, f"Output muito curto ({len(output)} chars)")

        # Salva texto reformulado
        output_md.write_text(output, encoding="utf-8")

        # Gera metadados básicos
        meta = {
            "modelo": f"ollama/{modelo}",
            "timestamp": datetime.now().isoformat(),
            "volume_original": len(texto_original),
            "volume_display": len(output),
            "proporcao_pct": round(len(output) / len(texto_original) * 100, 1),
            "marcadores_img": re.findall(r'\[IMG-(\d+)\]', output),
            "marcadores_video": re.findall(r'\[VIDEO-(\d+)\]', output),
            "glossario": "## Glossário" in output,
        }

        output_meta.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

        return (True, f"Ollama ({modelo}) gerou {len(output)} chars")

    except FileNotFoundError:
        return (False, "Ollama não encontrado")
    except subprocess.TimeoutExpired:
        return (False, "Timeout no Ollama (5 min)")
    except Exception as e:
        return (False, f"Erro: {type(e).__name__}: {e}")


def executar_agente_a(pasta_aula: Path, input_md: Path) -> tuple[bool, str]:
    """
    Prepara ambiente para execução do Agente A (M03) com fallback Ollama.

    Tenta:
    1. Gera prompt para execução manual via Claude Code
    2. Fallback: Ollama local (codex, luego llama3)

    Returns:
        (sucesso, mensagem)
    """
    output_dir = pasta_aula / "03_reformulado"
    output_md = output_dir / "texto-display.md"
    output_meta = output_dir / "display_meta.json"

    # Garante que a pasta de saída existe
    output_dir.mkdir(parents=True, exist_ok=True)

    # Tenta 1: Prepara prompt para Claude Code (manual ou via skill)
    prompt_path = output_dir / "_prompt_m03.txt"
    prompt = f"""# M03 — TEXTO DISPLAY

## Entrada
Arquivo original: `{input_md}`

## Tarefa
Reformule o markdown original para versão display de tela seguindo:
1. `skills/texto-display/SKILL.md` — regras de reescrita
2. `docs/voz-unigran.md` — tom, proibições, callouts

## Requisitos obrigatórios
- Preserve TODOS os marcadores [IMG-NN] do original
- Volume mínimo: 80% do original
- Citações: preservar intactas
- Adicione 3-6 marcadores [VIDEO-NN] sugeridos
- Inclua seção "Glossário" no final

## Saídas esperadas
1. `{output_md}` — texto reformulado
2. `{output_meta}` — metadados JSON com:
   - volume_original, volume_display, proporcao_pct
   - marcadores_img: lista de IDs
   - marcadores_video: lista de IDs
   - callouts: contagem por tipo
   - glossario_termos: lista de termos
   - bloom_niveis_cobertos: lista

## Conteúdo original
"""
    prompt += input_md.read_text(encoding="utf-8")

    prompt_path.write_text(prompt, encoding="utf-8")
    print(f"   📄 Prompt gerado: {prompt_path.name}")

    # Copiar markdown original para referência
    ref_path = output_dir / "original_referencia.md"
    shutil.copy2(input_md, ref_path)

    # Tenta 2: Fallback automático com Ollama
    print("\n   🔄 Tentando Ollama como fallback...")
    for modelo in ["codex", "llama3"]:
        print(f"   → Testando modelo: {modelo}")
        ok, msg = executar_agente_a_ollama(pasta_aula, input_md, modelo)
        if ok:
            print(f"   ✅ {msg}")
            return (True, f"Ollama ({modelo}) executou com sucesso. {msg}")
        print(f"   ⚠️  {modelo}: {msg}")

    return (True, f"Prompt preparado em {prompt_path}. Execute manualmente: claude /texto-display {prompt_path}")


def executar_agente_a_tela(curso: str, codigo: str, disciplina: str, aula_num: int, forcar: bool = False) -> dict:
    """
    Executa o M03 — Texto Display via interface (API).

    Returns:
        dict: {"ok": bool, "erro": str|None, "detalhes": dict}
    """
    curso_slug = slugify(curso)
    disciplina_slug = slugify(disciplina)
    pasta_aula = construir_caminhos(curso_slug, codigo, disciplina_slug, aula_num)

    # Verificar pré-condições
    ok, msg = verificar_pre_condicoes(pasta_aula)

    if not ok:
        if forcar and "já existe" in msg:
            criar_backup(pasta_aula)
        else:
            return {"ok": False, "erro": msg}

    # Encontrar arquivo de entrada
    markdown_dir = pasta_aula / "02_markdown"
    input_files = list(markdown_dir.glob("*.md"))

    if not input_files:
        return {"ok": False, "erro": "Nenhum arquivo .md encontrado em 02_markdown/"}

    input_md = input_files[0]

    # Executar Agente A
    ok, msg = executar_agente_a(pasta_aula, input_md)

    if not ok:
        return {"ok": False, "erro": msg}

    # Retornar informações sobre o prompt preparado
    prompt_path = pasta_aula / "03_reformulado" / "_prompt_m03.txt"

    return {
        "ok": True,
        "erro": None,
        "detalhes": {
            "prompt_path": str(prompt_path),
            "instrucao": f"Execute: claude /texto-display {prompt_path}",
        }
    }


def main():
    parser = argparse.ArgumentParser(description="M03 — Agente A: Texto Display")
    parser.add_argument("--curso", required=True, help="Nome do curso")
    parser.add_argument("--codigo", required=True, help="Código da disciplina (3 letras)")
    parser.add_argument("--disciplina", required=True, help="Nome da disciplina")
    parser.add_argument("--aula", required=True, type=int, help="Número da aula")
    parser.add_argument("--forcar", action="store_true", help="Reprocessar se já existir")
    parser.add_argument("--debug", action="store_true", help="Mostrar debug")

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("M03 — AGENTE A: TEXTO DISPLAY")
    print(f"{'='*60}\n")

    # Constrói caminhos
    curso_slug = slugify(args.curso)
    disciplina_slug = slugify(args.disciplina)
    pasta_aula = construir_caminhos(curso_slug, args.codigo, disciplina_slug, args.aula)

    print(f"Curso: {args.curso} ({curso_slug})")
    print(f"Disciplina: {args.codigo} — {args.disciplina}")
    print(f"Aula: {args.aula}")
    print(f"Pasta: {pasta_aula}\n")

    # Verifica pré-condições
    print("Verificando pré-condições...")
    ok, msg = verificar_pre_condicoes(pasta_aula)

    if not ok:
        if "--forcar" in sys.argv and "já existe" in msg:
            print(f"  ⚠️ {msg}")
            print("  --forcar detectado — criando backup e reprocessando\n")
            criar_backup(pasta_aula)
        else:
            print(f"  ❌ {msg}")
            sys.exit(1)
    else:
        print(f"  ✅ {msg}\n")

    # Encontra arquivo de entrada
    markdown_dir = pasta_aula / "02_markdown"
    input_files = list(markdown_dir.glob("*.md"))

    if not input_files:
        print("  ❌ Nenhum arquivo .md encontrado")
        sys.exit(1)

    input_md = input_files[0]
    print(f"Arquivo de entrada: {input_md.name}\n")

    # Executa Agente A
    print("Executando Agente A...")
    ok, msg = executar_agente_a(pasta_aula, input_md)

    if not ok:
        print(f"  ❌ {msg}")
        sys.exit(1)

    print(f"  ✅ {msg}\n")

    # Roda validador
    print("Rodando validador determinístico...")
    from modulo03.validador import validar_e_salvar_log

    resultado = validar_e_salvar_log(pasta_aula)

    if resultado["ok"]:
        print("  ✅ Validação APROVADA")
    else:
        print("  ❌ Validação REPROVADA")
        print("\n  Falhas:")
        for falha in resultado["falhas"]:
            print(f"    • {falha}")

    if resultado["alertas"]:
        print("\n  Alertas:")
        for alerta in resultado["alertas"]:
            print(f"    • {alerta}")

    print(f"\n  Métricas:")
    m = resultado["metricas"]
    print(f"    Volume: {m.get('volume_original', 0)} → {m.get('volume_display', 0)} palavras ({m.get('proporcao_pct', 0)}%)")
    print(f"    Imagens: {m.get('marcadores_img', 0)} | Vídeos: {m.get('marcadores_video', 0)}")

    print(f"\n{'='*60}")

    if not resultado["ok"]:
        print("\n⚠️  Validação falhou — não avançar sem revisão")
        print("    Corrija o texto-display.md ou use --forcar após corrigir\n")
        sys.exit(1)

    print("\n✅ M03 concluído com sucesso!")
    print("   Próximo passo: revisar em modulo03/display.html\n")


if __name__ == "__main__":
    main()
