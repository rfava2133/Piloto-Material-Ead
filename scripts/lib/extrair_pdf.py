"""
extrair_pdf.py — Extrai imagens de um PDF usando PyMuPDF (fitz).
Instalar: pip install pymupdf
"""
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


def extrair_imagens_pdf(pdf: Path, pasta_aula: Path,
                        min_largura: int = 100, min_altura: int = 100,
                        formatos: list = None) -> dict:
    """
    Extrai imagens de um PDF para 04_imagens/antigas/.
    Filtra imagens muito pequenas (ícones, ruído) por min_largura/min_altura.

    Retorna dict com resultado.
    """
    if fitz is None:
        return {"ok": False, "erro": "PyMuPDF não instalado. Rode: pip install pymupdf",
                "etapa": "pymupdf"}

    if formatos is None:
        formatos = ["png", "jpg", "jpeg"]

    destino = pasta_aula / "04_imagens" / "antigas"
    destino.mkdir(parents=True, exist_ok=True)

    imagens_extraidas = []
    descartadas = 0

    try:
        doc = fitz.open(str(pdf))
    except Exception as e:
        return {"ok": False, "erro": str(e), "etapa": "abrir_pdf"}

    contador = 0
    for num_pagina in range(len(doc)):
        pagina = doc[num_pagina]
        for img_info in pagina.get_images(full=True):
            xref = img_info[0]
            base = doc.extract_image(xref)
            ext = base["ext"].lower()
            if ext not in formatos:
                continue

            # filtro de tamanho
            largura = base.get("width", 0)
            altura = base.get("height", 0)
            if largura < min_largura or altura < min_altura:
                descartadas += 1
                continue

            contador += 1
            nome = f"pdf-p{num_pagina+1:03d}-{contador:03d}.{ext}"
            caminho = destino / nome
            with open(caminho, "wb") as f:
                f.write(base["image"])
            imagens_extraidas.append(nome)

    doc.close()

    return {
        "ok": True,
        "imagens_pdf": imagens_extraidas,
        "qtd_imagens_pdf": len(imagens_extraidas),
        "descartadas_pequenas": descartadas,
    }
