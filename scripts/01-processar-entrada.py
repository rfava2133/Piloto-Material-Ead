#!/usr/bin/env python3
"""
01-processar-entrada.py — Orquestrador da Etapa 1 da esteira UNIGRAN EAD.

Faz:
  1. Cria estrutura de pastas da aula
  2. Copia Word/PDF para 01_source/
  3. Converte Word → Markdown + extrai imagens do Word (Pandoc)
  4. Extrai imagens do PDF (PyMuPDF)
  5. Registra log

Uso (linha de comando):
  python3 01-processar-entrada.py \
      --codigo ADM \
      --disciplina "Fundamentos de Administração" \
      --aula 1 \
      --word /caminho/ADM-01.docx \
      --pdf /caminho/ADM-01.pdf

Também é chamado pela interface HTML via servidor.py.
"""
import argparse
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from lib import pastas, extrair_word, extrair_pdf, extrair_pdf_texto, logger


def carregar_config() -> dict:
    cfg_path = Path(__file__).parent / "config.yml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def processar(codigo, disciplina, numero_aula, word_path=None, pdf_path=None,
              forcar=False, curso="EAD"):
    cfg = carregar_config()
    raiz = Path(cfg["raiz"]).expanduser()

    aid = pastas.id_aula(codigo, numero_aula)

    # 1. estrutura de pastas
    pasta_aula = pastas.criar_estrutura(
        raiz, codigo, disciplina, numero_aula, cfg["subpastas"], curso
    )

    # checagem de reprocessamento
    if pastas.aula_ja_processada(pasta_aula) and not forcar:
        return {"ok": False, "aviso": "Aula já processada. Use forcar=True para reprocessar.",
                "pasta": str(pasta_aula)}

    resultado = {"aula_id": aid, "pasta": str(pasta_aula)}

    # 2. copiar fontes para 01_source/
    source = pasta_aula / "01_source"
    if word_path:
        word_dest = source / f"{aid}.docx"
        shutil.copy2(word_path, word_dest)
        word_path = word_dest
    if pdf_path:
        pdf_dest = source / f"{aid}-original.pdf"
        shutil.copy2(pdf_path, pdf_dest)
        pdf_path = pdf_dest

    # 3. Extrair texto (Word → Pandoc OU PDF → pymupdf4llm)
    if word_path:
        r_word = extrair_word.converter_word(word_path, pasta_aula, aid)
        resultado["texto"] = r_word
        resultado["texto"]["fonte"] = "word"
    elif pdf_path:
        r_pdf_texto = extrair_pdf_texto.extrair_texto_pdf(pdf_path, pasta_aula, aid)
        resultado["texto"] = r_pdf_texto
        resultado["texto"]["fonte"] = "pdf"
    else:
        resultado["texto"] = {"ok": False, "aviso": "Nenhum arquivo fornecido"}

    # 4. Imagens do PDF (se veio PDF)
    if pdf_path:
        ext = cfg["extracao"]
        r_pdf = extrair_pdf.extrair_imagens_pdf(
            pdf_path, pasta_aula,
            min_largura=ext["pymupdf_min_largura"],
            min_altura=ext["pymupdf_min_altura"],
            formatos=ext["formatos_imagem"],
        )
        resultado["imagens"] = r_pdf
    else:
        resultado["imagens"] = {"ok": False, "aviso": "Sem PDF fornecido"}

    # 5. log
    logger.registrar(pasta_aula, resultado)

    resultado["ok"] = True
    return resultado


def main():
    p = argparse.ArgumentParser(description="Etapa 1 — Extração de material")
    p.add_argument("--codigo", required=True, help="Código da disciplina (ex: ADM)")
    p.add_argument("--disciplina", required=True, help="Nome completo da disciplina")
    p.add_argument("--aula", type=int, required=True, help="Número da aula")
    p.add_argument("--curso", default="EAD", help="Nome do curso (ex: Administracao)")
    p.add_argument("--word", help="Caminho do .docx")
    p.add_argument("--pdf", help="Caminho do .pdf")
    p.add_argument("--forcar", action="store_true", help="Reprocessar se já existir")
    args = p.parse_args()

    r = processar(args.codigo, args.disciplina, args.aula,
                  args.word, args.pdf, args.forcar, args.curso)

    print("\n" + "=" * 50)
    if r.get("ok"):
        print(f"✅ {r['aula_id']} processada")
        print(f"📂 {r['pasta']}")
        if r["texto"].get("ok"):
            fonte = r["texto"].get("fonte", "desconhecida")
            print(f"📄 Markdown gerado ({fonte})")
            if fonte == "word":
                print(f"🖼  Imagens Word: {r['texto'].get('qtd_imagens_word', 0)}")
            elif fonte == "pdf":
                print(f"📄 Páginas PDF: {r['texto'].get('qtd_paginas', 0)}")
        if r.get("imagens", {}).get("ok"):
            print(f"🖼  Imagens PDF extraídas: {r['imagens']['qtd_imagens_pdf']} "
                  f"(descartadas: {r['imagens']['descartadas_pequenas']})")
    else:
        print(f"⚠  {r.get('aviso') or r.get('erro')}")
    print("=" * 50)


if __name__ == "__main__":
    main()
