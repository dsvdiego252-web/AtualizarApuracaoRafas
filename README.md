# Automação de Apuração ICMS/IPI (SPED) — Superus

Automação da interface do Superus (`C:\Superus\Superus.exe`) que roda
localmente na máquina onde o Superus está instalado e repete, para cada
loja configurada, a rotina descrita no roteiro original:

1. Abre a tela **Fiscal/Contábil → SPED - EFD ICMS/IPI**.
2. Para cada loja, localiza a escrituração do mês corrente, atualiza a
   **Data Final** para o dia anterior à execução ("ontem") e reprocessa.
3. Gera os relatórios **Apuração de ICMS por CFOP** e **Apuração de ICMS
   por Alíquota** e salva sobre os arquivos `.xlsx` já existentes na pasta
   do mês.
4. Repete para todas as lojas configuradas (hoje: Loja 01 e Loja 03).

Feito com [pywinauto](https://pywinauto.readthedocs.io/) (controle nativo
de janelas/diálogos do Windows) e [pyautogui](https://pyautogui.readthedocs.io/)
como reforço para os poucos botões que são apenas ícones sem texto.

## ⚠️ Antes de rodar de verdade: isto precisa de calibração

O roteiro original descreve cliques em telas do Superus cujos nomes
internos de controles (grade, botões de ícone, títulos exatos de
algumas janelas) não são conhecidos de antemão — eles só existem na
máquina real. O código já está todo escrito e organizado para reproduzir
o roteiro passo a passo, mas alguns pontos estão marcados no código como
`SUPOSIÇÃO A CALIBRAR` e podem precisar de um pequeno ajuste na primeira
execução real. Isso é normal em automação de interfaces gráficas de
sistemas legados — a seção **Calibração** abaixo explica como validar e
corrigir cada ponto rapidamente.

## Pré-requisitos

- Windows, com o **Superus já instalado, aberto e logado** (login
  automatizado não é suportado — a automação assume que alguém já entrou
  no sistema).
- Python 3.10+ instalado na mesma máquina.
- A pasta do mês corrente já deve existir em
  `...\Ano - {ANO}\{MM} - {Mês} {AA}` com os 4 arquivos `.xlsx` do mês
  anterior (a rotina só **sobrescreve** arquivos existentes, nunca cria
  pasta ou arquivo novo).

## Instalação

```powershell
cd C:\Automacao\AtualizarApuracaoRafas   # pasta onde você colocou este projeto
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuração

Tudo fica em `config.yaml` — caminho do executável, pasta de destino dos
relatórios (com placeholders `{ano}`, `{mes:02d}`, `{mes_abrev}`,
`{ano_curto}`) e a lista de lojas (número no Superus, nome exibido na
grade, nomes dos dois arquivos `.xlsx`). Adicionar uma loja nova é só
acrescentar um item na lista `lojas:` — não precisa mexer em código.

## Calibração (primeira execução, na máquina real)

1. Com o Superus aberto e logado, capture os 3 ícones necessários (ver
   `assets/README.md` para a lista exata e o que cada um significa):

   ```powershell
   python scripts\capturar_icone.py editar_escrituracao.png
   python scripts\capturar_icone.py sair_conferencia.png
   python scripts\capturar_icone.py exportar_excel.png
   ```

2. Rode a automação em **modo assistido**, para uma loja só, com data
   fixa de teste, e acompanhe o log/screenshots em `logs/<timestamp>/`:

   ```powershell
   # em config.yaml, deixe execucao.modo_assistido: true temporariamente
   python run.py --loja 1
   ```

3. Se algo falhar com uma mensagem apontando para `SUPOSIÇÃO A CALIBRAR`
   ou pedindo para usar `scripts/calibrar_ui.py`, rode-o para inspecionar
   a árvore de controles da janela em questão e ajustar o seletor
   correspondente em `src/apuracao_flow.py` ou `src/win_helpers.py`:

   ```powershell
   python scripts\calibrar_ui.py "SPED"
   python scripts\calibrar_ui.py "Alteração de escritura"
   ```

4. Depois de validar as duas lojas com sucesso, volte
   `modo_assistido: false` em `config.yaml` para rodar 100% desassistido.

## Uso manual

```powershell
python run.py                  # todas as lojas configuradas
python run.py --loja 1         # só a loja de número 1
python run.py --data 30082026  # força a data de execução (útil para testar)
```

Cada execução grava um log detalhado e screenshots de cada etapa em
`logs/<data-hora>/execucao.log` — em caso de falha em qualquer loja, a
rotina segue para as demais e reporta um resumo no final; o código de
saída do processo é `0` se tudo deu certo e `1` se alguma loja falhou
(útil para o Agendador de Tarefas sinalizar erro).

## Rodar automaticamente (Agendador de Tarefas do Windows)

```powershell
cd scripts
.\agendar_tarefa_windows.ps1 -CaminhoProjeto "C:\Automacao\AtualizarApuracaoRafas"
```

Isso cria uma tarefa diária (horário padrão 07:30, ajustável com
`-Hora`). **Importante:** como a rotina controla a interface gráfica do
Superus, ela só funciona com o computador ligado, o usuário conectado
(sessão interativa) e o Superus já aberto e logado nesse horário — não
funciona em segundo plano nem com a tela bloqueada. Deixe o Superus
aberto com a sessão do Windows desbloqueada nos dias/horários em que a
tarefa deve rodar.

## Cuidados de segurança já embutidos no código

- **Nunca clica o "Sair" da janela principal do Superus** — o ícone de
  saída da tela de Conferência e ajustes é procurado apenas dentro da
  área daquela janela específica, nunca na tela toda (ver
  `_atualizar_data_final_e_reprocessar` em `src/apuracao_flow.py`).
- Antes de repetir uma ação que dependia de foco de tela, a rotina tira
  um novo screenshot em vez de repetir cegamente um clique.
- Toda falha interrompe apenas a loja em questão — as demais continuam
  sendo processadas — e fica registrada com screenshot em `logs/`.

## Estrutura do projeto

```
config.yaml                       # lojas, caminhos, parâmetros de execução
run.py                            # ponto de entrada (CLI)
src/
  config.py                       # carga de config.yaml + cálculo de datas/pastas
  logging_setup.py                # logging + screenshots por execução
  win_helpers.py                  # automação de janelas/diálogos nativos (pywinauto)
  image_helpers.py                # clique em ícones por reconhecimento de imagem
  apuracao_flow.py                # Passos 1-4 do roteiro, loja por loja
scripts/
  calibrar_ui.py                  # inspeciona a árvore de controles de uma janela
  capturar_icone.py               # captura um ícone da tela para assets/
  agendar_tarefa_windows.ps1      # registra a tarefa no Agendador do Windows
assets/                           # ícones de referência (capturados na calibração)
logs/                             # log + screenshots de cada execução
```
