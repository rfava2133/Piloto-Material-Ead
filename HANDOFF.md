# HANDOFF — Estado da Sessão de Trabalho

> Atualizar ao final de cada sessão ou quando tokens começarem a escassear.
> Permite que outro agente (ou próxima sessão) retome sem reler o histórico do chat.

---

## Sessão atual

**Data:** 2026-06-11
**Branch:** `main` (tudo commitado)
**Último commit:** `2fe9776` — feat(hub): Conversa Inicial no separador, fix laudo e indicador de status IA

---

## O que foi feito nesta sessão

### 1. Fix crítico — laudo.html nunca renderizava o relatório
- **Problema:** `carregarDaURL()` checava `dados.status === 'ok'` mas o servidor retorna `'avaliada'`
- **Fix:** `modulo02/laudo.html` — mudado para `=== 'avaliada'`; fallback `aula_id` também corrigido (`dados.score?.aula_id`)

### 2. Conversa Inicial como seção separável (aula 00)
- **`scripts/02-separar-aulas.py`**: nova regex `RE_CONVERSA_INICIAL`, detecção nas páginas e no sumário → aula `0` → pasta `aulas/00/`, id `FUN-00`, arquivo `fun_aula00.md`
- **`interface/index.html`**: adicionada `<option value="0">Conversa Inicial</option>` no combo de aulas; "Todas" atualizado para "Todas (CI + 01-08)"
- `_disciplina.yml` não conta CI no `aulas_total`

### 3. Interface — modo de testes e indicador de IA
- Botões "⚡ Preencher para Testes" e "🧹 LIMPAR TESTES" na topbar
- Indicador de status da IA (verde/amarelo/vermelho) via `/api/ia-status`
- Banner de alerta de fallback (oculto por padrão)
- `MODO_TESTES = true` — auto-preenche Administração / Fundamentos / Aula 1 ao carregar
- **Servidor:** nova rota `/api/teste-pdf` serve `testes/adm_fund_aula01.pdf`

### 4. Reprocessamento do material de teste
- `fun_aula01.md` estava com o livro inteiro (extraído sem separação antes da correção)
- Rodado `--forcar` no separador: CI em p.6 (2.165 chars), Aula 01 em p.7–23 (31.018 chars, 7 imgs)

---

## Pendências conhecidas (não resolvidas)

### P1 — Sumário do PDF vaza no markdown (ANOTADO)
O separador pula páginas de sumário como *divisor*, mas o intervalo de páginas pode incluir a página do sumário no conteúdo de alguma aula (CI ou Aula 01 começa logo após o sumário). O markdown da Aula 01 começa com o final do texto da Conversa Inicial antes do `**AULA 1**`.

**Para resolver:** detectar página de sumário e excluí-la explicitamente do intervalo de qualquer aula.

### P2 — PDF multi-aula enviado como aula individual não é detectado
Quando o usuário sobe o livro inteiro selecionando "Aula 1" (não "Todas"), o extrator não avisa nem separa. Gera um `fun_aula01.md` com o conteúdo completo do livro.

**Para resolver:** no fluxo individual (`api/processar` com `modulo=extrator`), detectar se o PDF tem múltiplas aulas e redirecionar para o separador ou exibir aviso.

### P3 — HANDOFF.md não está no fluxo automático
Não há instrução no CLAUDE.md pedindo ao agente para atualizar este arquivo ao final de cada sessão.

**Para resolver:** adicionar instrução no CLAUDE.md (ou criar hook) para lembrar de atualizar o HANDOFF antes de encerrar.

---

## Próximos passos sugeridos

1. **Testar fluxo completo** via interface: subir PDF → separar → avaliar (M02) → ver laudo renderizando corretamente
2. **Resolver P1 (sumário):** filtrar página de sumário do intervalo de páginas no separador
3. **Criar HANDOFF automático:** adicionar instrução no CLAUDE.md
4. **M04–M08:** ainda pendentes (PDF Full, Micro-roteiros, Imagens, Quiz, Montagem)

---

## Contexto crítico para o próximo agente

- **Servidor rodando em `:5050`** — `python3 servidor.py` (porta 5000 ocupada pelo AirPlay do macOS)
- **Codigo gerado automaticamente** pelo front-end via `gerarCodigo(disciplina)` = primeiras 3 letras sem acento. "Fundamentos de Administração" → `FUN` (não `ADM`)
- **Score existe** em `cursos/administracao/FUN-fundamentos-de-administracao/aulas/01/03_avaliacao/score_v01.json` — gerado por análise heurística (fallback), não pelo Agente E completo
- **PDF de testes:** `testes/adm_fund_aula01.pdf` — apostila UNIGRAN com CI + Aula 01 (p.1–23)
- **Skill `analista-conteudo`** ativa para M02; **skill `texto-display`** ativa para M03
