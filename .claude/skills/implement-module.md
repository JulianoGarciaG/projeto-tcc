---
name: validate-module
description: Valida se um módulo foi concluído conforme o plano técnico antes de permitir a sincronização da documentação.
---

# Validar Módulo

## Objetivo

Verificar se o módulo implementado está completo, consistente e apto para prosseguir para a etapa de documentação.

Esta Skill atua como o ponto de controle entre a implementação e a sincronização da documentação.

## Fluxo de execução

Execute as etapas abaixo na ordem apresentada.

1. Leia o `plan.md` para compreender o contexto da implementação.
2. Leia o arquivo do módulo correspondente.
3. Compare a implementação realizada com o objetivo do módulo.
4. Verifique se todos os critérios de aceite foram atendidos.
5. Confirme que as dependências do módulo foram respeitadas.
6. Verifique se não existem alterações fora do escopo do módulo.
7. Caso existam pendências, interrompa o fluxo e reporte-as.
8. Caso o módulo esteja concluído, autorize a sincronização da documentação.

## Entradas

- `planner-docs/<feature>/plan.md`
- `planner-docs/<feature>/modules/<module>.md`
- Código implementado
- Lista de arquivos modificados
- CLAUDE.md, quando necessário

## Saídas

- Status da validação:
  - Aprovado
  - Reprovado

- Lista objetiva de pendências, quando existirem.

## Diretrizes

- Valide apenas o módulo atual.
- Nunca implemente código durante a validação.
- Nunca altere o plano técnico.
- Nunca consulte módulos que não sejam dependências diretas do módulo atual.
- Utilize o CLAUDE.md apenas como referência para validar convenções do projeto.

## Critérios de conclusão

Um módulo é considerado concluído quando:

- Seu objetivo foi integralmente atendido.
- Todos os critérios de aceite foram satisfeitos.
- As dependências foram respeitadas.
- Não existem alterações fora do escopo.
- Não restam decisões técnicas pendentes.

Após a aprovação, o próximo passo do fluxo é delegar a sincronização da documentação ao Documenter.