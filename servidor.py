#!/usr/bin/env python3
"""
servidor.py — Servidor local que conecta a interface HTML aos scripts do MÓDULO 01 — EXTRATOR.

Roda em http://127.0.0.1:5000
Instalar: pip install flask pyyaml

Uso:
  python3 servidor.py
  (depois abra http://127.0.0.1:5000 no navegador)
"""
import sys
import tempfile
import csv
from pathlib import Path
from collections import defaultdict

from flask import Flask, request, jsonify, send_from_directory
import yaml

sys.path.insert(0, str(Path(__file__).parent / "scripts"))
import importlib.util

# importa o orquestrador 01-processar-entrada.py (nome com hífen)
spec = importlib.util.spec_from_file_location(
    "processar", Path(__file__).parent / "scripts" / "01-processar-entrada.py"
)
processar_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(processar_mod)

app = Flask(__name__, static_folder="interface")

# Estado global para status do processamento (em memória)
processamento_status = {"ativo": False, "etapa": "", "mensagem": "", "concluido": False}


def cfg():
    with open(Path(__file__).parent / "scripts" / "config.yml", encoding="utf-8") as f:
        return yaml.safe_load(f)


@app.route("/")
def index():
    return send_from_directory("interface", "index.html")


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


@app.route("/api/processar", methods=["POST"])
def api_processar():
    """
    Recebe arquivos + metadados e processa conforme flag 'modulo'.

    - modulo=extrator: roda M01 (extrator) — retorna .md + imagens
    - modulo=analise: roda M02 (analise) — stub por enquanto, retorna em_breve
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

    try:
        aula_num = int(aula)
    except ValueError:
        return jsonify({"ok": False, "erro": "Número da aula inválido."}), 400

    # salva uploads temporariamente
    tmp = Path(tempfile.mkdtemp())
    word_path = pdf_path = None

    if "word" in request.files and request.files["word"].filename:
        word_path = tmp / request.files["word"].filename
        request.files["word"].save(word_path)

    if "pdf" in request.files and request.files["pdf"].filename:
        pdf_path = tmp / request.files["pdf"].filename
        request.files["pdf"].save(pdf_path)

    if not (word_path or pdf_path):
        return jsonify({"ok": False, "erro": "Envie ao menos um arquivo (Word ou PDF)."}), 400

    print(f"\n[DEBUG] Processando: curso={curso}, codigo={codigo}, disciplina={disciplina}, aula={aula_num}")
    print(f"[DEBUG] modulo={modulo}, word_path={word_path}, pdf_path={pdf_path}, forcar={forcar}")

    # Atualiza status para polling
    processamento_status = {"ativo": True, "etapa": "iniciando", "mensagem": "Iniciando processamento...", "concluido": False}

    if modulo == "analise":
        # M02 — Análise de conteúdo (stub por enquanto)
        processamento_status["etapa"] = "analise"
        processamento_status["mensagem"] = "Módulo 02 em desenvolvimento. Use 'extrator' por enquanto."
        processamento_status["concluido"] = True
        return jsonify({
            "ok": True,
            "status": "em_breve",
            "mensagem": "Módulo 02 (Análise de Conteúdo) será implementado em breve.",
            "redirect": "/modulo02/laudo.html"
        })
    else:
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


if __name__ == "__main__":
    c = cfg()["servidor"]
    print(f"\n🟢 Interface disponível em http://{c['host']}:{c['porta']}\n")
    app.run(host=c["host"], port=c["porta"], debug=False)
