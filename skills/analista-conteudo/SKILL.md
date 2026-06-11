---
name: analista-conteudo
description: Avalia material textual de aula EAD da UNIGRAN EAD antes da diagramação — atribui Verificação de Fundamentos (precisão conceitual e bibliográfica), pontua cinco Indicadores de Qualidade Didática com pesos, valida fontes externamente e emite um veredito recomendado. Use SEMPRE que o pedido envolver avaliar, analisar, revisar ou diagnosticar a qualidade pedagógica de um texto de aula, material didático ou conteúdo de professor — mesmo que o usuário não diga "Módulo 02" ou "analista" explicitamente. Dispara para frases como "avalia essa aula", "esse material está bom?", "analisa o conteúdo do professor", "verifica esse texto antes de diagramar", "roda o avaliador nessa disciplina". Não use para gerar quiz/atividades (módulo separado) nem para diagramar/formatar (a skill diagnostica substância, não corrige forma).
---

# Analista de Conteúdo — Módulo 02 (UNIGRAN EAD)

Analisa o texto de uma aula EAD **antes** da esteira de diagramação: atribui score por
critérios, valida a precisão consultando fontes externas, e emite um veredito **recomendado**.
**Não reescreve** o material — diagnostica.

Princípio central: a diagramação corrige **forma** (legibilidade, ortografia, layout); esta
análise julga **substância** (precisão, estrutura, qualidade das fontes). Um material pode ser
bonito e estar errado — o trabalho desta skill é pegar o errado.

A decisão final é sempre do aprovador humano. A skill recomenda; não condena de forma autônoma.

## Modelo

Use Opus para a análise — é diagnóstico de substância, não tarefa mecânica.

## Fluxo

### 1. Pré-voo (inventário antes de analisar)

Liste o que foi recebido e o efeito de cada ausência:
- Texto da aula: [recebido / ausente → se ausente, pare e solicite]
- Referência das imagens mapeadas: [recebida / ausente → B5 avalia só a descrição textual existente]
- Referência das chamadas de vídeo: [recebida / ausente → B1 não penaliza falta de chamada de vídeo]

Não invente insumos que não chegaram. Receba o material por caminho de arquivo (`.docx`,
`.pdf`, `.md`), nunca assuma conteúdo que não foi fornecido.

### 2. Verificação de Fundamentos (não-binária)

Cada fundamento recebe um nível: **SEM RESSALVA / RESSALVA / CRÍTICO**.
- **SEM RESSALVA** — nada a apontar.
- **RESSALVA** — achado corrigível sem recriar (ex.: citação órfã de obra real; imprecisão
  menor como ano faltante). Não condena; entra como intervenção de prioridade alta.
- **CRÍTICO** — erro de substância (ex.: referência inventada, atribuição de autoria errada,
  definição cientificamente incorreta). A skill **recomenda** recriar — a decisão é do aprovador.

**A1 — Precisão Conceitual e Científica:** conceitos, definições, teorias e autorias corretos?
Verificar contra fontes acadêmicas. CRÍTICO quando há erro factual relevante (ex.: atribuir a
Maslow uma teoria de Herzberg; data errada de obra seminal). RESSALVA quando a imprecisão é
menor e corrigível sem mudar a substância.

**A2 — Validade Bibliográfica e Fontes:** as obras citadas existem e sustentam o que o texto
afirma? A citação no corpo corresponde a uma entrada na lista? As fontes são adequadas ao
ensino superior? CRÍTICO quando há referência inventada ou base majoritariamente não-acadêmica.
RESSALVA quando há citação órfã de obra real ou dado bibliográfico incompleto.
> Guardrail anti-falso-positivo: para marcar "confirma", corrobore **autor + ano + editora** —
> um trecho de busca semelhante pode ser obra diferente. Referência não encontrada → registre
> **"não localizado"** (não conclua que é falsa nem que é válida).

**Flag advisória (não é fundamento):** sinalize terminologia institucional para o diagramador
ajustar, sem rebaixar o veredito. Ex.: "vestibular" → deve ser "matrícula"; usar "UNIGRAN EAD"
corretamente. É aviso de forma, não erro de substância.

### 3. Indicadores de Qualidade Didática (média ponderada 0–10)

Âncoras de calibração (valem para todos):
- **0–3 deficiente** — ausente ou prejudica o aprendizado.
- **4–6 funcional com lacunas** — presente, mas inconsistente; exige intervenção.
- **7–8 sólido** — cumpre bem; ajuste cosmético ou pontual.
- **9–10 exemplar** — referência, sem reparos.

