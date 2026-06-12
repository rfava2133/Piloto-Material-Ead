# HANDOFF — Estado da Sessão de Trabalho

> Atualizar ao final de cada sessão ou quando tokens começarem a escassear.
> Permite que outro agente (ou próxima sessão) retome sem reler o histórico do chat.

---

## Sessão atual

**Data:** 2026-06-11
**Branch:** `main` (tudo commitado)
**Último commit:** `2aa0ee9` — fix(M03): substituir confirm() por painel inline com botão copiar

---

## O que foi feito nesta sessão

### 1. Fix crítico — laudo.html nunca renderizava o relatório
- `modulo02/laudo.html`: `dados.status === 'ok'` → `'avaliada'`; fallback `aula_id` corrigido

### 2. Conversa Inicial como seção separável (aula 00)
- `scripts/02-separar-aulas.py`: detecta "Conversa Inicial" como aula `0` → pasta `aulas/00/`, id `FUN-00`
- `interface/index.html`: opção `Conversa Inicial` no combo de aulas; "Todas (CI + 01-08)"

### 3. Interface — modo de testes e indicador de IA
- Botões "⚡ Preencher para Testes" e "🧹 LIMPAR TESTES" na topbar
- Indicador de status da IA (verde/amarelo/vermelho) via `/api/ia-status`
- Rota `/api/teste-pdf` serve `testes/adm_fund_aula01.pdf`

### 4. Reprocessamento do material de teste com `--forcar`
- `fun_aula01.md` refeito: CI em p.6, Aula 01 em p.7–23 (31.018 chars, 7 imgs)

### 5. Fix M03 — botão "Criar Texto Display" não aparecia
- `m03-preview.html`: `actionBar` nunca era exibida — faltava `style.display = 'flex'` após M01 ok
- Com M02 pendente: botão âmbar com aviso; com M02 ok: botão azul

### 6. Fix M03 — UX do fluxo de execução
- Substituído `confirm()` do browser por painel inline com comando + botão Copiar
- **⚠️ AINDA INADEQUADO** — ver pendência crítica P1 abaixo

---

## Pendências críticas (próxima sessão obrigatória)

### 🔴 P1 — M03 exige terminal: INACEITÁVEL para usuário final
**Problema:** O fluxo atual de M03 gera um arquivo `_prompt_m03.txt` e pede ao usuário para rodar `claude /texto-display "..."` no terminal. Isso é impossível para o público-alvo (coordenadores pedagógicos sem conhecimento técnico).

**Causa raiz:** O `scripts/04-agente-a.py` foi projetado para rodar via skill do Claude Code, não via API direta. O `/api/m03-executar` no servidor apenas gera o prompt e devolve instruções.

**Solução necessária:** Reescrever `/api/m03-executar` para chamar a API Anthropic diretamente (SDK Python `anthropic`) com o mesmo prompt que está em `skills/texto-display/SKILL.md`. O servidor executa o Agente A internamente e grava `texto-display.md` + `display_meta.json` sem precisar de terminal.

**Arquivos-chave:**
- `servidor.py` → rota `/api/m03-executar` (linhas ~561–600)
- `scripts/04-agente-a.py` → lógica do Agente A (tem o prompt e fluxo completo)
- `skills/texto-display/SKILL.md` → rubrica do Agente A
- `.claude/agents/texto-display.md` → prompt do Agente A (Sonnet 4.6)

**Como fazer:**
```python
import anthropic
client = anthropic.Anthropic()
# Ler markdown da aula
# Montar prompt com rubrica de skills/texto-display/SKILL.md
# Chamar client.messages.create(model="claude-sonnet-4-6", ...)
# Gravar 03_reformulado/texto-display.md + display_meta.json
# Retornar {"ok": True, "markdown": "..."}
```

O frontend (`m03-preview.html`) já está pronto para receber o resultado direto — basta o servidor retornar `{"ok": True, "markdown": "..."}` e o painel de instrução de terminal some automaticamente.

---

## Pendências conhecidas (não críticas)

### P2 — Sumário do PDF vaza no markdown
O intervalo de páginas pode incluir a página de sumário no início da Aula 01. O markdown começa com o final do texto da Conversa Inicial antes do `**AULA 1**`. Para resolver: excluir explicitamente as páginas de sumário do intervalo de qualquer aula em `02-separar-aulas.py`.

### P3 — PDF multi-aula enviado como aula individual não é detectado
Quando o usuário sobe o livro inteiro selecionando "Aula 1" (não "Todas"), o extrator não avisa nem separa. Para resolver: detectar PDF multi-aula no fluxo individual e redirecionar para o separador.

---

## Próximos passos sugeridos (em ordem)

1. **🔴 CRÍTICO:** Implementar M03 sem terminal — chamar Anthropic SDK diretamente em `servidor.py`
2. Testar fluxo completo end-to-end: upload → M01 → M02 → M03 tudo na tela
3. Resolver P2 (sumário vazando no markdown)
4. M04–M08: ainda pendentes

---

## Contexto crítico para o próximo agente

- **Servidor rodando em `:5050`** — `python3 servidor.py` (porta 5000 ocupada pelo AirPlay do macOS)
- **Código gerado automaticamente** pelo front-end: `gerarCodigo(disciplina)` = primeiras 3 letras sem acento. "Fundamentos de Administração" → `FUN` (não `ADM`)
- **Score existe** em `cursos/administracao/FUN-fundamentos-de-administracao/aulas/01/03_avaliacao/score_v01.json` — gerado por análise heurística (fallback), não pelo Agente E completo
- **PDF de testes:** `testes/adm_fund_aula01.pdf` — apostila UNIGRAN com CI (p.6) + Aula 01 (p.7–23)
- **M02 laudo** funciona — acessível via `/modulo02/laudo.html?curso=Administração&codigo=FUN&disciplina=Fundamentos+de+Administração&aula=1`
- **M03 preview** acessível via `/m03-preview?curso=Administração&codigo=FUN&disciplina=Fundamentos+de+Administração&aula=1`
- **Usuário-alvo:** coordenadores pedagógicos sem conhecimento técnico — ZERO tolerância a terminal, CLI ou comandos manuais
- **Modelo M03:** `claude-sonnet-4-6` (Agente A)
- **Chave API:** usar `ANTHROPIC_API_KEY` do ambiente (já configurada no servidor)
