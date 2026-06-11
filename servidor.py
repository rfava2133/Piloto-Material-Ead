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
import json
import shutil
import tempfile
import csv
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlencode

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

app = Flask(__name__, static_folder="interface")

# Estado global para status do processamento (em memória)
processamento_status = {"ativo": False, "etapa": "", "mensagem": "", "concluido": False}


def cfg():
    with open(Path(__file__).parent / "scripts" / "config.yml", encoding="utf-8") as f:
        return yaml.safe_load(f)


@app.route("/")
def index():
    return send_from_directory("interface", "index.html")


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

        # Se o Agente E não preencheu bibliografia, extrai do markdown da aula (M01)
        a2 = score["fundamentos"].get("A2", {})
        if not a2.get("fontes_verificadas"):
            fontes_md = ref_mod.extrair_referencias_pasta(pasta_aula, numero_aula=aula_num)
            if fontes_md:
                a2["fontes_verificadas"] = fontes_md
                just = (a2.get("justificativa") or "").strip()
                if just in ("Referências localizáveis.", "Verificado via skill analista-conteudo.", ""):
                    a2["justificativa"] = (
                        f"{len(fontes_md)} referência(s) citada(s) no material — "
                        "validação externa pendente (Agente E)."
                    )
                score["fundamentos"]["A2"] = a2
    except (json.JSONDecodeError, OSError, TypeError, ValueError) as e:
        return jsonify({
            "status": "score_invalido",
            "aula_id": aula_id,
            "mensagem": f"Score inválido: {e}",
            "arquivo": str(scores[-1]) if scores else None,
        }), 404

    return jsonify({"status": "avaliada", "score": score, "arquivo": str(scores[-1])})


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
