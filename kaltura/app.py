#!/usr/bin/env python3
"""
Aplicação local para importar e validar vínculos de vídeos Kaltura.
Com autenticação Supabase.

Uso:
  python3 kaltura/app.py
  abrir http://127.0.0.1:5070
"""

from __future__ import annotations

import hashlib
import os
import sys
from argparse import Namespace
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory, session as flask_session

sys.path.insert(0, str(Path(__file__).resolve().parent))

import exportar_videos_catalogo as kaltura_export  # noqa: E402
import supabase_client as db  # noqa: E402

# ============================================
# CONFIGURAÇÃO
# ============================================
BASE_DIR = Path(__file__).resolve().parent
CATALOGO_CSV = BASE_DIR / "catalogo_teste_links_videos.csv"
VIDEOS_CSV = BASE_DIR / "videos_importados.csv"

kaltura_export.carregar_env(BASE_DIR / ".env")

app = Flask(__name__, static_folder=str(BASE_DIR / "static"))
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "kaltura-validador-secret-change-in-production"

# ============================================
# UTILITÁRIOS
# ============================================
def normalizar(valor: str) -> str:
    return kaltura_export.normalizar_texto(valor)


def disc_id(curso: str, disciplina: str, semestre: str) -> str:
    bruto = f"{normalizar(curso)}|{normalizar(disciplina)}|{normalizar(semestre)}"
    return hashlib.sha1(bruto.encode("utf-8")).hexdigest()[:16]


