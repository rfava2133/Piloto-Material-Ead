# Memory Index

- [Alinhamento de documentação](alinhamento-docs-2026-06.md) — Decisões de consistência entre CLAUDE.md, README.md e AGENTS.md
- [Pendências M01 — extrator/separador](projeto-pendencias-m01.md) — Sumário PDF vazando no markdown; PDF multi-aula enviado como aula única
- [Feedback UX usuário final](feedback-ux-usuario-final.md) — Zero terminal/CLI; tudo via browser guiado
- [Feedback tokens](feedback-tokens.md) — Informar estimativa de tokens ao final de cada resposta
- [M03 concluído — arquitetura e custo](projeto-m03-concluido.md) — SDK direto no servidor, ~R$1,10/aula, bugs de regex resolvidos
- [Workflow ATUALIZAR](00-atualizar-workflow.md) — Padrão: atualizar memória + git push

---

## Documentação Principal

| Arquivo | Local | Função |
|---------|-------|--------|
| **CLAUDE.md** | raiz | Instruções do projeto (lido automaticamente) |
| **AGENTS.md** | raiz | Prompt dos agentes (lido automaticamente) |
| **README.md** | `memory/` (symlink na raiz) | Visão geral, pipeline, status dos módulos |
| **HANDOFF.md** | `memory/` (symlink na raiz) | Estado da sessão para handoff |
| **MEMORY.md** | `memory/` | Este arquivo — índice de memórias |
