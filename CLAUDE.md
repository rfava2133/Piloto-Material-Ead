# CLAUDE.md — UNIGRAN EAD Esteira de Produção

> Este arquivo é lido automaticamente pelo Claude Code ao abrir o projeto.
> É a instrução-mãe. Tudo aqui prevalece, exceto `/docs/voz-unigran.md` em
> questões de tom e voz editorial.
> Leia também o `README.md` (symlink → `memory/README.md`) para o status atual de implementação de cada módulo.

## O QUE É ESTE PROJETO

Esteira de produção automatizada de material EAD UNIGRAN. Transforma material
bruto (Word/PDF do professor) em aula digital completa (HTML responsivo + PDF +
quiz interativo + micro-roteiros de vídeo), com avaliação automática de qualidade.

Escala alvo: ~1.200 disciplinas. Piloto: começar pelo material disponível.

## PRINCÍPIOS INVIOLÁVEIS

1. NUNCA gerar HTML final sem aprovação explícita do operador.
2. NUNCA pular a Etapa 2a (avaliação de qualidade — Agente E).
3. NUNCA editar arquivos em `01_source/` ou `02_markdown/` manualmente.
4. SEMPRE consultar `/docs/voz-unigran.md` antes de gerar texto.
5. SEMPRE criar backup antes de sobrescrever qualquer arquivo.
6. Idioma de trabalho e saída: português brasileiro.
7. ZERO terminal/CLI para o usuário final — tudo via interface web guiada.

## IDENTIDADE VISUAL (aprovada)

- Tipografia corpo: Literata 14.5pt / line-height 1.62
- Tipografia UI: Inter
- Cor primária: #0046A8
- Tinta: #1A1A1A (corpo) · #0D1117 (títulos)
- Papéis: #FBFAF7 (warm) · #F5EFE3 (sépia) · #1A1F26 (dark)
- Margens PDF: topo 18mm · rodapé 16mm · laterais 14mm
- 6 callouts: conceito-chave (azul) · atenção (gold) · resumo (verde) ·
  exercício (roxo) · dica (info-green) · leitura (cinza)

## PROIBIÇÕES EDITORIAIS

- Nunca "vestibular" → sempre "matrícula" ou "ingresso"
- Nunca "a Uni", "Unicão", artigo masculino → sempre "UNIGRAN"
- Nunca promessa de empregabilidade ou salário garantido
- Nunca culpabilizar o aluno
- Nunca exemplos políticos partidários ou religiosos específicos

## PIPELINE — MÓDULOS

| Módulo | Agente | Modelo | Status | Tarefa |
|--------|--------|--------|--------|--------|
| **M01 — Extrator** | — | determinístico | ✅ Completo | Pandoc + PyMuPDF → Markdown + imagens |
| **M01b — Separador** | — | determinístico | ✅ Completo | Separa PDF multi-aula em pastas individuais |
| **M02 — Analista de Conteúdo** | Agente E | claude-opus-4-7 | ✅ Completo | Avaliação de qualidade → índice 0–10 + veredito |
| **M03 — Texto Display** | Agente A | claude-sonnet-4-6 | ✅ Completo | Reformulação para tela (80% volume, callouts, glossário) |
| **M04 — PDF Full** | — | Puppeteer | 📋 Pendente | PDF do texto original |
| **M05 — Micro-roteiros** | Agente B | claude-sonnet-4-6 | 📋 Pendente | Roteiros de vídeo 60–120s |
| **M06 — Imagens** | Agente D | claude-haiku-4-5 | 📋 Pendente | Classificação em 3 trilhas + redesenho |
| **M07 — Quiz** | Agente C | claude-sonnet-4-6 | 📋 Pendente | Quiz HTML interativo |
| **M08 — Montagem HTML** | — | determinístico | 📋 Pendente | Combina texto + imagens + vídeos + quiz |

### M01 — Extrator (determinístico)
- Word (.docx) → Pandoc → Markdown + imagens em `04_imagens/antigas/`
- PDF → pymupdf4llm → Markdown + PyMuPDF → imagens
- Filtro: ícones < 100px descartados (configurável)

### M01b — Separador (determinístico)
- Detecta "Conversa Inicial" como aula 00
- Detecta "Aula 01", "Aula 02", etc. por regex no texto
- Cria pasta `aulas/NN/` para cada aula encontrada

### M02 — Analista de Conteúdo (IA + aritmética)
- Agente E (claude-opus-4-7) avalia via skill `analista-conteudo`
- **Fundamentos (A1, A2):** verificação de integridade → SEM_RESSALVA / RESSALVA / CRITICO
  - A1: Precisão Conceitual
  - A2: Validade Bibliográfica (guardrail: "não localizado" ≠ "falso")
- **Indicadores (B1–B5):** qualidade didática → notas 0–10
  - B1: Dialogicidade/Tom EAD (20%) — Moore, Freire
  - B2: Densidade Conceitual (15%) — Sweller
  - B3: Estrutura Pedagógica (30%) — Gagné, Biggs, Anderson & Krathwohl
  - B4: Engajamento (15%) — Knowles, Lave & Wenger
  - B5: Legibilidade Autoral (20%) — Mayer