def login_necessario(f):
    """Decorator para exigir autenticação."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not usuario_atual():
            return jsonify({"erro": "Não autorizado"}), 401
        return f(*args, **kwargs)
    return decorated


def usuario_atual() -> dict[str, Any] | None:
    """Retorna o usuário da sessão HTTP deste navegador."""
    user = flask_session.get("user")
    return user if isinstance(user, dict) else None


def email_usuario_atual() -> str | None:
    user = usuario_atual()
    if not user:
        return None
    email = user.get("email")
    return str(email) if email else None


# ============================================
# HELPERS DE DADOS
# ============================================
def montar_aulas(did: str) -> list[dict[str, Any]]:
    """Monta lista de aulas para uma disciplina."""
    disciplina = db.buscar_disciplina_por_id(did)
    if not disciplina:
        return []

    videos = db.listar_videos_por_disciplina(disciplina["id"])
    validacoes = db.listar_validacoes_por_disciplina(disciplina["id"])

    # Mapear validações por aula
    validacoes_map = {v["aula"]: v for v in validacoes}

    # Descobrir total de aulas
    numeros_importados = [v.get("aula", 0) for v in videos if v.get("aula")]
    total = max([8, *numeros_importados]) if numeros_importados else 8

    aulas = []
    for numero in range(1, total + 1):
        importado = next((v for v in videos if v.get("aula") == numero), None) or {}
        validacao = validacoes_map.get(numero, {})

        entry_id = validacao.get("entry_id") or importado.get("entry_id") or ""
        embed_url = validacao.get("embed_url") or importado.get("embed_url") or ""
        nome_video = validacao.get("nome_video") or importado.get("nome_video") or ""
        playlist_id = validacao.get("playlist_id") or importado.get("playlist_id") or disciplina.get("playlist_id", "")

        status_importacao = importado.get("kaltura_status") or ("sem_video" if not entry_id else "ok")
        status_validacao = validacao.get("status_validacao") or ("sem_video" if not entry_id else "pendente")

        aulas.append({
            "disc_id": did,
            "aula": numero,
            "playlist_id": playlist_id,
            "entry_id": entry_id,
            "embed_url": embed_url,
            "preview_embed_url": "",
            "preview_video_url": "",
            "nome_video": nome_video,
            "tags": importado.get("tags", ""),
            "duracao_seg": importado.get("duracao_seg", ""),
            "thumbnail_url": importado.get("thumbnail_url", ""),
            "status_importacao": status_importacao,
            "status_validacao": status_validacao,
            "observacao": validacao.get("observacao", ""),
            "responsavel": validacao.get("responsavel", ""),
            "validado_em": validacao.get("validado_em", ""),
        })

    return aulas


def catalogo_agrupado() -> dict[str, dict[str, Any]]:
    """Agrupar disciplinas do banco de dados."""
    disciplinas = db.listar_disciplinas()
    grupos: dict[str, dict[str, Any]] = {}

    for disc in disciplinas:
        did = disc["disc_id"]
        grupos[did] = {
            "id": disc["id"],
            "disc_id": did,
            "curso_final": disc["curso_final"],
            "disciplina": disc["disciplina"],
            "semestre": disc["semestre"],
            "professores": disc.get("professores", []),
            "playlist_id": disc.get("playlist_id", ""),
        }

    return grupos


def status_contadores(did: str, total_aulas: int) -> dict[str, int]:
    """Retorna contadores de status para uma disciplina."""
    disciplinas = catalogo_agrupado()
    disc = disciplinas.get(did)
    if not disc:
        return {"correto": 0, "corrigido": 0, "vinculo_errado": 0, "sem_video": 0, "pendente": total_aulas}

    disc_id_uuid = disc.get("id") or disc.get("disc_id")
    if len(str(disc_id_uuid)) == 36:
        return db.get_contadores_por_disciplina(str(disc_id_uuid), total_aulas)

    disciplina = db.buscar_disciplina_por_id(did)
    if disciplina:
        return db.get_contadores_por_disciplina(disciplina["id"], total_aulas)

    return {"correto": 0, "corrigido": 0, "vinculo_errado": 0, "sem_video": 0, "pendente": total_aulas}


# ============================================
# KALTURA PREVIEW
# ============================================
_KS_CACHE: dict[str, Any] = {"ks": "", "criado_em": None}
_CLIENT_CACHE: dict[str, Any] = {"client": None, "criado_em": None}


def gerar_preview_ks() -> str:
    criado_em = _KS_CACHE.get("criado_em")
    if _KS_CACHE.get("ks") and criado_em:
        idade = (datetime.now() - criado_em).total_seconds()
        if idade < 3300:
            return str(_KS_CACHE["ks"])

    kaltura_export.carregar_env(BASE_DIR / ".env")
    (
        KalturaClient,
        KalturaConfiguration,
        _KalturaFilterPager,
        _KalturaPlaylistFilter,
        KalturaSessionType,
    ) = kaltura_export.importar_kaltura()

    secret = kaltura_export.os.environ.get("KALTURA_ADMIN_SECRET")
    if not secret:
        return ""

    config = KalturaConfiguration()
    config.serviceUrl = kaltura_export.SERVICE_URL_PADRAO
    client = KalturaClient(config)
    ks = client.session.start(
        secret,
        "pipeline-kaltura-preview",
        KalturaSessionType.ADMIN,
        kaltura_export.PARTNER_ID_PADRAO,
        3600,
        "appId:pipeline-kaltura-preview",
    )
    _KS_CACHE["ks"] = ks
    _KS_CACHE["criado_em"] = datetime.now()
    return str(ks)


def preview_client():
    criado_em = _CLIENT_CACHE.get("criado_em")
    if _CLIENT_CACHE.get("client") and criado_em:
        idade = (datetime.now() - criado_em).total_seconds()
        if idade < 3300:
            return _CLIENT_CACHE["client"]

    kaltura_export.carregar_env(BASE_DIR / ".env")
    args = Namespace(
        admin_secret_env="KALTURA_ADMIN_SECRET",
        service_url=kaltura_export.SERVICE_URL_PADRAO,
        partner_id=kaltura_export.PARTNER_ID_PADRAO,
        expiry=3600,
    )
    client = kaltura_export.criar_client(args)
    _CLIENT_CACHE["client"] = client
    _CLIENT_CACHE["criado_em"] = datetime.now()
    return client


def url_preview(embed_url: str) -> str:
    from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

    if not embed_url:
        return ""
    try:
        ks = gerar_preview_ks()
    except Exception:
        return embed_url
    if not ks:
        return embed_url

    partes = urlsplit(embed_url)
    query = dict(parse_qsl(partes.query, keep_blank_values=True))
    query["ks"] = ks
    query["flashvars[ks]"] = ks
    return urlunsplit((partes.scheme, partes.netloc, partes.path, urlencode(query), partes.fragment))


def url_video_preview(entry_id: str) -> str:
    if not entry_id:
        return ""
    try:
        client = preview_client()
        flavors = client.flavorAsset.getByEntryId(entry_id)
        candidatos = [
            f for f in flavors
            if getattr(f, "fileExt", "") == "mp4" and int(getattr(f, "size", 0) or 0) > 0
        ]
        if not candidatos:
            return ""
        candidatos.sort(key=lambda f: int(getattr(f, "bitrate", 0) or 0), reverse=True)
        return str(client.flavorAsset.getUrl(candidatos[0].id))
    except Exception:
        return ""


# ============================================
# ROTAS DE PÁGINA
# ============================================
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/login")
def login_page():
    return send_from_directory(app.static_folder, "login.html")


# ============================================
# API DE AUTENTICAÇÃO
# ============================================
@app.route("/api/auth/login", methods=["POST"])
def api_login():
    dados = request.get_json(silent=True) or {}
    email = str(dados.get("email") or "").strip()
    senha = str(dados.get("senha") or "")

    if not email or not senha:
        return jsonify({"ok": False, "erro": "Email e senha são obrigatórios"}), 400

    try:
        user = db.autenticar(email, senha)
        flask_session.clear()
        flask_session["user"] = user
        return jsonify({"ok": True, "user": user})
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 401


@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    flask_session.clear()
    return jsonify({"ok": True})


@app.route("/api/auth/me")
def api_auth_me():
    user = usuario_atual()
    if user:
        return jsonify({"ok": True, "user": user})

    return jsonify({"ok": False, "erro": "Não autenticado"}), 401


# ============================================
# API DE DADOS (PROTEGIDA)
# ============================================
@app.route("/api/catalogo")
@login_necessario
def api_catalogo():
    from supabase import _sync
    client = db.get_supabase_client()

    # Buscar todas as disciplinas de uma vez
    disciplinas = db.listar_disciplinas()

    # Buscar todos os vídeos de uma vez
    response_videos = client.table("videos_kaltura").select("*").execute()
    todos_videos = response_videos.data or []

    # Buscar todas as validações de uma vez
    response_validacoes = client.table("validacoes").select("disciplina_id, status_validacao").execute()
    todas_validacoes = response_validacoes.data or []

    # Agrupar vídeos por disciplina_id
    videos_por_disc: dict[str, list] = {}
    for v in todos_videos:
        disc_id = v.get("disciplina_id", "")
        videos_por_disc.setdefault(disc_id, []).append(v)

    # Contar validações por disciplina_id e status
    contadores_por_disc: dict[str, dict[str, int]] = {}
    for v in todas_validacoes:
        disc_id = v.get("disciplina_id", "")
        status = v.get("status_validacao", "pendente")
        contadores_por_disc.setdefault(disc_id, {"correto": 0, "corrigido": 0, "vinculo_errado": 0, "sem_video": 0, "pendente": 0})
        if status in contadores_por_disc[disc_id]:
            contadores_por_disc[disc_id][status] += 1

    # Agrupar disciplinas por curso
    cursos_dict: dict[str, list[dict[str, Any]]] = {}

    for disc in disciplinas:
        disc_id_uuid = disc.get("id", "")
        curso = disc.get("curso_final", "")

        videos = videos_por_disc.get(disc_id_uuid, [])
        numeros = [v.get("aula", 0) for v in videos if isinstance(v.get("aula"), int) and v.get("aula") > 0]
        total_aulas = max([8, *numeros]) if numeros else 8

        # Contadores
        contadores = contadores_por_disc.get(disc_id_uuid, {"correto": 0, "corrigido": 0, "vinculo_errado": 0, "sem_video": 0, "pendente": total_aulas})
        # Calcular pendentes como diferença
        validadas = sum(contadores.get(s, 0) for s in ["correto", "corrigido", "vinculo_errado", "sem_video"])
        contadores["pendente"] = max(0, total_aulas - validadas)

        professores = disc.get("professores", [])
        if isinstance(professores, list):
            professores_str = " | ".join(professores)
        else:
            professores_str = str(professores)

        item = {
            "disc_id": disc.get("disc_id", ""),
            "curso_final": curso,
            "disciplina": disc.get("disciplina", ""),
            "semestre": disc.get("semestre", ""),
            "professores": professores_str,
            "playlist_id": disc.get("playlist_id", ""),
            "total_aulas": total_aulas,
            "contadores": contadores,
            "videos_importados": len([v for v in videos if v.get("entry_id")]),
        }
        cursos_dict.setdefault(curso, []).append(item)

    # Ordenar disciplinas por semestre e nome
    for lista in cursos_dict.values():
        lista.sort(key=lambda x: (x["semestre"], x["disciplina"].lower()))

    return jsonify({"cursos": sorted(cursos_dict.keys()), "disciplinas": cursos_dict})


@app.route("/api/disciplina/<did>")
@login_necessario
def api_disciplina(did: str):
    grupos = catalogo_agrupado()
    if did not in grupos:
        return jsonify({"erro": "Disciplina não encontrada"}), 404

    disciplina_uuid = grupos[did].get("id")
    videos = db.listar_videos_por_disciplina(str(disciplina_uuid)) if disciplina_uuid else []
    sem_match = [v for v in videos if v.get("kaltura_status") == "sem_match"]

    professores = grupos[did]["professores"]
    if isinstance(professores, list):
        professores = " | ".join(str(p) for p in professores if p)

    return jsonify({
        "disciplina": {
            **grupos[did],
            "professores": professores,
        },
        "aulas": montar_aulas(did),
        "sem_match": sem_match,
    })


@app.route("/api/preview/<entry_id>")
@login_necessario
def api_preview(entry_id: str):
    embed_url = kaltura_export.build_embed_url(
        kaltura_export.PARTNER_ID_PADRAO,
        kaltura_export.UICONF_ID_PADRAO,
        entry_id,
    )
    return jsonify({
        "entry_id": entry_id,
        "embed_url": embed_url,
        "preview_embed_url": url_preview(embed_url),
        "preview_video_url": url_video_preview(entry_id),
    })


@app.route("/api/importar", methods=["POST"])
@login_necessario
def api_importar():
    dados = request.get_json(silent=True) or {}
    limite = int(dados.get("limite_disciplinas") or 0)
    curso = str(dados.get("curso") or "").strip()

    try:
        saida = VIDEOS_CSV
        if curso:
            saida = BASE_DIR / f"videos_importados.tmp-{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"

        args = Namespace(
            entrada=CATALOGO_CSV,
            saida=saida,
            env=BASE_DIR / ".env",
            admin_secret_env="KALTURA_ADMIN_SECRET",
            partner_id=kaltura_export.PARTNER_ID_PADRAO,
            uiconf_id=kaltura_export.UICONF_ID_PADRAO,
            service_url=kaltura_export.SERVICE_URL_PADRAO,
            expiry=86400,
            limite_playlists=20,
            curso=curso,
            limite_disciplinas=limite,
        )
        kaltura_export.exportar(args)

        # Migrar dados do CSV para o Supabase
        total_linhas = migrar_csv_para_supabase(saida, curso)

        if saida != VIDEOS_CSV and saida.exists():
            saida.unlink()

        db.log_action(
            "importar_videos",
            "videos_kaltura",
            details={"curso": curso, "linhas": total_linhas},
            user_email=email_usuario_atual(),
        )

    except SystemExit as exc:
        return jsonify({"ok": False, "erro": str(exc)}), 400
    except Exception as exc:
        return jsonify({"ok": False, "erro": str(exc)}), 500

    return jsonify({"ok": True, "linhas": total_linhas})


def migrar_csv_para_supabase(caminho_csv: Path, curso: str) -> int:
    """Migra dados do CSV exportado para o Supabase."""
    import csv

    if not caminho_csv.exists():
        return 0

    total = 0
    with caminho_csv.open(newline="", encoding="utf-8-sig") as arquivo:
        leitor = csv.DictReader(arquivo)
        for row in leitor:
            curso_final = row.get("curso_final", "").strip()
            disciplina_nome = row.get("disciplina", "").strip()
            semestre = row.get("semestre", "").strip()

            # Criar/atualizar disciplina
            did = disc_id(curso_final, disciplina_nome, semestre)
            disc_data = {
                "disc_id": did,
                "curso_final": curso_final,
                "disciplina": disciplina_nome,
                "semestre": semestre,
                "professores": [row.get("professores", "")] if row.get("professores") else [],
                "playlist_id": row.get("playlist_id", ""),
            }
            disciplina = db.upsert_disciplina(disc_data)

            # Criar/atualizar vídeo
            aula = int(row.get("aula") or "0")
            if aula > 0 and row.get("entry_id"):
                video_data = {
                    "disciplina_id": disciplina["id"],
                    "disc_id": did,  # fallback
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


@app.route("/api/validar", methods=["POST"])
@login_necessario
def api_validar():
    dados = request.get_json(silent=True) or {}
    did = str(dados.get("disc_id") or "")

    grupos = catalogo_agrupado()
    if did not in grupos:
        return jsonify({"ok": False, "erro": "Disciplina não encontrada"}), 404

    try:
        aula = int(dados.get("aula") or "0")
    except ValueError:
        return jsonify({"ok": False, "erro": "Aula inválida"}), 400

    if aula <= 0:
        return jsonify({"ok": False, "erro": "Aula inválida"}), 400

    status = str(dados.get("status_validacao") or "pendente")
    permitidos = {"pendente", "correto", "corrigido", "vinculo_errado", "sem_video"}
    if status not in permitidos:
        return jsonify({"ok": False, "erro": "Status inválido"}), 400

    disciplina = grupos[did]

    # Buscar dados atuais
    aulas = montar_aulas(did)
    atual = next((a for a in aulas if a["aula"] == aula), {})

    entry_id = str(dados.get("entry_id") or atual.get("entry_id") or "").strip()
    embed_url = str(dados.get("embed_url") or atual.get("embed_url") or "").strip()

    if entry_id and not embed_url:
        embed_url = kaltura_export.build_embed_url(
            kaltura_export.PARTNER_ID_PADRAO,
            kaltura_export.UICONF_ID_PADRAO,
            entry_id,
        )

    nova = {
        "disc_id": did,
        "disciplina_id": grupos[did].get("id"),
        "aula": aula,
        "playlist_id": str(dados.get("playlist_id") or atual.get("playlist_id") or disciplina.get("playlist_id", "")),
        "entry_id": entry_id,
        "embed_url": embed_url,
        "status_validacao": status,
        "observacao": str(dados.get("observacao") or "").strip(),
        "responsavel": str(dados.get("responsavel") or "").strip(),
        "validado_em": datetime.now().isoformat(timespec="seconds"),
    }

    resultado = db.upsert_validacao(nova)

    db.log_action(
        "validar_video",
        "validacoes",
        record_id=resultado.get("id"),
        details={"disciplina": disciplina["disciplina"], "aula": aula, "status": status},
        user_email=email_usuario_atual(),
    )

    return jsonify({"ok": True, "validacao": resultado})


# ============================================
# INICIALIZAÇÃO
# ============================================
if __name__ == "__main__":
    print(f"\n  Validador Kaltura UNIGRAN")
    print(f"  Servidor: http://127.0.0.1:5070")
    print(f"  Banco: Supabase (configurar .env)\n")

    app.run(host="127.0.0.1", port=5070, debug=False)
