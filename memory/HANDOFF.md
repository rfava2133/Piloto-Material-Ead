# HANDOFF — Estado da Sessão de Trabalho

> Atualizar ao final de cada sessão ou quando tokens começarem a escassear.
> Permite que outro agente (ou próxima sessão) retome sem reler o histórico do chat.

---

## Sessão atual

**Data:** 2026-06-12
**Branch:** `main` — limpo
**Último commit:** `9a1b920` — docs(memory): atualiza HANDOFF e cria correcoes-tarde-2026-06-12.md

---

## Correções Tardia (2026-06-12 14:50–15:30)

| # | Correção | Arquivo | Descrição |
|---|----------|---------|-----------|
| 11 | **M02 — Reverter para skill** | `scripts/03-agente-e.py` | Revertido para commit `719b0df` — usa skill `/analista-conteudo`, não API direta |
| 12 | **M03 — Limite vídeos** | `skills/texto-display/SKILL.md` | Corrigido: "exatamente 1 vídeo por aula" (linha 104) |
| 13 | **Servidor — Contar imagens M01** | `servidor.py` | API `/api/m03-check` retorna `imagens_m01` |
| 14 | **Servidor — Reverter** | `servidor.py` | Revertido para commit `719b0df` — remove `_executar_m02_via_api()` |

---

## O que foi feito nesta sessão

### 1. Atualização de documentação para envio em chat
- `CLAUDE.md`: adicionado status completo dos módulos, arquitetura M03 via API direta, princípios atualizados (ZERO terminal/CLI)
- `README.md`: expandido com M01b Separador, detalhes do M03, melhorias no laudo, pendências P2/P3/P4, custos de API
- `HANDOFF.md`: este arquivo — estado consolidado para handoff

### 2. Correções de Interface e Funcionalidades

| # | Correção | Arquivo | Descrição |
|---|----------|---------|-----------|
| 1 | **A2 com bibliografia completa** | `modulo02/laudo.html` | Busca referência completa cruzando autor+ano com `referencias_bibliograficas` |
| 2 | **Status M02 "PENDENTE" corrigido** | `interface/m03-preview.html` | Veredito é string direta (`"APROVAR"`), não objeto com `rotulo` |
| 3 | **M01 cria marcadores [IMG-NN]** | `scripts/01-processar-entrada.py` | Função `normalizar_marcadores_imagens()` converte `**Figura N -**` e `Figura N:` para `[IMG-NN alt="..."]` |
| 4 | **Limite de vídeos: 1 por aula** | `skills/texto-display/SKILL.md` | Mudado de "3 a 6 vídeos" para "exatamente 1 vídeo por aula" |
| 5 | **Link UNIGRAN EAD → home** | `interface/index.html` | Brand agora aponta para `/` |
| 6 | **Botão Aprovação Professor** | `modulo03/display.html` | Adicionado botão para `aprovacao-professor.html` |
| 7 | **Métricas "encontrados"** | `display.html`, `m03-preview.html` | Renomeado de "sugeridos" para "encontrados" |
| 8 | **Contador Imagens M01** | `servidor.py`, `display.html` | API retorna `imagens_m01`; display mostra "Imagens (M01)" |
| 9 | **A2 busca simplificada** | `modulo02/laudo.html` | Busca por ano ou palavra-chave (commit `8c6609c`) |
| 10 | **Cache da API** | `modulo02/laudo.html` | Timestamp na URL para evitar cache (commit `91397a2`) |

---

## Estado Atual dos Módulos

