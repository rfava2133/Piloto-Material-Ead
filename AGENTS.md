# AGENTS.md — UNIGRAN EAD Esteira de Produção

> Este arquivo é lido automaticamente pelo Codex ao abrir o projeto.
> É a instrução-mãe. Tudo aqui prevalece, exceto `/docs/voz-unigran.md` em
> questões de tom e voz editorial.
Leia também o `README.md` para o status atual de implementação de cada módulo.

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
- Nunca "a Uni", "Unicao", artigo masculino → sempre "UNIGRAN"
- Nunca promessa de empregabilidade ou salário garantido
- Nunca culpabilizar o aluno
- Nunca exemplos políticos partidários ou religiosos específicos

## PIPELINE — MÓDULOS

| Módulo | Agente | Modelo | Tarefa |
|--------|--------|--------|--------|
| **M01 — Extrator** | — | determinístico | Pandoc + PyMuPDF → Markdown + imagens |
| **M02 — Analista de Conteúdo** | Agente E | Codex-opus-4-7 | Avaliação de qualidade → índice 0–10 |
| **M03 — Texto Display** | Agente A | claude-sonnet-4-6 | Texto reformulado |
| **M04 — PDF Full** | — | Puppeteer | PDF do texto original |
| **M05 — Micro-roteiros** | Agente B | Codex-sonnet-4-6 | Roteiros de vídeo 60–120s |
| **M06 — Imagens** | Agente D | Codex-haiku-4-5 | Classificação em 3 trilhas |
| **M07 — Quiz** | Agente C | Codex-sonnet-4-6 | Quiz HTML interativo |
| **M08 — Montagem HTML** | Agente C | Codex-sonnet-4-6 | Combina texto + imagens + vídeos + quiz |

- **M01:** 100% determinístico, sem IA
- **M02:** Agente E avalia; índice e veredito são aritmética pura via `modulo02/calculo.py`
- **M02 veredito APROVAR:** segue para M03
- **M02 veredito RECRIAR:** material vai para `07_incubadora/`, coordenador decide
- **M08:** gate de aprovação pelo coordenador antes de publicar

## MÓDULOS DETERMINÍSTICOS (SEM IA)

M01 (Extrator), M04 (PDF Full) e M08 (montagem HTML): scripts determinísticos.

## ESTRUTURA DE PASTAS POR AULA

```
cursos/{curso-slug}/{CODIGO-disciplina-slug}/aulas/{NN}/
├── 01_source/          INPUT (Word + PDF) — não editar
├── 02_markdown/        Pandoc gera — não editar
├── 03_avaliacao/       M02: laudo + score (criada na avaliação)
├── 03_reformulado/     Agentes A/B/C escrevem
├── 04_imagens/         Agente D + redesenho
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

- Código disciplina: 3 letras maiúsculas (ADM, PED, ENF)
- Pasta disciplina: {CODIGO}-{slug-kebab}
- ID aula: {CODIGO}-{NN}
- Arquivos versionados: Nome_v{NN}

## COMANDOS DISPONÍVEIS

- `/processar-aula {ID}` — pipeline completo de 1 aula
- `/batch-disciplina {CODIGO}` — todas as aulas de uma disciplina

## ESTADOS DO PAINEL

Não iniciado · Aguardando · Em revisão · Pronto