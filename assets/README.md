# Imagens de referência (calibração)

Esta pasta guarda recortes de tela usados pelo reconhecimento de imagem
(`src/image_helpers.py`) para clicar em ícones do Superus que não têm
texto acessível. Eles **não vêm prontos** — precisam ser capturados uma
vez na máquina real onde o Superus roda, usando:

```
python scripts/capturar_icone.py <nome-do-arquivo.png>
```

Posicione o mouse sobre o ícone (sem clicar) antes da contagem regressiva
terminar.

## Arquivos necessários

| Arquivo | Onde fica | Passo do roteiro |
|---|---|---|
| `editar_escrituracao.png` | 2º botão da barra de ferramentas da grade de escriturações (ícone de "alterar escrituração selecionada") | Passo 2.2 |
| `sair_conferencia.png` | Ícone de "porta" no canto superior direito da tela **Conferência e ajustes** | Passo 2.12 |
| `exportar_excel.png` | Ícone do Excel na barra de ferramentas da pré-visualização do relatório | Passo 3.4 |

**Atenção especial ao `sair_conferencia.png`**: capture apenas o ícone da
tela de Conferência e ajustes, nunca o botão "Sair" da barra lateral da
janela **principal** do Superus — aquele fecha o sistema inteiro. O
código já restringe a busca desse ícone à área da janela de Conferência
(veja `_atualizar_data_final_e_reprocessar` em `src/apuracao_flow.py`),
mas a imagem certa ainda precisa ser a do ícone certo.
