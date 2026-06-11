# UNIGRAN EAD — Esteira de Produção

## Visão Geral

Esteira de produção automatizada de material EAD UNIGRAN. Transforma material bruto
(Word ou PDF do professor) em aula digital completa: HTML responsivo + PDF + quiz
interativo + micro-roteiros de vídeo, com avaliação automática de qualidade.

**Escala alvo:** ~1.200 disciplinas (dados virão de planilha de cursos/professores)
**Piloto atual:** entrada manual pela interface (`dados/catalogo.csv`)

---

## Pipeline — Módulos

| Módulo | Agente | Modelo | Status | Implementação |
|--------|--------|--------|--------|---------------|
| **M01 — Extrator** | — | determinístico | ✅ Implementado | Pandoc + PyMuPDF |
| **M02 — Analista de Conteúdo** | Agente E | claude-opus-4-7 | ✅ Implementado | Avaliação + Relatório |
| **M03 — Texto Display (Agente A)** | Agente A | claude-sonnet-4-6 | ✅ Implementado | `04-agente-a.py`, `validador.py`, `display.html` |
| **M04 — PDF Full** | — | Puppeteer | 📋 Pendente | — |
| **M05 — Micro-roteiros (Agente B)** | Agente B | claude-sonnet-4-6 | 📋 Pendente | — |
| **M06 — Imagens (Agente D)** | Agente D | claude-haiku-4-5 | 📋 Pendente | — |
| **M07 — Quiz (Agente C)** | Agente C | claude-sonnet-4-6 | 📋 Pendente | — |
| **M08 — Montagem HTML** | Agente C | claude-sonnet-4-6 | 📋 Pendente | — |

> **Hub da esteira:** `python3 servidor.py` → `http://127.0.0.1:5050`  
> **Agente E:** skill `analista-conteudo` (Claude Code) grava `score_v01.json`; o servidor normaliza e recalcula via `calculo.py` antes de exibir o relatório.

> **Kaltura (separado):** o validador de links em `kaltura/` roda **à parte** da esteira — servidor próprio na porta `5070`, banco Supabase próprio. Documentação em [`kaltura/README.md`](kaltura/README.md).

---

# MÓDULO 01 — EXTRATOR ✅

Recebe Word ou PDF, extrai texto (Markdown) e imagens, cria estrutura de pastas.
100% determinístico, sem IA.

## Instalação

```bash
brew install pandoc python
pip install flask pyyaml pymupdf pymupdf4llm --break-system-packages
```

## Configuração — `scripts/config.yml`

```yaml
raiz: "/Users/rfava/projetos_ia/esteira_conteudo"

curso_padrao: "EAD"

sheets:
  sheet_id: ""
  aba_aulas: "aulas"
  aba_disciplinas: "disciplinas"
  habilitado: false          # true quando a planilha Google existir

subpastas:
  - "01_source"
  - "02_markdown"
  - "03_reformulado"
  - "04_imagens/antigas"
  - "04_imagens/prontas"
  - "05_output"
  - "06_revisao"
  - "07_incubadora/material_atualizado"
  - "07_incubadora/historico"

extracao:
  pandoc_extract_media: true
  pymupdf_min_largura: 100
  pymupdf_min_altura: 100
  formatos_imagem: ["png", "jpg", "jpeg"]

servidor:
  host: "127.0.0.1"
  porta: 5050  # 5000 ocupada pelo AirPlay Receiver do macOS
```

> **Nota:** `03_avaliacao/` não está no `config.yml` — o M02 cria essa pasta dinamicamente ao avaliar.

## Catálogo — `dados/catalogo.csv`

Colunas: `curso_final`, `disciplina`, `semestre`, `professor`. Alimenta o combo da interface via `/api/catalogo`.

## Como Usar — Interface Visual (Hub de Entrada)

```bash
python3 servidor.py
# abre http://127.0.0.1:5050
```

> **Nota:** a porta padrão é 5050 — a 5000 é ocupada pelo AirPlay Receiver do macOS.

