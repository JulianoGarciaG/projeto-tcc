---
name: handoff-documentation
description: Prepara e delega ao Documenter todas as informações necessárias para sincronizar a documentação após a conclusão de um módulo.
---

# Delegar Sincronização da Documentação

## Objetivo

Transferir ao Documenter apenas o contexto necessário para atualizar a documentação referente ao módulo recém-concluído.

Esta Skill encerra a responsabilidade de quem implementou sobre o módulo atual.

## Fluxo de execução

Execute as etapas abaixo na ordem apresentada.

1. Confirme que o módulo foi validado.
2. Identifique os arquivos modificados durante a implementação.
3. Identifique o `plan.md` correspondente.
4. Identifique o arquivo do módulo implementado.
5. Encaminhe essas informações ao Documenter.
6. Aguarde a conclusão da sincronização da documentação antes de prosseguir para o próximo módulo.

## Entradas

- `planner-docs/<feature>/plan.md`
- `planner-docs/<feature>/modules/<module>.md`
- Lista de arquivos modificados
- Resultado da validação do módulo

## Saídas

- Contexto preparado para o Documenter.
- Delegação concluída.

## Diretrizes

- Nunca atualize documentação.
- Nunca modifique arquivos `.md`.
- Nunca implemente código.
- Compartilhe apenas as informações necessárias para a sincronização da documentação.
- Aguarde a conclusão do Documenter antes de iniciar um novo módulo.

## Critérios de conclusão

A Skill é concluída quando:

- O contexto necessário foi entregue ao Documenter.
- A responsabilidade pela documentação foi transferida.
- A próxima janela de contexto está apta a iniciar o próximo módulo após o retorno do Documenter.