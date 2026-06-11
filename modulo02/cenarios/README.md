# 4 Cenários de Validação — Módulo 02

## Como Testar

1. Abra `../laudo.html` no navegador ou via hub: `http://127.0.0.1:5050/modulo02/laudo.html`
2. Clique em **"Usar Dados de Teste"** para ver o laudo padrão (6,30 🟠)
3. Para cada cenário abaixo, clique em **"📄 Carregar JSON"** e selecione o arquivo

### Via código

```bash
python3 modulo02/test_calculo.py
```

### Via servidor

`http://127.0.0.1:5050/modulo02/test-cenarios.html`

> Quando carregado via `/api/score`, o índice é **recalculado** por `calculo.py` a partir das notas — o valor gravado no JSON pode divergir do índice exibido na tela.

---

## Cenário 1 — 🟠 INTERVENÇÃO EDITORIAL

**Arquivo:** `cenario-1.json`

| Métrica | Valor |
|---------|-------|
| Índice | **5,70** |
| Veredito | 🟠 INTERVENCAO_EDITORIAL |
| A1 | SEM_RESSALVA |
| A2 | SEM_RESSALVA |

**Notas:** B1=6,0 · B2=6,0 · B3=5,0 · B4=6,0 · B5=6,0

**Valida:** Faixa laranja (5,0–6,4) sem fundamento crítico

---

## Cenário 2 — 🟡 APROVAR COM RESSALVA

**Arquivo:** `cenario-2.json`

| Métrica | Valor |
|---------|-------|
| Índice | **7,40** |
| Veredito | 🟡 APROVAR_COM_RESSALVA |
| A1 | SEM_RESSALVA |
| A2 | SEM_RESSALVA |

**Notas:** B1=7,0 · B2=7,0 · B3=8,0 · B4=7,0 · B5=7,5

**Valida:** Faixa âmbar (6,5–7,9) sem fundamento crítico

---

## Cenário 3 — 🔴 RECRIAR (por índice)

**Arquivo:** `cenario-3.json`

| Métrica | Valor |
|---------|-------|
| Índice | **4,00** |
| Veredito | 🔴 RECRIAR |
| A1 | SEM_RESSALVA |
| A2 | SEM_RESSALVA |

**Notas:** B1=4,0 · B2=5,0 · B3=3,0 · B4=5,0 · B5=4,0

**Valida:** Faixa vermelha por índice < 5,0 (sem bloco crítico)

---

## Cenário 4 — 🔴 RECRIAR (A2 CRÍTICO — override)

**Arquivo:** `cenario-4.json`

| Métrica | Valor |
|---------|-------|
| Índice | **8,45** |
| Veredito | 🔴 RECRIAR |
| A1 | SEM_RESSALVA |
| A2 | **CRITICO** |

**Notas:** B1=9,0 · B2=8,0 · B3=8,0 · B4=9,0 · B5=8,5

**Valida:** 
- Índice alto (8,45) mas veredito RECRIAR por A2 CRÍTICO
- **Bloco "Verificação de Fundamentos ≠ Índice de Qualidade" deve aparecer**
- Este é o cenário mais importante — demonstra que Fundamentos ≠ Índice

---

## Checklist de Validação Visual

- [ ] **Cenário 1:** Barra laranja `#EA580C` (NÃO marrom)
- [ ] **Cenário 2:** Barra âmbar `#CA8A04`
- [ ] **Cenário 3:** Barra vermelha `#DC2626`, sem bloco crítico
- [ ] **Cenário 4:** Barra vermelha `#DC2626`, **com bloco crítico visível**
- [ ] Gauge radial preenche da esquerda para direita
- [ ] Cantos retos (2px), não arredondados
- [ ] Tipografia: Inter (UI), Literata (corpo), JetBrains Mono (números)
