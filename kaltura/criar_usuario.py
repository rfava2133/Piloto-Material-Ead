#!/usr/bin/env python3
"""
Cria um usuário no Supabase Auth para o Validador Kaltura.

Uso:
  python3 criar_usuario.py email@unigran.br senha123
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import supabase_client as db  # noqa: E402


def criar_usuario(email: str, senha: str) -> bool:
    """Cria um usuário no Supabase Auth."""
    from supabase._sync.client import create_client
    import os

    # Carregar credenciais
    db.carregar_env(BASE_DIR / ".env")

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("ERRO: SUPABASE_URL ou SUPABASE_KEY não configurados")
        return False

    # Criar cliente com service_role key para bypass do RLS
    client = create_client(supabase_url, supabase_key)

    try:
        # Criar usuário com email confirmado
        response = client.auth.admin.create_user({
            "email": email,
            "password": senha,
            "email_confirm": True,
        })

        if response.user:
            print(f"\n✅ Usuário criado com sucesso!")
            print(f"   Email: {email}")
            print(f"   ID: {response.user.id}")
            print(f"\nAgora você pode fazer login em http://127.0.0.1:5070/login\n")
            return True
        else:
            print(f"ERRO: Não foi possível criar o usuário")
            return False

    except Exception as e:
        erro_msg = str(e)
        if "already been registered" in erro_msg.lower() or "duplicate" in erro_msg.lower():
            print(f"\n⚠️ Este email já está cadastrado no Supabase.")
            print(f"   Tente fazer login diretamente ou use outro email.\n")
        else:
            print(f"\nERRO: {erro_msg}\n")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("\nCria um usuário no Supabase Auth")
        print("\nUso: python3 criar_usuario.py email@unigran.br senha123\n")
        print("Exemplo: python3 criar_usuario.py responsavel@unigran.br SenhaForte123\n")
        sys.exit(1)

    email = sys.argv[1]
    senha = sys.argv[2]

    if len(senha) < 6:
        print("\n⚠️ A senha deve ter pelo menos 6 caracteres\n")
        sys.exit(1)

    sucesso = criar_usuario(email, senha)
    sys.exit(0 if sucesso else 1)
