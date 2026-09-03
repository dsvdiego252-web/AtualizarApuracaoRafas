#!/usr/bin/env python3
"""Roda a apuração de ICMS/IPI (SPED) no Superus para as lojas configuradas
em config.yaml, atualizando a Data Final para "ontem" e regravando os
relatórios de CFOP e Alíquota na pasta do mês corrente.

Uso:
    python run.py                  # roda todas as lojas
    python run.py --loja 1         # roda apenas a loja de número 1
    python run.py --data 30082026  # força a data de execução (para testes)

Pré-requisitos: Superus já aberto e logado na máquina (ver README.md).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.apuracao_flow import abrir_tela_sped, processar_loja
from src.config import Config, pasta_destino
from src.logging_setup import capturar_screenshot, configurar_logging
from src.win_helpers import SuperusAutomationError, conectar_superus, janela_principal


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--loja", type=int, help="Processar apenas a loja com este número")
    parser.add_argument("--data", type=str, help="Data de execução ddmmaaaa (padrão: hoje)")
    parser.add_argument("--config", type=str, default="config.yaml")
    args = parser.parse_args()

    hoje = _dt.datetime.strptime(args.data, "%d%m%Y").date() if args.data else _dt.date.today()

    logger, pasta_execucao = configurar_logging()
    logger.info("Início da execução — data de referência: %s", hoje.strftime("%d/%m/%Y"))

    config = Config.carregar(args.config)
    lojas = [l for l in config.lojas if args.loja is None or l.numero == args.loja]
    if not lojas:
        logger.error("Nenhuma loja encontrada para o filtro --loja=%s", args.loja)
        return 2

    destino = pasta_destino(config, hoje)
    logger.info("Pasta de destino dos relatórios: %s", destino)
    if not destino.exists():
        logger.error(
            "Pasta de destino não existe: %s — crie a pasta do mês antes de rodar "
            "(a rotina só sobrescreve arquivos existentes, nunca cria pastas novas).",
            destino,
        )
        return 2

    try:
        app = conectar_superus(config.caminho_executavel, config.exigir_processo_ja_aberto, config.timeout_janela_segundos)
        principal = janela_principal(app)
        sped_win, grade = abrir_tela_sped(principal)
    except SuperusAutomationError as erro:
        logger.error("Falha ao preparar o Superus: %s", erro)
        capturar_screenshot(pasta_execucao, "erro_abertura")
        return 1

    resultados: dict[str, str] = {}
    for loja in lojas:
        logger.info("=== Processando loja %s (%s) ===", loja.numero, loja.nome_superus)
        try:
            processar_loja(sped_win, grade, config, loja, hoje, destino, pasta_execucao)
            resultados[loja.nome_superus] = "OK"
        except Exception as erro:  # não interrompe as demais lojas
            logger.exception("Falha ao processar loja %s: %s", loja.nome_superus, erro)
            capturar_screenshot(pasta_execucao, f"erro_loja_{loja.numero}")
            resultados[loja.nome_superus] = f"FALHOU: {erro}"

    logger.info("=== Resumo da execução ===")
    houve_falha = False
    for nome, status in resultados.items():
        logger.info("%s: %s", nome, status)
        if status != "OK":
            houve_falha = True

    return 1 if houve_falha else 0


if __name__ == "__main__":
    raise SystemExit(main())
