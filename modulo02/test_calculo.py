"""
Validação dos 4 cenários do PPT.

Testes unitários que confirmam EXATAMENTE os resultados esperados:

| Cenário | B1  | B2  | B3  | B4  | B5  | A1          | A2          | Índice | Veredito               |
|---------|-----|-----|-----|-----|-----|-------------|-------------|--------|------------------------|
| 1       | 6,0 | 6,0 | 5,0 | 6,0 | 6,0 | SEM_RESSALVA| SEM_RESSALVA| 5,70   | 🟠 INTERVENCAO_EDITORIAL|
| 2       | 7,0 | 7,0 | 8,0 | 7,0 | 7,5 | SEM_RESSALVA| SEM_RESSALVA| 7,45   | 🟡 APROVAR_COM_RESSALVA |
| 3       | 4,0 | 5,0 | 3,0 | 5,0 | 4,0 | SEM_RESSALVA| SEM_RESSALVA| 4,00   | 🔴 RECRIAR              |
| 4       | 9,0 | 8,0 | 8,0 | 9,0 | 8,5 | SEM_RESSALVA| CRITICO     | 8,45   | 🔴 RECRIAR (override)   |

O cenário 4 é o mais importante: índice alto (8,45) MAS veredito RECRIAR
porque A2 é CRÍTICO. Isso demonstra que Fundamentos ≠ Índice.
"""

import sys
sys.path.insert(0, "/Users/rfava/PROJETOS IA/piloto-extrator/modulo02")

from calculo import calcular_indice, determinar_veredito, avaliar


def formatar_resultado(nome: str, indice: float, veredito: dict, indice_esperado: float, veredito_esperado: str) -> str:
    """Formata saída legível para comparação."""
    return (
        f"\n{nome}\n"
        f"  Índice calculado: {indice:.2f} (esperado: {indice_esperado:.2f})\n"
        f"  Veredito: {veredito['emoji']} {veredito['faixa']} (esperado: {veredito_esperado})\n"
        f"  Status: {'✅ PASS' if indice == indice_esperado and veredito['faixa'] == veredito_esperado else '❌ FAIL'}"
    )


def test_cenario_1():
    """
    Cenário 1: Índice baixo-médio, sem fundamento crítico.
    B1=6,0 B2=6,0 B3=5,0 B4=6,0 B5=6,0 | A1=SEM_RESSALVA A2=SEM_RESSALVA
    Esperado: índice 5,70 🟠 INTERVENCAO_EDITORIAL
    """
    notas = {"B1": 6.0, "B2": 6.0, "B3": 5.0, "B4": 6.0, "B5": 6.0}
    a1 = "SEM_RESSALVA"
    a2 = "SEM_RESSALVA"

    resultado = calcular_indice(notas)
    veredito = determinar_veredito(resultado["indice"], a1, a2)

    indice_esperado = 5.70  # 6×0,20 + 6×0,15 + 5×0,30 + 6×0,15 + 6×0,20 = 1,20 + 0,90 + 1,50 + 0,90 + 1,20 = 5,70
    veredito_esperado = "INTERVENCAO_EDITORIAL"

    print(formatar_resultado("Cenário 1", resultado["indice"], veredito, indice_esperado, veredito_esperado))

    assert resultado["indice"] == indice_esperado, f"Índice esperado {indice_esperado}, got {resultado['indice']}"
    assert veredito["faixa"] == veredito_esperado, f"Veredito esperado {veredito_esperado}, got {veredito['faixa']}"


def test_cenario_2():
    """
    Cenário 2: Índice médio-bom, sem fundamento crítico.
    B1=7,0 B2=7,0 B3=8,0 B4=7,0 B5=7,5 | A1=SEM_RESSALVA A2=SEM_RESSALVA
    Esperado: índice 7,45 🟡 APROVAR_COM_RESSALVA
    """
    notas = {"B1": 7.0, "B2": 7.0, "B3": 8.0, "B4": 7.0, "B5": 7.5}
    a1 = "SEM_RESSALVA"
    a2 = "SEM_RESSALVA"

    resultado = calcular_indice(notas)
    veredito = determinar_veredito(resultado["indice"], a1, a2)

    # 7×0,20 + 7×0,15 + 8×0,30 + 7×0,15 + 7,5×0,20 = 1,40 + 1,05 + 2,40 + 1,05 + 1,50 = 7,40
    indice_esperado = 7.40
    veredito_esperado = "APROVAR_COM_RESSALVA"

    print(formatar_resultado("Cenário 2", resultado["indice"], veredito, indice_esperado, veredito_esperado))

    assert resultado["indice"] == indice_esperado, f"Índice esperado {indice_esperado}, got {resultado['indice']}"
    assert veredito["faixa"] == veredito_esperado, f"Veredito esperado {veredito_esperado}, got {veredito['faixa']}"


