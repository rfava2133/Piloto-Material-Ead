---
name: correcoes-tarde-2026-06-12.md
description: Correções da tarde de 2026-06-12 — A2, métricas, cache da API
metadata:
  type: project
---

## Correções Implementadas — Tarde de 2026-06-12

### Resumo dos Commits

| Commit | Descrição |
|--------|-----------|
| `6fe39bb` | fix: múltiplas correções de interface e métricas |
| `8c6609c` | fix(laudo): A2 busca bibliografia por ano ou palavra-chave |
| `7160483` | docs(memory): adiciona status-2026-06-12-tarde.md |
| `91397a2` | fix(laudo): timestamp na API para evitar cache |

---

## 1. Link UNIGRAN EAD → Home

**Arquivo:** `interface/index.html:594`

**Mudança:**
```html
<!-- Antes -->
<a href="#" class="brand">

<!-- Depois -->
<a href="/" class="brand">
```

---

## 2. Botão Aprovação do Professor

**Arquivo:** `modulo03/display.html:760`

**Adicionado:**
```html
<button class="btn btn-secondary" onclick="abrirAprovacaoProfessor()">
  📄 Aprovação do Professor
</button>
```

---

## 3. Métricas Renomeadas

**Arquivos:** `interface/m03-preview.html`, `modulo03/display.html`

**Mudanças:**
- "Imagens" → "Imagens Encontradas" / "Imagens (display)"
- "Vídeos Sugeridos" → "Vídeos Encontrados"
- "Imagens (M01)" → nova métrica mostrando quantas imagens foram extraídas pelo M01

---

## 4. Contador Imagens M01

**Arquivo:** `servidor.py:514-518`

**Adicionado na API `/api/m03-check`:**
```python
# Contar imagens extraídas pelo M01 (04_imagens/antigas/)
qtd_imagens_m01 = 0
imagens_dir = pasta_aula / "04_imagens" / "antigas"
if imagens_dir.exists():
    qtd_imagens_m01 = len([f for f in imagens_dir.iterdir() 
                           if f.is_file() and f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.webp']])

return jsonify({
    "ok": True,
    "markdown": markdown,
    "meta": meta,
    "caminho": str(display_path),
    "imagens_m01": qtd_imagens_m01,
})
```

**Display:** `modulo03/display.html:741-744, 1045-1046`
- Nova métrica "Imagens (M01)" no UI
- JS preenche com `dados.imagens_m01`

---

## 5. A2 Busca Simplificada

**Arquivo:** `modulo02/laudo.html:1231-1262`

**Problema:** Condição `fonte.obra === 'Citação no corpo do texto'` nunca era verdadeira porque o Agente E sobrescreveu `obra` com texto longo.

**Solução:** Busca por **ano** ou **palavra-chave do autor**:
```javascript
if ((fonte.autor || '').length > 50) {
  corpo = `<span style="font-style:italic; color:var(--ink-muted);">"${trunc(fonte.autor, 90)}"</span>`;
  
  if (referenciasBibliograficas.length > 0) {
    // Tentar encontrar referência completa por ano ou palavra-chave
    const anoMatch = fonte.ano && referenciasBibliograficas.find(r => r.ano === fonte.ano);
    const autorMatch = (() => {
      const palavras = fonte.autor.toLowerCase().split(' ').filter(p => p.length > 3);
      return referenciasBibliograficas.find(r =>
        palavras.some(p => (r.autor || '').toLowerCase().includes(p))
      );
    })();
    const refCompleta = anoMatch || autorMatch;

    if (refCompleta) {
      // Exibe bibliografia completa 📚 Autor — Obra (ano) · URL
    }
  }
}
```

**Commit:** `8c6609c`

---

## 6. Cache da API

**Arquivo:** `modulo02/laudo.html:1086-1092`

**Problema:** Browser cacheava resposta da API `/api/score`, mostrando dados antigos.

**Solução:** Adicionar timestamp na URL:
```javascript
async function carregarDaURL() {
  const params = new URLSearchParams(location.search);
  if (!params.get('aula') || !params.get('codigo')) return;

  try {
    // Adiciona timestamp para evitar cache
    params.set('_t', Date.now().toString());
    const res = await fetch('/api/score?' + params.toString());
    // ...
  }
}
```

**Commit:** `91397a2`

---

## Pendências

| Item | Status | Observação |
|------|--------|------------|
| Re-executar M03 | ⏳ Pendente | M03 foi executado antes da SKILL.md atualizada (gerou 6 vídeos) |
| Imagens display | ⚠️ 0 marcadores | M03 não preservou marcadores `[IMG-NN]` do original |

**Como resolver:**
```bash
python3 scripts/04-agente-a.py --codigo FUN --disciplina "Fundamentos de Administracao" --aula 1 --forcar
```

---

*Criado em 2026-06-12 13:30*
