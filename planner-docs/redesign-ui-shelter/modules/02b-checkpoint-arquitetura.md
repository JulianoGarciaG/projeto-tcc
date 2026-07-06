# Objetivo

Gate de arquitetura (validacao shift-left) executado logo apos as fundacoes
(modulos 01 e 02), usando **uma unica tela real** como cobaia -- o proprio
Dashboard, por ser a tela que exercita simultaneamente o chrome novo, os
componentes de card/tabela/badge, o dark mode e o Chart.js. O objetivo e
provar as apostas arquiteturais do redesign ANTES de propaga-lo para as
outras 11 telas, para que um erro de fundacao seja corrigido com 1 tela
feita e nao com 13.

Este modulo NAO cria uma tela nova: ele conclui e estabiliza o reskin do
Dashboard (modulo 04) e o usa como banco de provas do que e transversal.

---

# Arquivos afetados

- Nenhum arquivo novo. Consolida `static/css/shelter.css` (01),
  `templates/base.html` + `static/js/theme.js` (02) e `templates/dashboard.html`
  (04). Correcoes descobertas aqui voltam para esses arquivos.

---

# Dependencias

- Modulo 01 (fundacoes).
- Modulo 02 (chrome + toggle de tema).
- Puxa o modulo 04 (dashboard) para frente: o Dashboard e implementado ate
  aqui justamente para servir de cobaia. Os demais modulos de tela (05-13)
  ficam BLOQUEADOS ate este checkpoint passar.

---

# Criterios de aceite (o gate)

Cada item abaixo corresponde a um dos riscos levantados na revisao do plano;
falhar em qualquer um bloqueia o inicio dos modulos 03-13.

- [ ] **Especificidade vs Bootstrap (risco 3):** no Dashboard renderizado,
      inspecionar no DevTools pelo menos: um `.btn` primario, um
      `.form-select`/`.form-control` da barra de filtros, o `.table` de
      lancamentos e um `.badge` de status -- confirmar que a regra vencedora
      na cascata e a do `shelter.css` (tokens), nao a do Bootstrap, em estado
      normal E em `:hover`/`:focus`. Nenhum override "perdendo" para o
      Bootstrap.
- [ ] **Sem FOUC (risco 1):** com o tema escuro salvo em localStorage,
      recarregar o Dashboard com throttling de rede (ex. "Slow 3G" no
      DevTools) e confirmar que NAO ha flash de fundo claro antes de
      escurecer -- prova que o `<script>` inline sincrono do `<head>` (modulo
      02) roda antes do primeiro paint. Repetir trocando de rota
      (Dashboard -> Login -> Dashboard).
- [ ] **Dark mode ponta a ponta (risco 1/3):** alternar o toggle e conferir
      no Dashboard: canvas, cards, texto, bordas, inputs/selects nativos,
      badges, `.table`, e os componentes Bootstrap presentes (toast de
      mensagem, se houver) trocam de tema coerentemente, sem "ilha" de cor
      antiga. Persistencia confirmada apos reload e apos fechar/reabrir o
      navegador.
- [ ] **Chart.js lendo CSS vars (risco 2):** confirmar que donut e barras
      renderizam com as cores dos tokens do tema ativo e que, ao acionar o
      toggle, ambos os graficos sao destruidos e recriados com as cores do
      novo tema (sem canvas duplicado, sem cor do tema anterior "presa").
      Alternar o tema 3+ vezes seguidas sem vazamento visual.
- [ ] **Integracao do evento de tema:** confirmar que `theme.js` (02) dispara
      `shelter:theme-changed` e que o `dashboard.html` (04) reage -- o
      contrato entre os dois modulos esta validado aqui, nao la no fim.
- [ ] `venv/Scripts/python manage.py check` e
      `venv/Scripts/python manage.py test imoveis` passando.
- [ ] Nenhuma view/form/model/signal/migration alterada (so
      `templates/**` e `static/**`).

---

# Saida do checkpoint

- **Passou:** liberar os modulos 03-13 (podem seguir em qualquer ordem/
  paralelo, cada um fazendo seu smoke check claro+escuro ao concluir).
- **Falhou:** as correcoes vao para os modulos 01/02/04 (fundacao), e o
  checkpoint e reexecutado. Nao iniciar as demais telas com a fundacao
  instavel.

---

# Riscos

- Tentacao de "pular" o gate para ganhar tempo -- e exatamente o atalho que
  o risco 6 (validacao tardia) pune: qualquer erro sistemico de
  especificidade, FOUC ou dark mode so reapareceria no modulo 14, ja
  multiplicado por 13 telas.
- O Dashboard e boa cobaia mas nao cobre 100% dos componentes (ex.: input
  file dashed do GED, segmented do laudo) -- estes seguem validados nos seus
  proprios modulos (07, 13); o checkpoint cobre o que e transversal a todas
  as telas.
