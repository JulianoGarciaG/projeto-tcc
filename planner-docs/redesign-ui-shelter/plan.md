# Plano - Redesign Visual Completo do App Web "Shelter"

## Objetivo

Reskin completo da camada de template/CSS do app web (sidebar, topbar, login,
dashboard, listagens, detalhes, formularios), aplicando os design tokens e
padroes de `DESIGN_BRIEF.md` (paleta clara/escura, chrome graphite, cards,
badges, segmented, tabelas, empty-states) e adicionando dark mode persistido.

**Fora de escopo (nao tocar):** `imoveis/models.py`, `imoveis/views.py`,
`imoveis/forms.py`, `imoveis/signals.py`, qualquer migration, e
`templates/documentos/*` (PDFs gerados, Rodada 4 + fix visual).

Fonte de verdade visual: `planner-docs/redesign-ui-shelter/DESIGN_BRIEF.md`.

---

## Estado atual (investigado)

- **Chrome:** `templates/base.html` ja tem sidebar 260px + topbar fixa +
  toasts Bootstrap; grupos de menu (Cadastros/Operacoes/Documentos/
  Administracao) ja batem 1:1 com o brief -- so precisa de reskin, nao de
  reestruturacao.
- **CSS:** hoje so existe `static/css/custom.css` (667 linhas), com tokens
  antigos (`--color-primary` etc.), fonte Montserrat (substituta temporaria de
  Gotham) e paleta antiga (`#F2B441`/`#3A3A3A`/`#F7F3EA`). Documentado em
  `docs/07_design_ui_ux.md`.
- **Bootstrap 5.3** (CSS + JS bundle) e usado em toda a aplicacao:
  - Grid/utilitarios (`row`, `col-*`, `g-*`, `d-flex`, `gap-*`, `text-muted`,
    `small`, `mb-*`, `ms-auto` etc.) aparecem em todos os 24 templates de
    tela.
  - `imoveis/forms.py` grava as classes `form-control`/`form-select`
    diretamente nos widgets de ~9 ModelForms (fora de escopo alterar).
  - Bootstrap JS: `modal` (confirmacao de exclusao em 8 templates --
    `imovel_list`, `contrato_list`, `inquilino_list`, `laudo_list`,
    `proprietario_list`, `recibo_list`, `lancamento_list`, `imovel_detail`
    notificacoes) e `toast` (mensagens flash em `base.html`). Nao ha uso de
    `collapse`/`dropdown`/`accordion` em nenhum template.
- **Chart.js 4.4.4** ja e usado no dashboard (via CDN), com 1 donut + 1 barras
  -- estrutura ja bate com o brief, mas as cores estao hardcoded em hex
  direto no script do `dashboard.html`, sem ler CSS vars nem redesenhar no
  toggle de tema.
- **Flatpickr/IMask** ja inicializados globalmente via `static/js/masks.js`
  por atributos `data-flatpickr`/`data-mask` -- nenhuma mudanca de
  comportamento necessaria, so CSS do popup do Flatpickr para dark mode.
- **Listagem de Imoveis** (`imovel_list.html`) so tem a vista Cards hoje;
  a vista Tabela do brief nao existe e precisa ser criada. As demais
  listagens (`contrato_list`, `inquilino_list`, `laudo_list`,
  `proprietario_list`, `recibo_list`, `lancamento_list`) ja sao so tabela.
- **Login** (`templates/login.html`) ja e um layout dedicado (nao estende
  `base.html`), estrutura split ja bate com o brief -- e reskin, nao
  reestruturacao.
- **GED** (`templates/ged/documentos.html`) e uma tela propria (grid de 5
  cards com tabela interna cada), nao se encaixa em nenhum dos 5 arquetipos
  de referencia do brief -- tratado como modulo proprio reaproveitando os
  componentes card/table/badge das fundacoes.
- **Telas de detalhe** (`imovel_detail`, `contrato_detail`, `laudo_detail`,
  `recibo_detail`) ja seguem o padrao do brief quase 1:1: action bar de
  botoes condicionais por status, cards com dl label-valor, tabelas filhas
  com empty-state. `contrato_detail.html` ja lista as versoes do GED
  versionado e os 4 blocos de upload (`contrato_anexar_documento`).