| Módulo | Status | Implementação |
|--------|--------|---------------|
| **M01 — Extrator** | ✅ Completo | Pandoc + PyMuPDF + **marcadores [IMG-NN] automáticos** |
| **M01b — Separador** | ✅ Completo | Detecta "Conversa Inicial" (aula 00) + "Aula 01-08" |
| **M02 — Analista** | ✅ Completo | Skill `analista-conteudo` + `calculo.py` (aritmética auditável) |
| **M03 — Texto Display** | ✅ Completo | API Anthropic direta (`_executar_m03_via_api()`), sem terminal |
| **M04 — PDF Full** | 📋 Pendente | Puppeteer |
| **M05 — Micro-roteiros** | 📋 Pendente | Agente B |
| **M06 — Imagens** | 📋 Pendente | Agente D |
| **M07 — Quiz** | 📋 Pendente | Agente C |
| **M08 — Montagem HTML** | 📋 Pendente | Determinístico |

---

## Arquitetura M03 (Entrega Principal da Sessão Anterior)

**Problema resolvido:** usuário não pode usar terminal/CLI.

**Solução:** `_executar_m03_via_api()` no `servidor.py`:
- Lê `skills/texto-display/SKILL.md` + `docs/voz-unigran.md` como contexto
- Prompt inclui contagem de palavras do original e mínimo obrigatório (80%)
- Saída estruturada: `<TEXTO_DISPLAY>...</TEXTO_DISPLAY>` + `<DISPLAY_META>...</DISPLAY_META>`
- Grava `03_reformulado/texto-display.md` + `display_meta.json`
- Validação automática via `validador.py` (regex `:::([\w-]+)` para callouts com hífen)
- Word boundary `\b` em palavras proibidas (evita falso positivo)

**Rotas API:**
- `POST /api/m03-executar` — executa M03
- `GET /api/m03-check` — verifica se M03 foi executado

**Interface:**
- `/m03-preview` — fluxo passo-a-passo
- `/modulo03/display.html?params` — tela de revisão com validador

---

## Melhorias Recentes

### Sessão 2026-06-12 (Tarde) — Commits `6fe39bb`, `8c6609c`, `91397a2`
1. **Link UNIGRAN EAD → home** — brand agora aponta para `/`
2. **Botão Aprovação Professor** — display.html tem botão para versão clean de aprovação
3. **Métricas renomeadas** — "Imagens/Vídeos Encontrados" (não "sugeridos")
4. **Contador Imagens M01** — API `/api/m03-check` retorna `imagens_m01`; display mostra "Imagens (M01)"
5. **A2 busca simplificada** (`8c6609c`) — laudo.html busca por ano ou palavra-chave do autor
6. **Cache da API** (`91397a2`) — timestamp na URL para evitar cache do browser

### Sessão 2026-06-12 (Manhã) — Commit `719b0df`
7. **A2 com bibliografia completa** — busca referência cruzando autor+ano
8. **Status M02 corrigido** — m03-preview.html acessa veredito como string
9. **M01 cria marcadores [IMG-NN]** — `normalizar_marcadores_imagens()` no extrator
10. **Vídeos: 1 por aula** — SKILL.md: "exatamente 1 vídeo"