| # | Indicador | Peso | Puxa ↓ / ↑ |
|---|---|---|---|
| B1 | Dialogicidade / tom EAD | 20% | ↓ despejo enciclopédico, sem voz do professor. ↑ perguntas retóricas, cotidiano, indica pausa para vídeo. |
| B2 | Densidade conceitual | 15% | ↓ teorias empilhadas sem respiro; repete o vídeo. ↑ ritmo digerível, compatível com tela. |
| B3 | Estrutura pedagógica | 30% | ↓ sem objetivos, sem síntese, seções soltas. ↑ progressão lógica, fechamento, assertivas verificáveis e gradação de complexidade que dão base para avaliação. |
| B4 | Engajamento | 15% | ↓ abstrato, sem exemplo. ↑ casos, analogias, conexão com a prática profissional. |
| B5 | Legibilidade autoral | 20% | ↓ títulos sem hierarquia, "veja a figura" sem descrição. ↑ parágrafos ≤6 linhas, H1/H2/H3 claros, figuras descritas. Typo puro NÃO pontua aqui — vira nota de rodapé. |

Cálculo (mostre a conta no laudo):
```
Índice = (B1×0.20)+(B2×0.15)+(B3×0.30)+(B4×0.15)+(B5×0.20)
Ex.: (6×.20)+(7×.15)+(7×.30)+(7×.15)+(8×.20) = 1.20+1.05+2.10+1.05+1.60 = 7.0
```
**NUNCA calcule índice ou veredito manualmente.** Você atribui as notas; a conta é do código:
```python
import sys; sys.path.insert(0, "modulo02")
from calculo import avaliar
resultado = avaliar({"B1": 6.0, "B2": 7.0, "B3": 7.0, "B4": 7.0, "B5": 8.0},
                    a1="SEM_RESSALVA", a2="SEM_RESSALVA")
# resultado["indice"]["indice"] → índice (2 casas) · resultado["veredito"]["faixa"] → veredito
```
Reproduza a conta retornada no laudo (transparência), mas o número e a faixa que valem são
os do `calculo.py` — arredondamento de 2 casas, regra das 4 faixas e override CRÍTICO inclusos.

### 4. Validação por fontes (obrigatória)

Antes de pontuar A1/A2, **busque ativamente** (Scholar, SciELO, repositórios, editoras).
Verifique: autoria de teorias; existência/dados das referências-chave; precisão factual de
afirmações centrais; alinhamento com consenso atual. Toda atribuição de autoria e toda
referência-chave recebem ao menos uma checagem, registrada no laudo com paráfrase curta
(nunca cópia longa) e fonte.

Sem acesso a busca: declare offline, marque A1/A2 como "não validado externamente — requer
verificação manual", reduza a confiança.

### 5. Veredito recomendado

A skill recomenda; **a decisão final é do aprovador humano**.
```
Algum fundamento CRÍTICO (A1 ou A2)?
├─ SIM → RECOMENDA 🔴 RECRIAR (aprovador confirma ou contesta)
└─ NÃO → veredito pelo Índice:
         ≥ 8.0       → 🟢 APROVAR (diagramação direta)
         6.5 – <8.0  → 🟡 APROVAR COM RESSALVA (camada editorial)
         5.0 – <6.5  → 🟠 INTERVENÇÃO EDITORIAL (decisão do aprovador)
         < 5.0       → 🔴 RECRIAR (base pedagógica fraca)
```
Achados em nível RESSALVA não rebaixam o veredito: entram como intervenção de prioridade alta.

## Saída (laudo)

A skill deve produzir **duas saídas**:

### 1. Laudo markdown (leitura humana)

```markdown
# Laudo — [Disciplina] · Aula [N]
Analista: Claude (Opus) | Data: [data] | Material: [arquivo]

## Veredito recomendado: [🟢/🟡/🟠/🔴]   Índice: [X.X]/10
> Recomendação da skill. Decisão final do aprovador.

## Pré-voo
[o que chegou / o que falta e efeito]

## Verificação de Fundamentos
- A1 Precisão conceitual: [SEM RESSALVA / RESSALVA / CRÍTICO] — [justificativa]
- A2 Validade bibliográfica: [SEM RESSALVA / RESSALVA / CRÍTICO] — [justificativa]
- Flag terminologia: [nenhuma / lista de ocorrências para o diagramador]

## Validação por fontes
| Item checado | O que a fonte diz | Confirma / Contradiz / Não localizado | Fonte |
|---|---|---|---|

## Indicadores de Qualidade Didática
| Indicador | Nota | Peso | Observação |
|---|---|---|---|
| B1 Dialogicidade | X/10 | 20% | ... |
| B2 Densidade conceitual | X/10 | 15% | ... |
| B3 Estrutura pedagógica | X/10 | 30% | ... |
| B4 Engajamento | X/10 | 15% | ... |
| B5 Legibilidade autoral | X/10 | 20% | ... |
| **Índice de Qualidade Didática** | **X.X** | 100% | [conta explícita] |

## Intervenções recomendadas
[priorizada — Alta / Média / Baixa; distinguir MANTÉM (base) de ADICIONA (camada nova)]

## Erros de substância (se houver fundamento CRÍTICO)
[lista específica, cada erro com a correção correta e a fonte que a sustenta]
```

