#!/usr/bin/env python3
"""
Script de migração dos CSVs atuais para o Supabase.

Uso:
  python3 kaltura/migrar_csv_supabase.py

O script:
1. Lê catalogo_teste_links_videos.csv → tabela disciplinas
2. Lê videos_importados.csv → tabela videos_kaltura
3. Lê validacoes_links_videos.csv → tabela validacoes
"""

from __future__ import annotations

import csv
import hashlib
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

# Adicionar diretório pai ao path para importar supabase_client
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import supabase_client as db  # noqa: E402

# ============================================
# UTILITÁRIOS
# ============================================
def normalizar_texto(valor: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", valor or "")
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    import re
    return re.sub(r"\s+", " ", sem_acento).strip().lower()


def disc_id(curso: str, disciplina: str, semestre: str) -> str:
    bruto = f"{normalizar_texto(curso)}|{normalizar_texto(disciplina)}|{normalizar_texto(semestre)}"
    return hashlib.sha1(bruto.encode("utf-8")).hexdigest()[:16]


def ler_csv(caminho: Path) -> list[dict[str, str]]:
    if not caminho.exists():
        return []
    with caminho.open(newline="", encoding="utf-8-sig") as arquivo:
        return [dict(row) for row in csv.DictReader(arquivo)]


# ============================================
# MIGRAÇÃO: DISCIPLINAS
# ============================================
def migrar_disciplinas(caminho_csv: Path) -> int:
    """Migra catálogo de disciplinas para o Supabase."""
    linhas = ler_csv(caminho_csv)
    if not linhas:
        print("  [!] arquivo catalogo não encontrado ou vazio")
        return 0

    grupos: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in linhas:
        curso = (row.get("curso_final") or "").strip()
        disciplina = (row.get("disciplina") or "").strip()
        semestre = (row.get("semestre") or "").strip()
        professor = (row.get("professor") or "").strip()
        playlist_id = (row.get("playlist_id") or "").strip()

        if not curso or not disciplina:
            continue

        chave = (normalizar_texto(curso), normalizar_texto(disciplina), normalizar_texto(semestre))
        grupo = grupos.setdefault(
            chave,
            {
                "curso": curso,
                "disciplina": disciplina,
                "semestre": semestre,
                "professores": [],
                "playlist_id": playlist_id,
            },
        )
        if professor and professor not in grupo["professores"]:
            grupo["professores"].append(professor)
        if playlist_id and not grupo["playlist_id"]:
            grupo["playlist_id"] = playlist_id

    total = 0
    for grupo in grupos.values():
        did = disc_id(grupo["curso"], grupo["disciplina"], grupo["semestre"])
        data = {
            "disc_id": did,
            "curso_final": grupo["curso"],
            "disciplina": grupo["disciplina"],
            "semestre": grupo["semestre"],
            "professores": grupo["professores"],
            "playlist_id": grupo["playlist_id"],
        }
        db.upsert_disciplina(data)
        total += 1

    return total


# ============================================
# MIGRAÇÃO: VÍDEOS
# ============================================
def migrar_videos(caminho_csv: Path) -> int:
    """Migra vídeos importados para o Supabase."""
    linhas = ler_csv(caminho_csv)
    if not linhas:
        print("  [!] arquivo videos_importados não encontrado ou vazio")
        return 0

    total = 0
    for row in linhas:
        curso_final = (row.get("curso_final") or "").strip()
        disciplina = (row.get("disciplina") or "").strip()
        semestre = (row.get("semestre") or "").strip()

        if not curso_final or not disciplina:
            continue

        did = disc_id(curso_final, disciplina, semestre)
        disciplina_db = db.buscar_disciplina_por_id(did)

        if not disciplina_db:
            # Criar disciplina se não existir
            data_disc = {
                "disc_id": did,
                "curso_final": curso_final,
                "disciplina": disciplina,
                "semestre": semestre,
                "professores": [],
                "playlist_id": row.get("playlist_id", ""),
            }
            disciplina_db = db.upsert_disciplina(data_disc)

        aula = int(row.get("aula") or "0")
        if aula > 0 and row.get("entry_id"):
            video_data = {
                "disciplina_id": disciplina_db["id"],
                "aula": aula,
                "entry_id": row.get("entry_id", ""),
                "nome_video": row.get("nome_video", ""),
                "embed_url": row.get("embed_url", ""),
                "thumbnail_url": row.get("thumbnail_url", ""),
                "tags": row.get("tags", ""),
                "duracao_seg": int(row.get("duracao_seg") or 0),
                "kaltura_status": row.get("kaltura_status", "ok"),
            }
            db.upsert_video(video_data)
            total += 1

    return total


# ============================================
# MIGRAÇÃO: VALIDAÇÕES
# ============================================
def migrar_validacoes(caminho_csv: Path) -> int:
    """Migra validações para o Supabase."""
    linhas = ler_csv(caminho_csv)
    if not linhas:
        print("  [!] arquivo validacoes não encontrado ou vazio")
        return 0

    total = 0
    for row in linhas:
        disc_id_str = (row.get("disc_id") or "").strip()
        if not disc_id_str:
            continue

        disciplina = db.buscar_disciplina_por_id(disc_id_str)
        if not disciplina:
            # Tentar recriar a partir dos dados
            curso_final = (row.get("curso_final") or "").strip()
            disciplina_nome = (row.get("disciplina") or "").strip()
            semestre = (row.get("semestre") or "").strip()

            if curso_final and disciplina_nome:
                did = disc_id(curso_final, disciplina_nome, semestre)
                data_disc = {
                    "disc_id": did,
                    "curso_final": curso_final,
                    "disciplina": disciplina_nome,
                    "semestre": semestre,
                    "professores": [],
                    "playlist_id": row.get("playlist_id", ""),
                }
                disciplina = db.upsert_disciplina(data_disc)
            else:
                continue

        aula = int(row.get("aula") or "0")
        if aula > 0:
            validacao_data = {
                "disciplina_id": disciplina["id"],
                "aula": aula,
                "entry_id": row.get("entry_id", ""),
                "embed_url": row.get("embed_url", ""),
                "status_validacao": row.get("status_validacao", "pendente"),
                "observacao": row.get("observacao", ""),
                "responsavel": row.get("responsavel", ""),
                "validado_em": row.get("validado_em") or datetime.now().isoformat(timespec="seconds"),
            }
            db.upsert_validacao(validacao_data)
            total += 1

    return total


# ============================================
# MAIN
# ============================================
def main() -> int:
    print("\n" + "=" * 50)
    print("Migração CSV → Supabase")
    print("=" * 50)

    # Verificar credenciais
    print("\n[1/4] Verificando conexão com Supabase...")
    try:
        client = db.get_supabase_client()
        # Testar conexão simples
        client.table("disciplinas").select("id").limit(1).execute()
        print("  [✓] Conexão OK")
    except Exception as e:
        print(f"  [✗] Erro: {e}")
        print("\n  Verifique o arquivo .env com SUPABASE_URL e SUPABASE_KEY")
        return 1

    # Migrar disciplinas
    print("\n[2/4] Migrando disciplinas...")
    total_disc = migrar_disciplinas(BASE_DIR / "catalogo_teste_links_videos.csv")
    print(f"  [✓] {total_disc} disciplinas migradas")

    # Migrar vídeos
    print("\n[3/4] Migrando vídeos...")
    total_videos = migrar_videos(BASE_DIR / "videos_importados.csv")
    print(f"  [✓] {total_videos} vídeos migrados")

    # Migrar validações
    print("\n[4/4] Migrando validações...")
    total_validacoes = migrar_validacoes(BASE_DIR / "validacoes_links_videos.csv")
    print(f"  [✓] {total_validacoes} validações migradas")

    print("\n" + "=" * 50)
    print(f"Resumo: {total_disc} disciplinas | {total_videos} vídeos | {total_validacoes} validações")
    print("=" * 50 + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
