#!/usr/bin/env python3
"""
servidor.py — Servidor local que conecta a interface HTML aos scripts da Etapa 1.

Roda em http://127.0.0.1:5000
Instalar: pip install flask pyyaml

Uso:
  python3 servidor.py
  (depois abra http://127.0.0.1:5000 no navegador)
"""
import sys
import tempfile
from pathlib import Path

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


def cfg():
    with open(Path(__file__).parent / "scripts" / "config.yml", encoding="utf-8") as f:
        return yaml.safe_load(f)


@app.route("/")
def index():
    return send_from_directory("interface", "index.html")


@app.route("/api/processar", methods=["POST"])
def api_processar():
    """Recebe arquivos + metadados, roda a Etapa 1, devolve resultado JSON."""
    curso = request.form.get("curso", "EAD").strip()
    codigo = request.form.get("codigo", "").strip()
    disciplina = request.form.get("disciplina", "").strip()
    aula = request.form.get("aula", "").strip()
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

    resultado = processar_mod.processar(
        codigo, disciplina, aula_num,
        str(word_path) if word_path else None,
        str(pdf_path) if pdf_path else None,
        forcar,
        curso,
    )
    return jsonify(resultado)


if __name__ == "__main__":
    c = cfg()["servidor"]
    print(f"\n🟢 Interface disponível em http://{c['host']}:{c['porta']}\n")
    app.run(host=c["host"], port=c["porta"], debug=False)