- **Índice:** `B1×0,20 + B2×0,15 + B3×0,30 + B4×0,15 + B5×0,20`
- **Veredito (4 faixas):**
  - 🟢 APROVAR: ≥ 8,0 e sem CRÍTICO
  - 🟡 APROVAR COM RESSALVA: 6,5–7,9 e sem CRÍTICO
  - 🟠 INTERVENÇÃO EDITORIAL: 5,0–6,4 e sem CRÍTICO
  - 🔴 RECRIAR: < 5,0 OU qualquer CRÍTICO
- **Fallback:** `_gerar_score_minimo()` (análise heurística) quando IA indisponível
- **Versionamento:** `score_v01.json`, `score_v02.json` — nunca sobrescreve

### M03 — Texto Display (IA + validação determinística)
- Agente A (claude-sonnet-4-6) reformula via API Anthropic direta (sem terminal)
- **Regras:**
  - Volume mínimo: 80% do original — reescrever, não resumir
  - Citações: preservar intactas (M02 já validou)
  - Marcadores IMG: todos os `[IMG-NN]` mantidos
  - Callouts: máximo 2 por tópico, sintaxe `:::conceito-chave`
  - Vídeos: sugerir 3–6 marcadores `[VIDEO-NN]`
  - Glossário: 5–8 termos no final
  - Estrutura: abertura (pergunta-gancho) → H2 humanos → tópicos → fechamento (bullets)
- **Validação (`validador.py`):**
  - Crítico: volume ≥ 80%, IMG preservadas, glossário presente, sem palavras proibidas
  - Alerta: sem pergunta-gancho, sem bullets, sem vídeos
  - Palavras proibidas: "vestibular", "a Uni", "Unicão", "estaremos" (word boundary `\b`)
- **Versionamento:** backup automático ao reprocessar

### M08 — Montagem HTML (determinístico)
- Gate de aprovação do coordenador antes de publicar

## MÓDULOS DETERMINÍSTICOS (SEM IA)

M01 (Extrator), M01b (Separador), M04 (PDF Full), M08 (Montagem HTML).

## ESTRUTURA DE PASTAS POR AULA

```
cursos/{curso-slug}/{CODIGO-disciplina-slug}/aulas/{NN}/
├── 01_source/          INPUT (Word + PDF) — não editar
├── 02_markdown/        Pandoc/pyMuPDF gera — não editar
├── 03_avaliacao/       M02: laudo + score (criada na avaliação)
├── 03_reformulado/     M03: texto-display.md + display_meta.json
├── 04_imagens/
│   ├── antigas/        Extraídas automaticamente
│   ├── classificacao.json
│   └── prontas/        Redesenhadas
├── 05_output/          HTML + PDF finais
├── 06_revisao/         Notas do coordenador
└── 07_incubadora/      Material com veredito RECRIAR
    ├── material_atualizado/
    └── historico/
```

## NOMENCLATURA

- Código disciplina: 3 letras maiúsculas (ADM, PED, ENF) — `gerarCodigo()` no JS
- Pasta disciplina: `{CODIGO}-{slug-kebab}`
- ID aula: `{CODIGO}-{NN}` (ex: `ADM-01`, `FUN-00` para Conversa Inicial)
- Arquivos versionados: `Nome_v{NN}.md`, `score_v{NN}.json`

## COMANDOS DISPONÍVEIS

- Hub web: `python3 servidor.py` → `http://127.0.0.1:5050`
- `/processar-aula {ID}` — pipeline completo de 1 aula
- `/batch-disciplina {CODIGO}` — todas as aulas de uma disciplina
- Skill `/analista-conteudo` — Agente E (M02)
- Skill `/texto-display` — Agente A (M03)

## ESTADOS DO PAINEL

Não iniciado · Aguardando · Em revisão · Pronto

## MODO FALLBACK (IA INDISPONÍVEL)

Quando créditos da IA se esgotam ou API indisponível:

| Módulo | Prioridade (IA) | Fallback (local) |
|--------|-----------------|------------------|
| **M02** | Claude Opus (skill) | `_gerar_score_minimo()` — heurística |
| **M03** | Claude Sonnet (API) | Gera `_prompt_m03.txt` para execução manual |

**Indicador visual:** Topbar mostra status (🟢 online / 🟡 fallback / 🔴 offline).
**API `/api/ia-status`:** Retorna status geral e por módulo.

## ARQUITETURA M03 (API DIRETA)

M03 executa via `_executar_m03_via_api()` no `servidor.py`:
- Lê `skills/texto-display/SKILL.md` + `docs/voz-unigran.md` como contexto
- Prompt inclui contagem de palavras e mínimo obrigatório (80%)
- Saída estruturada: `<TEXTO_DISPLAY>...</TEXTO_DISPLAY>` + `<DISPLAY_META>...</DISPLAY_META>`
- Grava `03_reformulado/texto-display.md` + `display_meta.json`
- Rota `/api/m03-executar` (POST) e `/api/m03-check` (GET)

## CONTEXTOS CRÍTICOS

- **Servidor:** `python3 servidor.py` → `http://127.0.0.1:5050` (5000 = AirPlay macOS)
- **Chave API:** `ANTHROPIC_API_KEY` em `.env` na raiz (carregada automaticamente)
- **Material de teste:** `testes/adm_fund_aula01.pdf` — CI (p.6) + Aula 01 (p.7–23)
- **Usuário-alvo:** coordenadores pedagógicos — ZERO tolerância a terminal/CLI
