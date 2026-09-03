#!/usr/bin/env python3
"""Utilitário de calibração: imprime a árvore de controles de uma janela
do Superus (via pywinauto), para descobrir nomes/classes reais de botões,
grades e diálogos e ajustar os seletores usados em src/.

Rode isto na máquina real com o Superus aberto na tela desejada.

Uso:
    python scripts/calibrar_ui.py "SPED"        # regex do título da janela
    python scripts/calibrar_ui.py "Alteração de escritura"
"""
from __future__ import annotations

import sys

from pywinauto import Desktop


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python scripts/calibrar_ui.py <regex-do-titulo-da-janela>")
        raise SystemExit(1)
    titulo_regex = sys.argv[1]
    desktop = Desktop(backend="win32")
    janela = desktop.window(title_re=titulo_regex)
    janela.print_control_identifiers()


if __name__ == "__main__":
    main()
