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

## PIPELINE — 5 MACRO-MÓDULOS

**MÓDULO 01 — EXTRATOR**
   - Pandoc: Word → Markdown limpo (+ extrai imagens do Word)
   - PyMuPDF: extrai imagens do PDF
   - Cria estrutura de pastas da aula
   - 100% determinístico, sem IA

2. ANÁLISE + GERAÇÃO DE TEXTO
   - 2a Agente E (Opus 4.7): avalia qualidade → score 0-100
   - 2b Report: BOM segue · RUIM dispara coordenador
   - 2c Agente A (Opus 4.7): texto display
   - 2d PDF Full (Puppeteer): do texto original
   - 2e Fila HTML: aguarda imagens + vídeos

3. MINI-ROTEIROS DE VÍDEO
   - Agente B (Sonnet 4.6): roteiros 60-120s

4. PROCESSAMENTO DE IMAGENS
   - Agente D (Haiku 4.5): classifica em 3 trilhas
   - Vetor (Mermaid) · Chart (Chart.js) · Foto (Gemini)

5. MONTAR HTML FINAL
   - Combina texto + imagens + vídeos + quiz (Agente C, Sonnet 4.6)
   - Gate de aprovação: Coordenador

## MODELOS POR AGENTE

| Agente | Modelo | Tarefa |
|--------|--------|--------|
| E | Codex-opus-4-7 | Avaliação de qualidade |
| A | Codex-opus-4-7 | Texto display |
| B | Codex-sonnet-4-6 | Micro-roteiros |
| C | Codex-sonnet-4-6 | Quiz HTML interativo |
| D | Codex-haiku-4-5 | Classificação de imagens |

Módulo 01 (Extrator), PDF Full e montagem HTML: scripts determinísticos, sem IA.

## ESTRUTURA DE PASTAS POR AULA

```
disciplinas/{CODIGO}-{slug}/aula-{NN}/
├── 01_source/          INPUT (Word + PDF) — não editar
├── 02_markdown/        Pandoc gera — não editar
├── 03_reformulado/     Agentes A/B/C escrevem
├── 04_imagens/         Agente D + redesenho
│   ├── antigas/        Extraídas automaticamente
│   ├── classificacao.json
│   └── prontas/        Redesenhadas
├── 05_output/          HTML + PDF finais
├── 06_revisao/         Notas do coordenador
└── 07_incubadora/      Material com score < 70
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