- **Formularios** simples (imovel, proprietario, inquilino, contrato,
  notificacao, renovacao, distrato, recibo, lancamento) sao so 1 card com
  grid de campos -- reskin mecanico. `laudo_form.html` e o unico complexo:
  formset de itens de vistoria (estado via select do Django, sem segmented
  control hoje) + formset dinamico de testemunhas + JS de contrato
  dependente do imovel (`contratos_por_imovel_json`) -- nao alterar essa
  logica, so o visual.

---

## Decisao de arquitetura 1 - Bootstrap fica

**Recomendacao: manter Bootstrap 5.3 (CSS + JS bundle), sobrepondo 100% do
visual com os novos tokens/componentes.** Nao remover.

Justificativa:
1. `imoveis/forms.py` (fora de escopo) grava classe `form-control` /
   `form-select` em dezenas de widgets -- os campos gerados por
   `{{ form.campo }}` sempre terao essas classes. Remover Bootstrap
   quebraria a unica forma de estiliza-los sem tocar em forms.py.
2. Utilitarios de grid/layout Bootstrap (row/col-*/g-*/d-flex/gap/
   text-muted/small/mb-* etc.) aparecem em todos os 24 templates --
   reescreve-los seria uma reescrita completa de markup, nao um reskin,
   com risco de regressao muito maior que o pedido.
3. Bootstrap JS so e usado para `modal` (confirmacao de exclusao) e
   `toast` (flash messages) -- ambos os padroes continuam no design (o
   brief nao pede remove-los), so precisam de reskin visual via CSS
   (`.modal-content`, `.toast`, `.btn-close` etc.).
4. Essa e a mesma estrategia ja usada desde a Rodada 1 (`custom.css` ja
   sobrescreve `.btn-primary`, `.form-control`, `.table thead th` etc.) --
   o redesign estende essa pratica com tokens/paleta novos, dark mode e
   componentes novos (segmented, empty-state, input dashed), sem trocar o
   motor.

## Decisao de arquitetura 2 - novo arquivo static/css/shelter.css

Criar `static/css/shelter.css` do zero (tokens + overrides de Bootstrap +
componentes) em vez de remendar `custom.css` incrementalmente -- a paleta,
os nomes de variavel e a tipografia mudam por completo (Montserrat para
Inter; `--color-primary` para `--brand`; adicao de dark mode). Modulo 01
detalha o conteudo; modulos seguintes trocam o link em `base.html` e
`login.html` de `custom.css` para `shelter.css`. `custom.css` deixa de ser
referenciado (decisao de manter ou apagar o arquivo fica com quem
implementar/usuario -- o plano nao exige apaga-lo).

## Decisao de arquitetura 3 - Dark mode

`data-theme` no elemento html (nao no body), aplicado o mais cedo possivel
(script inline no head, antes do CSS pintar, para evitar flash de tema
errado) lendo localStorage. Toggle fica no topbar (novo botao, nao existe
hoje). Overrides de componentes nativos do Bootstrap (`.modal-content`,
`.toast`, `.alert`) e do popup do Flatpickr (`.flatpickr-calendar`) entram
como CSS no proprio `shelter.css` (modulo 01), lidos via seletor de tema
escuro. Chart.js precisa ser redesenhado (destroy + new Chart) quando o
tema muda -- tratado no modulo do dashboard, ouvindo um evento customizado
disparado pelo script de toggle.

## Decisao de arquitetura 4 - Toggle Cards/Tabela (Imoveis)

JS vanilla dedicado (`static/js/imovel-view-toggle.js`), sem framework,
alternando a exibicao de dois containers (cards/tabela) e persistindo a
escolha em localStorage. Exclusivo de `imovel_list.html` (as demais
listagens so tem vista tabela, conforme o brief).

## Decisao de arquitetura 5 - Estrategia de especificidade CSS vs Bootstrap

O risco de os overrides do `shelter.css` perderem para as classes nativas do
Bootstrap (que trazem seletores com modificadores de maior peso, ex.
`.btn-primary`, `.form-control:focus`, `.table > :not(caption) > * > *`) e
real e precisa de uma regra explicita -- nao basta "sobrescrever". Estrategia
obrigatoria (detalhada no modulo 01):

1. **Ordem de carga:** o `<link>` do `shelter.css` vem DEPOIS do bundle do
   Bootstrap em `base.html`/`login.html` -- em empate de especificidade, o
   ultimo declarado vence.
