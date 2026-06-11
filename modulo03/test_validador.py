#!/usr/bin/env python3
"""
M03 — Testes do Validador

Testa os casos de falha do validador.py
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from validador import (
    validar,
    contar_palavras,
    extrair_marcadores_img,
    extrair_marcadores_video,
    tem_secao_glossario,
    tem_abertura_com_pergunta,
    tem_fechamento_com_bullets,
    palavras_proibidas,
)


class TestContagemPalavras(unittest.TestCase):
    def test_contagem_simples(self):
        self.assertEqual(contar_palavras("Olá mundo"), 2)
        self.assertEqual(contar_palavras("Um dois três quatro cinco"), 5)

    def test_contagem_vazio(self):
        self.assertEqual(contar_palavras(""), 0)
        self.assertEqual(contar_palavras("   "), 0)

    def test_contagem_com_acentos(self):
        self.assertEqual(contar_palavras("café açúcar lápis"), 3)


class TestExtracaoMarcadores(unittest.TestCase):
    def test_img_simples(self):
        texto = "Veja [IMG-01] e [IMG-02]"
        self.assertEqual(extrair_marcadores_img(texto), ["01", "02"])

    def test_img_com_alt(self):
        texto = 'Veja [IMG-01 alt="Gráfico de vendas"]'
        marcadores = extrair_marcadores_img(texto)
        self.assertEqual(len(marcadores), 1)
        self.assertEqual(marcadores[0], "01")

    def test_video_simples(self):
        texto = "Assista [VIDEO-01] e [VIDEO-02]"
        self.assertEqual(extrair_marcadores_video(texto), ["[VIDEO-01]", "[VIDEO-02]"])


class TestValidador(unittest.TestCase):
    def setUp(self):
        """Cria estrutura temporária para testes."""
        self.temp_dir = tempfile.mkdtemp()
        self.pasta_aula = Path(self.temp_dir)

        # Cria subpastas
        (self.pasta_aula / "02_markdown").mkdir()
        (self.pasta_aula / "03_reformulado").mkdir()

    def tearDown(self):
        """Remove estrutura temporária."""
        shutil.rmtree(self.temp_dir)

    def test_volume_abaixo_80_por_cento_falha(self):
        """Texto com volume < 80% deve falhar."""
        # Original com 100 palavras
        original = "palavra " * 100
        (self.pasta_aula / "02_markdown" / "test.md").write_text(original)

        # Display com 50 palavras (50%)
        display = "palavra " * 50
        (self.pasta_aula / "03_reformulado" / "texto-display.md").write_text(display)

        resultado = validar(self.pasta_aula)

        self.assertFalse(resultado["ok"])
        self.assertTrue(any("80%" in f for f in resultado["falhas"]))

    def test_volume_acima_80_por_cento_passa(self):
        """Texto com volume >= 80% deve passar (se tiver glossário)."""
        original = "palavra " * 100
        (self.pasta_aula / "02_markdown" / "test.md").write_text(original)

        display = """palavra palavra palavra palavra palavra palavra palavra palavra palavra palavra
palavra palavra palavra palavra palavra palavra palavra palavra palavra palavra
palavra palavra palavra palavra palavra palavra palavra palavra palavra palavra
palavra palavra palavra palavra palavra palavra palavra palavra palavra palavra
palavra palavra palavra palavra palavra palavra palavra palavra palavra palavra
palavra palavra palavra palavra palavra palavra palavra palavra palavra palavra
palavra palavra palavra palavra palavra palavra palavra palavra palavra palavra
palavra palavra palavra palavra palavra palavra palavra palavra palavra palavra
palavra palavra palavra palavra palavra palavra palavra palavra palavra palavra
palavra palavra palavra palavra palavra palavra palavra palavra palavra

