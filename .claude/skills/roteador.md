---
name: roteador
description: >-
  Use no INÍCIO de qualquer tarefa nova de implementação, antes de escrever
  código, para escolher a abordagem certa: prompt direto, Plan Mode + opusplan,
  ou o subagente Planner. Dispare quando o usuário trouxer uma feature, um
  brief, um bug não-trivial, ou perguntar "como devo fazer / por onde começo /
  qual abordagem". Não dispare no meio de uma implementação já em curso.
---

# Roteador de abordagem

Confirme a abordagem contra o **código real** (não contra o palpite do brief).
A rota vinda do brief de enquadramento é provisória; o escopo real manda.

## Como decidir

1. Varra o escopo real (Grep/Glob/Read ou subagente Explore). Conte os arquivos
   que a mudança realmente toca.
2. Escolha:

| Escopo real | Rota |
|---|---|
| 1-3 arquivos, isolado (CRUD, campo novo, template/CSS) | **Prompt direto.** Sem Plan Mode — é overhead aqui. |
| ~4 a ~10 arquivos, feature coesa, cabe em uma sessão | **Plan Mode + `/model opusplan`.** Rota padrão. |
| ~15+ arquivos, OU implementação em várias sessões/dias/pessoas | **Subagente Planner.** Só aqui a estrutura em disco se paga. |

3. Se o escopo real divergir do brief, **troque de rota** e avise em uma linha.

## Regras

- Na dúvida entre prompt direto e Plan Mode, prefira Plan Mode: planejar em
  read-only custa menos que codar, descobrir problema, desfazer e refazer.
- Na dúvida entre Plan Mode e Planner, prefira Plan Mode. O Planner só vence
  quando a tarefa **não cabe em uma sessão** — não por número de arquivos, mas
  por durabilidade (sobreviver ao fim da sessão) ou coordenação entre janelas.
- Ao usar Plan Mode, peça o plano com especificidade: arquivos a editar, funções
  alteradas em cada um, ordem de operações. Plano vago vira parágrafo inútil.
- Ao terminar a implementação, rode a skill `validate-implementation`.