2. **Casar/superar a especificidade do alvo:** cada override deve espelhar a
   especificidade real do seletor Bootstrap que combate (ex.: para vencer
   `.table > :not(caption) > * > *` usa-se um seletor equivalente, nao apenas
   `.table td`). Documentar no CSS, ao lado de cada bloco, qual seletor
   Bootstrap ele neutraliza.
3. **Preferir tokens a `!important`:** onde o Bootstrap usa CSS var propria
   (ex. `--bs-body-color`, `--bs-border-color`, `--bs-table-bg`,
   `--bs-btn-*`), redefinir a var do Bootstrap com o token do Shelter em vez
   de brigar por especificidade -- e o caminho mais limpo e cobre estados
   (hover/focus/disabled) de uma vez.
4. **`!important` so como ultimo recurso** e restrito a utilitarios do
   Bootstrap com `!important` proprio (ex. `.text-muted`, `.bg-*`, `.d-*`),
   que so podem ser vencidos por outro `!important`. Listar cada uso no CSS.
5. **Nao usar `@layer`** para embrulhar o Bootstrap (o bundle via CDN nao esta
   em layer; envolver so o `shelter.css` em layer o rebaixaria e pioraria o
   problema).

Consequencia de processo: essa estrategia e a primeira coisa validada no
checkpoint (modulo 02b), numa tela real, antes de propagar para as demais.

---

## Inventario de templates e modulo responsavel

| Template | Modulo |
|---|---|
| `templates/base.html` | 02 |
| `templates/login.html` | 03 |
| `templates/dashboard.html` | 04 |
| `templates/contratos/contrato_list.html` | 05 |
| `templates/inquilinos/inquilino_list.html` | 05 |
| `templates/proprietarios/proprietario_list.html` | 05 |
| `templates/laudos/laudo_list.html` | 05 |
| `templates/recibos/recibo_list.html` | 05 |
| `templates/financeiro/lancamento_list.html` | 05 |
| `templates/imoveis/imovel_list.html` | 06 |
| `templates/ged/documentos.html` | 07 |
| `templates/imoveis/imovel_detail.html` | 08 |
| `templates/contratos/contrato_detail.html` | 09 |
| `templates/laudos/laudo_detail.html` | 10 |
| `templates/recibos/recibo_detail.html` | 11 |
| `templates/imoveis/imovel_form.html` | 12 |
| `templates/imoveis/notificacao_form.html` | 12 |
| `templates/inquilinos/inquilino_form.html` | 12 |
| `templates/proprietarios/proprietario_form.html` | 12 |
| `templates/contratos/contrato_form.html` | 12 |
| `templates/contratos/renovacao_form.html` | 12 |
| `templates/contratos/distrato_form.html` | 12 |
| `templates/recibos/recibo_form.html` | 12 |
| `templates/financeiro/lancamento_form.html` | 12 |
| `templates/laudos/laudo_form.html` | 13 |
| `static/css/shelter.css` (novo) | criado no 01, consumido nos demais |
| `static/js/theme.js` (novo) | 02 |
| `static/js/imovel-view-toggle.js` (novo) | 06 |
| `templates/documentos/*` (PDFs) | fora de escopo -- nao tocar |

---

## Resumo dos modulos

01. Fundacoes - tokens e componentes CSS - cria `static/css/shelter.css`
    com paleta clara/escura, tipografia (Inter), primitivas de forma e
    classes de componente (card, badge, botoes, segmented, table,
    empty-state, input-dashed, kpi-card), incluindo overrides dark de
    Bootstrap nativo e do Flatpickr. Nenhum template e tocado ainda.
02. Chrome - sidebar, topbar e toggle de tema - reskin de `base.html` +
    novo `static/js/theme.js`.
02b. Checkpoint de arquitetura (shift-left) - valida numa unica tela real
    (o proprio Dashboard, ja com chrome + graficos) as 4 apostas
    arquiteturais (especificidade vs Bootstrap, ausencia de FOUC, dark mode
    ponta a ponta, Chart.js lendo CSS vars) ANTES de propagar o reskin para
    as outras 11 telas. Gate obrigatorio: se falhar, corrige-se a fundacao
    (01/02) antes de seguir. Sem esse gate, um erro de fundacao so
    apareceria no modulo 14, ja com 13 telas feitas.
03. Login - reskin de `login.html`.
04. Dashboard - KPIs e graficos - reskin de `dashboard.html` + migracao do
    Chart.js para ler CSS vars e redesenhar no toggle de tema.
