"""
referencias.py — Extrai referências bibliográficas do markdown da aula (M01).

Usado quando o score do Agente E não traz fontes_verificadas (produção).
Status 'citada' = encontrada no texto, ainda não validada externamente pelo Agente E.
"""
import re
from pathlib import Path


def _dedupe(refs: list) -> list:
    vistos = set()
    out = []
    for r in refs:
        chave = (
            re.sub(r"\s+", " ", r.get("autor", "").lower())[:40],
            r.get("ano", ""),
            re.sub(r"\s+", " ", r.get("obra", "").lower())[:50],
        )
        if chave in vistos or not r.get("autor"):
            continue
        vistos.add(chave)
        out.append(r)
    return out


def _recortar_bloco_aula(texto: str, numero_aula: int | None) -> str:
    """Isola o trecho do markdown referente a uma aula (PDF único com várias aulas)."""
    if not numero_aula:
        return texto
    padrao_inicio = rf"(?mi)^##\s*Aula\s*\n\s*##\s*\*\*{numero_aula:02d}\*\*"
    m = re.search(padrao_inicio, texto)
    if not m:
        return texto
    resto = texto[m.end() :]
    m2 = re.search(r"(?mi)^##\s*Aula\s*\n\s*##\s*\*\*\d{2}\*\*", resto)
    fim = m.end() + m2.start() if m2 else len(texto)
    return texto[m.start() : fim]


def _blocos_bibliograficos(texto: str) -> list[str]:
    """Retorna blocos de texto candidatos a bibliografia."""
    blocos = []

    # Seções explícitas: Referências, Bibliografia, Vale a ler
    for m in re.finditer(
        r"(?mi)^#{1,3}\s*(?:refer[eê]ncias|bibliografia|referencias|vale a ler(?:\s+pena)?)\s*$",
        texto,
    ):
        resto = texto[m.end() :]
        prox = re.search(r"(?mi)^#{1,3}\s+", resto)
        bloco = resto[: prox.start()] if prox else resto
        blocos.append(bloco)

    # Linhas soltas após "Vale a ler" (OCR quebra o heading)
    for m in re.finditer(
        r"(?mi)(?:^|\n)\s*(?:vale a ler[^.\n]*|¢ vale a ler[^.\n]*)\s*\n(.+?)(?:\n## |\Z)",
        texto,
        re.DOTALL,
    ):
        blocos.append(m.group(1))

    if not blocos:
        blocos.append(texto)

    return blocos


def _parse_linha_referencia(linha: str) -> dict | None:
    """Parseia uma linha de bibliografia (APA simplificado)."""
    linha = linha.strip().strip("|")
    linha = re.sub(r"\*\*", "", linha)
    if len(linha) < 12:
        return None
    if re.match(r"^[\.\s\d\-_]+$", linha):
        return None
    if re.match(r"^#{1,3}\s", linha):
        return None

    # URL / Disponível em
    url_m = re.search(r"(?i)dispon[ií]vel\s+em:\s*(https?://[^\s\)\]<>]+)", linha)
    if url_m:
        url = url_m.group(1).rstrip(".")
        titulo_m = re.match(r"^(.+?)\.\s*Dispon[ií]vel", linha, re.I)
        obra = titulo_m.group(1).strip() if titulo_m else url[:100]
        autor = obra.split(",")[0].strip()[:60] if "," in obra else re.sub(
            r"^https?://(www\.)?", "", url
        ).split("/")[0]
        ano_m = re.search(r"(\d{4})", linha)
        return {
            "autor": autor,
            "ano": ano_m.group(1) if ano_m else "",
            "obra": obra[:180],
            "status": "citada",
        }

    # SOBRENOME, Nome. Título. Editora, ano.
    if not re.match(r"^[A-ZÁÀÂÃÉÈÍÓÔÕÚÇ]", linha):
        return None
    if "Disponível em:" in linha or "disponível em:" in linha:
        return None

    m = re.match(
        r"^([A-ZÁÀÂÃÉÈÍÓÔÕÚÇ][^,]+,\s*(?:[A-ZÁÀÂÃÉÈÍÓÔÕÚÇ]\.\s*)+)\s*(.+)$",
        linha,
    )
    if not m:
        m = re.match(r"^([A-ZÁÀÂÃÉÈÍÓÔÕÚÇ][^,]+,\s*.+?)\.\s*(.+)$", linha)
    if not m:
        return None

    autor = m.group(1).strip()
    resto = re.sub(r"_+|\*+", " ", m.group(2)).strip()
    resto = re.sub(r"\s+", " ", resto)
    ano_m = re.search(r"(\d{4})\.?\s*$", resto)
    ano = ano_m.group(1) if ano_m else ""
    obra = resto
    if ano:
        obra = resto[: resto.rfind(ano)].strip().rstrip("., ")
    if len(obra) < 3:
        return None
    return {"autor": autor, "ano": ano, "obra": obra[:180], "status": "citada"}


