"""Localização e clique de ícones sem texto via correspondência de imagem.

Usado como alternativa para os poucos pontos do roteiro que são botões de
ícone sem texto acessível (ex.: o 2º botão da barra de ferramentas da
grade, o ícone de "porta" para sair da tela de Conferência, o ícone do
Excel na pré-visualização do relatório). As imagens de referência ficam
em assets/ e precisam ser capturadas uma vez na máquina real — ver
scripts/capturar_icone.py.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional, Tuple

import pyautogui

logger = logging.getLogger("apuracao_superus")

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


class IconeNaoEncontradoError(RuntimeError):
    pass


def localizar_icone(
    nome_arquivo: str,
    regiao: Optional[Tuple[int, int, int, int]] = None,
    confianca: float = 0.85,
    timeout: float = 10,
) -> Tuple[int, int]:
    caminho = ASSETS_DIR / nome_arquivo
    if not caminho.exists():
        raise IconeNaoEncontradoError(
            f"Imagem de referência '{nome_arquivo}' não encontrada em assets/. "
            "Capture-a na máquina real com scripts/capturar_icone.py (veja assets/README.md)."
        )
    fim = time.monotonic() + timeout
    while time.monotonic() < fim:
        try:
            local = pyautogui.locateCenterOnScreen(str(caminho), region=regiao, confidence=confianca)
        except pyautogui.ImageNotFoundException:
            local = None
        if local:
            return local
        time.sleep(0.5)
    raise IconeNaoEncontradoError(
        f"Ícone '{nome_arquivo}' não encontrado na tela dentro do tempo limite. "
        "A janela pode ter perdido o foco (outro programa passou à frente) ou o "
        "ícone mudou — confira o screenshot de erro salvo em logs/ e recalibre a "
        "imagem se necessário."
    )


def clicar_icone(nome_arquivo: str, **kwargs) -> None:
    x, y = localizar_icone(nome_arquivo, **kwargs)
    pyautogui.moveTo(x, y, duration=0.15)
    pyautogui.click()
