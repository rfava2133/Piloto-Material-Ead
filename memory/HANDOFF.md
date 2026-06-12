# HANDOFF — Estado da Sessão de Trabalho

> Atualizar ao final de cada sessão ou quando tokens começarem a escassear.
> Permite que outro agente (ou próxima sessão) retome sem reler o histórico do chat.

---

## Sessão atual

**Data:** 2026-06-12
**Branch:** `main` — limpo (sem commits pendentes)
**Último commit:** `7d11dfe docs(handoff): registro completo da sessão 2026-06-11`

---

## O que foi feito nesta sessão

### 1. Atualização de documentação para envio em chat
- `CLAUDE.md`: adicionado status completo dos módulos, arquitetura M03 via API direta, princípios atualizados (ZERO terminal/CLI)
- `README.md`: expandido com M01b Separador, detalhes do M03, melhorias no laudo, pendências P2/P3/P4, custos de API
- `HANDOFF.md`: este arquivo — estado consolidado para handoff

---

## Estado Atual dos Módulos

| Módulo | Status | Implementação |
|--------|--------|---------------|
| **M01 — Extrator** | ✅ Completo | Pandoc + PyMuPDF, 100% determinístico |
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

## Melhorias Recentes (sessão 2026-06-11)

1. **Fix crítico — laudo.html:** `dados.status === 'ok'` → `'avaliada'`; fallback `aula_id` corrigido
2. **Conversa Inicial como aula 00:** `02-separar-aulas.py` detecta "Conversa Inicial" → pasta `aulas/00/`
3. **Interface — modo de testes:** botões "⚡ Preencher para Testes" e "🧹 LIMPAR TESTES"
4. **Indicador de IA:** status via `/api/ia-status` (🟢/🟡/🔴)
5. **Reprocessamento com `--forcar`:** material de teste atualizado (31.018 chars, 7 imgs)
6. **Fix M03 — botão visível:** `actionBar` exibida corretamente
7. **M03 sem terminal:** execução via API Anthropic direta
8. **Validador M03:** regex callouts com hífen, word boundary em palavras proibidas
9. **Laudo M02:** A2 com trechos de corpo como itálico, truncagem de autor/obra

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
- **Texto Display:** `03_reformulado/texto-display.md` — 80.2% volume, 6 vídeos, 7 imagens, glossário ✅

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
