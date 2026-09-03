"""Camada de automação da interface do Superus (pywinauto).

Suposição: o Superus é um app Windows clássico (Delphi/VCL ou similar).
As caixas de diálogo padrão do Windows (MessageBox "Sim/Não/OK", "Salvar
como") são localizadas pela classe "#32770", o que é bem confiável. Já os
controles internos do Superus (grade de escriturações, botões de ícone
sem texto, formulários próprios) não têm identificadores conhecidos de
antemão — este módulo tenta localizá-los por texto/tipo via UI Automation
e, quando isso falha, o chamador cai para correspondência de imagem
(ver image_helpers.py). Use scripts/calibrar_ui.py na máquina real para
inspecionar a árvore de controles e ajustar os seletores se algo não for
encontrado.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Optional

from pywinauto import Desktop
from pywinauto.application import Application
from pywinauto.findwindows import ElementNotFoundError

logger = logging.getLogger("apuracao_superus")


class SuperusAutomationError(RuntimeError):
    """Erro de automação da rotina (falha esperada e tratável)."""


def _bate(padrao_regex: str, texto: str) -> bool:
    return re.search(padrao_regex, texto, re.IGNORECASE) is not None


def conectar_superus(caminho_executavel: str, exigir_ja_aberto: bool, timeout: int) -> Application:
    app = Application(backend="win32")
    try:
        app.connect(path=caminho_executavel, timeout=5)
        logger.info("Conectado a uma instância já aberta do Superus.")
        return app
    except (ElementNotFoundError, Exception):
        pass

    if exigir_ja_aberto:
        raise SuperusAutomationError(
            "Superus não está em execução. Esta rotina espera que o Superus já "
            "esteja aberto e com login efetuado (login automatizado NÃO é "
            "suportado). Abra e faça login no Superus manualmente antes de "
            "rodar a automação, ou ajuste 'exigir_processo_ja_aberto: false' em "
            "config.yaml para que a automação apenas inicie o executável "
            "(o login ainda precisará ser feito manualmente)."
        )

    logger.warning("Superus não encontrado em execução — iniciando o executável.")
    app.start(caminho_executavel)
    time.sleep(timeout)
    return app


def janela_principal(app: Application):
    """Retorna a janela do Superus que tem a barra de menu (Fiscal/Contábil
    etc.), não necessariamente a última janela em foco — se o Superus foi
    deixado aberto numa tela filha (ex.: grade do SPED), `top_window()`
    pega essa tela filha, que não tem menu próprio.
    """
    for candidata in app.windows(visible_only=True):
        try:
            if candidata.menu() is not None:
                return candidata
        except Exception:
            continue
    return app.top_window()


def aguardar_janela(titulo_regex: str, timeout: float = 30, backend: str = "win32"):
    """Aguarda e retorna a primeira janela de topo cujo título bate com o regex."""
    desktop = Desktop(backend=backend)
    fim = time.monotonic() + timeout
    ultimo_erro: Optional[Exception] = None
    while time.monotonic() < fim:
        try:
            janela = desktop.window(title_re=titulo_regex)
            if janela.exists():
                janela.wait("exists enabled visible", timeout=2)
                return janela
        except Exception as erro:
            ultimo_erro = erro
        time.sleep(0.5)
    raise SuperusAutomationError(
        f"Tempo esgotado aguardando janela '{titulo_regex}'. Último erro: {ultimo_erro}"
    )


def clicar_botao(janela, titulo_regex: str, timeout: float = 15) -> None:
    botao = janela.child_window(title_re=titulo_regex, control_type="Button")
    botao.wait("exists enabled visible", timeout=timeout)
    botao.click_input()


def confirmar_dialogo(mensagem_regex: str, botao_regex: str = "(?i)^sim$", timeout: float = 20) -> bool:
    """Se um diálogo padrão do Windows contendo `mensagem_regex` aparecer, clica `botao_regex`.

    Retorna True se o diálogo apareceu e foi tratado dentro do timeout,
    False se não apareceu (algumas confirmações desta rotina são
    condicionais, ex.: o aviso de "Total ICMS a recolher").
    """
    desktop = Desktop(backend="win32")
    fim = time.monotonic() + timeout
    while time.monotonic() < fim:
        for janela in desktop.windows(class_name="#32770"):
            try:
                texto = janela.window_text() + " " + " ".join(c.window_text() for c in janela.children())
            except Exception:
                continue
            if _bate(mensagem_regex, texto):
                logger.info("Diálogo detectado (%s) — clicando '%s'.", mensagem_regex, botao_regex)
                clicar_botao(janela, botao_regex)
                return True
        time.sleep(0.4)
    return False


def campo_apos_rotulo(janela, rotulo_regex: str):
    """Encontra o campo editável associado a um rótulo de texto.

    Formulários Delphi/VCL normalmente não associam Label a Edit via
    'LabelledBy' na árvore de acessibilidade — esta heurística assume que
    o campo é um dos controles editáveis logo após o rótulo na ordem dos
    widgets. Se isso não bater no Superus real, use scripts/calibrar_ui.py
    para inspecionar a janela e ajuste aqui (por exemplo, trocando por um
    índice fixo).
    """
    filhos = janela.children()
    for i, filho in enumerate(filhos):
        try:
            texto = filho.window_text()
        except Exception:
            continue
        if texto and _bate(rotulo_regex, texto):
            for candidato in filhos[i + 1 : i + 4]:
                if candidato.friendly_class_name() in ("Edit", "TEdit"):
                    return candidato
    raise SuperusAutomationError(
        f"Não encontrei o campo editável após o rótulo '{rotulo_regex}'. Use "
        "scripts/calibrar_ui.py para inspecionar a janela e ajuste "
        "campo_apos_rotulo() em src/win_helpers.py."
    )


def digitar_data(campo, data_ddmmaaaa: str) -> None:
    """Posiciona no início do campo e digita os 8 dígitos, como descrito no roteiro."""
    campo.set_focus()
    campo.type_keys("{HOME}", pause=0.05)
    campo.type_keys(data_ddmmaaaa, pause=0.05)


def digitar_caminho_arquivo(dialogo_salvar, caminho_completo: str) -> None:
    """Digita o caminho completo no campo 'Nome do arquivo' de um diálogo
    Salvar como nativo do Windows e confirma — evita ter que navegar pelas
    pastas manualmente, já que o diálogo aceita caminho absoluto.
    """
    campo = dialogo_salvar.child_window(class_name="Edit", found_index=0)
    campo.set_focus()
    campo.set_edit_text(caminho_completo)
    dialogo_salvar.type_keys("{ENTER}")
