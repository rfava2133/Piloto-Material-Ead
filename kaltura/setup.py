#!/usr/bin/env python3
"""
Script de setup inicial do Validador Kaltura.

Uso:
  python3 setup.py

O script:
1. Verifica dependências Python
2. Verifica arquivo .env
3. Testa conexão com Supabase
4. Orienta sobre criação do primeiro usuário
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ============================================
# VERIFICAR DEPENDÊNCIAS
# ============================================
def verificar_dependencias() -> bool:
    """Verifica se todas as dependências estão instaladas."""
    print("\n[1/4] Verificando dependências Python...")

    dependencias = {
        "flask": "Flask",
        "supabase": "supabase",
        "KalturaClient": "KalturaApiClient",
        "lxml": "lxml",
    }

    faltando = []
    for modulo, pip_nome in dependencias.items():
        try:
            __import__(modulo)
        except ImportError:
            faltando.append(pip_nome)

    if faltando:
        print(f"  [✗] Dependências faltando: {', '.join(faltando)}")
        print(f"\n  Instale com: pip install {' '.join(faltando)} --break-system-packages\n")
        return False

    print("  [✓] Todas as dependências OK")
    return True


# ============================================
# VERIFICAR .ENV
# ============================================
def verificar_env() -> bool:
    """Verifica se o arquivo .env existe e tem as variáveis necessárias."""
    print("\n[2/4] Verificando arquivo .env...")

    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        print(f"  [✗] Arquivo .env não encontrado em {env_path}")
        print(f"\n  Copie o modelo: cp .env.example .env\n")
        return False

    conteudo = env_path.read_text(encoding="utf-8")
    variaveis_necessarias = {
        "KALTURA_ADMIN_SECRET": "Kaltura Admin Secret",
        "SUPABASE_URL": "Supabase URL",
        "SUPABASE_KEY": "Supabase Service Role Key",
    }

    faltando = []
    for var, descricao in variaveis_necessarias.items():
        if var not in conteudo:
            faltando.append(f"{var} ({descricao})")
        elif f'{var}="sua_' in conteudo or f"{var}=\"sua_" in conteudo:
            print(f"  [!] {var} ainda não configurado (valor placeholder)")
            faltando.append(f"{var} ({descricao})")

    if faltando:
        print(f"  [✗] Variáveis faltando no .env:")
        for var in faltando:
            print(f"      - {var}")
        print("\n  Edite o arquivo .env e preencha as variáveis necessárias.\n")
        return False

    print("  [✓] .env configurado")
    return True


# ============================================
# TESTAR SUPABASE
# ============================================
def testar_supabase() -> bool:
    """Testa conexão com o Supabase."""
    print("\n[3/4] Testando conexão com Supabase...")

    sys.path.insert(0, str(BASE_DIR))
    try:
        import supabase_client as db

        client = db.get_supabase_client()

        # Testar conexão simples
        response = client.table("disciplinas").select("id").limit(1).execute()

        print("  [✓] Conexão com Supabase OK")
        print(f"  [i] Tabelas acessíveis: disciplinas, videos_kaltura, validacoes, audit_log")
        return True

    except Exception as e:
        erro_msg = str(e)
        print(f"  [✗] Erro ao conectar: {erro_msg}")

        if "SUPABASE_URL" in erro_msg or "SUPABASE_KEY" in erro_msg:
            print("\n  Verifique as variáveis SUPABASE_URL e SUPABASE_KEY no .env")
        elif "relation" in erro_msg.lower() or "does not exist" in erro_msg.lower():
            print("\n  As tabelas não existem ainda.")
            print("  Rode o schema.sql no SQL Editor do Supabase:")
            print("  1. Acesse https://supabase.com")
            print("  2. Selecione seu projeto")
            print("  3. Vá para SQL Editor")
            print("  4. Copie e execute o conteúdo de schema.sql")
        else:
            print("\n  Verifique:")
            print("  - SUPABASE_URL está correta (https://xxxxx.supabase.co)")
            print("  - SUPABASE_KEY é a service_role key (não a anon key)")
            print("  - O projeto Supabase está ativo")

        return False


# ============================================
# TESTAR KALTURA
# ============================================
def testar_kaltura() -> bool:
    """Testa conexão com a API Kaltura."""
    print("\n[4/4] Testando conexão com Kaltura...")

    import exportar_videos_catalogo as kaltura

    try:
        kaltura.carregar_env(BASE_DIR / ".env")
        secret = os.environ.get("KALTURA_ADMIN_SECRET")

        if not secret or secret == "6099da500742bb67e03279ad6fdff50c":
            print("  [!] KALTURA_ADMIN_SECRET não configurado ou usando valor padrão")
            print("      A importação de vídeos não funcionará sem o secret correto")
            return True  # Não impede o setup, só alerta

        # Testar criação de cliente (sem fazer chamada real)
        from argparse import Namespace
        args = Namespace(
            admin_secret_env="KALTURA_ADMIN_SECRET",
            service_url=kaltura.SERVICE_URL_PADRAO,
            partner_id=kaltura.PARTNER_ID_PADRAO,
            expiry=3600,
        )
        client = kaltura.criar_client(args)

        print("  [✓] Conexão com Kaltura OK")
        return True

    except Exception as e:
        print(f"  [!] Aviso: {e}")
        print("      A importação de vídeos pode não funcionar")
        return True  # Não impede o setup


# ============================================
# ORIENTAÇÕES FINAIS
# ============================================
def imprimir_orientacoes() -> None:
    """Imprime orientações sobre próximos passos."""
    print("\n" + "=" * 60)
    print("SETUP CONCLUÍDO")
    print("=" * 60)

    print("\n📋 PRÓXIMOS PASSOS:\n")

    print("1. Criar usuário responsável no Supabase:")
    print("   - Acesse https://supabase.com")
    print("   - Vá para Authentication → Users")
    print("   - Clique em 'Add user'")
    print("   - Crie o usuário com email institucional (ex: nome@unigran.br)")
    print("   - Marque 'Email verified' para não precisar confirmar email")
    print()

    print("2. Rodar a aplicação:")
    print(f"   cd {BASE_DIR}")
    print("   python3 app.py")
    print()

    print("3. Acessar o sistema:")
    print("   - Abra http://127.0.0.1:5070")
    print("   - Faça login com o usuário criado")
    print()

    print("4. (Opcional) Migrar dados CSV existentes:")
    print("   python3 migrar_csv_supabase.py")
    print()

    print("=" * 60)


# ============================================
# MAIN
# ============================================
def main() -> int:
    print("\n" + "=" * 60)
    print("SETUP — Validador Kaltura UNIGRAN")
    print("=" * 60)

    passos = [
        verificar_dependencias,
        verificar_env,
        testar_supabase,
        testar_kaltura,
    ]

    falhas = 0
    for passo in passos:
        if not passo():
            falhas += 1
            if passo == testar_supabase:
                # Supabase é crítico
                print("\n  Setup não pode continuar sem Supabase configurado.")
                print("  Configure o Supabase e rode este script novamente.\n")
                return 1

    imprimir_orientacoes()

    if falhas > 0:
        print(f"\n  [!] {falhas} aviso(s) durante o setup — revise acima\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
