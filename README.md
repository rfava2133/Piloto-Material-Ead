# UNIGRAN EAD — Esteira de Produção

## Visão Geral

Esteira de produção automatizada de material EAD UNIGRAN. Transforma material bruto
(Word ou PDF do professor) em aula digital completa: HTML responsivo + PDF + quiz
interativo + micro-roteiros de vídeo, com avaliação automática de qualidade.

**Escala alvo:** ~1.200 disciplinas (dados virão de planilha de cursos/professores)
**Piloto atual:** entrada manual pela interface

---

## Pipeline — Módulos

| Módulo | Agente | Modelo | Status | Implementação |
|--------|--------|--------|--------|---------------|
| **M01 — Extrator** | — | determinístico | ✅ Implementado | Pandoc + PyMuPDF |
| **M02 — Analista de Conteúdo** | Agente E | claude-opus-4-7 | ✅ Implementado | Avaliação + Laudo |
| **M03 — Texto Display (Agente A)** | Agente A | claude-opus-4-7 | 📋 Pendente | — |
| **M04 — PDF Full** | — | Puppeteer | 📋 Pendente | — |
| **M05 — Micro-roteiros (Agente B)** | Agente B | claude-sonnet-4-6 | 📋 Pendente | — |
| **M06 — Imagens (Agente D)** | Agente D | claude-haiku-4-5 | 📋 Pendente | — |
| **M07 — Montagem HTML (Agente C)** | Agente C | claude-sonnet-4-6 | 📋 Pendente | — |
| **M08 — Quiz (Agente C)** | Agente C | claude-sonnet-4-6 | 📋 Pendente | — |

> **Nota:** O M02 está implementado com cálculo determinístico (`modulo02/calculo.py`).
> A chamada à API do Claude (Agente E) será integrada via Skill `analista-conteudo`.

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
raiz: "/Users/rfava/PROJETOS IA/piloto-extrator"

subpastas:
  - "01_source"
  - "02_markdown"
  - "03_avaliacao"
  - "04_reformulado"
  - "05_imagens/antigas"
  - "05_imagens/prontas"
  - "06_output"
  - "07_revisao"
  # _incubadora/ criada dinamicamente pelo M02 quando veredito = RECRIAR

extracao:
  pandoc_extract_media: true
  pymupdf_min_largura: 100
  pymupdf_min_altura: 100
  formatos_imagem: ["png", "jpg", "jpeg"]

servidor:
  host: "127.0.0.1"
  porta: 5000
```

## Como Usar — Interface Visual (Hub de Entrada)

```bash
python3 servidor.py
# abre http://127.0.0.1:5000
```

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
    --curso "administracao" \
    --codigo ADM \
    --disciplina "Fundamentos de Administração" \
    --aula 1 \
    --word /caminho/aula.docx   # ou --pdf /caminho/aula.pdf
```

## Estrutura de Pastas Gerada

```
cursos/
└── {curso}/
    └── disciplinas/
        └── {CODIGO}-{slug}/
            ├── _disciplina.yml
            └── aula-{NN}/
                ├── 01_source/        M01: originais
                ├── 02_markdown/      M01: texto extraído
                ├── 03_avaliacao/     M02: laudo + score
                ├── 04_reformulado/   M03+M05+M08
                ├── 05_imagens/
                │   ├── antigas/      M01: extraídas
                │   └── prontas/      M06: redesenhadas
                ├── 06_output/        M07: HTML + PDF finais
                ├── 07_revisao/       Coordenador
                ├── _incubadora/      condicional (veredito RECRIAR)
                │   ├── material_atualizado/
                │   └── historico/
                └── _log.json
```

## Roteamento por Formato

```
Veio Word (.docx)
  → Pandoc → 02_markdown/{ID}.md + imagens → 05_imagens/antigas/

Veio PDF
  → pymupdf4llm → 02_markdown/{ID}.md
  → PyMuPDF → 05_imagens/antigas/
```

## `_disciplina.yml`

```yaml
codigo: "ADM"
nome: "Fundamentos de Administração"
slug: "ADM-fundamentos-administracao"
curso: "administracao"
aulas_total: 0
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
| `modulo02/test_calculo.py` | Valida os 4 cenários do PPT (5,70 · 7,15 · 4,00 · 8,45) |
| `modulo02/laudo.html` | Tela visual do laudo para o coordenador |
| `.claude/agents/analista-conteudo.md` | Prompt do Agente E (Opus 4.7) |
| `scripts/03-agente-e.py` | Script de execução do Agente E |

## Como Usar — Interface Visual

1. No hub de entrada (`http://127.0.0.1:5000`):
   - Selecione Curso, Disciplina e Aula
   - Arraste o arquivo Word ou PDF
   - Clique em **"Analisar conteúdo primeiro"**

2. O sistema irá:
   - Extrair o material (M01)
   - Executar o Agente E (avaliação)
   - Redirecionar para `/modulo02/laudo.html?curso=..&aula=N`

3. O laudo carrega automaticamente se o score já existir

