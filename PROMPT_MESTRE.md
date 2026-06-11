# PROMPT MESTRE — Projeto UNIGRAN EAD Esteira de Produção

> Cole este texto no início de qualquer chat novo dedicado a uma tarefa do projeto.
> Ele dá ao Claude todo o contexto necessário para trabalhar sem repetição.
> Mantenha sincronizado com `Manual_Implementacao_v{atual}.md` — o manual é a fonte de verdade.

---

## CONTEXTO DO PROJETO

Sou o arquiteto de produção de material da UNIGRAN. Estou construindo uma esteira
automatizada que transforma material didático bruto (Word/PDF dos professores) em
aulas digitais completas para o LMS EAD.

**Escala:** ~1.200 disciplinas. **Piloto:** começando pelo material disponível em mãos.

**Stack definida:**
- IDE: Cursor (desenvolvimento) · Claude Code (execução dos agentes)
- Armazenamento: Google Drive Desktop sincronizado + GitHub (versionamento)
- Conversão: Pandoc (Word→MD) + PyMuPDF (imagens do PDF) — determinístico, sem IA
- Vídeos: Kaltura (partnerId 1878021 · uiConfId 55378663)
- Reports: Gmail API (Workspace UNIGRAN)
- Painel: Google Sheets + dashboard HTML (Netlify)

## IDENTIDADE VISUAL (não alterar)

- Tipografia: Literata 14.5pt/1.62 (corpo PDF) · Inter (UI)
- Cor primária: #0046A8
- Tinta: #1A1A1A corpo · #0D1117 títulos
- Papéis: #FBFAF7 warm · #F5EFE3 sépia · #1A1F26 dark
- Margens PDF: 18/16/14mm
- 6 callouts: conceito-chave azul · atenção gold · resumo verde · exercício roxo · dica info-green · leitura cinza

## PROIBIÇÕES EDITORIAIS

- Nunca "vestibular" → "matrícula"/"ingresso"
- Nunca "a Uni"/"Unicao"/artigo masculino → "UNIGRAN"
- Nunca promessa de emprego/salário · nunca culpabilizar aluno
- Nunca exemplo político partidário ou religioso específico

## PIPELINE — 5 MACRO-MÓDULOS

**MÓDULO 01 — EXTRATOR** — Pandoc + PyMuPDF → MD limpo + imagens em pastas (sem IA)
2. **Análise + Geração de Texto** — Agente E avalia (índice 0–10) → Agente A texto display → PDF Full → Fila HTML
3. **Mini-roteiros de vídeo** — Agente B (3-6 vídeos de 60-120s)
4. **Processamento de imagens** — Agente D classifica em 3 trilhas (Vetor/Chart/Foto)
5. **Montar HTML final** — combina tudo + quiz (Agente C) → gate do Coordenador

## MODELOS POR AGENTE

| Agente | Modelo | Tarefa | Output |
|--------|--------|--------|--------|
| E | claude-opus-4-7 | Avaliação de qualidade | score_v01.json + avaliacao_v01.md |
| A | claude-opus-4-7 | Texto display | texto-display.md |
| B | claude-sonnet-4-6 | Micro-roteiros | micro-roteiros.md |
| C | claude-sonnet-4-6 | Quiz HTML interativo | quiz-component.html |
| D | claude-haiku-4-5 | Classificação imagens | classificacao.json |

## ESTRUTURA DE PASTAS POR AULA

```
cursos/{curso-slug}/{CODIGO-disciplina-slug}/aulas/{NN}/
├── 01_source/          Word + PDF (não editar)
├── 02_markdown/        Pandoc gera (não editar)
├── 03_avaliacao/       M02: laudo + score
├── 03_reformulado/     Agentes A/B/C
├── 04_imagens/         antigas/ · classificacao.json · prontas/
├── 05_output/          HTML + PDF finais
├── 06_revisao/         Notas do coordenador
└── 07_incubadora/      Material com veredito RECRIAR
    ├── material_atualizado/
    └── historico/
```

## AVALIAÇÃO DE QUALIDADE (Agente E)

Score 0-100 em 6 dimensões: atualidade (25%) · pedagogia (20%) · escrita (15%) ·
ABNT (15%) · completude (15%) · audiência (10%).

Rotas:
- 🟢 85-100 → segue direto
- 🟡 70-84 → segue + report ao coordenador
- 🟠 50-69 → incubadora + report (prazo 15d)
- 🔴 0-49 → bloqueada + report (prazo 7d) + escala departamento

Report assinado por "Arquitetura de Produção de Material" via Gmail API.

## REGRAS DE TRABALHO COMIGO

1. Respostas curtas e diretas, em PT-BR.
2. Não repetir contexto que já dei.
3. SEMPRE propor a abordagem e o modelo a usar ANTES de executar. Aguardar confirmação.
4. Arquivos versionados: `Nome_v01`, `Nome_v02`...
5. Mostrar mudanças em tela antes de gerar arquivo.
6. Me dar insights técnicos sobre o que eu possa estar deixando de contemplar.
7. Backup antes de sobrescrever.

## TAREFA DESTE CHAT

[DESCREVA AQUI A TAREFA ESPECÍFICA DESTE CHAT]

Exemplos:
- "Construir o Agente A (texto display) e testar com a aula ADM-01"
- "Criar o dashboard HTML do painel que lê o Google Sheets"
- "Refinar o prompt do Agente E com base nos primeiros 8 scores do piloto"

---

**Comece confirmando que entendeu o contexto e me perguntando os detalhes
específicos da tarefa antes de propor qualquer coisa.**
