"""
pastas.py — Criação da estrutura de pastas de uma aula.
"""
from pathlib import Path
import re


def slugify(texto: str) -> str:
    """Converte 'Fundamentos de Administração' → 'fundamentos-administracao'."""
    texto = texto.lower().strip()
    # remove acentos básicos
    acentos = str.maketrans("áàâãäéèêëíìîïóòôõöúùûüç", "aaaaaeeeeiiiiooooouuuuc")
    texto = texto.translate(acentos)
    texto = re.sub(r"[^a-z0-9\s-]", "", texto)
    texto = re.sub(r"\s+", "-", texto)
    texto = re.sub(r"-+", "-", texto)
    return texto.strip("-")


def nome_pasta_disciplina(codigo: str, nome: str) -> str:
    """ADM + 'Fundamentos de Administração' → 'ADM-fundamentos-administracao'."""
    return f"{codigo.upper()}-{slugify(nome)}"


def id_aula(codigo: str, numero: int) -> str:
    """ADM + 1 → 'ADM-01'."""
    return f"{codigo.upper()}-{numero:02d}"


def criar_estrutura(raiz: Path, codigo: str, nome_disc: str,
                    numero_aula: int, subpastas: list, nome_curso: str = "EAD") -> Path:
    """
    Cria toda a estrutura de pastas de uma aula.
    Retorna o Path da pasta da aula.
    Idempotente: não sobrescreve se já existir.

    Estrutura: cursos/{curso}/{disciplina}/aulas/{numero}/
    """
    pasta_curso = raiz / "cursos" / slugify(nome_curso)
    pasta_disc = pasta_curso / nome_pasta_disciplina(codigo, nome_disc)
    pasta_aula = pasta_disc / "aulas" / f"{numero_aula:02d}"

    for sub in subpastas:
        (pasta_aula / sub).mkdir(parents=True, exist_ok=True)

    return pasta_aula


def aula_ja_processada(pasta_aula: Path) -> bool:
    """Verifica se já existe Markdown gerado (evita reprocessar sem querer)."""
    md_dir = pasta_aula / "02_markdown"
    if not md_dir.exists():
        return False
    return any(md_dir.glob("*.md"))