**Fluxo:**
1. **Identifique a aula:**
   - Selecione o **Curso** (carrega do catálogo `dados/catalogo.csv`)
   - Selecione a **Disciplina** (filtra pelo curso, ordena por semestre)
   - Selecione o número da **Aula** (1 a 8)
   - Info de semestre e professor aparece automaticamente

2. **Suba o material:**
   - Escolha: **"Já diagramado"** (com imagens) ou **"Texto novo"**
   - Arraste o arquivo Word (.docx) ou PDF
   - Opcional: adicione imagens separadas (.png/.jpg ou .zip)

3. **Escolha o próximo passo:**
   - **Analisar conteúdo primeiro** (Recomendado) → M02 avalia substância
   - **Extrair direto — Módulo 01** → Gera .md + imagens imediatamente

## Como Usar — Linha de Comando

```bash
python3 scripts/01-processar-entrada.py \
    --curso "Administração" \
    --codigo ADM \
    --disciplina "Fundamentos de Administração" \
    --aula 1 \
    --word /caminho/aula.docx   # ou --pdf /caminho/aula.pdf
```

> O parâmetro `--curso` aceita o nome legível (ex.: `"Administração"`); internamente vira slug (`administracao`).

## Estrutura de Pastas Gerada

```
cursos/
└── {curso-slug}/
    └── {CODIGO-disciplina-slug}/
        ├── _disciplina.yml          # criado por 02-separar-aulas.py
        └── aulas/{NN}/
            ├── 01_source/           M01: originais
            ├── 02_markdown/         M01: texto extraído
            ├── 03_avaliacao/        M02: laudo + score (criada na avaliação)
            ├── 03_reformulado/      M03+M05
            ├── 04_imagens/
            │   ├── antigas/         M01: extraídas
            │   └── prontas/         M06: redesenhadas
            ├── 05_output/           M07+M08: HTML + PDF finais
            ├── 06_revisao/          Coordenador
            ├── 07_incubadora/       M01 cria; M02 grava se veredito = RECRIAR
            │   ├── material_atualizado/
            │   └── historico/
            └── _log.json
```

Exemplo: `cursos/administracao/ADM-fundamentos-administracao/aulas/01/`


## Roteamento por Formato

```
Veio Word (.docx)
  → Pandoc → 02_markdown/{ID}.md + imagens → 04_imagens/antigas/

Veio PDF
  → pymupdf4llm → 02_markdown/{ID}.md
  → PyMuPDF → 04_imagens/antigas/
```

## `_disciplina.yml`

```yaml
codigo: "ADM"
nome: "Fundamentos de Administração"
slug: "ADM-fundamentos-administracao"
curso: "Administração"
aulas_total: 8
professor:
  nome: ""
  email: ""
coordenador:
  nome: ""
  email: ""    # M02 usa para disparar reports (quando planilha chegar)
```

---

# MÓDULO 02 — ANALISTA DE CONTEÚDO ✅

Avalia a substância do material antes de qualquer reformulação.
**Princípio:** a diagramação corrige a forma; o analista julga a substância.
**Decisão humana:** o módulo recomenda; o coordenador decide. Nunca recriar automático.

## Componentes

| Arquivo | Função |
|---------|--------|
| `modulo02/calculo.py` | Aritmética pura: índice + veredito (sem IA) |
| `modulo02/test_calculo.py` | Valida os 4 cenários do PPT (5,70 · 7,40 · 4,00 · 8,45) |
| `modulo02/laudo.html` | Tela visual do **Relatório** (carregamento automático por URL) |
| `modulo02/referencias.py` | Extrai referências do markdown quando o Agente E não as grava |
| `modulo02/cenarios/` | JSONs de teste dos 4 vereditos — ver `cenarios/README.md` |
| `skills/analista-conteudo/SKILL.md` | Skill do Agente E — rubricas + schema obrigatório do score |
| `.claude/agents/analista-conteudo.md` | Prompt do Agente E (Opus 4.7) |
| `servidor.py` `/api/score` | Normaliza score, recalcula via `calculo.py` e enriquece A2 com refs |

