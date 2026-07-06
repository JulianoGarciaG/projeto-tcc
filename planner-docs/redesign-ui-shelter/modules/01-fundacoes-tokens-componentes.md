# Objetivo

Criar `static/css/shelter.css` com os design tokens (paleta clara/escura),
tipografia, primitivas de forma e as classes de componente reutilizaveis
descritas no `DESIGN_BRIEF.md` (secoes 1 e 4), incluindo os overrides
necessarios sobre os componentes nativos do Bootstrap (form-control,
form-select, btn, table, modal, toast, alert) e do popup do Flatpickr para
que herdem os tokens e reajam ao dark mode. Nenhum template e alterado
neste modulo -- e apenas a fundacao CSS que os demais modulos vao consumir.

---

# Arquivos afetados

- `static/css/shelter.css` (novo arquivo)

---

## Documentacao relacionada

- docs/07_design_ui_ux.md
  Reescrever secoes 2 (Paleta de Cores) e 3 (Tipografia) com os novos
  tokens (`--canvas`, `--surface`, `--brand` etc., fonte Inter) e paleta
  clara/escura. Impacto: alto, e a base de toda a secao de design.

- CLAUDE.md
  Registrar a decisao de manter Bootstrap 5.3 (CSS+JS) e a introducao do
  arquivo `static/css/shelter.css` (substituindo `custom.css` como fonte de
  estilo) na secao "Stack" e em "ESTADO ATUAL" apos a rodada de redesign
  ser concluida (nao atualizar antes de todos os modulos estarem prontos).

---

# Dependencias

Nenhuma. Este e o modulo raiz de todo o redesign.

---

# Criterios de aceite

- [ ] `static/css/shelter.css` define `:root` com todos os tokens claros do
      brief (`--canvas`, `--surface`, `--sunken`, `--border`,
      `--border-strong`, `--ink`, `--muted`, `--brand`, `--brand-hover`,
      `--brand-soft`, `--graphite`, `--graphite-hi`, `--ok`/`--ok-bg`,
      `--danger`/`--danger-bg`, `--info`/`--info-bg`, `--warn`/`--warn-bg`,
      `--neu`/`--neu-bg`, `--shadow`, `--ph`).
- [ ] `[data-theme="dark"]` redefine os mesmos tokens com os valores escuros
      do brief.
- [ ] Fonte Inter (400/500/600/700/800) referenciada via Google Fonts,
      `font-feature-settings: 'tnum' 1` aplicado globalmente para numeros
      tabulares.
- [ ] Primitivas de forma implementadas: raio de cartao 10px, raio de
      inputs/botoes 8px, raio de badges/pills 100px, raio do segmented
      6-7px; sidebar 260px; topbar/header 64px; inputs 40-42px de altura
      (48-50px no Login); foco de input com borda 2px `--brand` +
      box-shadow `rgba(224,153,21,.16)`; labels 11-12px/700/uppercase/
      letter-spacing .04-.05em cor `--muted`.
- [ ] Classes de componente criadas e documentadas por comentario no
      proprio CSS: `.card` (com `.card-header`/`.card-body`), badge/pill de
      status (`.badge` + variantes ok/danger/info/warn/neu), botao primario
      laranja, botao graphite, botao outline, botoes de acao de linha
      (ver/editar/excluir), `.segmented` (wrapper + item ativo), input file
      dashed, `.table` (header sunken, th uppercase muted), empty-state
      (`bi-inbox` + texto muted centralizado), `.kpi-card`.
- [ ] Overrides aplicados sobre seletores nativos do Bootstrap para que
      sigam os tokens em ambos os temas: `.form-control`, `.form-select`,
      `.btn` (variantes usadas hoje), `.table`, `.modal-content`,
      `.modal-header`/`.modal-footer`, `.toast`, `.alert`, `.card` nativo
      (usado hoje em `imovel_list.html` para os cards com foto).
- [ ] **Estrategia de especificidade (Decisao 5 do plan.md) aplicada e
      comprovada:** onde o Bootstrap 5.3 expoe CSS var propria, o override
      redefine a var em vez de brigar por peso -- no minimo
      `--bs-body-bg`/`--bs-body-color` (canvas/ink), `--bs-border-color`
      (border), `--bs-secondary-color` (muted), `--bs-table-bg`/
      `--bs-table-color`/`--bs-table-border-color`, `--bs-btn-*` das
      variantes usadas, `--bs-modal-bg`, `--bs-toast-bg`. Redefinidas tambem
      dentro de `[data-theme="dark"]` para cobrir o tema escuro de uma vez.
- [ ] Para seletores Bootstrap com especificidade acima de classe unica
      (ex. `.table > :not(caption) > * > *`, `.form-control:focus`,
      `.btn-check:checked + .btn`), o override do Shelter usa um seletor de
      especificidade igual ou maior, com um comentario ao lado indicando qual
      regra Bootstrap ele neutraliza. Nenhum override depende so de "vir
      depois" quando a especificidade do alvo e maior.
- [ ] Uso de `!important` limitado a vencer utilitarios Bootstrap que ja tem
      `!important` proprio (`.text-muted`, `.bg-*`, `.d-*` etc.); cada
      ocorrencia listada em comentario. Nenhum `@layer` envolvendo o
      Bootstrap (ver Decisao 5).
- [ ] Overrides do popup do Flatpickr (`.flatpickr-calendar` e elementos
      internos) para o tema escuro.
- [ ] Placeholder hachurado (`--ph`) implementado como classe utilitaria
      para uso nos cards de imovel sem foto (consumido no modulo 06).
- [ ] `venv/Scripts/python manage.py check` continua passando (nenhuma
      mudanca de Python neste modulo, apenas checagem de sanidade).
- [ ] Nenhum template HTML foi alterado neste modulo.

---

# Riscos

- Nomear classes de forma que colidam com classes utilitarias do Bootstrap
  (ex.: reaproveitar `.card` nativo) exige cuidado para nao quebrar layouts
  existentes que dependem do `.card` do Bootstrap sem querer o novo visual
  antes dos demais modulos rodarem -- como nenhum template ainda referencia
  `shelter.css` neste modulo, o risco pratico e nulo ate o modulo 02 trocar
  o link do CSS.
- Overrides de dark mode em componentes Bootstrap (`.modal`, `.toast`) sao
  dificeis de validar sem os templates ligados a `shelter.css` -- validacao
  completa fica para o modulo 14.
