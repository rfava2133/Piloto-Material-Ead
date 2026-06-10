# Validador Kaltura UNIGRAN

> **Módulo temporário** — fora da esteira principal de produção (`servidor.py`).
> Usado enquanto o catálogo de vídeos da Kaltura é conferido manualmente antes
> de integrar os links definitivos às aulas da esteira.

Aplicação web para validar se os vídeos da Kaltura correspondem às aulas de cada disciplina.

**Status:** ✅ Operacional (testado em 2026-06-10)  
**Stack:** Flask + Supabase (PostgreSQL + Auth)  
**Porta:** `5070` (independente do hub principal na `5050`)

---

## 🚀 Acesso Rápido

```bash
cd kaltura
python3 app.py
# Abre http://127.0.0.1:5070
```

**Usuários disponíveis:**
| Email | Senha |
|-------|-------|
| `analista.usa@unigran.br` | `Yhs2312*` |
| `giovane@unigran.br` | `123456` |

---

## 📋 Fluxo de Trabalho

1. **Login** — acesse com email/senha
2. **Selecionar curso** — carrega disciplinas do catálogo
3. **Selecionar disciplina** — mostra aulas 1-8 (ou mais)
4. **Conferir vídeo** — assista e valide:
   - ✅ **Vínculo correto** — vídeo pertence à aula
   - ❌ **Vínculo errado** — vídeo não corresponde
   - 🔄 **Reverter para análise** — desfaz a validação e volta a aula para `pendente`
5. **Progresso** — acompanhe validações por disciplina

> Aulas já validadas continuam clicáveis na lista lateral: abra a aula e use
> **Reverter para análise** para reavaliá-la.

---

## 🛠️ Instalação

### 1. Dependências Python

```bash
pip install -r requirements.txt --break-system-packages
```

### 2. Configurar `.env`

```bash
cp .env.example .env
```

Edite `.env` com suas credenciais do Supabase e Kaltura:

```env
# Kaltura
KALTURA_ADMIN_SECRET="seu_admin_secret"

# Supabase
SUPABASE_URL="https://xxxxx.supabase.co"
SUPABASE_KEY="sua_service_role_key"
```

### 3. Rodar a aplicação

```bash
python3 app.py
```

Acesse: **http://127.0.0.1:5070**

---

## ️ Banco de Dados (Supabase)

### Tabelas

| Tabela | Descrição |
|--------|-----------|
| `disciplinas` | Catálogo de cursos/disciplinas (1000+ registros) |
| `videos_kaltura` | Vídeos importados da Kaltura por aula |
| `validacoes` | Validações humanas dos vínculos vídeo-aula |
| `audit_log` | Log de auditoria das ações |

### Schema

O schema completo está em `schema.sql`. Para aplicar:

1. Acesse https://supabase.com
2. Vá para **SQL Editor**
3. Copie e execute o conteúdo de `schema.sql`

Todas as tabelas têm **Row Level Security (RLS)** ativado.

---

## 📁 Scripts Utilitários

| Script | Função |
|--------|--------|
| `setup.py` | Verifica dependências, .env e conexão Supabase |
| `migrar_csv_supabase.py` | Migra CSVs legados para o Supabase |
| `criar_usuario.py` | Cria usuários no Supabase Auth |

### Criar novo usuário

```bash
python3 criar_usuario.py novo.usuario@unigran.br SenhaForte123
```

### Migrar dados de CSVs existentes

```bash
python3 migrar_csv_supabase.py
```

---

## 🔌 API Endpoints

### Autenticação

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/auth/login` | POST | Login (email, senha) |
| `/api/auth/logout` | POST | Logout |
| `/api/auth/me` | GET | Usuário atual |

### Dados (requer autenticação)

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/catalogo` | GET | Lista cursos e disciplinas |
| `/api/disciplina/<did>` | GET | Detalhes de uma disciplina |
| `/api/importar` | POST | Importa vídeos da Kaltura |
| `/api/validar` | POST | Salva validação de aula |
| `/api/preview/<entry_id>` | GET | URL de preview do vídeo |

---

## 📊 Estrutura de Dados

### Disciplina

```json
{
  "disc_id": "hash_curso_disciplina_semestre",
  "curso_final": "Administração",
  "disciplina": "Empreendedorismo",
  "semestre": "1º",
  "professores": ["Prof. A", "Prof. B"],
  "playlist_id": "kaltura_playlist_id"
}
```

### Validação

```json
{
  "disciplina_id": "uuid",
  "aula": 1,
  "status_validacao": "correto",
  "observacao": "",
  "responsavel": "analista.usa@unigran.br",
  "validado_em": "2026-06-10T17:00:00"
}
```

**Status possíveis:**
- `correto` — aprovado
- `corrigido` — aprovado com ajuste
- `vinculo_errado` — precisa revisar
- `sem_video` — aula sem vídeo
- `pendente` — aguardando análise (usado também ao reverter uma validação)

