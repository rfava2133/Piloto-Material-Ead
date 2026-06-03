# Instruções de Chat — Como organizar o trabalho com IA

> Como estruturar os chats do projeto para não perder contexto nem desperdiçar tokens.

## Arquitetura de 2 níveis

```
┌─────────────────────────────────────────────┐
│  CHAT NÚCLEO (este, o atual)                │
│  • Decisões arquiteturais                   │
│  • Aprovações de mudança de rota            │
│  • Evolução dos manuais (v01 → v02 → ...)   │
│  • Memória persistente do projeto           │
│  NÃO usar para execução repetitiva          │
└─────────────────────────────────────────────┘
                    │ gera
                    ▼
┌─────────────────────────────────────────────┐
│  CHATS FILHOS (um por tarefa)               │
│  • Construir um agente específico           │
│  • Testar uma aula                          │
│  • Criar o dashboard                        │
│  • Refinar um prompt                        │
│  Cada um recebe o PROMPT_MESTRE.md no topo  │
└─────────────────────────────────────────────┘
```

## Quando usar cada um

| Situação | Onde |
|---|---|
| Decidir nova etapa do pipeline | Núcleo |
| Mudar modelo de um agente | Núcleo |
| Atualizar manual | Núcleo |
| Construir/testar 1 agente | Chat filho |
| Processar 1 aula | Chat filho |
| Criar uma tela/script isolado | Chat filho |
| Debugar um problema pontual | Chat filho |

## Como abrir um chat filho

1. Copie todo o conteúdo de `docs/PROMPT_MESTRE.md`
2. Cole no início do chat novo
3. Preencha a seção "TAREFA DESTE CHAT"
4. Anexe o manual atual se a tarefa for complexa
5. Trabalhe focado naquela tarefa

## Disciplina de sincronização

- O `Manual_Implementacao_v{atual}.md` é a FONTE DE VERDADE.
- Toda decisão importante volta ao núcleo e vira nova versão do manual.
- O `PROMPT_MESTRE.md` deve refletir sempre o manual mais recente.
- Quando o manual muda de versão, atualize o PROMPT_MESTRE.

## Modelo recomendado por tipo de chat

| Chat | Modelo recomendado | Por quê |
|---|---|---|
| Núcleo (decisões) | Opus 4.7 | Julgamento arquitetural crítico |
| Construir agente texto | Opus 4.7 | Qualidade da reescrita não-negociável |
| Construir agente quiz/roteiro | Sonnet 4.6 | Geração estruturada, bom custo |
| Scripts/automação | Sonnet 4.6 | Suficiente para código |
| Dashboard/HTML | Sonnet 4.6 | Suficiente para frontend |
| Classificação simples | Haiku 4.5 | Tarefa leve |

## O que mantém o contexto vivo

1. **Memórias do Claude** (este chat núcleo) — acumulam automaticamente
2. **PROMPT_MESTRE.md** — contexto portátil para qualquer chat
3. **Manual_Implementacao** — documentação completa e versionada
4. **CLAUDE.md** — instrução que o Claude Code lê no projeto
5. **.cursorrules** — regras que o Cursor lê

Esses 5 artefatos juntos garantem que nenhum chat comece do zero.
