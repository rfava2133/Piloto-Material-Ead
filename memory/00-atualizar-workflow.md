---
name: atualizar-workflow
description: Workflow padrão quando usuário pede ATUALIZAR
metadata:
  type: feedback
---

## Quando o usuário pede "ATUALIZAR"

Sempre que o usuário usar o comando **ATUALIZAR**, executar:

### 1. Atualizar arquivos de memória/contexto
- `memory/README.md` — visão geral e status dos módulos
- `memory/HANDOFF.md` — estado atual da sessão
- `memory/MEMORY.md` — índice de memórias (se necessário)
- `CLAUDE.md` — instruções do projeto (se houver mudanças estruturais)
- `AGENTS.md` — prompt dos agentes (se houver mudanças estruturais)

### 2. Commit e push para o git
```bash
git add -A
git commit -m "docs(memory): atualização dos arquivos de contexto e memória"
git push
```

### Princípios
- Manter consistência entre todos os arquivos de documentação
- Symlinks na raiz (`README.md`, `HANDOFF.md`) apontam para `memory/`
- `CLAUDE.md` e `AGENTS.md` permanecem na raiz (lidos automaticamente)
- Commit messages seguem padrão: `docs(memory): <descrição>`

**Por que:** Centralizar documentação em `/memory/` facilita manutenção e handoff entre sessões.
