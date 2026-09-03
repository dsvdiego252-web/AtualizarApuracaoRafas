#!/usr/bin/env python3
"""Utilitário de calibração: captura um recorte da tela ao redor do mouse
e salva em assets/, para servir de imagem de referência para os cliques
por reconhecimento de imagem (ver src/image_helpers.py).

Uso:
    python scripts/capturar_icone.py editar_escrituracao.png

Posicione o mouse sobre o ícone desejado (sem clicar) e aguarde a
contagem regressiva; a captura sai de um recorte de 40x40 pixels
centrado no cursor. Ajuste o tamanho com --largura/--altura se o ícone
for maior ou menor.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import pyautogui

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("nome_arquivo", help="Nome do arquivo a salvar em assets/, ex.: editar_escrituracao.png")
    parser.add_argument("--largura", type=int, default=40)
    parser.add_argument("--altura", type=int, default=40)
    parser.add_argument("--espera", type=float, default=4.0, help="Segundos de contagem regressiva antes de capturar")
    args = parser.parse_args()

    print(f"Posicione o mouse sobre o ícone (sem clicar). Capturando em {args.espera:.0f}s...")
    time.sleep(args.espera)

    x, y = pyautogui.position()
    caixa = (int(x - args.largura / 2), int(y - args.altura / 2), args.largura, args.altura)

    ASSETS_DIR.mkdir(exist_ok=True)
    destino = ASSETS_DIR / args.nome_arquivo
    imagem = pyautogui.screenshot(region=caixa)
    imagem.save(destino)
    print(f"Salvo em {destino}")


if __name__ == "__main__":
    main()
