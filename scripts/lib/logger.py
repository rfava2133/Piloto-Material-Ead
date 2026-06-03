"""
logger.py — Registra o que aconteceu em cada processamento (_log.json por aula).
"""
import json
from pathlib import Path
from datetime import datetime


def registrar(pasta_aula: Path, dados: dict) -> Path:
    """
    Grava/atualiza _log.json na pasta da aula.
    Acumula histórico de execuções.
    """
    log_path = pasta_aula / "_log.json"

    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            historico = json.load(f)
    else:
        historico = {"aula": pasta_aula.name, "execucoes": []}

    dados["timestamp"] = datetime.now().isoformat(timespec="seconds")
    historico["execucoes"].append(dados)

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)

    return log_path