05. Listagens padrao (tabela) - reskin dos 6 templates de listagem simples
    (contratos, inquilinos, proprietarios, laudos, recibos, lancamentos).
06. Listagem de Imoveis - Cards + Tabela - reskin dos cards + criacao da
    vista tabela + segmented toggle + JS de persistencia.
07. GED - Documentos - reskin de `ged/documentos.html`.
08. Detalhe - Imovel - reskin de `imovel_detail.html`.
09. Detalhe - Contrato - reskin de `contrato_detail.html`.
10. Detalhe - Laudo - reskin de `laudo_detail.html`.
11. Detalhe - Recibo - reskin de `recibo_detail.html`.
12. Formularios - CRUD simples - reskin dos 9 formularios de card unico
    (imovel, notificacao, inquilino, proprietario, contrato, renovacao,
    distrato, recibo, lancamento).
13. Formulario - Laudo (checklist e testemunhas) - reskin de
    `laudo_form.html`, incluindo o segmented control Bom/Regular/Ruim
    sobre o select existente e o formset dinamico de testemunhas.
14. Validacao cruzada - temas e responsividade - checklist manual final
    (claro/escuro x mobile/desktop) em todas as telas, sem codigo novo.

## Ordem de implementacao e dependencias

- 01 fundacoes -- sem dependencias.
- 02 chrome + toggle de tema -- depende de 01.
- 02b checkpoint de arquitetura -- depende de 01, 02. **Gate**: nenhum dos
  modulos 03 a 13 deve comecar antes de 02b passar (evita retrabalho em massa
  se uma decisao de fundacao estiver errada).
- 03 login -- depende de 01, 02 e do gate 02b (independente do restante de 02).
- 04 dashboard -- depende de 01, 02 (o proprio 02b usa o dashboard como
  cobaia, entao 04 e concluido/estabilizado junto do checkpoint).
- 05 listagens padrao -- depende de 01, 02.
- 06 listagem imoveis -- depende de 01, 02.
- 07 GED -- depende de 01, 02.
- 08 detalhe imovel -- depende de 01, 02.
- 09 detalhe contrato -- depende de 01, 02.
- 10 detalhe laudo -- depende de 01, 02.
- 11 detalhe recibo -- depende de 01, 02.
- 12 formularios simples -- depende de 01, 02.
- 13 formulario laudo -- depende de 01, 02, 12.
- 14 validacao cruzada -- depende de TODOS os modulos anteriores.

Modulos 03 a 13 sao mutuamente independentes entre si (podem ser
implementados em qualquer ordem ou em paralelo) uma vez que 01 e 02 estejam
concluidos -- exceto 13, que depende de 12 apenas para reaproveitar a
convencao de card/footer sticky de formulario (nao ha dependencia de
arquivo).

---

## Observacoes gerais

- Nenhum model/view/form/signal/migration e alterado em nenhum modulo --
  cada modulo lista explicitamente "Arquivos afetados" e todos sao
  templates html e arquivos static css/js.
- Regra de encoding do projeto: templates so podem ser editados com o Edit
  tool (nunca Get-Content/Set-Content do PowerShell) -- vale para todos os
  modulos.
- `templates/documentos/*` (PDFs) permanece intocado em todos os modulos.
- Cada modulo e auto-contido: deve ser possivel implementa-lo (numa janela de
  contexto regular do Claude Code, sem subagente dedicado) lendo apenas
  CLAUDE.md, este plan.md, o DESIGN_BRIEF.md (para a especificacao visual da
  tela especifica) e o proprio modulo.
- **Validacao shift-left:** a verificacao NAO fica concentrada so no fim. O
  modulo 02b e um gate de arquitetura logo apos a fundacao, e cada modulo de
  tela (03 a 13) so e dado por concluido apos um smoke check da propria tela
  nos dois temas (claro/escuro) e nos dois breakpoints -- nao se acumula
  divida visual para o modulo 14. O modulo 14 passa a ser a validacao
  cruzada final (regressao entre telas), nao a primeira vez que alguem olha
  cada tela.
- Modulo 14 nao gera codigo -- e o checklist de validacao manual final,
  seguindo o mesmo padrao usado em rodadas anteriores (ex.:
  `planner-docs/fix-visual-pdfs-gerados/modules/05-validacao-visual-manual.md`).
