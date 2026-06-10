#!/usr/bin/env python3
"""
Exporta videos Kaltura por disciplina para uma planilha CSV de teste.

Fluxo:
  catalogo_teste_links_videos.csv
    -> busca playlist pelo nome da disciplina ou usa playlist_id existente
    -> executa a playlist
    -> grava uma linha por video/aula com embed_url

Credenciais ficam fora do Git, em .env ou variavel de ambiente.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


PARTNER_ID_PADRAO = 1878021
UICONF_ID_PADRAO = 55378663
SERVICE_URL_PADRAO = "https://www.kaltura.com/"
BASE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class DisciplinaCatalogo:
    curso: str
    disciplina: str
    semestre: str
    professores: str
    playlist_id: str = ""


def normalizar_texto(valor: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", valor or "")
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento).strip().lower()


def carregar_env(caminho: Path) -> None:
    if not caminho.exists():
        return

    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        chave = chave.strip()
        valor = valor.strip().strip('"').strip("'")
        os.environ.setdefault(chave, valor)


def parse_aula(nome: str, tags: str = "") -> int | None:
    padroes_nome = [
        r"^aula\s*0?(\d{1,2})\s*-",
        r"^aula\s*0?(\d{1,2})\b",
    ]
    for padrao in padroes_nome:
        match = re.search(padrao, nome or "", re.IGNORECASE)
        if match:
            return int(match.group(1))

    for tag in re.split(r"[,;\s]+", tags or ""):
        match = re.fullmatch(r"au+la0?(\d{1,2})", tag.strip(), re.IGNORECASE)
        if match:
            return int(match.group(1))

    return None


def build_embed_url(partner_id: int, uiconf_id: int, entry_id: str) -> str:
    player_id = f"kaltura_player_{entry_id.replace('_', '')}"
    return (
        f"https://cdnapisec.kaltura.com/p/{partner_id}/sp/{partner_id}00/"
        f"embedIframeJs/uiconf_id/{uiconf_id}/partner_id/{partner_id}"
        f"?iframeembed=true&playerId={player_id}"
        f"&entry_id={entry_id}&flashvars[streamerType]=auto"
    )


def build_thumbnail_url(partner_id: int, entry_id: str) -> str:
    return f"https://cdnsecakmi.kaltura.com/p/{partner_id}/thumbnail/entry_id/{entry_id}"


def importar_kaltura():
    try:
        from KalturaClient import KalturaClient, KalturaConfiguration
        from KalturaClient.Plugins.Core import (
            KalturaFilterPager,
            KalturaPlaylistFilter,
            KalturaSessionType,
        )
    except ImportError as exc:
        raise SystemExit(
            "Dependencia ausente: instale com "
            "`pip install KalturaApiClient --break-system-packages`."
        ) from exc

    return KalturaClient, KalturaConfiguration, KalturaFilterPager, KalturaPlaylistFilter, KalturaSessionType


def criar_client(args: argparse.Namespace):
    (
        KalturaClient,
        KalturaConfiguration,
        _KalturaFilterPager,
        _KalturaPlaylistFilter,
        KalturaSessionType,
    ) = importar_kaltura()

    admin_secret = os.environ.get(args.admin_secret_env)
    if not admin_secret:
        raise SystemExit(
            f"Variavel {args.admin_secret_env} nao encontrada. "
            "Defina no .env ou exporte no terminal antes de rodar."
        )

    config = KalturaConfiguration()
    config.serviceUrl = args.service_url
    client = KalturaClient(config)
    ks = client.session.start(
        admin_secret,
        "pipeline-kaltura-teste",
        KalturaSessionType.ADMIN,
        args.partner_id,
        args.expiry,
        "appId:pipeline-kaltura-teste",
    )
    client.setKs(ks)
    return client


def objeto_para_dict(obj: Any) -> dict[str, Any]:
    return {
        "id": getattr(obj, "id", ""),
        "name": getattr(obj, "name", ""),
        "tags": getattr(obj, "tags", "") or "",
        "duration": getattr(obj, "duration", "") or "",
    }


def listar_objetos(resposta: Any) -> list[Any]:
    if resposta is None:
        return []
    if isinstance(resposta, list):
        return resposta
    objetos = getattr(resposta, "objects", None)
    if objetos is not None:
        return list(objetos)
    return list(resposta)


def carregar_catalogo(caminho: Path) -> list[DisciplinaCatalogo]:
    with caminho.open(newline="", encoding="utf-8-sig") as arquivo:
        leitor = csv.DictReader(arquivo)
        campos = leitor.fieldnames or []
        obrigatorios = {"curso_final", "disciplina", "semestre", "professor"}
        faltando = obrigatorios.difference(campos)
        if faltando:
            raise SystemExit(f"Colunas obrigatorias ausentes no CSV: {', '.join(sorted(faltando))}")

        grupos: dict[tuple[str, str, str], dict[str, Any]] = {}
        for row in leitor:
            curso = (row.get("curso_final") or "").strip()
            disciplina = (row.get("disciplina") or "").strip()
            semestre = (row.get("semestre") or "").strip()
            professor = (row.get("professor") or "").strip()
            playlist_id = (row.get("playlist_id") or "").strip()
            if not disciplina:
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

    return [
        DisciplinaCatalogo(
            curso=grupo["curso"],
            disciplina=grupo["disciplina"],
            semestre=grupo["semestre"],
            professores=" | ".join(grupo["professores"]),
            playlist_id=grupo["playlist_id"],
        )
        for grupo in grupos.values()
    ]


def resolver_playlist_por_nome(client: Any, nome_disciplina: str, limite: int) -> tuple[str, str, str]:
    _KalturaClient, _KalturaConfiguration, KalturaFilterPager, KalturaPlaylistFilter, _KalturaSessionType = importar_kaltura()

    filtro = KalturaPlaylistFilter()
    filtro.nameLike = nome_disciplina

    pager = KalturaFilterPager()
    pager.pageSize = limite

    resposta = client.playlist.list(filtro, pager)
    playlists = listar_objetos(resposta)
    if not playlists:
        return "", "", "sem_playlist"

    alvo = normalizar_texto(nome_disciplina)
    candidatos = [p for p in playlists if normalizar_texto(getattr(p, "name", "")) == alvo]
    escolhido = candidatos[0] if candidatos else playlists[0]

    status = "playlist_exata" if candidatos else "playlist_aproximada"
    return getattr(escolhido, "id", ""), getattr(escolhido, "name", ""), status


def exportar(args: argparse.Namespace) -> int:
    carregar_env(args.env)
    client = criar_client(args)
    disciplinas = carregar_catalogo(args.entrada)

    if args.curso:
        alvo = normalizar_texto(args.curso)
        disciplinas = [d for d in disciplinas if normalizar_texto(d.curso) == alvo]

    if args.limite_disciplinas:
        disciplinas = disciplinas[: args.limite_disciplinas]

    linhas: list[dict[str, Any]] = []

    for disciplina in disciplinas:
        playlist_id = disciplina.playlist_id
        playlist_nome = ""
        status_playlist = "playlist_do_csv" if playlist_id else ""

        if not playlist_id:
            playlist_id, playlist_nome, status_playlist = resolver_playlist_por_nome(
                client,
                disciplina.disciplina,
                args.limite_playlists,
            )

        base = {
            "curso_final": disciplina.curso,
            "disciplina": disciplina.disciplina,
            "semestre": disciplina.semestre,
            "professores": disciplina.professores,
            "playlist_id": playlist_id,
            "playlist_nome": playlist_nome,
            "kaltura_status": status_playlist,
        }

        if not playlist_id:
            linhas.append({**base, **linha_vazia_video("sem_playlist")})
            continue

        try:
            entries = listar_objetos(client.playlist.execute(playlist_id))
        except Exception as exc:  # noqa: BLE001 - queremos relatorio em CSV no teste.
            linhas.append({**base, **linha_vazia_video(f"erro_playlist: {exc}")})
            continue

        if not entries:
            linhas.append({**base, **linha_vazia_video("sem_video")})
            continue

        for ordem, entry in enumerate(entries, start=1):
            dados = objeto_para_dict(entry)
            aula = parse_aula(dados["name"], dados["tags"])
            status_video = "ok" if aula is not None else "sem_match"
            linhas.append(
                {
                    **base,
                    "kaltura_status": status_video,
                    "ordem_playlist": ordem,
                    "aula": aula or "",
                    "entry_id": dados["id"],
                    "nome_video": dados["name"],
                    "tags": dados["tags"],
                    "duracao_seg": dados["duration"],
                    "embed_url": build_embed_url(args.partner_id, args.uiconf_id, dados["id"]),
                    "thumbnail_url": build_thumbnail_url(args.partner_id, dados["id"]),
                }
            )

    gravar_csv(args.saida, linhas)
    print(f"{len(linhas)} linhas exportadas em {args.saida}")
    return 0


def linha_vazia_video(status: str) -> dict[str, Any]:
    return {
        "kaltura_status": status,
        "ordem_playlist": "",
        "aula": "",
        "entry_id": "",
        "nome_video": "",
        "tags": "",
        "duracao_seg": "",
        "embed_url": "",
        "thumbnail_url": "",
    }


def gravar_csv(caminho: Path, linhas: list[dict[str, Any]]) -> None:
    campos = [
        "curso_final",
        "disciplina",
        "semestre",
        "professores",
        "playlist_id",
        "playlist_nome",
        "kaltura_status",
        "ordem_playlist",
        "aula",
        "entry_id",
        "nome_video",
        "tags",
        "duracao_seg",
        "embed_url",
        "thumbnail_url",
    ]

    if caminho.exists():
        carimbo = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = caminho.with_name(f"{caminho.stem}.backup-{carimbo}{caminho.suffix}")
        shutil.copy2(caminho, backup)
        print(f"Backup criado: {backup}")

    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(linhas)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Exporta playlists/entries Kaltura para CSV de teste do catalogo."
    )
    parser.add_argument(
        "--entrada",
        type=Path,
        default=BASE_DIR / "catalogo_teste_links_videos.csv",
        help="CSV de entrada com curso_final, disciplina, semestre, professor e opcionalmente playlist_id.",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=BASE_DIR / "catalogo_teste_links_videos_resultado.csv",
        help="CSV longo de saida, com uma linha por video/aula.",
    )
    parser.add_argument("--env", type=Path, default=BASE_DIR / ".env", help="Arquivo .env local.")
    parser.add_argument("--admin-secret-env", default="KALTURA_ADMIN_SECRET")
    parser.add_argument("--partner-id", type=int, default=PARTNER_ID_PADRAO)
    parser.add_argument("--uiconf-id", type=int, default=UICONF_ID_PADRAO)
    parser.add_argument("--service-url", default=SERVICE_URL_PADRAO)
    parser.add_argument("--expiry", type=int, default=86400)
    parser.add_argument("--limite-playlists", type=int, default=20)
    parser.add_argument("--curso", default="", help="Importa apenas um curso do catalogo.")
    parser.add_argument(
        "--limite-disciplinas",
        type=int,
        default=0,
        help="Para teste rapido: processa apenas as N primeiras disciplinas unicas.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    return exportar(args)


if __name__ == "__main__":
    raise SystemExit(main())