## Glossário
**Termo:** definição
"""
        (self.pasta_aula / "03_reformulado" / "texto-display.md").write_text(display)

        resultado = validar(self.pasta_aula)

        self.assertTrue(resultado["ok"])

    def test_sem_glossario_falha(self):
        """Texto sem glossário deve falhar."""
        original = "texto qualquer"
        (self.pasta_aula / "02_markdown" / "test.md").write_text(original)

        display = "Texto reformulado sem glossário no final."
        (self.pasta_aula / "03_reformulado" / "texto-display.md").write_text(display)

        resultado = validar(self.pasta_aula)

        self.assertFalse(resultado["ok"])
        self.assertTrue(any("Glossário" in f for f in resultado["falhas"]))

    def test_com_glossario_passa(self):
        """Texto com glossário deve passar (nesta verificação)."""
        original = "texto qualquer"
        (self.pasta_aula / "02_markdown" / "test.md").write_text(original)

        display = """
Texto reformulado.

## Glossário
**Termo 1:** definição simples
**Termo 2:** outra definição
"""
        (self.pasta_aula / "03_reformulado" / "texto-display.md").write_text(display)

        resultado = validar(self.pasta_aula)

        self.assertNotIn("Glossário não encontrado", resultado["falhas"])

    def test_com_vestibular_falha(self):
        """Texto com 'vestibular' deve falhar."""
        original = "texto"
        (self.pasta_aula / "02_markdown" / "test.md").write_text(original)

        display = "Para ingressar via vestibular, você deve..."
        (self.pasta_aula / "03_reformulado" / "texto-display.md").write_text(display)

        resultado = validar(self.pasta_aula)

        self.assertFalse(resultado["ok"])
        self.assertTrue(any("vestibular" in f for f in resultado["falhas"]))

    def test_com_a_uni_falha(self):
        """Texto com 'a Uni' deve falhar."""
        original = "texto"
        (self.pasta_aula / "02_markdown" / "test.md").write_text(original)

        display = "Na a Uni, você aprende..."
        (self.pasta_aula / "03_reformulado" / "texto-display.md").write_text(display)

        resultado = validar(self.pasta_aula)

        self.assertFalse(resultado["ok"])

    def test_texto_correto_passa(self):
        """Texto correto deve passar em todas as verificações."""
        original = """
# Introdução

[IMG-01]

Texto com conceito importante.

## Glossário
**Conceito:** definição
"""
        (self.pasta_aula / "02_markdown" / "test.md").write_text(original)

        # Display com volume similar + glossário + todos elementos
        display = """
Você já se perguntou como funciona este conceito na prática?

[IMG-01 alt="Ilustração do conceito"]

Texto reformulado com volume adequado para display.

Vamos explorar cada aspecto deste conceito fundamental.

Primeiro, entendemos a base teórica.

Depois, aplicamos a situações reais.

[VIDEO-01]

## Glossário
**Conceito:** definição simples
"""
        (self.pasta_aula / "03_reformulado" / "texto-display.md").write_text(display)

        resultado = validar(self.pasta_aula)

        self.assertTrue(resultado["ok"])

    def test_img_faltante_falha(self):
        """IMG do original faltando no display deve falhar."""
        original = "Veja [IMG-01] e [IMG-02]"
        (self.pasta_aula / "02_markdown" / "test.md").write_text(original)

        display = "Veja [IMG-01]"  # IMG-02 faltando
        (self.pasta_aula / "03_reformulado" / "texto-display.md").write_text(display)

        resultado = validar(self.pasta_aula)

        self.assertFalse(resultado["ok"])
        self.assertTrue(any("02" in f for f in resultado["falhas"]))


class TestPalavrasProibidas(unittest.TestCase):
    def test_vestibular_detectado(self):
        self.assertIn("vestibular", palavras_proibidas("ingresso via vestibular"))

    def test_a_uni_detectado(self):
        self.assertIn("a Uni", palavras_proibidas("estude na a Uni"))

    def test_unicao_detectado(self):
        self.assertIn("Unicão", palavras_proibidas("bem-vindo à Unicão"))

    def test_estaremos_detectado(self):
        self.assertTrue(any("estaremos" in p for p in palavras_proibidas("estaremos vendo")))

    def test_texto_limpo(self):
        self.assertEqual(palavras_proibidas("texto limpo sem proibições"), [])


if __name__ == "__main__":
    unittest.main()
