#!/usr/bin/env python3
"""
02-separar-aulas.py — Detecta e separa automaticamente as aulas de um PDF único.

Estratégia (por PÁGINA, não por posição de texto):
  1. Abre o PDF e procura, página a página, o início de cada aula:
     - Detector A: página de abertura com "NN" / "Aula" em linhas separadas
       (padrão das apostilas diagramadas UNIGRAN)
     - Detector B: linha "Aula NN" ou "# Aula NN — Título" no texto da página
  2. Páginas de sumário (3+ marcadores distintos de aula) são ignoradas.
  3. Cada aula = intervalo de páginas [início, próximo início - 1].
  4. Por aula: gera Markdown (pymupdf4llm) + extrai imagens (PyMuPDF)
     na estrutura padrão do M01.

Uso:
  python3 scripts/02-separar-aulas.py \
      --codigo TDI \
      --disciplina "Paisagismo e Sustentabilidade" \
      --pdf templates_design/paisagismo_sustentabilidade.pdf \
      --curso "design-interiores"
"""
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from lib import pastas, extrair_pdf, logger

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import pymupdf4llm
except ImportError:
    pymupdf4llm = None


# Linha "Aula NN" isolada ou "# Aula NN — Título" (Detector B)
RE_AULA_INLINE = re.compile(
    r"^(?:#+\s*)?aula\s+(\d{1,2})\b\s*(?:[—–:.\-].*)?$",
    re.MULTILINE | re.IGNORECASE,
)
RE_SO_NUMERO = re.compile(r"^\d{1,2}$")
# Linha de sumário: "Título......................NN"
RE_LINHA_SUMARIO = re.compile(r"\.{3,}\s*(\d{1,3})\s*$")
# "Conversa Inicial" como heading ou linha isolada
RE_CONVERSA_INICIAL = re.compile(
    r"^(?:#+\s*)?conversa\s+inicial\s*$",
    re.MULTILINE | re.IGNORECASE,
)


def carregar_config() -> dict:
    cfg_path = Path(__file__).parent / "config.yml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _detectar_abertura(linhas: list) -> int | None:
    """
    Detector A — página de abertura de aula diagramada:
    um número isolado ("01") adjacente à palavra "Aula" em linhas separadas.
    Retorna o número da aula ou None.
    """
    primeiras = [l.strip() for l in linhas[:8] if l.strip()]
    for i, linha in enumerate(primeiras):
        if RE_SO_NUMERO.match(linha):
            vizinhas = primeiras[max(0, i - 2):i] + primeiras[i + 1:i + 3]
            if any(v.lower() == "aula" for v in vizinhas):
                return int(linha)
    return None


def _parse_sumario(texto: str) -> dict:
    """
    Extrai do sumário {numero_aula: pagina_impressa}.
    Cada "Aula NN" é seguida do título com pontilhado e número de página
    (o título pode ocupar mais de uma linha — ex.: Aula 06).
    """
    linhas = texto.splitlines()
    paginas = {}
    aula_atual = None
    for linha in linhas:
        # Detecta "Conversa inicial" no sumário → aula 0
        if re.match(r"^\s*conversa\s+inicial\s*$", linha, re.IGNORECASE):
            aula_atual = 0
            continue
        m_aula = re.match(r"^\s*aula\s+(\d{1,2})\s*$", linha, re.IGNORECASE)
        if m_aula:
            aula_atual = int(m_aula.group(1))
            continue
        if aula_atual is not None:
            m_pag = RE_LINHA_SUMARIO.search(linha)
            if m_pag:
                paginas[aula_atual] = int(m_pag.group(1))
                aula_atual = None
    return paginas


