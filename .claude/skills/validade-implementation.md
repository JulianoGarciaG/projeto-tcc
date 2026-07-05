---
name: validate-implementation
description: Valida se um módulo foi implementado corretamente antes de considerá-lo concluído.
---

# Validar Implementação

## Objetivo

Verificar se o módulo implementado atende integralmente ao plano definido pelo Planner antes que ele seja considerado concluído.

Esta Skill realiza uma validação técnica da implementação, sem modificar o código.

## Fluxo de execução

Execute as etapas abaixo na ordem apresentada.

1. Revise o módulo correspondente no plano técnico.
2. Compare a implementação realizada com o objetivo do módulo.
3. Verifique se todos os critérios de aceite foram atendidos.
4. Confirme que apenas arquivos relacionados ao módulo foram alterados.
5. Identifique inconsistências, omissões ou alterações fora do escopo.
6. Caso existam pendências, reporte-as de forma objetiva.
7. Caso tudo esteja correto, considere o módulo validado.

## Entradas

- Plano técnico do Planner.
- Código implementado.
- Lista de arquivos modificados.
- CLAUDE.md, quando necessário para consulta de convenções.

## Saídas

- Status da validação (Aprovado ou Reprovado).
- Lista de pendências encontradas, quando existirem.

## Diretrizes

- Nunca altere o código durante a validação.
- Nunca implemente funcionalidades faltantes.
- Nunca modifique o plano técnico.
- Considere apenas o módulo em análise.
- Valide somente requisitos explicitamente definidos pelo Planner.
- Utilize as convenções do projeto apenas como referência de conformidade.

## Critérios de conclusão

A validação é concluída quando:

- Todos os critérios de aceite forem atendidos.
- Não houver alterações fora do escopo do módulo.
- Não existirem inconsistências relevantes entre o plano e a implementação.