### 2. JSON estruturado (leitura automática — OBRIGATÓRIO)

**IMPORTANTE:** O JSON deve ser gravado diretamente em `{pasta_da_aula}/03_avaliacao/score_vNN.json`.

Use a função `proxima_versao()` para determinar a versão (v01, v02, ...). Nunca sobrescreva.

```json
{
  "aula_id": "PSU-01",
  "fundamentos": {
    "A1": {"severidade": "SEM_RESSALVA", "justificativa": "..."},
    "A2": {"severidade": "SEM_RESSALVA", "justificativa": "...",
           "fontes_verificadas": [
             {"obra": "...", "autor": "...", "ano": "...", "status": "confirmada|nao_localizada"}
           ]}
  },
  "indicadores": {
    "B1": {"nota": 7.0, "peso": 0.20, "contribuicao": 1.40, "justificativa": "..."},
    "B2": {"nota": 6.5, "peso": 0.15, "contribuicao": 0.97, "justificativa": "..."},
    "B3": {"nota": 7.5, "peso": 0.30, "contribuicao": 2.25, "justificativa": "..."},
    "B4": {"nota": 6.0, "peso": 0.15, "contribuicao": 0.90, "justificativa": "..."},
    "B5": {"nota": 8.0, "peso": 0.20, "contribuicao": 1.60, "justificativa": "..."}
  }
}
```

**Schema obrigatório:**
- `aula_id`: string (ex: "ADM-01")
- `fundamentos.A1.severidade`: "SEM_RESSALVA" | "RESSALVA" | "CRITICO"
- `fundamentos.A1.justificativa`: string
- `fundamentos.A2.severidade`: "SEM_RESSALVA" | "RESSALVA" | "CRITICO"
- `fundamentos.A2.justificativa`: string
- `fundamentos.A2.fontes_verificadas`: array (pode ser vazio)
- `indicadores.B1–B5.nota`: número entre 0 e 10
- `indicadores.B1–B5.peso`: número (0.20, 0.15, 0.30, 0.15, 0.20)
- `indicadores.B1–B5.contribuicao`: número (nota × peso)
- `indicadores.B1–B5.justificativa`: string

**NÃO inclua** `indice` ou `veredito` no JSON — o `calculo.py` calcula deterministicamente.

**Rodapé machine-readable (legado, opcional):**
```
VEREDITO=[VERDE|AMARELO|LARANJA|VERMELHO] INDICE=[X.X] A1=[SR|R|C] A2=[SR|R|C] PROXIMA_ACAO=[diagramar|camada_editorial|decisao_aprovador|recriar] DECISAO=HUMANA
```

## Conduta

- Não invente verificações. Se não buscou, marque como não validado.
- Distinga forma (B5 / typo) de substância (fundamentos).
- Seja específico: "a Seção 3 traz 5 escolas e 12 autores em fila sem exemplo" ajuda; rótulos
  vagos não.
- Cite as fontes; paráfrase curta, nunca cópia longa.
- Não rebaixe por estilo do professor; avalie eficácia pedagógica, não preferência estética.
- Sinalize incerteza explicitamente. Referência não localizável → "não localizei".
- O Índice serve à decisão, não ao ranking.
- Não avalie vídeo, quiz ou imagem em si — só verifique se o texto os integra.
- Reprodutível: mesma entrada → mesmo veredito. Mostre a conta.
- A skill recomenda; o aprovador decide. Nada escala sem o aval humano.

## Referência teórica dos critérios

Os critérios têm lastro verificado. Use estas atribuições ao justificar a análise:
- B1 Dialogicidade — Moore, Teoria da Distância Transacional (1993); Freire, Pedagogia do Oprimido (1968).
- B2 Densidade — Sweller, Cognitive Load Theory (Cognitive Science v.12, 1988).
- B3 Estrutura — Gagné, The Conditions of Learning (1965); Biggs, Constructive Alignment (Higher Education v.32, 1996); Anderson & Krathwohl, revisão da Taxonomia de Bloom (2001).
- B4 Engajamento — Knowles, andragogia; Lave & Wenger, aprendizagem situada (1991).
- B5 Legibilidade — Mayer, Teoria Cognitiva da Aprendizagem Multimídia (2001).

Atenção à precisão: a sequência cognitiva lembrar→entender→aplicar→analisar→avaliar→criar é da
revisão de Anderson & Krathwohl (2001), NÃO do Bloom original de 1956. Os pesos são decisão
institucional da UNIGRAN EAD, não derivados de estudo empírico.
