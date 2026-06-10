#!/usr/bin/env python3
"""
Verifica as políticas RLS atuais no Supabase.
"""

from pathlib import Path
import supabase_client as db

BASE_DIR = Path(__file__).resolve().parent

# Carregar cliente
client = db.get_supabase_client(BASE_DIR / ".env")

# Tentar inserir uma disciplina de teste
try:
    test_data = {
        "disc_id": "test_rls_check",
        "curso_final": "Teste",
        "disciplina": "Teste RLS",
        "semestre": "1º",
        "professores": [],
        "playlist_id": "",
    }
    response = client.table("disciplinas").insert(test_data).execute()
    print("✓ Inserção com chave anon funcionou!")
    print(f"  ID criado: {response.data[0]['id'] if response.data else 'N/A'}")

    # Limpar teste
    if response.data:
        client.table("disciplinas").delete().eq("disc_id", "test_rls_check").execute()
except Exception as e:
    print(f"✗ Inserção falhou: {e}")
    print("\nVocê precisa usar a service_role key para inserções.")
    print("\nPara conseguir a service_role key:")
    print("1. Acesse https://supabase.com/dashboard/project/ulkwtuheqtcarpimzfvn")
    print("2. Vá em Settings (engrenagem) → API")
    print("3. Copie a 'service_role key' (não a 'anon public key')")
    print("4. Atualize o .env com a chave completa")