> **Atenção:** a tabela `validacoes` **não** possui as colunas `playlist_id` e
> `nome_video` (ver `schema.sql`). O cliente (`supabase_client.upsert_validacao`)
> filtra o payload e envia apenas colunas existentes no schema.

---

## 🔐 Segurança

- **Autenticação:** Supabase Auth (email/senha)
- **RLS:** Row Level Security em todas as tabelas
- **Sessão:** Flask sessions com cookie seguro
- **Audit log:** Todas as ações são registradas

---

## 🌐 Deploy (Produção)

Para uso multi-usuário:

1. **Servidor:** VM ou servidor interno da UNIGRAN
2. **Ambiente:** Variáveis `.env` no servidor
3. **HTTPS:** Use um reverse proxy (nginx/Caddy)
4. **WSGI:** Gunicorn ou uWSGI (não use Flask dev server)

Exemplo com Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5070 app:app
```

---

## 🧪 Testes

### Verificar setup

```bash
python3 setup.py
```

### Testar conexão Supabase

```bash
python3 -c "import supabase_client as db; print(db.listar_disciplinas()[:3])"
```

### Testar login

```bash
curl -X POST http://127.0.0.1:5070/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"analista.usa@unigran.br","senha":"Yhs2312*"}'
```

---

## 📁 Arquivos do Projeto

```
kaltura/
├── app.py                        # Servidor Flask principal
├── supabase_client.py            # Cliente Supabase (auth + DB)
├── exportar_videos_catalogo.py   # Importador API Kaltura
├── migrar_csv_supabase.py        # Migração CSV → Supabase
├── criar_usuario.py              # Cria usuários Auth
├── setup.py                      # Script de setup inicial
├── check_rls.py                  # Verifica políticas RLS
├── schema.sql                    # Schema do banco
├── static/
│   ├── index.html                # App principal
│   └── login.html                # Tela de login
├── .env                          # Credenciais (não versionar)
├── .env.example                  # Modelo de .env
├── requirements.txt              # Dependências Python
└── README.md                     # Este arquivo
```

---

## 🐛 Correções Conhecidas (2026-06-10)

### 1. Erro "The string did not match the expected pattern" ao selecionar disciplina

- **Sintoma:** Safari exibia essa mensagem ao trocar de disciplina; as aulas não carregavam.
- **Causa raiz:** `/api/disciplina/<did>` chamava `videos_por_disciplina()`, que fazia
  **uma query ao Supabase por disciplina** (~1000+ queries). A requisição levava >2 min
  e retornava **500** (HTML), que o navegador tentava parsear como JSON.
- **Correção:** o endpoint agora busca vídeos **apenas da disciplina selecionada**
  (1 query). `catalogo_agrupado()` passou a expor o UUID (`id`) da disciplina.
  Resultado: ~2s em vez de ~126s.

### 2. Erro 500 ao clicar em "Vínculo correto"

- **Sintoma:** `Erro ao salvar: Erro 500` ao validar uma aula.
- **Causa raiz:** o payload enviado ao Supabase incluía `playlist_id` e `nome_video`,
  colunas que **não existem** na tabela `validacoes` (erro `PGRST204`).
- **Correção:** `upsert_validacao` filtra o payload por uma whitelist de colunas
  (`_COLUNAS_VALIDACAO`) antes do insert/update.

### 3. Bug no resolve de `disciplina_id` em `upsert_validacao`

- **Causa raiz:** o `disc_id` era removido do payload **antes** de ser usado para
  resolver o `disciplina_id` (UUID), quebrando o fallback.
- **Correção:** o hash é guardado em variável antes da limpeza do payload.

### 4. Tratamento de erros no frontend

- `getJson()` agora detecta respostas não-JSON (ex.: páginas de erro HTML) e exibe
  mensagem clara com o código HTTP, em vez do erro críptico de parse do Safari.
- Erros ao trocar de disciplina aparecem na barra de aviso.

---

## 📝 Histórico

| Data | Mudança |
|------|---------|
| 2026-06-10 | Migração para Supabase + autenticação |
| 2026-06-10 | Otimização da API `/api/catalogo` (3 queries) |
| 2026-06-10 | Criação de usuários via script |
| 2026-06-10 | Fix: `/api/disciplina` com 1 query (era 1000+, dava timeout/500) |
| 2026-06-10 | Fix: `/api/validar` 500 — whitelist de colunas em `upsert_validacao` |
| 2026-06-10 | Fix: resolve de `disciplina_id` via `disc_id` em `upsert_validacao` |
| 2026-06-10 | UX: `getJson()` trata respostas não-JSON com mensagem clara |
| 2026-06-10 | Novo: botão **Reverter para análise** (volta aula para `pendente`) |
| 2026-06-10 | UX: aulas validadas continuam clicáveis (para permitir reversão) |
| 2026-06-10 | ✅ Validado em produção local — carregamento, validação e reversão OK |

---

*Atualizado em 2026-06-10 — operacional; módulo temporário de conferência de links*
