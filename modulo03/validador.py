#!/usr/bin/env python3
"""
M03 — Validador de Texto Display

Validação determinística (sem IA) do output do Agente A.
Verifica regras editoriais antes de avançar no pipeline.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any


def contar_palavras(texto: str) -> int:
    """Conta palavras em um texto (separadas por whitespace)."""
    return len(re.findall(r'\b\w+\b', texto, flags=re.UNICODE))


def extrair_marcadores_img(texto: str) -> List[str]:
    """Extrai todos os marcadores [IMG-NN] do texto (apenas o ID)."""
    return re.findall(r'\[IMG-(\d+)(?:\s+alt="[^"]*")?\]', texto)


def extrair_marcadores_video(texto: str) -> List[str]:
    """Extrai todos os marcadores [VIDEO-NN] do texto."""
    return re.findall(r'\[VIDEO-\d+\]', texto)


def extrair_citacoes(texto: str) -> List[str]:
    """Extrai citações entre aspas do texto."""
    return re.findall(r'"([^"]{20,})"', texto)


def tem_secao_glossario(texto: str) -> bool:
    """Verifica se existe seção de glossário no final do texto."""
    # Procura por "Glossário" nas últimas 30% do texto
    corte = len(texto) // 3 * 2
    return "Glossário" in texto[corte:] or "glossário" in texto[corte:]


def tem_abertura_com_pergunta(texto: str) -> bool:
    """Verifica se há pergunta-gancho nas primeiras linhas."""
    primeiras_linhas = texto[:500].lower()
    return "?" in primeiras_linhas[:200]


def tem_fechamento_com_bullets(texto: str) -> bool:
    """Verifica se há síntese com bullets no final."""
    ultimas_linhas = texto[-800:].lower()
    # Procura por padrão de bullet (- ou * ou •) repetido
    bullets = re.findall(r'^\s*[-*•]\s+', ultimas_linhas, re.MULTILINE)
    return len(bullets) >= 3


def palavras_proibidas(texto: str) -> List[str]:
    """Retorna lista de palavras proibidas encontradas no texto."""
    proibidas = []
    padroes = [
        (r'\bvestibular\b', 'vestibular'),
        (r'\ba Uni\b', 'a Uni'),
        (r'\bUnicão\b', 'Unicão'),
        (r'\bestaremos\b', 'estaremos (gerundismo)'),
    ]
    for padrao, nome in padroes:
        if re.search(padrao, texto, re.IGNORECASE):
            proibidas.append(nome)
    return proibidas


def validar(pasta_aula: Path) -> Dict[str, Any]:
    """
    Valida o texto display de uma aula.

    Args:
        pasta_aula: Caminho para a pasta da aula (ex: cursos/administracao/ADM-disc/aulas/01)

    Returns:
        Dict com:
            - ok: bool (True se passou em todas as verificações)
            - falhas: List[str] (lista de falhas críticas)
            - alertas: List[str] (lista de alertas não-críticos)
            - metricas: Dict com volumes e proporções
    """
    falhas = []
    alertas = []

    # Caminhos
    markdown_original = pasta_aula / "02_markdown"
    texto_display_path = pasta_aula / "03_reformulado" / "texto-display.md"

    # Verifica se arquivos existem
    if not texto_display_path.exists():
        return {
            "ok": False,
            "falhas": ["texto-display.md não encontrado"],
            "alertas": [],
            "metricas": {}
        }

    # Lê arquivos
    display_text = texto_display_path.read_text(encoding="utf-8")

    # Encontra o arquivo original (pode haver vários .md)
    originais = list(markdown_original.glob("*.md"))
    if not originais:
        return {
            "ok": False,
            "falhas": ["Nenhum arquivo .md encontrado em 02_markdown/"],
            "alertas": [],
            "metricas": {}
        }

    # Usa o primeiro arquivo .md encontrado
    original_path = originais[0]
    original_text = original_path.read_text(encoding="utf-8")

    # 1. Volume ≥ 80%
    volume_original = contar_palavras(original_text)
    volume_display = contar_palavras(display_text)
    proporcao = (volume_display / volume_original * 100) if volume_original > 0 else 0

    if proporcao < 80:
        falhas.append(f"Volume {proporcao:.0f}% — abaixo do mínimo de 80%")
    elif proporcao < 85:
        alertas.append(f"Volume {proporcao:.0f}% — próximo do limite mínimo")

    # 2. Marcadores IMG preservados
    imgs_original = set(extrair_marcadores_img(original_text))
    imgs_display = set(extrair_marcadores_img(display_text))
    imgs_faltantes = imgs_original - imgs_display

    if imgs_faltantes:
        falhas.append(f"Marcadores IMG faltando: {', '.join(sorted(imgs_faltantes))}")

    # 3. Glossário presente
    if not tem_secao_glossario(display_text):
        falhas.append("Glossário não encontrado no final do texto")

    # 4. Abertura com pergunta-gancho
    if not tem_abertura_com_pergunta(display_text):
        alertas.append("Abertura sem pergunta-gancho evidente")

    # 5. Fechamento com bullets
    if not tem_fechamento_com_bullets(display_text):
        alertas.append("Fechamento sem síntese em bullets")

    # 6. Palavras proibidas
    proibidas_encontradas = palavras_proibidas(display_text)
    if proibidas_encontradas:
        falhas.append(f"Palavras proibidas: {', '.join(proibidas_encontradas)}")

    # 7. Citações preservadas (verificação básica)
    citacoes_original = set(extrair_citacoes(original_text))
    citacoes_display = set(extrair_citacoes(display_text))
    citacoes_faltantes = citacoes_original - citacoes_display

    if citacoes_faltantes:
        # Alerta apenas — pode ser reformulação legítima
        alertas.append(f"Citações que podem ter sido removidas: {len(citacoes_faltantes)}")

    # 8. Marcadores de vídeo (pelo menos 1 sugerido)
    videos = extrair_marcadores_video(display_text)
    if len(videos) < 1:
        alertas.append("Nenhum marcador [VIDEO-NN] sugerido")
    elif len(videos) > 8:
        alertas.append(f"Muitos marcadores de vídeo ({len(videos)}), ideal é 3-6")

    # 9. Callouts (verificação de sintaxe)
    callouts_validos = ["conceito-chave", "atencao", "resumo", "exercicio", "dica", "leitura"]
    callouts_encontrados = re.findall(r':::([\w-]+)', display_text)
    callouts_invalidos = [c for c in callouts_encontrados if c not in callouts_validos]

    if callouts_invalidos:
        falhas.append(f"Callouts com sintaxe inválida: {', '.join(callouts_invalidos)}")

    # Contagem de callouts por tipo
    callouts_count = {tipo: callouts_encontrados.count(tipo) for tipo in callouts_validos}

    return {
        "ok": len(falhas) == 0,
        "falhas": falhas,
        "alertas": alertas,
        "metricas": {
            "volume_original": volume_original,
            "volume_display": volume_display,
            "proporcao_pct": round(proporcao, 1),
            "marcadores_img": len(imgs_display),
            "marcadores_video": len(videos),
            "callouts": callouts_count
        }
    }


def validar_e_salvar_log(pasta_aula: Path) -> Dict[str, Any]:
    """
    Valida e salva o resultado em _log.json na pasta da aula.
    """
    resultado = validar(pasta_aula)

    log_path = pasta_aula / "_log.json"
    log_entry = {
        "modulo": "M03",
        "acao": "validacao",
        "resultado": resultado
    }

    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            log = json.load(f)
        if isinstance(log, list):
            log.append(log_entry)
        else:
            log = [log, log_entry]
    else:
        log = [log_entry]

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    return resultado


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python validador.py <pasta_da_aula>")
        print("Ex: python validador.py cursos/administracao/ADM-disc/aulas/01")
        sys.exit(1)

    pasta = Path(sys.argv[1])
    resultado = validar_e_salvar_log(pasta)

    print("\n=== M03 — Resultado da Validação ===\n")

    if resultado["ok"]:
        print("✅ Validação APROVADA")
    else:
        print("❌ Validação REPROVADA")
        print("\nFalhas:")
        for falha in resultado["falhas"]:
            print(f"  • {falha}")

    if resultado["alertas"]:
        print("\nAlertas:")
        for alerta in resultado["alertas"]:
            print(f"  • {alerta}")

    if resultado["metricas"]:
        print("\nMétricas:")
        print(f"  Volume original: {resultado['metricas']['volume_original']} palavras")
        print(f"  Volume display: {resultado['metricas']['volume_display']} palavras")
        print(f"  Proporção: {resultado['metricas']['proporcao_pct']}%")

    sys.exit(0 if resultado["ok"] else 1)
