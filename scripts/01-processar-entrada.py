#!/usr/bin/env python3
"""
01-processar-entrada.py — Orquestrador do MÓDULO 01 — EXTRATOR da esteira UNIGRAN EAD.

Faz:
  1. Cria estrutura de pastas da aula
  2. Copia Word/PDF para 01_source/
  3. Converte Word → Markdown + extrai imagens do Word (Pandoc)
  4. Extrai imagens do PDF (PyMuPDF)
  5. Normaliza referências de imagens para marcadores [IMG-NN]
  6. Registra log

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
import re
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


def normalizar_marcadores_imagens(md_path: Path) -> dict:
    """
    Normaliza referências de imagens no markdown para o formato [IMG-NN].

    Detecta padrões como:
    - **Figura 1 -** descrição
    - **Figura 2:** descrição
    - Figura 1: descrição
    - ![alt](media/image.png)

    E substitui por: [IMG-01 alt="descrição"]

    Retorna dict com quantidade normalizada.
    """
    if not md_path.exists():
        return {"ok": False, "aviso": "Markdown não encontrado"}

    texto = md_path.read_text(encoding="utf-8")
    original = texto
    contador = 0

    # Padrão 1: **Figura N -** ou **Figura N:** (negrito)
    def replace_figura_negrito(m):
        nonlocal contador
        contador += 1
        num = m.group(1)
        desc = m.group(2).strip()
        return f'[IMG-{num:02d} alt="{desc}"]'

    texto = re.sub(
        r'\*\*Figura\s+(\d+)\s*[-:]\*\*\s*(.+?)(?=\n|$)',
        replace_figura_negrito,
        texto,
        flags=re.IGNORECASE
    )

    # Padrão 2: Figura N: descrição (sem negrito)
    def replace_figura_simples(m):
        nonlocal contador
        contador += 1
        num = m.group(1)
        desc = m.group(2).strip()
        return f'[IMG-{num:02d} alt="{desc}"]'

    texto = re.sub(
        r'(?<!\*\*)Figura\s+(\d+)\s*:\s*(.+?)(?=\n|$)',
        replace_figura_simples,
        texto,
        flags=re.IGNORECASE
    )

    # Padrão 3: ![alt](media/image.png) ou ![alt](image.png)
    def replace_markdown_img(m):
        nonlocal contador
        contador += 1
        alt = m.group(1) or ''
        return f'[IMG-{contador:02d} alt="{alt}"]'

    texto = re.sub(
        r'!\[([^\]]*)\]\([^)]+\)',
        replace_markdown_img,
        texto
    )

    # Salvar se houve mudança
    if texto != original:
        md_path.write_text(texto, encoding="utf-8")
        return {"ok": True, "qtd_imagens_normalizadas": contador}

    return {"ok": True, "qtd_imagens_normalizadas": 0}


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
        r_word = extrair_word.converter_word(word_path, pasta_aula, codigo, numero_aula)
        resultado["texto"] = r_word
        resultado["texto"]["fonte"] = "word"
    elif pdf_path:
        r_pdf_texto = extrair_pdf_texto.extrair_texto_pdf(pdf_path, pasta_aula, codigo, numero_aula)
        resultado["texto"] = r_pdf_texto
        resultado["texto"]["fonte"] = "pdf"
    else:
        resultado["texto"] = {"ok": False, "aviso": "Nenhum arquivo fornecido"}

    # 3b. Normalizar referências de imagens para marcadores [IMG-NN]
    if resultado["texto"].get("ok") and resultado["texto"].get("markdown"):
        md_path = Path(resultado["texto"]["markdown"])
        r_norm = normalizar_marcadores_imagens(md_path)
        resultado["texto"]["imagens_normalizadas"] = r_norm

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

    # Consolidar contagem de imagens
    qtd_word = resultado.get("texto", {}).get("qtd_imagens_word", 0)
    qtd_pdf = resultado.get("imagens", {}).get("qtd_imagens_pdf", 0)
    qtd_normalizadas = resultado.get("texto", {}).get("imagens_normalizadas", {}).get("qtd_imagens_normalizadas", 0)
    resultado["total_imagens_referenciadas"] = qtd_normalizadas

    resultado["ok"] = True
    return resultado


def main():
    p = argparse.ArgumentParser(description="MÓDULO 01 — EXTRATOR de material")
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
            # Imagens normalizadas (marcadores [IMG-NN])
            qtd_norm = r["texto"].get("imagens_normalizadas", {}).get("qtd_imagens_normalizadas", 0)
            if qtd_norm > 0:
                print(f"🏷️  Marcadores [IMG-NN] criados: {qtd_norm}")
        if r.get("imagens", {}).get("ok"):
            print(f"🖼  Imagens PDF extraídas: {r['imagens']['qtd_imagens_pdf']} "
                  f"(descartadas: {r['imagens']['descartadas_pequenas']})")
    else:
        print(f"⚠  {r.get('aviso') or r.get('erro')}")
    print("=" * 50)


if __name__ == "__main__":
    main()
