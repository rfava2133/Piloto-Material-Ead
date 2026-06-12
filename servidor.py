#!/usr/bin/env python3
"""
servidor.py — Servidor local que conecta a interface HTML aos scripts do MÓDULO 01 — EXTRATOR.

Roda em http://127.0.0.1:5050
Instalar: pip install flask pyyaml

Uso:
  python3 servidor.py
  (depois abra http://127.0.0.1:5050 no navegador)
"""
import sys
import os
import json
import shutil
import tempfile
import csv
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlencode

# Carrega ANTHROPIC_API_KEY de .env se não estiver no ambiente
_env_path = Path(__file__).parent / ".env"
if _env_path.exists() and not os.environ.get("ANTHROPIC_API_KEY"):
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import yaml

sys.path.insert(0, str(Path(__file__).parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent / "modulo02"))
import importlib.util

from lib import pastas
import calculo  # modulo02/calculo.py — índice e veredito auditáveis
import referencias as ref_mod  # modulo02/referencias.py — fallback bibliográfico


def _importar_script(nome_modulo: str, arquivo: str):
    """Importa um script de scripts/ cujo nome tem hífen (uma vez, no boot)."""
    spec = importlib.util.spec_from_file_location(
        nome_modulo, Path(__file__).parent / "scripts" / arquivo
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


processar_mod = _importar_script("processar", "01-processar-entrada.py")
separar_mod = _importar_script("separar_aulas", "02-separar-aulas.py")
agente_e_mod = _importar_script("agente_e", "03-agente-e.py")
agente_a_mod = None  # Import lazy para evitar erro de sintaxe (04-agente-a.py tem hífen)

app = Flask(__name__, static_folder="interface")

# Estado global para status do processamento (em memória)
processamento_status = {"ativo": False, "etapa": "", "mensagem": "", "concluido": False}


def cfg():
    with open(Path(__file__).parent / "scripts" / "config.yml", encoding="utf-8") as f:
        return yaml.safe_load(f)


@app.route("/")
def index():
    return send_from_directory("interface", "index.html")


@app.route("/api/teste-pdf")
def api_teste_pdf():
    """Serve o PDF de testes para modo de demonstração."""
    from flask import send_file
    pdf_path = Path(__file__).parent / "testes" / "adm_fund_aula01.pdf"
    if pdf_path.exists():
        return send_file(str(pdf_path), mimetype="application/pdf")
    return jsonify({"erro": "PDF de testes não encontrado"}), 404


@app.route("/modulo02/<path:arquivo>")
def modulo02_estatico(arquivo):
    """Serve as telas do M02 (ex.: /modulo02/laudo.html)."""
    return send_from_directory("modulo02", arquivo)


def _salvar_uploads(files, tmp: Path):
    """
    Salva uploads e retorna (word_path, pdf_path).

    Aceita o campo 'documento' (hub atual, roteia pela extensão) e
    mantém compatibilidade com os campos 'word' e 'pdf' (CLI/legado).
    """
    word_path = pdf_path = None

    doc = files.get("documento")
    if doc and doc.filename:
        nome = secure_filename(doc.filename)
        destino = tmp / nome
        doc.save(destino)
        if nome.lower().endswith(".docx"):
            word_path = destino
        elif nome.lower().endswith(".pdf"):
            pdf_path = destino

    for campo, ext in (("word", ".docx"), ("pdf", ".pdf")):
        f = files.get(campo)
        if f and f.filename:
            destino = tmp / secure_filename(f.filename)
            f.save(destino)
            if campo == "word":
                word_path = destino
            else:
                pdf_path = destino

    return word_path, pdf_path


@app.route("/api/catalogo", methods=["GET"])
def api_catalogo():
    """Lê dados/catalogo.csv e retorna JSON estruturado por curso."""
    csv_path = Path(__file__).parent / "dados" / "catalogo.csv"
    if not csv_path.exists():
        return jsonify({"erro": "Catálogo não encontrado"}), 404

    cursos_set = set()
    disciplinas_por_curso = defaultdict(list)
    seen = set()  # evitar duplicatas exatas

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            curso = row["curso_final"].strip()
            disciplina = row["disciplina"].strip()
            semestre = row["semestre"].strip()
            professor = row["professor"].strip()

            cursos_set.add(curso)

            # Evitar duplicatas exatas (mesma disciplina+semestre+professor)
            key = (disciplina, semestre, professor)
            if key not in seen:
                seen.add(key)
                disciplinas_por_curso[curso].append({
                    "disciplina": disciplina,
                    "semestre": semestre,
                    "professor": professor
                })

    # Ordenar cursos A-Z
    cursos = sorted(cursos_set)

    # Ordenar disciplinas por semestre e depois A-Z
    for curso in disciplinas_por_curso:
        disciplinas_por_curso[curso].sort(key=lambda x: (x["semestre"], x["disciplina"].lower()))

    return jsonify({
        "cursos": cursos,
        "disciplinas": dict(disciplinas_por_curso)
    })


@app.route("/api/status", methods=["GET"])
def api_status():
    """Retorna status atual do processamento (para polling)."""
    return jsonify(processamento_status)


@app.route("/api/ia-status", methods=["GET"])
def api_ia_status():
    """Verifica disponibilidade do Claude (IA)."""
    import subprocess
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return jsonify({
                "geral": "online",
                "mensagem": "IA disponível.",
                "modo_fallback": False,
                "modulos": {
                    "M02": {"modelo": "claude-opus-4-7", "status": "online"},
                    "M03": {"modelo": "claude-sonnet-4-6", "status": "online"}
                }
            })
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass

    return jsonify({
        "geral": "fallback",
        "mensagem": "⚠️ IA FORA DO AR — Timeout. M02/M03 usarão modo fallback.",
        "modo_fallback": True,
        "modulos": {
            "M02": {"modelo": "claude-opus-4-7", "status": "online"},
            "M03": {"modelo": "claude-sonnet-4-6", "status": "online"}
        }
    })


def _normalizar_severidade(valor) -> str:
    """'CRÍTICO' / 'sem ressalva' / ' Ressalva ' → CRITICO / SEM_RESSALVA / RESSALVA."""
    import unicodedata
    if isinstance(valor, dict):
        valor = valor.get("severidade", "")
    texto = unicodedata.normalize("NFD", str(valor))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.upper().strip().replace(" ", "_").replace("-", "_")
    return texto if texto in ("SEM_RESSALVA", "RESSALVA", "CRITICO") else "SEM_RESSALVA"


def _normalizar_score(dados: dict, aula_id: str) -> dict:
    """
    Converte qualquer formato de score já produzido pelas IAs para o
    contrato que o laudo.html consome — e SEMPRE recalcula índice e
    veredito via modulo02/calculo.py a partir das notas.

    O veredito escrito pela IA é ignorado: a conta é do código (auditável).
    """
    # --- fundamentos: aceita objeto {severidade,...} ou string direta
    fund_bruto = dados.get("fundamentos", {})
    fundamentos = {}
    for chave in ("A1", "A2"):
        item = fund_bruto.get(chave, {})
        if not isinstance(item, dict):
            item = {"severidade": item}
        item = dict(item)
        item["severidade"] = _normalizar_severidade(item)
        fundamentos[chave] = item
    a1 = fundamentos["A1"]["severidade"]
    a2 = fundamentos["A2"]["severidade"]

    # --- indicadores: aceita {"B1": {"nota": 7}} ou {"B1": 7}
    ind_bruto = dados.get("indicadores", {})
    notas = {}
    justificativas = {}
    for chave, item in ind_bruto.items():
        if isinstance(item, dict):
            nota = item.get("nota")
            justificativas[chave] = item.get("justificativa", "")
        else:
            nota = item
        if chave in calculo.PESOS and isinstance(nota, (int, float)):
            notas[chave] = float(nota)

    # --- índice: recalculado das notas; sem notas, usa o número gravado
    if notas:
        indice = calculo.calcular_indice(notas)["indice"]
    else:
        bruto = dados.get("indice", 0)
        indice = float(bruto.get("indice", 0) if isinstance(bruto, dict) else bruto or 0)

    # --- veredito: SEMPRE recalculado (regra das 4 faixas + override CRÍTICO)
    veredito = calculo.determinar_veredito(indice, a1, a2)

    indicadores = {}
    for chave, nota in notas.items():
        peso = calculo.PESOS[chave]
        indicadores[chave] = {
            "nota": nota,
            "peso": peso,
            "contribuicao": round(nota * peso, 2),
            "justificativa": justificativas.get(chave, ""),
        }

    return {
        "aula_id": dados.get("aula_id", aula_id),
        "indice": indice,
        "veredito": veredito["faixa"],
        "emoji": veredito["emoji"],
        "acao": veredito["acao_coordenador"],
        "fundamentos": fundamentos,
        "indicadores": indicadores,
    }


@app.route("/api/score", methods=["GET"])
def api_score():
    """
    Localiza o score_v*.json gerado pelo Agente E (M02) para uma aula.
    Usado pelo laudo.html para carregar o laudo automaticamente.

    Estados possíveis:
    - sem_material: aula ainda não foi extraída pelo M01
    - aguardando_avaliacao: material extraído, sem score ainda
    - avaliada: score válido encontrado
    - erro_agente_e: falha na avaliação (arquivo de erro presente)
    - score_invalido: score existe mas não passou na validação
    """
    curso = request.args.get("curso", "").strip()
    codigo = request.args.get("codigo", "").strip()
    disciplina = request.args.get("disciplina", "").strip()
    aula = request.args.get("aula", "").strip()

    try:
        aula_num = int(aula)
    except ValueError:
        return jsonify({"erro": "Número da aula inválido."}), 400

    raiz = Path(cfg()["raiz"]).expanduser()
    pasta_aula = (
        raiz / "cursos" / pastas.slugify(curso)
        / pastas.nome_pasta_disciplina(codigo, disciplina)
        / "aulas" / f"{aula_num:02d}"
    )
    aula_id = pastas.id_aula(codigo, aula_num)

    if not pasta_aula.exists():
        return jsonify({
            "status": "sem_material",
            "aula_id": aula_id,
            "mensagem": "Aula ainda não foi extraída pelo Módulo 01.",
        }), 404

    # Verifica se há erro do Agente E (fallback removido — erro é explícito)
    log_path = pasta_aula / "_log.json"
    if log_path.exists():
        try:
            log = json.loads(log_path.read_text(encoding="utf-8"))
            if isinstance(log, list):
                ultimo_log = log[-1] if log else {}
            else:
                ultimo_log = log

            if ultimo_log.get("modulo") == "M02" and ultimo_log.get("erro") in ("erro_agente_e", "score_invalido"):
                return jsonify({
                    "status": "erro_agente_e",
                    "aula_id": aula_id,
                    "mensagem": f"Erro na avaliação: {ultimo_log.get('mensagem', 'Erro desconhecido')}",
                    "sugestao": ultimo_log.get("sugestao", "Tente reavaliar a aula."),
                }), 404
        except (json.JSONDecodeError, OSError):
            pass  # Ignora erro de log, continua para verificação de score

    # procura score_v*.json em qualquer subpasta (03_avaliacao etc.)
    scores = sorted(pasta_aula.glob("*/score_v*.json"))
    if not scores:
        return jsonify({
            "status": "aguardando_avaliacao",
            "aula_id": aula_id,
            "pasta": str(pasta_aula),
            "mensagem": "Material extraído. Aguardando avaliação do Agente E.",
        }), 404

    try:
        dados = json.loads(scores[-1].read_text(encoding="utf-8"))
        score = _normalizar_score(dados, aula_id)

        # Validação estrita: verifica se score tem estrutura mínima
        if not score.get("fundamentos") or not score.get("indicadores"):
            return jsonify({
                "status": "score_invalido",
                "aula_id": aula_id,
                "mensagem": "Score existe mas estrutura é inválida (sem fundamentos ou indicadores).",
                "arquivo": str(scores[-1]),
            }), 404

        # Verifica se todas as notas B1-B5 estão presentes
        indicadores = score.get("indicadores", {})
        notas_faltantes = {"B1", "B2", "B3", "B4", "B5"} - set(indicadores.keys())
        if notas_faltantes:
            return jsonify({
                "status": "score_invalido",
                "aula_id": aula_id,
                "mensagem": f"Notas faltando: {', '.join(sorted(notas_faltantes))}",
                "arquivo": str(scores[-1]),
            }), 404

        # Extrair referências bibliográficas completas do markdown (para cruzar com citações do corpo)
        a2 = score["fundamentos"].get("A2", {})
        referencias_bibliograficas = ref_mod.extrair_referencias_pasta(pasta_aula, numero_aula=aula_num)

        # Se não tem fontes verificadas, extrai do markdown
        if not a2.get("fontes_verificadas"):
            if referencias_bibliograficas:
                a2["fontes_verificadas"] = referencias_bibliograficas
                just = (a2.get("justificativa") or "").strip()
                if just in ("Referências localizáveis.", "Verificado via skill analista-conteudo.", ""):
                    a2["justificativa"] = (
                        f"{len(referencias_bibliograficas)} referência(s) citada(s) no material — "
                        "validação externa pendente (Agente E)."
                    )
                score["fundamentos"]["A2"] = a2

        # Adicionar referências_bibliograficas ao score (para o laudo cruzar dados)
        if referencias_bibliograficas:
            score["referencias_bibliograficas"] = referencias_bibliograficas
    except (json.JSONDecodeError, OSError, TypeError, ValueError) as e:
        return jsonify({
            "status": "score_invalido",
            "aula_id": aula_id,
            "mensagem": f"Score inválido: {e}",
            "arquivo": str(scores[-1]) if scores else None,
        }), 404

    return jsonify({"status": "avaliada", "score": score, "arquivo": str(scores[-1])})


# ============================================
# ROTAS M03 — TEXTO DISPLAY
# ============================================

@app.route("/m03-preview")
def m03_preview():
    """Tela de preview do fluxo M03 (passo-a-passo)."""
    return send_from_directory("interface", "m03-preview.html")


@app.route("/modulo03/<path:arquivo>")
def modulo03_estatico(arquivo):
    """Serve arquivos estáticos do M03 (ex.: display.html)."""
    return send_from_directory("modulo03", arquivo)


@app.route("/api/m01-check", methods=["GET"])
def api_m01_check():
    """Verifica se M01 foi executado e retorna markdown."""
    curso = request.args.get("curso", "").strip()
    codigo = request.args.get("codigo", "").strip()
    disciplina = request.args.get("disciplina", "").strip()
    aula = request.args.get("aula", "").strip()

    try:
        aula_num = int(aula)
    except ValueError:
        return jsonify({"ok": False, "erro": "Número da aula inválido."}), 400

    raiz = Path(cfg()["raiz"]).expanduser()
    pasta_aula = (
        raiz / "cursos" / pastas.slugify(curso)
        / pastas.nome_pasta_disciplina(codigo, disciplina)
        / "aulas" / f"{aula_num:02d}"
    )

    if not pasta_aula.exists():
        return jsonify({"ok": False, "erro": "Pasta da aula não encontrada."}), 404

    # Procurar markdown em 02_markdown
    markdown_dir = pasta_aula / "02_markdown"
    if not markdown_dir.exists():
        return jsonify({"ok": False, "erro": "M01 não executado — sem markdown."}), 404

    md_files = list(markdown_dir.glob("*.md"))
    if not md_files:
        return jsonify({"ok": False, "erro": "Nenhum arquivo .md encontrado."}), 404

    md_path = md_files[0]
    markdown = md_path.read_text(encoding="utf-8")

    return jsonify({
        "ok": True,
        "markdown": markdown,
        "caminho": str(md_path),
    })


@app.route("/api/m03-check", methods=["GET"])
def api_m03_check():
    """Verifica se M03 foi executado e retorna texto-display."""
    curso = request.args.get("curso", "").strip()
    codigo = request.args.get("codigo", "").strip()
    disciplina = request.args.get("disciplina", "").strip()
    aula = request.args.get("aula", "").strip()

    try:
        aula_num = int(aula)
    except ValueError:
        return jsonify({"ok": False, "erro": "Número da aula inválido."}), 400

    raiz = Path(cfg()["raiz"]).expanduser()
    pasta_aula = (
        raiz / "cursos" / pastas.slugify(curso)
        / pastas.nome_pasta_disciplina(codigo, disciplina)
        / "aulas" / f"{aula_num:02d}"
    )

    if not pasta_aula.exists():
        return jsonify({"ok": False, "erro": "Pasta da aula não encontrada."}), 404

    # Procurar texto-display em 03_reformulado
    reformulado_dir = pasta_aula / "03_reformulado"
    if not reformulado_dir.exists():
        return jsonify({"ok": False, "erro": "M03 não executado."}), 404

    display_path = reformulado_dir / "texto-display.md"
    meta_path = reformulado_dir / "display_meta.json"

    if not display_path.exists():
        return jsonify({"ok": False, "erro": "texto-display.md não encontrado."}), 404

    markdown = display_path.read_text(encoding="utf-8")
    meta = None
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    # Contar imagens extraídas pelo M01 (04_imagens/antigas/)
    qtd_imagens_m01 = 0
    imagens_dir = pasta_aula / "04_imagens" / "antigas"
    if imagens_dir.exists():
        qtd_imagens_m01 = len([f for f in imagens_dir.iterdir() if f.is_file() and f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.webp']])

    return jsonify({
        "ok": True,
        "markdown": markdown,
        "meta": meta,
        "caminho": str(display_path),
        "imagens_m01": qtd_imagens_m01,
    })


@app.route("/api/m02-decisao", methods=["POST"])
def api_m02_decisao():
    """Processa decisão do M02 (APROVAR ou RECRIAR)."""
    curso = request.args.get("curso", "").strip()
    codigo = request.args.get("codigo", "").strip()
    disciplina = request.args.get("disciplina", "").strip()
    aula = request.args.get("aula", "")
    decisao = request.args.get("decisao", "").strip().lower()

    if not (curso and codigo and disciplina and aula):
        return jsonify({"ok": False, "erro": "Parâmetros inválidos."}), 400

    try:
        aula_num = int(aula)
    except ValueError:
        return jsonify({"ok": False, "erro": "Número da aula inválido."}), 400

    raiz = Path(cfg()["raiz"]).expanduser()
    pasta_aula = (
        raiz / "cursos" / pastas.slugify(curso)
        / pastas.nome_pasta_disciplina(codigo, disciplina)
        / "aulas" / f"{aula_num:02d}"
    )

    if not pasta_aula.exists():
        return jsonify({"ok": False, "erro": "Pasta da aula não encontrada."}), 404

    if decisao == "recrir":
        # Mover para incubadora
        incubadora_dir = pasta_aula / "07_incubadora" / "material_atualizado"
        incubadora_dir.mkdir(parents=True, exist_ok=True)

        # Copiar markdown e score para incubadora
        markdown_dir = pasta_aula / "02_markdown"
        avaliacao_dir = pasta_aula / "03_avaliacao"

        if markdown_dir.exists():
            for f in markdown_dir.iterdir():
                shutil.copy2(f, incubadora_dir / f.name)
        if avaliacao_dir.exists():
            for f in avaliacao_dir.iterdir():
                shutil.copy2(f, incubadora_dir / f.name)

        # Atualizar _log.json
        log_path = pasta_aula / "_log.json"
        if log_path.exists():
            log = json.loads(log_path.read_text(encoding="utf-8"))
            if isinstance(log, dict):
                log["veredito_m02"] = "RECRIAR"
                log["decisao_timestamp"] = datetime.now().isoformat()
                log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")

        return jsonify({
            "ok": True,
            "mensagem": "Material movido para 07_incubadora/material_atualizado",
        })

    return jsonify({"ok": False, "erro": "Decisão não reconhecida."}), 400


def _executar_m03_via_api(pasta_aula: Path, forcar: bool = False) -> dict:
    """Executa M03 chamando Anthropic API diretamente, sem terminal."""
    import re
    try:
        import anthropic
    except ImportError:
        return {"ok": False, "erro": "SDK Anthropic não instalado. Rode: pip install anthropic"}

    raiz = Path(__file__).parent
    skill_path = raiz / "skills" / "texto-display" / "SKILL.md"
    voz_path = raiz / "docs" / "voz-unigran.md"
    skill_content = skill_path.read_text(encoding="utf-8") if skill_path.exists() else ""
    voz_content = voz_path.read_text(encoding="utf-8") if voz_path.exists() else ""

    input_files = list((pasta_aula / "02_markdown").glob("*.md"))
    if not input_files:
        return {"ok": False, "erro": "Nenhum .md em 02_markdown/"}
    texto_original = input_files[0].read_text(encoding="utf-8")

    palavras_orig = len(texto_original.split())
    minimo_palavras = int(palavras_orig * 0.80)

    system_prompt = f"""Você é o Agente A da esteira UNIGRAN EAD — Módulo 03 Texto Display.

## REGRAS DE REESCRITA
{skill_content}

## VOZ E TOM
{voz_content}

## REGRA DE VOLUME — CRÍTICA
O texto original tem {palavras_orig} palavras. Sua versão display DEVE ter no mínimo {minimo_palavras} palavras.
REESCREVA e EXPANDA — nunca resuma. Cada conceito do original deve aparecer na versão display,
desenvolvido com exemplos, analogias e linguagem cotidiana. Se ao revisar seu texto perceber que
está abaixo de {minimo_palavras} palavras, expanda antes de entregar.

## CALLOUTS — SINTAXE OBRIGATÓRIA
Use exatamente estes nomes (com hífen): conceito-chave, atencao, resumo, exercicio, dica, leitura
Formato: :::conceito-chave\\n texto \\n:::

## FORMATO DE SAÍDA OBRIGATÓRIO
Produza a resposta em DUAS seções separadas por tags:
1. Entre <TEXTO_DISPLAY> e </TEXTO_DISPLAY>: o markdown reformulado completo
2. Entre <DISPLAY_META> e </DISPLAY_META>: o JSON de metadados conforme schema do SKILL.md

Não inclua nenhum texto fora dessas duas tags."""

    user_message = f"""Reformule o markdown abaixo para versão display de tela seguindo todas as regras.
LEMBRE: mínimo de {minimo_palavras} palavras na versão final.

--- MATERIAL ORIGINAL ({palavras_orig} palavras) ---
{texto_original}
--- FIM DO MATERIAL ORIGINAL ---"""

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=16384,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        resposta = response.content[0].text

        texto_match = re.search(r'<TEXTO_DISPLAY>(.*?)</TEXTO_DISPLAY>', resposta, re.DOTALL)
        meta_match = re.search(r'<DISPLAY_META>(.*?)</DISPLAY_META>', resposta, re.DOTALL)

        texto_display = texto_match.group(1).strip() if texto_match else resposta.strip()
        meta_json = {}
        if meta_match:
            try:
                meta_json = json.loads(meta_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        output_dir = pasta_aula / "03_reformulado"
        output_dir.mkdir(parents=True, exist_ok=True)
        display_path = output_dir / "texto-display.md"
        meta_path = output_dir / "display_meta.json"

        if display_path.exists() and forcar:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy2(display_path, output_dir / f"texto-display_v{ts}.md")
            if meta_path.exists():
                shutil.copy2(meta_path, output_dir / f"display_meta_v{ts}.json")

        display_path.write_text(texto_display, encoding="utf-8")

        palavras_orig = len(texto_original.split())
        palavras_display = len(texto_display.split())
        meta_json.update({
            "modelo": "claude-sonnet-4-6",
            "timestamp": datetime.now().isoformat(),
            "volume_original": palavras_orig,
            "volume_display": palavras_display,
            "proporcao_pct": round(palavras_display / palavras_orig * 100, 1) if palavras_orig else 0,
            "marcadores_img": re.findall(r'\[IMG-\d+(?:\s+alt="[^"]*")?\]', texto_display),
            "marcadores_video": re.findall(r'\[VIDEO-\d+\]', texto_display),
            "glossario": "## Glossário" in texto_display,
        })
        meta_path.write_text(json.dumps(meta_json, indent=2, ensure_ascii=False), encoding="utf-8")

        return {"ok": True, "markdown": texto_display, "meta": meta_json}

    except Exception as e:
        return {"ok": False, "erro": f"{type(e).__name__}: {e}"}


@app.route("/api/m03-executar", methods=["POST"])
def api_m03_executar():
    """Executa o M03 — Texto Display via API Anthropic direta (sem terminal)."""
    dados = request.get_json() or {}
    curso = dados.get("curso", "").strip()
    codigo = dados.get("codigo", "").strip()
    disciplina = dados.get("disciplina", "").strip()
    aula = dados.get("aula", "")
    forcar = dados.get("forcar", False)

    if not (curso and codigo and disciplina and aula):
        return jsonify({"ok": False, "erro": "Parâmetros inválidos."}), 400

    try:
        aula_num = int(aula)
    except ValueError:
        return jsonify({"ok": False, "erro": "Número da aula inválido."}), 400

    raiz = Path(cfg()["raiz"]).expanduser()
    pasta_aula = (
        raiz / "cursos" / pastas.slugify(curso)
        / pastas.nome_pasta_disciplina(codigo, disciplina)
        / "aulas" / f"{aula_num:02d}"
    )

    if not pasta_aula.exists():
        return jsonify({"ok": False, "erro": "Pasta da aula não encontrada."}), 404

    markdown_dir = pasta_aula / "02_markdown"
    if not markdown_dir.exists() or not list(markdown_dir.glob("*.md")):
        return jsonify({"ok": False, "erro": "Material não extraído (M01 pendente)."}), 400

    display_path = pasta_aula / "03_reformulado" / "texto-display.md"
    if display_path.exists() and not forcar:
        markdown = display_path.read_text(encoding="utf-8")
        return jsonify({"ok": True, "markdown": markdown, "ja_existia": True})

    score_path = pasta_aula / "03_avaliacao" / "score_v01.json"
    if score_path.exists():
        score = json.loads(score_path.read_text(encoding="utf-8"))
        veredito_raw = score.get("veredito", "")
        veredito = veredito_raw.get("rotulo", "") if isinstance(veredito_raw, dict) else veredito_raw
        if veredito == "RECRIAR":
            return jsonify({"ok": False, "erro": "Veredito RECRIAR — aguardando aprovação do coordenador."}), 400

    resultado = _executar_m03_via_api(pasta_aula, forcar)

    if not resultado.get("ok"):
        return jsonify({"ok": False, "erro": resultado.get("erro")}), 500

    return jsonify({
        "ok": True,
        "markdown": resultado["markdown"],
        "meta": resultado.get("meta"),
    })


# ============================================
# ROTAS EXISTENTES
# ============================================

@app.route("/api/processar", methods=["POST"])
def api_processar():
    """
    Recebe arquivos + metadados e processa conforme flag 'modulo'.

    - modulo=extrator: roda M01 (extrator) — retorna .md + imagens
    - modulo=analise: roda M02 (analise) — stub por enquanto
    - aula="todas": separa automaticamente as 8 aulas do arquivo único
    """
    global processamento_status

    curso = request.form.get("curso", "EAD").strip()
    codigo = request.form.get("codigo", "").strip()
    disciplina = request.form.get("disciplina", "").strip()
    aula = request.form.get("aula", "").strip()
    modulo = request.form.get("modulo", "extrator").strip()  # 'extrator' ou 'analise'
    forcar = request.form.get("forcar", "false") == "true"

    if not (curso and codigo and disciplina and aula):
        return jsonify({"ok": False, "erro": "Preencha curso, código, disciplina e aula."}), 400

    # Verificar se é "todas" as aulas
    if aula.lower() == "todas":
        return processar_todas_aulas(curso, codigo, disciplina, request.files, forcar)

    try:
        aula_num = int(aula)
    except ValueError:
        return jsonify({"ok": False, "erro": "Número da aula inválido."}), 400

    # salva uploads temporariamente
    tmp = Path(tempfile.mkdtemp())
    try:
        word_path, pdf_path = _salvar_uploads(request.files, tmp)

        if not (word_path or pdf_path):
            return jsonify({"ok": False, "erro": "Envie ao menos um arquivo (Word ou PDF)."}), 400

        print(f"\n[DEBUG] Processando: curso={curso}, codigo={codigo}, disciplina={disciplina}, aula={aula_num}")
        print(f"[DEBUG] modulo={modulo}, word_path={word_path}, pdf_path={pdf_path}, forcar={forcar}")

        # Atualiza status para polling
        processamento_status = {"ativo": True, "etapa": "iniciando", "mensagem": "Iniciando processamento...", "concluido": False}

        if modulo == "analise":
            # M02 — extrai o material (M01) e roda o Agente E (avaliação)
            processamento_status["etapa"] = "analise"
            processamento_status["mensagem"] = "Extraindo material para análise..."

            r_extracao = processar_mod.processar(
                codigo, disciplina, aula_num,
                str(word_path) if word_path else None,
                str(pdf_path) if pdf_path else None,
                forcar,
                curso,
            )
            # "aula já processada" não impede a análise — material existe
            if not r_extracao.get("ok") and not r_extracao.get("aviso"):
                processamento_status["concluido"] = True
                return jsonify(r_extracao)

            # Roda Agente E — avaliação de qualidade
            processamento_status["mensagem"] = "Executando Agente E (avaliação)..."

            r_avaliacao = agente_e_mod.agente_e(
                codigo, disciplina, aula_num, curso, forcar
            )

            if not r_avaliacao.get("ok"):
                processamento_status["concluido"] = True
                return jsonify(r_avaliacao)

            processamento_status["concluido"] = True
            params = urlencode({
                "curso": curso, "codigo": codigo,
                "disciplina": disciplina, "aula": aula_num,
            })
            return jsonify({
                "ok": True,
                "status": "avaliacao_concluida",
                "redirect": f"/modulo02/laudo.html?{params}",
                "extracao": r_extracao,
                "avaliacao": r_avaliacao,
            })

        # M01 — Extrator (implementado)
        processamento_status["etapa"] = "extrator"
        processamento_status["mensagem"] = "Executando Módulo 01 — Extrator..."

        resultado = processar_mod.processar(
            codigo, disciplina, aula_num,
            str(word_path) if word_path else None,
            str(pdf_path) if pdf_path else None,
            forcar,
            curso,
        )

        print(f"[DEBUG] Resultado: {resultado.get('texto', {})}")
        processamento_status["ativo"] = False
        processamento_status["concluido"] = True
        processamento_status["resultado"] = resultado
        return jsonify(resultado)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def processar_todas_aulas(curso, codigo, disciplina, files, forcar):
    """
    Processa arquivo único contendo todas as aulas da disciplina.
    Separa automaticamente em pastas individuais (scripts/02-separar-aulas.py).
    """
    global processamento_status

    processamento_status = {
        "ativo": True,
        "etapa": "separando",
        "mensagem": "Separando aulas do arquivo único...",
        "concluido": False
    }

    tmp = Path(tempfile.mkdtemp())
    try:
        _, pdf_path = _salvar_uploads(files, tmp)

        if not pdf_path:
            return jsonify({"ok": False, "erro": "Envie um arquivo PDF para processar todas as aulas."}), 400

        resultado = separar_mod.separar_aulas(
            codigo, disciplina, str(pdf_path), curso, forcar
        )

        if resultado.get("ok"):
            return jsonify({
                "ok": True,
                "tipo": "todas_aulas",
                "total_aulas": resultado["total_aulas"],
                "aulas_processadas": resultado["aulas_processadas"],
                "aulas_puladas": resultado.get("aulas_puladas", []),
                "pasta_disciplina": resultado["pasta_disciplina"],
                "detalhes": resultado.get("detalhes", {})
            })
        return jsonify({
            "ok": False,
            "erro": resultado.get("erro", "Erro ao separar aulas")
        })

    except Exception as e:
        print(f"[ERRO] processar_todas_aulas: {e}")
        return jsonify({"ok": False, "erro": str(e)}), 500
    finally:
        processamento_status["ativo"] = False
        processamento_status["concluido"] = True
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    c = cfg()["servidor"]
    print(f"\n🟢 Interface disponível em http://{c['host']}:{c['porta']}\n")
    app.run(host=c["host"], port=c["porta"], debug=False)