## Como Usar — Interface Visual

1. No hub de entrada (`http://127.0.0.1:5050`):
   - Selecione Curso, Disciplina e Aula
   - Arraste o arquivo Word ou PDF
   - Clique em **"Analisar conteúdo primeiro"**

2. O servidor extrai o material (M01) e redireciona para o relatório da aula

3. Execute o Agente E no Claude Code para gerar o `score_v01.json`:
   - A skill `analista-conteudo` é ativada automaticamente ao pedir "avalia essa aula"
   - O score é gravado em `03_avaliacao/score_v01.json`

4. No relatório, clique **"Verificar novamente"** — a tela carrega e exibe o resultado corrigido

> **Garantia:** independente do formato que o Agente E produza, o `/api/score` sempre recalcula índice e veredito via `calculo.py` — o veredito da IA nunca chega à tela diretamente.

## Como Usar — Linha de Comando

```bash
# Avaliar uma aula específica
python3 scripts/03-agente-e.py \
    --codigo ADM \
    --disciplina "Fundamentos de Administração" \
    --aula 1 \
    --curso "Administração"

# Reavaliar (ignora score existente)
python3 scripts/03-agente-e.py --forcar ...
```

## Como Abrir o Relatório

1. **Automático:** Após a avaliação, o hub redireciona para `/modulo02/laudo.html?params`
2. **Manual:** Abra `modulo02/laudo.html` e carregue `03_avaliacao/score_v01.json`
3. **URL direta:** `http://127.0.0.1:5050/modulo02/laudo.html?curso=Administração&codigo=ADM&disciplina=...&aula=1`

## Outputs por Aula

```
03_avaliacao/
├── avaliacao_v01.md     # Laudo completo (markdown)
└── score_v01.json       # Dados estruturados (JSON)

07_incubadora/           # criada pelo M01; M02 grava laudo + motivo se veredito = RECRIAR
```

## Dois mecanismos independentes

### Verificação de Fundamentos (A1 e A2)
Condição de integridade — não gera índice, gera severidade.

| Fundamento | O que verifica | Severidades |
|---|---|---|
| **A1 — Precisão Conceitual** | Conceitos, definições, autorias, atualidade | SEM_RESSALVA · RESSALVA · CRITICO |
| **A2 — Validade Bibliográfica** | Referências reais, localizáveis, consistentes | SEM_RESSALVA · RESSALVA · CRITICO |

Guardrail A2: se não localiza a fonte → "não localizado para análise humana".
Nunca conclui sozinho que a fonte é falsa.

### Índice de Qualidade Didática (0–10)
`Índice = B1×0,20 + B2×0,15 + B3×0,30 + B4×0,15 + B5×0,20`

| Indicador | Peso | Base teórica |
|---|---|---|
| B1 — Dialogicidade / Tom EAD | 20% | Moore (1993) · Freire (1968/1970) |
| B2 — Densidade Conceitual | 15% | Sweller (1988) |
| B3 — Estrutura Pedagógica | 30% | Gagné (1965) · Biggs (1996) · Anderson & Krathwohl (2001) |
| B4 — Engajamento | 15% | Knowles · Lave & Wenger (1991) |
| B5 — Legibilidade Autoral | 20% | Mayer (2001/2014) |

Os pesos são decisão institucional deliberada da UNIGRAN EAD — não empíricos.
B3 tem maior peso porque o alinhamento entre objetivos, conteúdo e avaliação é o
fator que mais impacta a aprendizagem real (Biggs, 1996).

## Regra de veredito (4 faixas)

| Faixa | Condição | Ação do coordenador |
|---|---|---|
| 🟢 APROVAR | Índice ≥ 8,0 e sem CRÍTICO | Libera para diagramação |
| 🟡 APROVAR COM RESSALVA | 6,5–7,9 e sem CRÍTICO | Segue com relatório de ajustes |
| 🟠 INTERVENÇÃO EDITORIAL | 5,0–6,4 e sem CRÍTICO | Decide: edita ou devolve ao autor |
| 🔴 RECRIAR | Índice < 5,0 OU qualquer CRÍTICO | Retorna ao autor |

