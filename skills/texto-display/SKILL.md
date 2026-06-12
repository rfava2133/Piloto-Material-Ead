# SKILL — Texto Display (Agente A)

## Modelo
`claude-sonnet-4-6`

## Ativação
Ativada ao pedir "reescreve para display" ou "M03 texto display".

## Documentos obrigatórios (ler antes de gerar)
1. `docs/voz-unigran.md` — tom, estrutura, proibições, callouts, acessibilidade
2. `02_markdown/{ID}.md` — texto original aprovado pelo M02

## Regras de reescrita

### Estrutura obrigatória por aula
1. **Abertura:** pergunta-gancho + caso real (3–5 linhas)
2. **Tópicos com H2 humano** ("Como o mercado define preços")
   — NUNCA H2 burocrático ("3.2 Mecanismos de Precificação")
3. **Cada tópico:** explica → exemplifica → aplica → checa
4. **Fechamento:** síntese em 5 bullets + ponte para próxima aula

### Parágrafos
- 3–5 linhas máximo (leitura em tela)
- Frases: 15–20 palavras em média

### Callouts — usar com critério (máximo 2 por tópico)
- `:::conceito-chave` — definição central do bloco
- `:::atencao` — erro comum ou armadilha
- `:::resumo` — consolidação ao final de cada tópico
- `:::exercicio` — aplicação prática
- `:::dica` — mnemônica ou atalho mental
- `:::leitura` — aprofundamento opcional

### Marcadores de imagem
- `[IMG-01]`, `[IMG-02]`, etc.
- Formato descritivo: `[IMG-01 alt="Gráfico mostrando crescimento de vendas"]`
- **NUNCA remover marcadores do original**

### Marcadores de vídeo (M03 SUGERE posição)
- `[VIDEO-01]` — após o H2 onde o conceito mais se beneficia de explicação audiovisual
- Critério: prefira posições após conceito abstrato ou processo sequencial
- **Sugerir exatamente 1 vídeo por aula**

### Glossário
- 5–8 termos técnicos ao final
- Formato: `**Termo:** definição em linguagem cotidiana`
- Anotar no `display_meta.json` os termos para o template renderizar como balões laterais

### Citações
- Preservar **INTACTAS** — o M02 já validou, o M03 não toca

### Diversidade de exemplos
- Variar setores: comércio, indústria, serviço, agronegócio, saúde, educação, tecnologia
- Variar regiões implicitamente (voz-unigran.md seção 5)
- Nunca exemplos exclusivos de grandes capitais

### Volume
- **NUNCA reduzir abaixo de 80% do original** — reescrever, não resumir

### Tom
- 2ª pessoa: "você vai aprender", "veja como"
- Voz ativa, presente do indicativo
- Conceito em linguagem cotidiana primeiro, termo técnico entre parênteses

### Proibições absolutas (da voz-unigran.md)
- Sem "vestibular" → "matrícula" ou "ingresso"
- Sem "a Uni" → "UNIGRAN"
- Sem promessas de emprego ou salário
- Sem culpabilizar o aluno
- Sem exemplos políticos partidários ou religiosos

## Output obrigatório: display_meta.json

```json
{
  "aula_id": "ADM-01",
  "volume_original": 3200,
  "volume_display": 2700,
  "proporcao_pct": 84,
  "marcadores_img": ["IMG-01", "IMG-02"],
  "marcadores_video": ["VIDEO-01", "VIDEO-02", "VIDEO-03"],
  "callouts": {
    "conceito-chave": 3,
    "atencao": 1,
    "resumo": 4,
    "exercicio": 2,
    "dica": 1,
    "leitura": 1
  },
  "glossario_termos": ["Administração", "Planejamento", "Controle"],
  "bloom_niveis_cobertos": ["Lembrar", "Entender", "Aplicar"]
}
```

## Checklist de verificação antes de entregar
- [ ] Volume ≥ 80% do original
- [ ] Todos os `[IMG-NN]` do original preservados
- [ ] Seção "Glossário" presente no final
- [ ] Abertura com pergunta-gancho + caso real
- [ ] Fechamento com síntese em bullets
- [ ] Nenhuma palavra proibida ("vestibular", "a Uni", "Unicão", "estaremos")
- [ ] Citações do original preservadas intactas
- [ ] Callouts usados com critério (máx 2 por tópico)
- [ ] 3–6 marcadores `[VIDEO-NN]` sugeridos
