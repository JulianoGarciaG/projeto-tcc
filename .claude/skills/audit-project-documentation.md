---
name: audit-project-documentation
description: Analisa toda a base de código e a documentação existente para reconstruir, reorganizar e sincronizar a documentação técnica do projeto.
---

# Auditoria Geral da Documentação

## Objetivo

Realizar uma auditoria completa do projeto para garantir que a documentação represente fielmente o estado atual do código.

Esta Skill deve ser utilizada durante a criação inicial da documentação, grandes refatorações ou sempre que a documentação estiver significativamente desatualizada.

Ao contrário da sincronização incremental, esta Skill possui autorização para reorganizar toda a estrutura documental do projeto.

## Fluxo de execução

Execute as etapas abaixo na ordem apresentada.

1. Leia o `CLAUDE.md`.
2. Analise a estrutura completa do projeto.
3. Identifique os principais componentes da arquitetura.
4. Leia toda a documentação existente.
5. Compare documentação e código.
6. Identifique documentos obsoletos.
7. Identifique informações ausentes.
8. Identifique oportunidades de reorganização da documentação.
9. Atualize, mova, renomeie, crie ou remova documentos quando necessário.
10. Garanta que toda documentação esteja consistente entre si antes de concluir.

## Entradas

- CLAUDE.md
- Código-fonte completo
- Diretório `/docs`

## Saídas

- Documentação sincronizada.
- Estrutura documental reorganizada.
- Relatório resumido das alterações realizadas.

## Diretrizes

- Considere o código como fonte de verdade.
- Utilize o CLAUDE.md como referência arquitetural.
- Não preserve documentos apenas por existirem.
- Elimine duplicações.
- Consolide documentos redundantes.
- Divida documentos excessivamente grandes quando necessário.
- Crie novos documentos sempre que melhorar a organização.
- Renomeie documentos para refletirem melhor seu conteúdo.
- Remova documentos sem utilidade ou completamente obsoletos.
- Preserve uma organização simples e consistente.
- Nunca modifique código.

## Critérios de conclusão

A auditoria é concluída quando:

- Toda documentação representa corretamente o estado atual do projeto.
- Não existirem documentos redundantes.
- Não existirem documentos obsoletos.
- A estrutura documental estiver organizada de forma lógica.
- Toda informação possuir um único local de manutenção.