**Cenário 4 do PPT:** índice 8,45 (ótimo) + A2 CRÍTICO → veredito RECRIAR.
Verificação de Fundamentos ≠ Índice de Qualidade. São independentes.

## Aritmética é código, não IA

A IA (Agente E) atribui notas 0–10 por indicador.
O `calculo.py` faz a conta — o coordenador vê a conta exata.
Isso responde: "a máquina só acha?" — não, o cálculo é auditável.

## Validações Implementadas (pós-correção)

O M02 agora valida estritamente antes de gerar score:

| Validação | O que verifica | Resultado se falhar |
|---|---|---|
| `validar_notas()` | Exatamente B1–B5 presentes | `score_invalido` |
| `validar_notas()` | Cada nota entre 0 e 10 | `score_invalido` |
| `validar_severidade()` | A1/A2 ∈ {SEM_RESSALVA, RESSALVA, CRITICO} | `score_invalido` |
| `avaliar_com_ia()` | Skill retorna JSON estruturado | `erro_agente_e` (sem fallback) |

### Estados da API `/api/score`

| Estado | Significado |
|---|---|
| `sem_material` | Aula não extraída pelo M01 |
| `aguardando_avaliacao` | Material extraído, Agente E ainda não rodou |
| `avaliada` | Score válido presente e verificado |
| `erro_agente_e` | Falha explícita do Agente E (sem score gerado) |
| `score_invalido` | Score existe mas não passou na validação |

### Versionamento Automático

Os arquivos de avaliação são versionados automaticamente:
- `score_v01.json`, `score_v02.json`, ...
- `avaliacao_v01.md`, `avaliacao_v02.md`, ...

Use `--forcar` para reavaliar — cria nova versão, não sobrescreve.

### Modo Fallback (IA indisponível)

Quando os créditos da IA se esgotam ou a skill está offline, o sistema opera em **modo fallback**:

| Módulo | Com IA | Fallback (sem IA) |
|--------|--------|-------------------|
| **M02** | Claude Opus (skill) | **Ollama local** (codex, llama3) → JSON estruturado |
| **M03** | Claude Sonnet (skill) | **Ollama local** (codex, llama3) → texto-display.md |

**Fluxo automático:**
1. Tenta skill `/analista-conteudo` ou `/texto-display`
2. Se falhar (timeout, erro, sem créditos) → tenta Ollama com `codex`
3. Se `codex` falhar → tenta `llama3`
4. Se tudo falhar → retorna erro explícito

**Instalar Ollama:**
```bash
brew install ollama
ollama pull codex      # ou llama3
```

**Indicador visual:** Topbar mostra status (🟢 online / 🟡 fallback Ollama / 🔴 offline).

**API `/api/ia-status`:** Retorna status geral e por módulo.

## Regra de veredito (4 faixas)

| Faixa | Condição | Ação do coordenador |
|---|---|---|
| 🟢 APROVAR | Índice ≥ 8,0 e sem CRÍTICO | Libera para diagramação |
| 🟡 APROVAR COM RESSALVA | 6,5–7,9 e sem CRÍTICO | Segue com relatório de ajustes |
| 🟠 INTERVENÇÃO EDITORIAL | 5,0–6,4 e sem CRÍTICO | Decide: edita ou devolve ao autor |
| 🔴 RECRIAR | Índice < 5,0 OU qualquer CRÍTICO | Retorna ao autor |

**Cenário 4 do PPT:** índice 8,45 (ótimo) + A2 CRÍTICO → veredito RECRIAR.
Verificação de Fundamentos ≠ Índice de Qualidade. São independentes.

## Aritmética é código, não IA

A IA (Agente E) atribui notas 0–10 por indicador.
O `calculo.py` faz a conta — o coordenador vê a conta exata.
Isso responde: "a máquina só acha?" — não, o cálculo é auditável.

---

# MÓDULO 03 — TEXTO DISPLAY ✅

