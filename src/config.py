"""Carrega e resolve a configuração da rotina de apuração Superus."""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

MESES_ABREV_PT = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
}


@dataclass(frozen=True)
class Loja:
    numero: int
    nome_superus: str
    arquivo_cfop: str
    arquivo_aliquota: str


@dataclass(frozen=True)
class Config:
    caminho_executavel: str
    exigir_processo_ja_aberto: bool
    timeout_janela_segundos: int
    pasta_relatorios_padrao: str
    lojas: list[Loja]
    data_final_override: Optional[str]
    pausa_entre_acoes_segundos: float
    timeout_processamento_segundos: int
    modo_assistido: bool

    @staticmethod
    def carregar(caminho: str | Path = "config.yaml") -> "Config":
        dados = yaml.safe_load(Path(caminho).read_text(encoding="utf-8"))
        lojas = [Loja(**loja) for loja in dados["lojas"]]
        return Config(
            caminho_executavel=dados["superus"]["executavel"],
            exigir_processo_ja_aberto=dados["superus"].get("exigir_processo_ja_aberto", True),
            timeout_janela_segundos=dados["superus"].get("timeout_janela_segundos", 30),
            pasta_relatorios_padrao=dados["pasta_relatorios"]["padrao"],
            lojas=lojas,
            data_final_override=dados["execucao"].get("data_final_override"),
            pausa_entre_acoes_segundos=dados["execucao"].get("pausa_entre_acoes_segundos", 0.6),
            timeout_processamento_segundos=dados["execucao"].get("timeout_processamento_segundos", 240),
            modo_assistido=dados["execucao"].get("modo_assistido", False),
        )


def data_final_apuracao(config: Config, hoje: Optional[_dt.date] = None) -> _dt.date:
    """Data final da escrituração: sempre o dia anterior à execução (ontem)."""
    if config.data_final_override:
        return _dt.datetime.strptime(config.data_final_override, "%d%m%Y").date()
    hoje = hoje or _dt.date.today()
    return hoje - _dt.timedelta(days=1)


def data_final_ddmmaaaa(config: Config, hoje: Optional[_dt.date] = None) -> str:
    return data_final_apuracao(config, hoje).strftime("%d%m%Y")


def competencia_mes_ano(hoje: Optional[_dt.date] = None) -> tuple[int, int]:
    hoje = hoje or _dt.date.today()
    return hoje.month, hoje.year


def competencia_str(hoje: Optional[_dt.date] = None) -> str:
    """Texto de competência como costuma aparecer na grade (MM/AAAA).

    Suposição a validar na máquina real — se o Superus exibir em outro
    formato (ex.: 'Ago/2026'), ajuste esta função.
    """
    mes, ano = competencia_mes_ano(hoje)
    return f"{mes:02d}/{ano}"


def pasta_destino(config: Config, hoje: Optional[_dt.date] = None) -> Path:
    mes, ano = competencia_mes_ano(hoje)
    caminho = config.pasta_relatorios_padrao.format(
        ano=ano,
        mes=mes,
        mes_abrev=MESES_ABREV_PT[mes],
        ano_curto=str(ano)[-2:],
    )
    return Path(caminho)