def detectar_inicios_aulas(doc) -> dict:
    """
    Retorna {numero_aula: indice_pagina_0based} combinando duas fontes:

    1. Detecção direta: página de abertura ("NN"/"Aula") ou linha "Aula NN".
       Páginas de sumário (3+ aulas citadas) são puladas como divisor,
       mas têm suas páginas impressas parseadas.
    2. Sumário: preenche as aulas que a detecção direta não encontrou
       (capas de aula em que o título não é texto extraível). O offset
       impresso → índice do PDF é calibrado pelas aulas detectadas em (1).
    """
    inicios = {}
    sumario = {}

    for idx in range(len(doc)):
        texto = doc[idx].get_text()
        linhas = texto.splitlines()

        marcadores = {int(m) for m in RE_AULA_INLINE.findall(texto)}
        tem_conversa = bool(RE_CONVERSA_INICIAL.search(texto))

        if len(marcadores) >= 3:
            if not sumario:
                sumario = _parse_sumario(texto)
            continue  # página de sumário não é divisor

        # Detecta "Conversa Inicial" como aula 0
        if tem_conversa and 0 not in inicios:
            inicios[0] = idx
            print(f"   ℹ️  Conversa Inicial detectada na p.{idx+1}")
            continue

        num = _detectar_abertura(linhas)
        if num is None and len(marcadores) == 1:
            num = marcadores.pop()

        if num is None or num in inicios:
            continue

        # exige sequência crescente (evita falsos positivos no meio do texto)
        nums_numerados = {k for k in inicios if k > 0}
        if nums_numerados and num <= max(nums_numerados):
            continue

        inicios[num] = idx

    # Completa com o sumário as aulas não detectadas diretamente
    if sumario:
        # calibra offset (pagina impressa N costuma ser doc[N-1])
        # usa apenas aulas numeradas (>0) para calcular offset
        offsets = [inicios[n] - (sumario[n] - 1) for n in inicios if n > 0 and n in sumario]
        offset = max(set(offsets), key=offsets.count) if offsets else 0

        for num, pag_impressa in sumario.items():
            idx = pag_impressa - 1 + offset
            if num not in inicios and 0 <= idx < len(doc):
                inicios[num] = idx
                label = "Conversa Inicial" if num == 0 else f"Aula {num:02d}"
                print(f"   ℹ️  {label}: início obtido pelo sumário (p.{idx+1})")

    return inicios


def _extrair_markdown_paginas(pdf_path: Path, paginas: list) -> str:
    """Markdown de um subconjunto de páginas (0-based)."""
    if pymupdf4llm is not None:
        try:
            return pymupdf4llm.to_markdown(str(pdf_path), pages=paginas)
        except Exception as e:
            print(f"⚠️  pymupdf4llm falhou ({e}); usando texto simples")
    doc = fitz.open(str(pdf_path))
    texto = "\n\n".join(doc[p].get_text() for p in paginas)
    doc.close()
    return texto


def _backup_se_existir(arquivo: Path):
    """Princípio 5: backup antes de sobrescrever."""
    if arquivo.exists():
        carimbo = datetime.now().strftime("%Y%m%d-%H%M%S")
        destino = arquivo.with_suffix(arquivo.suffix + f".bak-{carimbo}")
        shutil.copy2(arquivo, destino)
        print(f"   🗂  Backup criado: {destino.name}")