Reformula o markdown aprovado (M02) em versão display para tela: HTML responsivo + PDF final.

## Componentes

| Arquivo | Função |
|---------|--------|
| `skills/texto-display/SKILL.md` | Rubrica de reescrita + regras de marcação |
| `.claude/agents/texto-display.md` | Prompt do Agente A (Sonnet 4.6) |
| `modulo03/validador.py` | Validação determinística (sem IA) |
| `modulo03/test_validador.py` | Casos de teste do validador |
| `modulo03/display.html` | Tela de revisão (Opção B) |
| `scripts/04-agente-a.py` | Execução via linha de comando |

## Fluxo

```
02_markdown/{ID}.md (aprovado M02)
        ↓
   Agente A (Sonnet 4.6)
        ↓
03_reformulado/
├── texto-display.md       ← fonte única da aula HTML e do PDF final
└── display_meta.json      ← metadados para o pipeline
        ↓
   validador.py (automático)
        ↓
   display.html (revisão humana)
        ↓
   Aprovar → M04 (Imagens)
```

## Como Usar — Linha de Comando

```bash
python3 scripts/04-agente-a.py \
    --curso "Administração" \
    --codigo ADM \
    --disciplina "Fundamentos de Administração" \
    --aula 1

# Reprocessar (cria backup do existente)
python3 scripts/04-agente-a.py --forcar ...
```

## Regras de Reescrita (voz-unigran.md)

- **Volume mínimo:** 80% do original — reescrever, não resumir
- **Citações:** preservar intactas (M02 já validou)
- **Marcadores IMG:** todos os `[IMG-NN]` devem ser mantidos
- **Callouts:** máximo 2 por tópico (6 tipos: conceito, atenção, resumo, exercício, dica, leitura)
- **Vídeos:** sugerir 3–6 marcadores `[VIDEO-NN]`
- **Glossário:** 5–8 termos no final
- **Estrutura:** abertura (pergunta-gancho) → H2 humanos → tópicos (explica→exemplifica→aplica→checa) → fechamento (bullets)

## Validação (validador.py)

Verificações críticas (falha → bloqueia):
- Volume ≥ 80%
- Marcadores IMG preservados
- Glossário presente
- Palavras proibidas ausentes ("vestibular", "a Uni", "Unicão", "estaremos")

Alertas (não bloqueiam):
- Abertura sem pergunta-gancho
- Fechamento sem bullets
- Nenhum [VIDEO-NN] sugerido

## Tela de Revisão (display.html)

- Renderiza callouts com cores institucionais
- Placeholders visuais para `[IMG-NN]` e `[VIDEO-NN]`
- Painel lateral com resultado do validador
- Toggle "Ver markdown original"
- Botão **"Aprovar e seguir para imagens →"** (só ativo se validador ok)

---

# MÓDULO KALTURA — CONFERÊNCIA DE LINKS *(separado da esteira)*

> **Escopo:** ferramenta auxiliar que **roda à parte** — servidor, banco e deploy independentes.
> Não faz parte do pipeline M01–M08 nem do hub `servidor.py`.
> Será descontinuado quando os links estiverem corrigidos e integrados à esteira.

Documentação completa, instalação e operação: **[`kaltura/README.md`](kaltura/README.md)**

```bash
cd kaltura && python3 app.py   # http://127.0.0.1:5070
```

---

## Notas gerais

- Slug: `slugify()` remove acentos e gera kebab-case
- Filtro de imagens: ícones < 100px descartados (configurável)
- Reprocessamento: requer "reprocessar" na interface ou `--forcar`
- Log acumulativo: cada execução adiciona entrada ao `_log.json`
- Planilha de cursos: quando chegar, alimenta combo da interface e gera
  `_disciplina.yml` automaticamente com nomes e emails

---

## Estrutura de Arquivos do Projeto

