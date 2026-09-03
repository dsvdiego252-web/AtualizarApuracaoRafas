# Passo a passo — Automação de Apuração Superus

Guia para instalar e rodar esta automação no computador onde o Superus
está instalado. Siga na ordem.

---

## 1. Extrair os arquivos

Extraia o arquivo `.zip` que você baixou em uma pasta fácil de achar, por
exemplo `C:\Automacao\ApuracaoSuperus`. Todos os passos abaixo assumem
que você vai abrir o **PowerShell dentro dessa pasta**.

Para abrir o PowerShell já dentro da pasta: abra a pasta no Explorador de
Arquivos, clique na barra de endereço, digite `powershell` e pressione
Enter.

---

## 2. Instalar o Python (se ainda não tiver)

1. Baixe em: https://www.python.org/downloads/windows/ (botão amarelo
   "Download Python 3.x.x").
2. Rode o instalador. **Marque a caixinha "Add python.exe to PATH"** na
   primeira tela antes de clicar em "Install Now" — isso é importante,
   sem isso os comandos abaixo não funcionam.
3. Para conferir que instalou certo, no PowerShell digite:
   ```
   python --version
   ```
   Deve aparecer algo como `Python 3.12.x`.

---

## 3. Instalar as dependências do projeto

No PowerShell, dentro da pasta do projeto:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Isso pode demorar um ou dois minutos. Se der erro de "não é possível
executar scripts" no `activate`, rode antes:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
e tente o `.venv\Scripts\activate` de novo.

---

## 4. Conferir o arquivo `config.yaml`

Abra `config.yaml` (pode ser com o Bloco de Notas) e confira:

- `executavel:` → o caminho do Superus está certo? (padrão:
  `C:\Superus\Superus.exe`)
- `pasta_relatorios: padrao:` → o caminho da pasta onde ficam os
  relatórios está certo?
- `lojas:` → as lojas e nomes dos arquivos `.xlsx` estão certos?

Só mexa aqui se algo estiver diferente do que você usa hoje. Se estiver
tudo igual ao que já é usado, pode pular este passo.

---

## 5. Abrir e logar no Superus

Abra o Superus manualmente e faça login, como você já faz normalmente.
**A automação não faz login sozinha** — ela espera encontrar o Superus já
aberto.

---

## 6. Capturar os 3 ícones (só na primeira vez)

A automação precisa "aprender" a aparência de 3 botões que são só ícone
(sem texto). Ainda no PowerShell (com `.venv` ativado, do passo 3), rode
um comando de cada vez:

```powershell
python scripts\capturar_icone.py editar_escrituracao.png
```
→ Depois de rodar o comando, você tem uns 4 segundos: passe o mouse (sem
clicar) por cima do **2º botão da barra de ferramentas da grade de
escriturações** (o ícone de "alterar escrituração selecionada", na tela
SPED - EFD ICMS/IPI) e espere a contagem terminar.

```powershell
python scripts\capturar_icone.py sair_conferencia.png
```
→ Passe o mouse sobre o **ícone de "porta" no canto superior direito da
tela "Conferência e ajustes"** (⚠️ não confunda com o botão "Sair" da
barra lateral da janela principal do Superus — aquele fecha o sistema
inteiro; o ícone certo é só o da telinha de Conferência).

```powershell
python scripts\capturar_icone.py exportar_excel.png
```
→ Passe o mouse sobre o **ícone do Excel** na barra de ferramentas da
pré-visualização de um relatório (abra qualquer relatório do SPED,
clique no ícone de impressora/F11, escolha uma opção e OK para ver essa
telinha de pré-visualização).

Se você não tiver certeza de qual ícone é qual, me manda um print da
tela que eu te mostro exatamente onde é.

---

## 7. Primeiro teste (modo assistido, uma loja só)

1. Abra `config.yaml` de novo e mude a linha:
   ```yaml
   modo_assistido: false
   ```
   para:
   ```yaml
   modo_assistido: true
   ```
   Salve o arquivo.

2. No PowerShell, rode:
   ```powershell
   python run.py --loja 1
   ```

3. Acompanhe o que acontece na tela. Se tudo correr bem, o terminal
   termina mostrando `Loja 'APFARIA - MATRIZ' processada com sucesso.` e
   depois um resumo com `OK`.

4. **Se der erro**: o terminal mostra uma mensagem em vermelho explicando
   o que faltou. Não se preocupe — isso é esperado na primeira vez (a
   automação precisa de pequenos ajustes finos que só aparecem testando
   na tela real). Me manda:
   - o texto do erro que apareceu no terminal, e
   - a pasta `logs\<data-e-hora-da-execução>` inteira (tem um arquivo
     `execucao.log` e prints de tela de cada etapa).

   Com isso eu ajusto o código e te devolvo a correção.

5. Repita o teste para a outra loja:
   ```powershell
   python run.py --loja 3
   ```

---

## 8. Rodar valendo (sem parar para confirmar)

Depois que a Loja 1 e a Loja 3 rodarem certinho no passo 7, volte o
`config.yaml` para:
```yaml
modo_assistido: false
```

E rode as duas de uma vez:
```powershell
python run.py
```

---

## 9. Deixar rodando sozinho todo dia

Para não precisar abrir o PowerShell manualmente:

```powershell
cd scripts
.\agendar_tarefa_windows.ps1 -CaminhoProjeto "C:\Automacao\ApuracaoSuperus"
```

(troque o caminho pelo lugar onde você extraiu o projeto no passo 1).

Isso cria uma tarefa no Agendador de Tarefas do Windows que roda todo dia
às 07:30 (dá para mudar o horário com `-Hora "08:00"` no mesmo comando,
por exemplo).

**Único cuidado**: nesse horário, o computador precisa estar ligado, você
(ou alguém) precisa estar logado no Windows com a tela desbloqueada, e o
Superus já aberto e logado — a automação clica na tela de verdade, então
não funciona com o computador desligado, hibernando ou com a tela
travada.

---

## Resumo rápido (depois de já calibrado uma vez)

No dia a dia, para rodar manualmente quando quiser:
```powershell
cd C:\Automacao\ApuracaoSuperus
.venv\Scripts\activate
python run.py
```