def separar_aulas(
    codigo: str,
    disciplina: str,
    pdf_path: str,
    curso: str = "EAD",
    forcar: bool = False,
) -> dict:
    """
    Separa automaticamente as aulas de um arquivo PDF único.
    Gera, por aula, a mesma estrutura e nomenclatura do M01.
    """
    if fitz is None:
        return {"ok": False, "erro": "PyMuPDF não instalado. Rode: pip install pymupdf"}

    cfg = carregar_config()
    raiz = Path(cfg["raiz"]).expanduser()
    ext_cfg = cfg["extracao"]
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        return {"ok": False, "erro": f"Arquivo PDF não encontrado: {pdf_path}"}

    print(f"📖 Lendo PDF: {pdf_path.name}")
    doc = fitz.open(str(pdf_path))
    total_paginas = len(doc)

    inicios = detectar_inicios_aulas(doc)
    doc.close()

    if not inicios:
        print("⚠️  Nenhuma divisão de aula encontrada. Tratando como aula única...")
        inicios = {1: 0}

    numeros = sorted(inicios)

    def _label(n):
        return "Conversa Inicial" if n == 0 else f"Aula {n:02d}"

    print(f"✅ {len(numeros)} seção(ões) detectada(s): "
          + ", ".join(f"{_label(n)} (p.{inicios[n]+1})" for n in numeros))

    aulas_processadas = []
    puladas = []
    detalhes = {}

    for i, num_aula in enumerate(numeros):
        pag_ini = inicios[num_aula]
        pag_fim = inicios[numeros[i + 1]] - 1 if i + 1 < len(numeros) else total_paginas - 1
        paginas = list(range(pag_ini, pag_fim + 1))

        print(f"\n📚 {_label(num_aula)} — páginas {pag_ini+1} a {pag_fim+1}")

        aid = pastas.id_aula(codigo, num_aula)
        pasta_aula = pastas.criar_estrutura(
            raiz, codigo, disciplina, num_aula, cfg["subpastas"], curso
        )

        if pastas.aula_ja_processada(pasta_aula) and not forcar:
            print(f"   ⏭  {aid} já processada — pulando (use forcar para reprocessar)")
            puladas.append(num_aula)
            continue

        # 01_source/ — PDF original (referência por aula, como no M01)
        pdf_dest = pasta_aula / "01_source" / f"{aid}-original.pdf"
        if not pdf_dest.exists():
            shutil.copy2(pdf_path, pdf_dest)

        # 02_markdown/ — mesma nomenclatura do M01 ({codigo}_aulaNN.md)
        markdown_path = pasta_aula / "02_markdown" / pastas.nome_arquivo_md(codigo, num_aula)
        _backup_se_existir(markdown_path)
        texto_aula = _extrair_markdown_paginas(pdf_path, paginas)
        markdown_path.write_text(texto_aula, encoding="utf-8")

        # 04_imagens/antigas/ — imagens só das páginas desta aula
        r_imgs = extrair_pdf.extrair_imagens_pdf(
            pdf_path, pasta_aula,
            min_largura=ext_cfg["pymupdf_min_largura"],
            min_altura=ext_cfg["pymupdf_min_altura"],
            formatos=ext_cfg["formatos_imagem"],
            paginas=paginas,
        )

        resultado_aula = {
            "aula_id": aid,
            "fonte": "pdf_unico",
            "paginas": [pag_ini + 1, pag_fim + 1],
            "texto": {"ok": True, "markdown": str(markdown_path)},
            "imagens": r_imgs,
        }
        logger.registrar(pasta_aula, resultado_aula)

        aulas_processadas.append(num_aula)
        detalhes[aid] = {
            "texto_path": str(markdown_path),
            "paginas": f"{pag_ini+1}-{pag_fim+1}",
            "qtd_caracteres": len(texto_aula),
            "qtd_imagens": r_imgs.get("qtd_imagens_pdf", 0),
        }
        print(f"   ✅ {aid}: {len(texto_aula)} caracteres · "
              f"{r_imgs.get('qtd_imagens_pdf', 0)} imagens")

    # _disciplina.yml na MESMA árvore onde as aulas foram criadas
    pasta_disciplina = (
        raiz / "cursos" / pastas.slugify(curso)
        / pastas.nome_pasta_disciplina(codigo, disciplina)
    )
    pasta_disciplina.mkdir(parents=True, exist_ok=True)
    yml_path = pasta_disciplina / "_disciplina.yml"
    if not yml_path.exists() or forcar:
        dados_yml = {
            "codigo": codigo.upper(),
            "nome": disciplina,
            "slug": pastas.nome_pasta_disciplina(codigo, disciplina),
            "curso": curso,
            "aulas_total": sum(1 for n in numeros if n > 0),  # CI (0) não conta como aula
            "professor": {"nome": "", "email": ""},
            "coordenador": {"nome": "", "email": ""},
        }
        yml_path.write_text(
            yaml.dump(dados_yml, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        print(f"\n📋 _disciplina.yml: {yml_path}")

    return {
        "ok": True,
        "total_aulas": len(numeros),
        "aulas_processadas": aulas_processadas,
        "aulas_puladas": puladas,
        "pasta_disciplina": str(pasta_disciplina),
        "detalhes": detalhes,
    }


def main():
    import argparse

    p = argparse.ArgumentParser(description="Separar aulas de arquivo PDF único")
    p.add_argument("--codigo", required=True, help="Código da disciplina (ex: TDI)")
    p.add_argument("--disciplina", required=True, help="Nome da disciplina")
    p.add_argument("--pdf", required=True, help="Caminho do PDF com todas as aulas")
    p.add_argument("--curso", default="EAD", help="Nome do curso")
    p.add_argument("--forcar", action="store_true", help="Reprocessar se já existir")
    args = p.parse_args()

    r = separar_aulas(args.codigo, args.disciplina, args.pdf, args.curso, args.forcar)

    print("\n" + "=" * 60)
    if r.get("ok"):
        print(f"✅ {r['total_aulas']} aula(s) detectada(s) · "
              f"{len(r['aulas_processadas'])} processada(s)")
        if r.get("aulas_puladas"):
            print(f"⏭  Puladas (já processadas): {r['aulas_puladas']}")
        print(f"📂 Disciplina: {r['pasta_disciplina']}")
        for aid, d in r.get("detalhes", {}).items():
            print(f"   • {aid}: p.{d['paginas']} · {d['qtd_caracteres']} chars · "
                  f"{d['qtd_imagens']} imgs")
    else:
        print(f"⚠️  {r.get('erro', 'Erro desconhecido')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
