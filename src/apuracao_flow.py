"""Fluxo da rotina de apuração ICMS/IPI no Superus.

Implementa, na ordem, os Passos 1–4 do roteiro original:
  1. Abrir a tela de escriturações (Fiscal/Contábil -> SPED - EFD ICMS/IPI).
  2. Para cada loja: atualizar a Data Final para "ontem" e reprocessar.
  3. Gerar e salvar os relatórios (CFOP e Alíquota) de cada loja.
  4. Repetir para todas as lojas configuradas.

Vários pontos dependem de detalhes da interface do Superus que não podem
ser confirmados sem rodar contra o app real (nomes exatos de janelas
internas, se a grade expõe o texto das linhas via UI Automation, etc.).
Esses pontos estão sinalizados com "SUPOSIÇÃO A CALIBRAR" nos comentários
— use scripts/calibrar_ui.py na máquina do Superus para validar/ajustar.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

from .config import Config, Loja, competencia_str, data_final_ddmmaaaa
from .image_helpers import clicar_icone
from .logging_setup import capturar_screenshot
from .win_helpers import (
    SuperusAutomationError,
    aguardar_janela,
    campo_apos_rotulo,
    clicar_botao,
    confirmar_dialogo,
    digitar_caminho_arquivo,
    digitar_data,
)

logger = logging.getLogger("apuracao_superus")

# SUPOSIÇÃO A CALIBRAR: título exato do menu/submenu no Superus.
CAMINHO_MENU_SPED = "Fiscal/Contábil->SPED - EFD ICMS/IPI"


def abrir_tela_sped(janela_principal):
    """Passo 1: abre a tela de escriturações do SPED - EFD ICMS/IPI."""
    janela_principal.set_focus()
    janela_principal.menu_select(CAMINHO_MENU_SPED)
    sped_win = aguardar_janela(r"SPED.*ICMS.*IPI", timeout=30)

    # SUPOSIÇÃO A CALIBRAR: tipo/classe real da grade. Tentamos alguns
    # candidatos comuns antes de desistir.
    grade = None
    for tentativa in (
        dict(control_type="Table"),
        dict(control_type="DataGrid"),
        dict(class_name_re=r"(?i)(grid|dbgrid)"),
    ):
        try:
            candidato = sped_win.child_window(**tentativa)
            candidato.wait("exists visible", timeout=3)
            grade = candidato
            break
        except Exception:
            continue
    if grade is None:
        raise SuperusAutomationError(
            "Não localizei a grade de escriturações na tela do SPED. Use "
            "scripts/calibrar_ui.py \"SPED\" na máquina real para descobrir a "
            "classe/tipo correto e ajuste abrir_tela_sped() em src/apuracao_flow.py."
        )
    return sped_win, grade


def _localizar_linha_grade(grade, loja: Loja, competencia_texto: str) -> bool:
    """Vai até o fim da grade (Ctrl+End) e sobe procurando a linha da
    loja/competência informadas, lendo o texto do item com foco.

    SUPOSIÇÃO A CALIBRAR: depende de a grade expor o texto da linha via UI
    Automation (window_text do item focado). Grades "pintadas" (owner-draw)
    podem não expor isso — nesse caso, ative modo_assistido em config.yaml
    para selecionar a linha manualmente na primeira calibração.
    """
    grade.set_focus()
    grade.type_keys("^{END}")
    time.sleep(0.3)
    for _ in range(60):
        texto_linha = ""
        try:
            item = grade.get_focus()
            texto_linha = item.window_text() if item else ""
        except Exception:
            pass
        if texto_linha and loja.nome_superus.upper() in texto_linha.upper() and competencia_texto in texto_linha:
            return True
        grade.type_keys("{UP}")
        time.sleep(0.15)
    return False


def _selecionar_linha_loja(grade, config: Config, loja: Loja, hoje) -> None:
    competencia_texto = competencia_str(hoje)
    encontrada = _localizar_linha_grade(grade, loja, competencia_texto)
    if encontrada:
        return
    if config.modo_assistido:
        logger.warning(
            "Não localizei automaticamente a linha da loja '%s' / competência %s. "
            "Selecione manualmente a linha correta na grade do Superus e pressione "
            "ENTER aqui no terminal para continuar.",
            loja.nome_superus,
            competencia_texto,
        )
        input()
        return
    raise SuperusAutomationError(
        f"Não localizei a linha da loja '{loja.nome_superus}' / competência "
        f"{competencia_texto} na grade. Ative 'modo_assistido: true' em "
        "config.yaml para calibrar manualmente, ou ajuste "
        "_localizar_linha_grade() em src/apuracao_flow.py."
    )


def _clicar_editar_escrituracao(sped_win, grade) -> None:
    """Clica o 2º botão da barra de ferramentas da grade ("alterar
    escrituração selecionada"). Tenta primeiro via UI Automation (toolbar
    + índice do botão); se não achar, cai para reconhecimento de imagem.
    """
    try:
        barra = sped_win.child_window(control_type="ToolBar")
        botoes = barra.children(control_type="Button")
        botoes[1].click_input()  # 2º botão, índice 1
        return
    except Exception:
        logger.debug("Não achei o botão via UI Automation — tentando por imagem.")
    clicar_icone("editar_escrituracao.png")


def _atualizar_data_final_e_reprocessar(sped_win, grade, config: Config, loja: Loja, hoje, pasta_execucao: Path) -> None:
    """Passo 2, para uma loja já com a linha selecionada na grade."""
    _clicar_editar_escrituracao(sped_win, grade)

    janela_alteracao = aguardar_janela(r"Alteração de escritura", timeout=15)
    campo_data_final = campo_apos_rotulo(janela_alteracao, r"Data Final")
    digitar_data(campo_data_final, data_final_ddmmaaaa(config, hoje))
    clicar_botao(janela_alteracao, r"(?i)^ok$")

    confirmar_dialogo(r"situação da escrituração retornará", botao_regex=r"(?i)^sim$", timeout=15)
    houve_pergunta = confirmar_dialogo(
        r"Deseja executar.*processamento", botao_regex=r"(?i)^sim$", timeout=15
    )
    if not houve_pergunta:
        raise SuperusAutomationError(
            "Não recebi a pergunta 'Deseja executar/agendar o processamento?' após "
            "salvar a alteração de escrituração — verifique o screenshot de erro."
        )

    janela_registros = aguardar_janela(r"Registros a serem processados", timeout=15)
    clicar_botao(janela_registros, r"(?i)^ok$")

    janela_confirmacao = aguardar_janela(r"Confirmação de execução", timeout=15)
    clicar_botao(janela_confirmacao, r"(?i)^ok$")

    logger.info("Aguardando processamento da loja '%s' (até %ss)...", loja.nome_superus, config.timeout_processamento_segundos)
    concluido = confirmar_dialogo(
        r"Processamento concluído", botao_regex=r"(?i)^sim$", timeout=config.timeout_processamento_segundos
    )
    if not concluido:
        capturar_screenshot(pasta_execucao, f"timeout_processamento_{loja.numero}")
        raise SuperusAutomationError(
            f"Processamento da loja '{loja.nome_superus}' não concluiu dentro do "
            f"tempo limite ({config.timeout_processamento_segundos}s)."
        )

    janela_conferencia = aguardar_janela(r"Conferência e ajustes", timeout=20)
    capturar_screenshot(pasta_execucao, f"conferencia_{loja.numero}")

    # Aviso condicional sobre "Total ICMS a recolher" — responder Não.
    confirmar_dialogo(r"Total ICMS a recolher", botao_regex=r"(?i)^n[aã]o$", timeout=5)

    # IMPORTANTE (segurança): o botão de sair aqui é o ícone de "porta" da
    # PRÓPRIA tela de Conferência e ajustes — nunca o "Sair" da barra
    # lateral da janela PRINCIPAL do Superus (aquele fecha o sistema
    # inteiro). Por isso restringimos a busca do ícone à região da janela
    # de Conferência, nunca à tela toda.
    regiao_conferencia = janela_conferencia.rectangle()
    regiao = (regiao_conferencia.left, regiao_conferencia.top, regiao_conferencia.width(), regiao_conferencia.height())
    clicar_icone("sair_conferencia.png", regiao=regiao)


def _gerar_relatorio(sped_win, grade, config: Config, loja: Loja, hoje, pasta_destino: Path, opcao_relatorio: str, nome_arquivo: str) -> None:
    """Passo 3: gera e salva um relatório (CFOP ou Alíquota) para a loja
    já selecionada na grade.
    """
    _selecionar_linha_loja(grade, config, loja, hoje)
    grade.set_focus()
    grade.type_keys("{F11}")

    janela_relatorios = aguardar_janela(r"Relatórios SPED ICMS.?IPI", timeout=15)
    opcao = janela_relatorios.child_window(title_re=opcao_relatorio)
    opcao.click_input()
    clicar_botao(janela_relatorios, r"(?i)^ok$")

    # SUPOSIÇÃO A CALIBRAR: título real da janela de pré-visualização.
    janela_preview = aguardar_janela(r"(Visualiza|Pré-visualiza|Preview)", timeout=30)
    regiao_preview = janela_preview.rectangle()
    regiao = (regiao_preview.left, regiao_preview.top, regiao_preview.width(), regiao_preview.height())
    clicar_icone("exportar_excel.png", regiao=regiao)

    dialogo_salvar = aguardar_janela(r"Salvar como", timeout=15)
    caminho_completo = str(pasta_destino / nome_arquivo)
    digitar_caminho_arquivo(dialogo_salvar, caminho_completo)
    confirmar_dialogo(r"já existe.*substitu", botao_regex=r"(?i)^sim$", timeout=10)

    janela_preview.set_focus()
    janela_preview.type_keys("{F9}")
    clicar_botao(janela_relatorios, r"(?i)^cancela$")


def processar_loja(sped_win, grade, config: Config, loja: Loja, hoje, pasta_destino: Path, pasta_execucao: Path) -> None:
    """Passos 2 e 3 completos para uma loja."""
    _selecionar_linha_loja(grade, config, loja, hoje)
    _atualizar_data_final_e_reprocessar(sped_win, grade, config, loja, hoje, pasta_execucao)

    _gerar_relatorio(
        sped_win, grade, config, loja, hoje, pasta_destino,
        opcao_relatorio=r"Apuração de ICMS por CFOP",
        nome_arquivo=loja.arquivo_cfop,
    )
    _gerar_relatorio(
        sped_win, grade, config, loja, hoje, pasta_destino,
        opcao_relatorio=r"Apuração de ICMS por Al[íi]quota",
        nome_arquivo=loja.arquivo_aliquota,
    )
    logger.info("Loja '%s' processada com sucesso.", loja.nome_superus)