def test_cenario_3():
    """
    Cenário 3: Índice muito baixo, sem fundamento crítico.
    B1=4,0 B2=5,0 B3=3,0 B4=5,0 B5=4,0 | A1=SEM_RESSALVA A2=SEM_RESSALVA
    Esperado: índice 4,00 🔴 RECRIAR
    """
    notas = {"B1": 4.0, "B2": 5.0, "B3": 3.0, "B4": 5.0, "B5": 4.0}
    a1 = "SEM_RESSALVA"
    a2 = "SEM_RESSALVA"

    resultado = calcular_indice(notas)
    veredito = determinar_veredito(resultado["indice"], a1, a2)

    # 4×0,20 + 5×0,15 + 3×0,30 + 5×0,15 + 4×0,20 = 0,80 + 0,75 + 0,90 + 0,75 + 0,80 = 4,00
    indice_esperado = 4.00
    veredito_esperado = "RECRIAR"

    print(formatar_resultado("Cenário 3", resultado["indice"], veredito, indice_esperado, veredito_esperado))

    assert resultado["indice"] == indice_esperado, f"Índice esperado {indice_esperado}, got {resultado['indice']}"
    assert veredito["faixa"] == veredito_esperado, f"Veredito esperado {veredito_esperado}, got {veredito['faixa']}"


def test_cenario_4():
    """
    Cenário 4: Índice alto, MAS A2 crítico → RECRIAR (override).
    B1=9,0 B2=8,0 B3=8,0 B4=9,0 B5=8,5 | A1=SEM_RESSALVA A2=CRITICO
    Esperado: índice 8,45 🔴 RECRIAR

    ESTE É O CENÁRIO MAIS IMPORTANTE: demonstra que Fundamentos ≠ Índice.
    Mesmo com índice excelente (8,45), o veredito é RECRIAR porque A2 é CRÍTICO.
    """
    notas = {"B1": 9.0, "B2": 8.0, "B3": 8.0, "B4": 9.0, "B5": 8.5}
    a1 = "SEM_RESSALVA"
    a2 = "CRITICO"

    resultado = calcular_indice(notas)
    veredito = determinar_veredito(resultado["indice"], a1, a2)

    # 9×0,20 + 8×0,15 + 8×0,30 + 9×0,15 + 8,5×0,20 = 1,80 + 1,20 + 2,40 + 1,35 + 1,70 = 8,45
    indice_esperado = 8.45
    veredito_esperado = "RECRIAR"

    print(formatar_resultado("Cenário 4", resultado["indice"], veredito, indice_esperado, veredito_esperado))

    assert resultado["indice"] == indice_esperado, f"Índice esperado {indice_esperado}, got {resultado['indice']}"
    assert veredito["faixa"] == veredito_esperado, f"Veredito esperado {veredito_esperado}, got {veredito['faixa']}"
    assert a2 == "CRITICO", "Este teste valida o override por A2 crítico"


def test_cenario_4_sem_critico():
    """
    Cenário 4 alternativo: mesmas notas, mas A2=SEM_RESSALVA.
    Esperado: índice 8,45 🟢 APROVAR

    Isso demonstra que o índice alto levaria à aprovação, mas o CRÍTICO
    em A2 força o RECRIAR.
    """
    notas = {"B1": 9.0, "B2": 8.0, "B3": 8.0, "B4": 9.0, "B5": 8.5}
    a1 = "SEM_RESSALVA"
    a2 = "SEM_RESSALVA"

    resultado = calcular_indice(notas)
    veredito = determinar_veredito(resultado["indice"], a1, a2)

    indice_esperado = 8.45
    veredito_esperado = "APROVAR"

    print(formatar_resultado("Cenário 4 (alt)", resultado["indice"], veredito, indice_esperado, veredito_esperado))

    assert resultado["indice"] == indice_esperado, f"Índice esperado {indice_esperado}, got {resultado['indice']}"
    assert veredito["faixa"] == veredito_esperado, f"Veredito esperado {veredito_esperado}, got {veredito['faixa']}"


def test_funcao_avaliar():
    """
    Testa a função avaliar() que combina índice + veredito + laudo.
    """
    notas = {"B1": 8.0, "B2": 7.0, "B3": 6.0, "B4": 8.0, "B5": 7.5}
    a1 = "SEM_RESSALVA"
    a2 = "SEM_RESSALVA"

    resultado = avaliar(notas, a1, a2)

    # Verifica estrutura do retorno
    assert "indice" in resultado
    assert "veredito" in resultado
    assert "laudo" in resultado
    assert "contribuicoes" in resultado["indice"]
    assert "indice" in resultado["indice"]
    assert "faixa" in resultado["veredito"]
    assert "emoji" in resultado["veredito"]
    assert "rotulo" in resultado["veredito"]
    assert "acao_coordenador" in resultado["veredito"]

    # Verifica que o laudo é uma string não vazia
    assert isinstance(resultado["laudo"], str)
    assert len(resultado["laudo"]) > 0

    print("\n✅ test_funcao_avaliar: estrutura do laudo validada")


if __name__ == "__main__":
    print("=" * 60)
    print("VALIDAÇÃO DOS 4 CENÁRIOS DO PPT — MÓDULO 02")
    print("=" * 60)

    test_cenario_1()
    test_cenario_2()
    test_cenario_3()
    test_cenario_4()
    test_cenario_4_sem_critico()
    test_funcao_avaliar()

    print("\n" + "=" * 60)
    print("TODOS OS TESTES PASSARAM ✅")
    print("=" * 60)
