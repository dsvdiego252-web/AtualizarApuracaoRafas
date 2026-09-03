"""Configuração de logging com pasta por execução e captura de screenshots.

Cada execução grava seu próprio log e screenshots em logs/<timestamp>/,
para permitir auditar depois exatamente o que a rotina fez (ou onde
falhou) numa máquina onde ninguém está olhando a tela.
"""
from __future__ import annotations

import datetime as _dt
import logging
from pathlib import Path

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"


def configurar_logging() -> tuple[logging.Logger, Path]:
    LOGS_DIR.mkdir(exist_ok=True)
    timestamp = _dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    pasta_execucao = LOGS_DIR / timestamp
    pasta_execucao.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("apuracao_superus")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    formato = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")

    arquivo = logging.FileHandler(pasta_execucao / "execucao.log", encoding="utf-8")
    arquivo.setFormatter(formato)
    arquivo.setLevel(logging.DEBUG)

    console = logging.StreamHandler()
    console.setFormatter(formato)
    console.setLevel(logging.INFO)

    logger.addHandler(arquivo)
    logger.addHandler(console)
    return logger, pasta_execucao


def capturar_screenshot(pasta_execucao: Path, nome: str) -> Path:
    from PIL import ImageGrab

    destino = pasta_execucao / f"{nome}.png"
    ImageGrab.grab().save(destino)
    return destino
