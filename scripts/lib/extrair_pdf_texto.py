"""
extrair_pdf_texto.py — Extrai texto de PDF e converte para Markdown.
Usa pymupdf4llm para preservação de formatação.

Instalar: pip install pymupdf4llm
"""
from pathlib import Path

try:
    import pymupdf4llm
except ImportError:
    pymupdf4llm = None


def extrair_texto_pdf(pdf: Path, pasta_aula: Path, id_aula: str) -> dict:
    """
    Extrai texto de um PDF e salva como Markdown.

    - Markdown vai para 02_markdown/{id_aula}.md

    Retorna dict com resultado.
    """
    if pymupdf4llm is None:
        return {
            "ok": False,
            "erro": "pymupdf4llm não instalado. Rode: pip install pymupdf4llm",
            "etapa": "pymupdf4llm"
        }

    md_destino = pasta_aula / "02_markdown" / f"{id_aula}.md"
    md_destino.parent.mkdir(parents=True, exist_ok=True)

    try:
        # pymupdf4llm.to_markdown() retorna string Markdown
        md_text = pymupdf4llm.to_markdown(str(pdf))

        with open(md_destino, "w", encoding="utf-8") as f:
            f.write(md_text)

        # Conta páginas do PDF
        import fitz  # PyMuPDF para contar páginas
        doc = fitz.open(str(pdf))
        qtd_paginas = len(doc)
        doc.close()

        return {
            "ok": True,
            "markdown": str(md_destino),
            "qtd_paginas": qtd_paginas,
            "fonte": "pdf"
        }

    except Exception as e:
        return {
            "ok": False,
            "erro": str(e),
            "etapa": "pymupdf4llm"
        }