```
esteira_conteudo/
├── .claude/
│   └── agents/
│       └── analista-conteudo.md    # M02: Prompt do Agente E
├── dados/
│   └── catalogo.csv                # Catálogo de cursos/disciplinas (piloto)
├── docs/
│   ├── INSTRUCOES_CHAT.md
│   └── PROMPT_MESTRE.md
├── interface/
│   └── index.html                  # Hub de entrada (:5050)
├── modulo02/
│   ├── calculo.py                  # M02: Aritmética pura (índice + veredito)
│   ├── test_calculo.py             # M02: Validação dos 4 cenários
│   ├── laudo.html                  # M02: Tela visual para coordenador
│   ├── referencias.py              # M02: Extrai refs do markdown (fallback A2)
│   ├── test-cenarios.html          # M02: Guia de teste dos cenários
│   └── cenarios/                   # JSONs + README dos 4 vereditos
├── scripts/
│   ├── config.yml                  # Configuração da esteira
│   ├── 01-processar-entrada.py     # M01: Extrator (Pandoc + PyMuPDF)
│   ├── 02-separar-aulas.py         # M01b: Separa PDF único em aulas
│   ├── 03-agente-e.py              # M02: Avaliação de qualidade
│   └── 04-agente-a.py              # M03: Texto Display
├── skills/
│   ├── analista-conteudo/          # Skill do Agente E (Claude Code)
│   └── texto-display/              # Skill do Agente A (M03)
├── modulo02/
│   ├── calculo.py                  # M02: Aritmética pura (índice + veredito)
│   ├── test_calculo.py             # M02: Validação dos 4 cenários
│   ├── laudo.html                  # M02: Tela visual para coordenador
│   ├── referencias.py              # M02: Extrai refs do markdown (fallback A2)
│   ├── test-cenarios.html          # M02: Guia de teste dos cenários
│   └── cenarios/                   # JSONs + README dos 4 vereditos
├── modulo03/
│   ├── validador.py                # M03: Validação determinística
│   ├── test_validador.py           # M03: Casos de teste
│   └── display.html                # M03: Tela de revisão
├── templates_design/               # Templates HTML/PDF aprovados
├── cursos/                         # Material processado (gerado pelo M01)
│   └── {curso-slug}/{CODIGO-slug}/aulas/{NN}/
├── kaltura/                        # SEPARADO: validador de links (Flask :5070)
│   └── README.md                   # Documentação completa — roda à parte
├── CLAUDE.md                       # Instruções do projeto
├── AGENTS.md
├── README.md                       # Este arquivo
└── servidor.py                     # Hub da esteira (Flask :5050)
```

---

*Atualizado em 2026-06-11*

---

## 📋 Resumo do Status

### ✅ Implementado (esteira)

| Módulo | Funcionalidade | Arquivos |
|--------|----------------|----------|
| **M01** | Extração Word/PDF → Markdown + imagens | `01-processar-entrada.py`, `02-separar-aulas.py` |
| **M01b** | Separação automática de PDF único | `02-separar-aulas.py` |
| **M02** | Avaliação de qualidade (Agente E) | `03-agente-e.py`, `calculo.py`, `laudo.html` |
| **M03** | Texto Display (Agente A) | `04-agente-a.py`, `validador.py`, `display.html` |

### 🔧 Interface da esteira

- Hub de entrada com catálogo de disciplinas (`interface/index.html`)
- Laudo visual com carregamento automático (`modulo02/laudo.html` — tela de **Relatório**)
- API REST (`servidor.py`): `/api/catalogo`, `/api/processar`, `/api/score`

### 📦 Fora da esteira (documentado)

| Módulo | Função | Documentação |
|--------|--------|--------------|
| **Kaltura** *(temp.)* | Conferência humana de vínculos vídeo ↔ aula | [`kaltura/README.md`](kaltura/README.md) — roda em `:5070`, Supabase próprio |

### 📊 Métricas do M02

- **2 Fundamentos** (A1, A2): verificação de integridade
- **5 Indicadores** (B1–B5): qualidade didática
- **4 Vereditos**: APROVAR · APROVAR_COM_RESSALVA · INTERVENCAO · RECRIAR
- **07_incubadora/**: M02 grava laudo + motivo automaticamente quando veredito = RECRIAR
