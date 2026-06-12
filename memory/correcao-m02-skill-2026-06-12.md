---
name: correcao-m02-skill-2026-06-12
description: Reversão do M02 para usar skill /analista-conteudo (não API direta)
metadata:
  type: feedback
---

## Problema
A versão anterior foi alterada para usar API Anthropic direta, mas o M02 foi projetado para usar a **skill `/analista-conteudo`** via Claude Code CLI.

Além disso:
- M03 estava sugerindo 6 vídeos em vez de **1 por aula**
- Imagens extraídas pelo M01 não estavam sendo computadas no display

## Correções

### 1. M02 — Reverter para skill
**Arquivo:** `scripts/03-agente-e.py`

**Mudança:** Revertido para commit `719b0df` que usa:
```python
result = subprocess.run(
    ["claude", "/analista-conteudo", str(texto_file)],
    capture_output=True, text=True, timeout=300,
    cwd=str(Path(__file__).parent.parent)
)
```

**Não usa API direta** — a skill é acionada via Claude Code CLI.

### 2. M03 — Limite de vídeos
**Arquivo:** `skills/texto-display/SKILL.md` (linha 104)

**Mudança:**
```markdown
<!-- Antes -->
- [ ] 3–6 marcadores `[VIDEO-NN]` sugeridos

<!-- Depois -->
- [ ] Exatamente 1 marcador `[VIDEO-01]` sugerido por aula
```

### 3. Servidor — Contar imagens M01
**Arquivo:** `servidor.py` (API `/api/m03-check`)

**Adicionado:**
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
    "imagens_m01": qtd_imagens_m01,  # NOVO
})
```

## Status
- ✅ M02: Usa skill `/analista-conteudo` (claude-opus-4-7)
- ✅ M03: 1 vídeo por aula
- ✅ Imagens M01: Contadas no display

## Arquivos Modificados
- `scripts/03-agente-e.py` — Revertido para versão com skill
- `servidor.py` — Revertido + adicionado contador de imagens
- `skills/texto-display/SKILL.md` — Limite de 1 vídeo
