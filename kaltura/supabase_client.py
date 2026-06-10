#!/usr/bin/env python3
"""
Cliente Supabase para o Validador Kaltura UNIGRAN.

Fornece:
  - Autenticação (email/senha)
  - CRUD para disciplinas, vídeos e validações
  - Cache de sessão local
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from supabase import Client, create_client

# ============================================
# CACHE DE SESSÃO
# ============================================
_SESSION_CACHE: dict[str, Any] = {
    "client": None,
    "user": None,
    "created_at": None,
}

# TTL da sessão: 55 minutos (refresh antes de expirar em 1h)
SESSION_TTL_SECONDS = 3300


def carregar_env(caminho: Path) -> None:
    """Carrega variáveis do arquivo .env para os.environ."""
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


def get_supabase_client(env_path: Path | None = None) -> Client:
    """
    Retorna o cliente Supabase, reutilizando sessão em cache se válida.
    """
    criado_em = _SESSION_CACHE.get("created_at")
    if _SESSION_CACHE.get("client") and criado_em:
        idade = (datetime.now() - criado_em).total_seconds()
        if idade < SESSION_TTL_SECONDS:
            return _SESSION_CACHE["client"]

    if env_path is None:
        env_path = Path(__file__).resolve().parent / ".env"

    carregar_env(env_path)

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")  # service_role ou anon

    if not supabase_url or not supabase_key:
        raise RuntimeError(
            "SUPABASE_URL e/ou SUPABASE_KEY não configurados. "
            "Verifique o arquivo .env"
        )

    client = create_client(supabase_url, supabase_key)
    _SESSION_CACHE["client"] = client
    _SESSION_CACHE["created_at"] = datetime.now()
    return client


def get_user() -> dict[str, Any] | None:
    """Retorna o usuário autenticado em cache."""
    return _SESSION_CACHE.get("user")


def set_user(user: dict[str, Any] | None) -> None:
    """Define o usuário autenticado em cache."""
    _SESSION_CACHE["user"] = user
    if user is None:
        _SESSION_CACHE["created_at"] = None


# ============================================
# AUTENTICAÇÃO
# ============================================
def autenticar(email: str, senha: str, env_path: Path | None = None) -> dict[str, Any]:
    """
    Autentica usuário no Supabase Auth.
    Retorna dados do usuário ou lança exceção.
    """
    client = get_supabase_client(env_path)

    response = client.auth.sign_in_with_password({
        "email": email,
        "password": senha,
    })

    if not response.user:
        raise ValueError("Email ou senha inválidos")

    user_data = {
        "id": response.user.id,
        "email": response.user.email,
        "created_at": response.user.created_at,
    }
    set_user(user_data)
    return user_data


def logout(env_path: Path | None = None) -> None:
    """Invalida a sessão local e faz logout no Supabase."""
    client = get_supabase_client(env_path)
    try:
        client.auth.sign_out()
    except Exception:
        pass  # Ignora erros se já estiver desconectado
    finally:
        set_user(None)


def verificar_sessao() -> bool:
    """Verifica se há uma sessão válida em cache."""
    return _SESSION_CACHE.get("user") is not None


# ============================================
# DISCIPLINAS
# ============================================
def listar_disciplinas(curso: str | None = None) -> list[dict[str, Any]]:
    """
    Lista disciplinas do catálogo.
    Se curso informado, filtra por curso_final.
    """
    client = get_supabase_client()
    query = client.table("disciplinas").select("*")

    if curso:
        query = query.eq("curso_final", curso)

    # Ordenar por curso, semestre, disciplina (cada order() é uma chamada separada)
    response = query.execute()
    data = response.data or []

    # Ordenar manualmente no Python
    data.sort(key=lambda x: (x.get("curso_final", ""), x.get("semestre", ""), x.get("disciplina", "")))
    return data


def buscar_disciplina_por_id(disc_id: str) -> dict[str, Any] | None:
    """Busca uma disciplina pelo disc_id (hash)."""
    client = get_supabase_client()
    response = client.table("disciplinas").select("*").eq("disc_id", disc_id).execute()
    return response.data[0] if response.data else None


def criar_disciplina(data: dict[str, Any]) -> dict[str, Any]:
    """Cria ou atualiza uma disciplina no catálogo."""
    client = get_supabase_client()

    # Verifica se já existe pelo disc_id
    existing = buscar_disciplina_por_id(data["disc_id"])
    if existing:
        response = client.table("disciplinas").update(data).eq("disc_id", data["disc_id"]).execute()
        return response.data[0] if response.data else data

    response = client.table("disciplinas").insert(data).execute()
    return response.data[0] if response.data else data


def upsert_disciplina(data: dict[str, Any]) -> dict[str, Any]:
    """Upsert de disciplina (cria ou atualiza)."""
    client = get_supabase_client()
    response = client.table("disciplinas").upsert(data, on_conflict="disc_id").execute()
    return response.data[0] if response.data else data


# ============================================
# VÍDEOS KALTURA
# ============================================
def listar_videos_por_disciplina(disciplina_id: str) -> list[dict[str, Any]]:
    """Lista todos os vídeos de uma disciplina."""
    client = get_supabase_client()
    response = client.table("videos_kaltura").select("*").eq("disciplina_id", disciplina_id).order("aula").execute()
    return response.data or []


def criar_video(data: dict[str, Any]) -> dict[str, Any]:
    """Cria um vídeo no banco."""
    client = get_supabase_client()
    response = client.table("videos_kaltura").insert(data).execute()
    return response.data[0] if response.data else data


def upsert_video(data: dict[str, Any]) -> dict[str, Any]:
    """
    Upsert de vídeo.
    Usa UNIQUE(disciplina_id, aula) para conflito.
    """
    client = get_supabase_client()

    # Remover disc_id se presente (não é coluna da tabela)
    data.pop("disc_id", None)

    # Verificar se disciplina_id existe
    if "disciplina_id" not in data or not data["disciplina_id"]:
        raise ValueError("disciplina_id é obrigatório para upsert_video")

    # Verificar se já existe
    existing = client.table("videos_kaltura").select("id").eq("disciplina_id", data["disciplina_id"]).eq("aula", data["aula"]).execute()

    if existing.data:
        video_id = existing.data[0]["id"]
        # Remover campos que podem causar conflito no update
        update_data = {k: v for k, v in data.items() if k not in ("id", "disciplina_id", "aula")}
        response = client.table("videos_kaltura").update(update_data).eq("id", video_id).execute()
        return response.data[0] if response.data else data

    response = client.table("videos_kaltura").insert(data).execute()
    return response.data[0] if response.data else data


def limpar_videos_por_curso(curso: str) -> int:
    """Remove todos os vídeos de um curso (para reimportação)."""
    client = get_supabase_client()

    # Buscar todas as disciplinas do curso
    disciplinas = client.table("disciplinas").select("id").eq("curso_final", curso).execute()
    disciplina_ids = [d["id"] for d in disciplinas.data or []]

    if not disciplina_ids:
        return 0

    response = client.table("videos_kaltura").delete().in_("disciplina_id", disciplina_ids).execute()
    return len(response.data or [])


# ============================================
# VALIDAÇÕES
# ============================================
def listar_validacoes_por_disciplina(disciplina_id: str) -> list[dict[str, Any]]:
    """Lista todas as validações de uma disciplina."""
    client = get_supabase_client()
    response = client.table("validacoes").select("*").eq("disciplina_id", disciplina_id).order("aula").execute()
    return response.data or []


def criar_validacao(data: dict[str, Any]) -> dict[str, Any]:
    """Cria uma validação."""
    client = get_supabase_client()
    response = client.table("validacoes").insert(data).execute()
    return response.data[0] if response.data else data


# Colunas existentes na tabela validacoes (ver schema.sql)
_COLUNAS_VALIDACAO = {
    "id", "disciplina_id", "aula", "entry_id", "embed_url",
    "status_validacao", "observacao", "responsavel", "validado_em",
}


def upsert_validacao(data: dict[str, Any]) -> dict[str, Any]:
    """
    Upsert de validação.
    Usa UNIQUE(disciplina_id, aula) para conflito.
    """
    client = get_supabase_client()

    disc_id_hash = str(data.get("disc_id") or "")

    if not data.get("disciplina_id") and disc_id_hash:
        disciplina = buscar_disciplina_por_id(disc_id_hash)
        if disciplina:
            data["disciplina_id"] = disciplina["id"]

    # Manter apenas colunas que existem na tabela (descarta disc_id, playlist_id, nome_video etc.)
    data = {k: v for k, v in data.items() if k in _COLUNAS_VALIDACAO}

    # Verificar se já existe
    existing = client.table("validacoes").select("id").eq("disciplina_id", data["disciplina_id"]).eq("aula", data["aula"]).execute()

    if existing.data:
        validacao_id = existing.data[0]["id"]
        # Remover campos que podem causar conflito no update
        update_data = {k: v for k, v in data.items() if k not in ("id", "disciplina_id", "aula")}
        response = client.table("validacoes").update(update_data).eq("id", validacao_id).execute()
        return response.data[0] if response.data else data

    response = client.table("validacoes").insert(data).execute()
    return response.data[0] if response.data else data


def buscar_validacao(disciplina_id: str, aula: int) -> dict[str, Any] | None:
    """Busca uma validação específica por disciplina e aula."""
    client = get_supabase_client()
    response = client.table("validacoes").select("*").eq("disciplina_id", disciplina_id).eq("aula", aula).execute()
    return response.data[0] if response.data else None


# ============================================
# ESTATÍSTICAS / CONTADORES
# ============================================
def get_contadores_por_disciplina(disciplina_id: str, total_aulas: int) -> dict[str, int]:
    """Retorna contadores de status de validação para uma disciplina."""
    client = get_supabase_client()

    response = client.table("validacoes").select("status_validacao").eq("disciplina_id", disciplina_id).execute()
    validacoes = response.data or []

    contadores = {
        "correto": 0,
        "corrigido": 0,
        "vinculo_errado": 0,
        "sem_video": 0,
        "pendente": 0,
    }

    for v in validacoes:
        status = v.get("status_validacao", "pendente")
        if status in contadores:
            contadores[status] += 1

    # Contar pendentes como diferença
    validadas = sum(contadores[s] for s in ["correto", "corrigido", "vinculo_errado", "sem_video"])
    contadores["pendente"] = max(0, total_aulas - validadas)

    return contadores


# ============================================
# AUDIT LOG
# ============================================
def log_action(
    action: str,
    table_name: str,
    record_id: str | None = None,
    details: dict[str, Any] | None = None,
    env_path: Path | None = None,
) -> None:
    """Registra uma ação no audit log."""
    client = get_supabase_client(env_path)
    user = get_user()

    data = {
        "user_email": user.get("email") if user else "anon",
        "action": action,
        "table_name": table_name,
        "record_id": record_id,
        "details": details or {},
    }

    try:
        client.table("audit_log").insert(data).execute()
    except Exception:
        pass  # Audit log não deve quebrar o fluxo principal