### Sessão 2026-06-11
11. **Fix crítico — laudo.html:** `dados.status === 'ok'` → `'avaliada'`
12. **Conversa Inicial como aula 00:** `aulas/00/`
13. **Interface — modo de testes:** botões auto-preenchimento
14. **Indicador de IA:** `/api/ia-status` (🟢//🔴)
15. **M03 sem terminal:** API Anthropic direta
16. **Validador M03:** regex callouts, word boundary

---

## Pendências Conhecidas

| ID | Descrição | Impacto |
|----|-----------|---------|
| **P2** | Sumário do PDF vaza no markdown (páginas de sumário incluídas no intervalo da Aula 01) | Média — requer ajuste em `02-separar-aulas.py` |
| **P3** | PDF multi-aula enviado como aula individual não é detectado | Média — requer redirecionamento para separador |
| **P4** | `display.html` usa validação inline (cliente), não a do servidor | Baixa — resultado é equivalente, mas poderia buscar via API |

---

## Próximos Passos Sugeridos (em ordem)

1. **Resolver P2** — excluir páginas de sumário explicitamente em `02-separar-aulas.py`
2. **Resolver P3** — detectar PDF multi-aula no fluxo individual e redirecionar
3. **M04 — PDF Full** (Puppeteer) — gerar PDF do texto display
4. **M05 — Micro-roteiros** (Agente B) — roteiros de vídeo 60-120s
5. **M06 — Imagens** (Agente D) — classificação em 3 trilhas
6. **M07 — Quiz** (Agente C) — quiz HTML interativo
7. **M08 — Montagem HTML** — combinar todos os elementos

---

## Contexto Crítico para o Próximo Agente

### Servidor e API
- **Hub:** `python3 servidor.py` → `http://127.0.0.1:5050` (porta 5000 = AirPlay macOS)
- **Chave API:** `ANTHROPIC_API_KEY` em `.env` na raiz (carregada automaticamente)
- **SDK instalado:** `pip install anthropic`

### Material de Teste
- **PDF:** `testes/adm_fund_aula01.pdf` — apostila UNIGRAN com CI (p.6) + Aula 01 (p.7–23)
- **Pasta de teste:** `cursos/administracao/FUN-fundamentos-de-administracao/aulas/01/`
- **Score:** `03_avaliacao/score_v01.json` — heurístico (fallback), não Agente E completo
- **Texto Display:** `03_reformulado/texto-display.md` — 80.2% volume, 1 vídeo, 7 imagens, glossário ✅
- **Imagens no M01:** marcadores `[IMG-NN]` criados automaticamente a partir de `**Figura N -**`

### URLs de Teste
- Hub: `http://127.0.0.1:5050`
- Laudo M02: `/modulo02/laudo.html?curso=Administração&codigo=FUN&disciplina=Fundamentos+de+Administração&aula=1`
- M03 Preview: `/m03-preview?curso=...&codigo=...&disciplina=...&aula=...`
- Display M03: `/modulo03/display.html?curso=...&codigo=...&disciplina=...&aula=...`

### Convenções
- **Código disciplina:** `gerarCodigo(disciplina)` = primeiras 3 letras sem acento → "Fundamentos de Administração" → `FUN`
- **Aula 00:** Conversa Inicial (ID: `{CODIGO}-00`)
- **Usuário-alvo:** coordenadores pedagógicos — ZERO tolerância a terminal ou CLI

### Custo de API (referência)
| Módulo | Modelo | Custo por aula | Tokens (in/out) |
|--------|--------|---------------|-----------------|
| M02 — Analista | claude-opus-4-7 | ~USD 0.08 | ~3k / ~1k |
| M03 — Texto Display | claude-sonnet-4-6 | ~USD 0.19 | ~7.5k / ~5k |

**Escala total (9.600 aulas):** ~USD 1.820 só M03

---

## Premissas Editoriais (NÃO NEGOCIÁVEIS)

### Proibições
- Nunca "vestibular" → sempre "matrícula" ou "ingresso"
- Nunca "a Uni", "Unicão", artigo masculino → sempre "UNIGRAN"
- Nunca promessa de empregabilidade ou salário garantido
- Nunca culpabilizar o aluno
- Nunca exemplos políticos partidários ou religiosos específicos

### Identidade Visual
- Tipografia corpo: Literata 14.5pt / line-height 1.62
- Tipografia UI: Inter
- Cor primária: #0046A8
- 6 callouts: conceito-chave, atenção, resumo, exercício, dica, leitura

### Princípios de Pipeline
1. NUNCA gerar HTML final sem aprovação explícita do operador
2. NUNCA pular M02 (avaliação de qualidade — Agente E)
3. NUNCA editar arquivos em `01_source/` ou `02_markdown/` manualmente
4. SEMPRE consultar `/docs/voz-unigran.md` antes de gerar texto
5. SEMPRE criar backup antes de sobrescrever qualquer arquivo
6. Idioma de trabalho e saída: português brasileiro

---

*Atualizado em 2026-06-12*