## Como Usar — Linha de Comando

```bash
# Avaliar uma aula específica
python3 scripts/03-agente-e.py \
    --codigo ADM \
    --disciplina "Fundamentos de Administração" \
    --aula 1 \
    --curso "administracao"

# Reavaliar (ignora score existente)
python3 scripts/03-agente-e.py --forcar ...
```

## Como Abrir o Laudo

1. **Automático:** Após a avaliação, o hub redireciona para `/modulo02/laudo.html?params`
2. **Manual:** Abra `modulo02/laudo.html` e carregue `03_avaliacao/score_v01.json`
3. **URL direta:** `http://127.0.0.1:5000/modulo02/laudo.html?curso=adm&codigo=ADM&disciplina=...&aula=1`

## Outputs por Aula

```
03_avaliacao/
├── avaliacao_v01.md     # Laudo completo (markdown)
└── score_v01.json       # Dados estruturados (JSON)
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

## Outputs por aula

```
03_avaliacao/
├── avaliacao_v01.md     laudo completo (humano lê)
└── score_v01.json       machine-readable (pipeline consome)

_incubadora/             criada apenas se veredito = RECRIAR
```

## Componentes técnicos

| Arquivo | Função |
|---|---|
| `modulo02/calculo.py` | Aritmética pura: índice + veredito (sem IA) |
| `modulo02/test_calculo.py` | Valida os 4 cenários do PPT (7,15·5,70·4,00·8,45) |
| `.claude/agents/analista-conteudo.md` | Prompt do Agente E (Opus 4.7) |
| `modulo02/laudo.html` | Tela visual do laudo para o coordenador |

## Aritmética é código, não IA

A IA (Agente E) atribui notas 0–10 por indicador.
O `calculo.py` faz a conta — o coordenador vê a conta exata.
Isso responde: "a máquina só acha?" — não, o cálculo é auditável.

---

## Notas gerais

- Slug: `slugify()` remove acentos e gera kebab-case
- Filtro de imagens: ícones < 100px descartados (configurável)
- Reprocessamento: requer "reprocessar" na interface ou `--forcar`
- Log acumulativo: cada execução adiciona entrada ao `_log.json`
- Planilha de cursos: quando chegar, alimenta combo da interface e gera
  `_disciplina.yml` automaticamente com nomes e emails

---

---

## Estrutura de Arquivos do Projeto

```
piloto-extrator/
├── .claude/
│   └── agents/
│       └── analista-conteudo.md    # M02: Prompt do Agente E
├── modulo02/
│   ├── calculo.py                  # M02: Aritmética pura (índice + veredito)
│   ├── test_calculo.py             # M02: Validação dos 4 cenários
│   ├── laudo.html                  # M02: Tela visual para coordenador
│   └── test-cenarios.html          # M02: Guia de teste dos cenários
├── scripts/
│   ├── 01-processar-entrada.py     # M01: Extrator (Pandoc + PyMuPDF)
│   ├── 02-separar-aulas.py         # M01b: Separa PDF único em aulas
│   └── 03-agente-e.py              # M02: Avaliacao de qualidade
├── cursos/
│   └── {curso}/disciplinas/{CODIGO}-{slug}/aula-{NN}/
│       ├── 01_source/              # Material bruto (não editar)
│       ├── 02_markdown/            # Texto extraído
│       ├── 03_avaliacao/           # M02: avaliacao_v01.md + score_v01.json
│       ├── 04_reformulado/         # M03+M05+M08
│       ├── 05_imagens/
│       ├── 06_output/              # M07: HTML + PDF finais
│       ├── 07_revisao/             # Coordenador
│       └── _incubadora/            # Criado se veredito = RECRIAR
├── CLAUDE.md                       # Instruções do projeto
├── README.md                       # Este arquivo
├── servidor.py                     # Interface web (Flask)
└── etapa01-unigran.zip             # Material bruto de referência
```

---

*Atualizado em 2026-06-09*

---

## 📋 Resumo do Status

### ✅ Implementado

| Módulo | Funcionalidade | Arquivos |
|--------|----------------|----------|
| **M01** | Extração Word/PDF → Markdown + imagens | `01-processar-entrada.py`, `02-separar-aulas.py` |
| **M01b** | Separação automática de PDF único | `02-separar-aulas.py` |
| **M02** | Avaliação de qualidade (Agente E) | `03-agente-e.py`, `calculo.py`, `laudo.html` |

### 🔧 Interface

- Hub de entrada com catálogo de disciplinas (`interface/index.html`)
- Laudo visual com carregamento automático (`modulo02/laudo.html`)
- API REST (`servidor.py`): `/api/catalogo`, `/api/processar`, `/api/score`

### 📊 Métricas do M02

- **2 Fundamentos** (A1, A2): verificação de integridade
- **5 Indicadores** (B1–B5): qualidade didática
- **4 Vereditos**: APROVAR · APROVAR_COM_RESSALVA · INTERVENCAO · RECRIAR
- **_incubadora/**: criada automaticamente para material RECRIAR
