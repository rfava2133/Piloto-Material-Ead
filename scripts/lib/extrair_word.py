"""
extrair_word.py — Converte Word para Markdown e extrai imagens embutidas.
Usa Pandoc (precisa estar instalado: brew install pandoc).
"""
import subprocess
from pathlib import Path


def converter_word(docx: Path, pasta_aula: Path, id_aula: str) -> dict:
    """
    Converte .docx para Markdown limpo e extrai imagens embutidas.

    - Markdown vai para 02_markdown/{id_aula}.md
    - Imagens extraídas vão para 04_imagens/antigas/

    Retorna dict com resultado.
    """
    md_destino = pasta_aula / "02_markdown" / f"{id_aula}.md"
    midia_destino = pasta_aula / "04_imagens" / "antigas"
    midia_destino.mkdir(parents=True, exist_ok=True)

    comando = [
        "pandoc",
        str(docx),
        "-o", str(md_destino),
        "--wrap=none",                       # não quebra linhas artificialmente
        "--extract-media", str(midia_destino),
        "-t", "markdown_strict+pipe_tables",  # markdown limpo + tabelas
    ]

    try:
        subprocess.run(comando, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        return {"ok": False, "erro": e.stderr, "etapa": "pandoc"}
    except FileNotFoundError:
        return {"ok": False, "erro": "Pandoc não encontrado. Rode: brew install pandoc",
                "etapa": "pandoc"}

    # Pandoc cria subpasta 'media' — move imagens para antigas/ direto
    media_sub = midia_destino / "media"
    imagens_extraidas = []
    if media_sub.exists():
        for img in media_sub.iterdir():
            if img.is_file():
                novo = midia_destino / f"word-{img.name}"
                img.rename(novo)
                imagens_extraidas.append(novo.name)
        media_sub.rmdir()

    return {
        "ok": True,
        "markdown": str(md_destino),
        "imagens_word": imagens_extraidas,
        "qtd_imagens_word": len(imagens_extraidas),
    }
