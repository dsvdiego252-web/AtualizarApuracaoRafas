<#
.SYNOPSIS
    Registra a rotina de apuração Superus no Agendador de Tarefas do Windows.

.DESCRIPTION
    Cria uma tarefa que roda run.py diariamente em um horário configurável.
    A tarefa só funciona com o usuário conectado e a tela desbloqueada,
    pois a rotina controla a interface gráfica do Superus — não é possível
    rodar em segundo plano/sessão 0 nem com a tela bloqueada.

.PARAMETER Hora
    Horário de disparo, formato HH:mm (padrão 07:30).

.PARAMETER CaminhoProjeto
    Pasta onde este projeto está (contendo run.py e config.yaml).

.PARAMETER CaminhoPython
    Caminho do interpretador Python a usar (padrão: "python" do PATH).

.EXAMPLE
    .\agendar_tarefa_windows.ps1 -CaminhoProjeto "C:\Automacao\AtualizarApuracaoRafas"
#>
param(
    [string]$Hora = "07:30",
    [Parameter(Mandatory = $true)][string]$CaminhoProjeto,
    [string]$CaminhoPython = "python",
    [string]$NomeTarefa = "Apuracao Superus - Loja 01 e 03"
)

$acao = New-ScheduledTaskAction -Execute $CaminhoPython -Argument "run.py" -WorkingDirectory $CaminhoProjeto
$gatilho = New-ScheduledTaskTrigger -Daily -At $Hora
$configuracoes = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Hours 1)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $NomeTarefa -Action $acao -Trigger $gatilho `
    -Settings $configuracoes -Principal $principal -Force

Write-Host "Tarefa '$NomeTarefa' agendada para rodar todo dia às $Hora."
Write-Host ""
Write-Host "IMPORTANTE: o computador precisa estar ligado, com o usuario $env:USERNAME"
Write-Host "conectado (sessao interativa) e o Superus ja aberto e logado nesse"
Write-Host "horario -- a rotina controla a interface do Superus e nao funciona"
Write-Host "em segundo plano nem com a tela bloqueada."
