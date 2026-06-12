---
name: correcoes-interface-2026-06-12
description: 4 correções implementadas: A2 bibliografia, status M02, marcadores [IMG-NN], limite vídeos
metadata:
  type: project
---

## Correções Implementadas (commit `719b0df`)

### 1. A2 — Bibliografia Completa

**Problema:** Referências citadas no corpo do texto apareciam apenas com trecho entre aspas, sem a obra completa.

**Solução:** `modulo02/laudo.html` agora busca a referência completa cruzando `autor+ano` com `a2.referencias_bibliograficas` quando `obra == "Citação no corpo do texto"`.

**Código:**
```javascript
if (fonte.obra === 'Citação no corpo do texto' && a2.referencias_bibliograficas) {
  const sobrenome = (fonte.autor || '').split(' ')[0].toLowerCase();
  const refCompleta = a2.referencias_bibliograficas.find(
    r => (r.autor || r.citação || '').toLowerCase().includes(sobrenome) && r.ano === fonte.ano
  );
  if (refCompleta) {
    // Exibe: 📚 Autor — Obra (ano) · URL
  }
}
```

---

### 2. Status M02 — "PENDENTE" após M03 concluído

**Problema:** Status M02 aparecia como "PENDENTE" mesmo após avaliação concluída.

**Causa:** Código acessava `m02.score?.veredito?.rotulo`, mas `veredito` é string direta (`"APROVAR"`), não objeto.

**Solução:**
```javascript
const veredito = m02.score?.veredito || '';
if (m02.status === 'avaliada' && ['APROVAR', 'APROVAR COM RESSALVA', 'INTERVENCAO_EDITORIAL'].includes(veredito)) {
  statusM02.textContent = '✅ ' + veredito;
}
```

**Arquivo:** `interface/m03-preview.html:536-538`

---

### 3. M01 — Criar Marcadores [IMG-NN]

**Problema:** Métricas mostravam "0 imagens" porque o M01 extraía imagens como arquivos mas não criava marcadores `[IMG-NN]` no markdown.

**Solução:** Nova função `normalizar_marcadores_imagens()` em `scripts/01-processar-entrada.py`:

**Detecta e converte:**
- `**Figura 1 -** descrição` → `[IMG-01 alt="descrição"]`
- `**Figura 2:** descrição` → `[IMG-02 alt="descrição"]`
- `Figura N: descrição` (sem negrito) → `[IMG-NN alt="descrição"]`
- `![alt](media/image.png)` → `[IMG-NN alt="alt"]`

**Impacto:** Métricas de imagens agora funcionam corretamente. M03 preserva marcadores durante reescrita.

**Arquivo:** `scripts/01-processar-entrada.py:74-110`

---

### 4. SKILL.md — Limite de Vídeos

**Problema:** M03 gerava 3-6 vídeos por aula, mas usuário quer apenas 1 vídeo por aula.

**Solução:** Alterado em `skills/texto-display/SKILL.md:42`:
- **Antes:** "Sugerir de 3 a 6 por aula"
- **Depois:** "**Sugerir exatamente 1 vídeo por aula**"

**Impacto:** Novas execuções do M03 gerarão apenas `[VIDEO-01]`.

---

## Arquivos Modificados

| Arquivo | Linha(s) | Mudança |
|---------|----------|---------|
| `modulo02/laudo.html` | 1220-1260 | Busca referência completa quando obra é genérica |
| `interface/m03-preview.html` | 536-538 | Acesso correto a veredito (string) |
| `scripts/01-processar-entrada.py` | 74-110 | `normalizar_marcadores_imagens()` |
| `skills/texto-display/SKILL.md` | 42 | Limite: 1 vídeo por aula |

---

## Como Aplicar

Para materiais já processados:
1. **Imagens:** Re-executar M01 com `--forcar` para criar marcadores [IMG-NN]
2. **Vídeos:** Re-executar M03 para gerar apenas 1 vídeo
3. **A2 e Status:** Recarregar páginas — correção é automática

---

*Criado em 2026-06-12 — commit `719b0df`*