def _extrair_de_bloco(bloco: str) -> list:
    refs = []
    for linha in bloco.splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("---"):
            continue
        ref = _parse_linha_referencia(linha)
        if ref:
            refs.append(ref)
    return refs


def _extrair_citacoes_corpo(texto: str) -> list:
    """Citações no corpo: Sobrenome (2006) — só sobrenome isolado."""
    refs = []
    padrao = re.compile(
        r"(?<![A-Za-záàâãéèíóôõúçÁÀÂÃÉÈÍÓÔÕÚÇ])"
        r"([A-ZÁÀÂÃÉÈÍÓÔÕÚÇ][a-záàâãéèíóôõúç]+"
        r"(?:\s+(?:et\s+al\.|[A-ZÁÀÂÃÉÈÍÓÔÕÚÇ][a-záàâãéèíóôõúç]+))*)"
        r"\s*\((\d{4}(?:-\d{2,4})?)\)"
    )
    ignorar = {"figura", "tabela", "capítulo", "aula", "disponível", "org"}
    for m in padrao.finditer(texto):
        autor = m.group(1).strip()
        if autor.lower().split()[0] in ignorar:
            continue
        refs.append({
            "autor": autor,
            "ano": m.group(2),
            "obra": "Citação no corpo do texto",
            "status": "citada",
        })
    return refs


def extrair_referencias_markdown(texto: str, numero_aula: int | None = None) -> list:
    """
    Extrai referências do markdown. Retorna lista no formato do score:
    {autor, ano, obra, status: 'citada'}
    """
    texto = _recortar_bloco_aula(texto, numero_aula)
    refs = []

    for bloco in _blocos_bibliograficos(texto):
        refs.extend(_extrair_de_bloco(bloco))

    # Se não achou seção, varre linhas com padrão APA no bloco da aula
    if not refs:
        for linha in texto.splitlines():
            ref = _parse_linha_referencia(linha)
            if ref:
                refs.append(ref)

    # Citações no corpo só se ainda não há lista estruturada
    if len(refs) < 2:
        refs.extend(_extrair_citacoes_corpo(texto))

    return _dedupe(refs)[:40]


def extrair_referencias_pasta(pasta_aula: Path, numero_aula: int | None = None) -> list:
    """Lê 02_markdown/*.md da aula e extrai referências."""
    md_dir = pasta_aula / "02_markdown"
    if not md_dir.exists():
        return []
    arquivos = sorted(md_dir.glob("*.md"))
    if not arquivos:
        return []

    if numero_aula is None:
        m = re.search(r"aulas[/\\](\d{2})", str(pasta_aula))
        if m:
            numero_aula = int(m.group(1))

    try:
        texto = arquivos[0].read_text(encoding="utf-8")
    except OSError:
        return []
    return extrair_referencias_markdown(texto, numero_aula)
