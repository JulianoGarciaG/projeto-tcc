# 04 — Design & UI/UX
> Sistema Integrado de Gestão Imobiliária

---

## 1. Identidade Visual

**Empresa:** Shelter

![Logo Shelter](../static/assets/Shelter_LOGO.svg)

### Diretrizes de Aplicação da Logo

| Contexto | Arquivo | Observações |
|---|---|---|
| Sidebar (topo, sempre expandida) | `Shelter_LOGO_white.svg` | Sobre fundo `--graphite`; centralizada no header de 64px (`width: 90%`, `object-fit: contain`) |
| Login (painel esquerdo) | `Shelter_LOGO_white.svg` | Sobre fundo escuro `#3A3A3A` |
| PDFs (`templates/documentos/base_pdf.html`) | `Shelter_LOGO.jpg` | Versão rasterizada, compatível com xhtml2pdf |
| Favicon (`<link rel="icon">` em `base.html`/`login.html`) | `Shelter_ICON.svg` | Apenas o símbolo gráfico dourado (4 losangos), recortado do `Shelter_LOGO.svg` original — sem wordmark |

> Os arquivos da logo estão em `static/assets/` (`Shelter_LOGO.svg`, `Shelter_LOGO_white.svg`, `Shelter_LOGO.jpg`, `Shelter_LOGO_white.jpg`, `Shelter_ICON.svg`).
> Nunca distorcer proporções. Nunca aplicar sobre fundos que conflitem com `#F2B441` ou `#3A3A3A`.

### Personalidade
O sistema deve transmitir uma experiência **moderna e limpa** — interface sem ruído visual, foco no conteúdo, espaçamento generoso e hierarquia clara.

---

## 2. Paleta de Cores

> **Redesign "Shelter" (redesign-ui-shelter):** a paleta do app web migrou para um sistema de **tokens (CSS custom properties)** com dois temas — claro (`:root`) e escuro (`[data-theme="dark"]`) — definidos em `static/css/shelter.css`. O tema é alternável em runtime pelo toggle da topbar (ver seções 5–6). O legado `--color-*` (`custom.css`) sobrevive apenas na **página de Login** (`templates/login.html`), até a migração do módulo 03. Os **PDFs gerados** (`templates/documentos/`) mantêm sua própria paleta de marca (ver seção 17), fora do escopo deste redesign.

### Tokens de superfície e texto

| Token | Claro (`:root`) | Escuro (`[data-theme="dark"]`) | Uso |
|---|---|---|---|
| `--canvas` | `#F4F5F7` | `#16181C` | Background geral das páginas |
| `--surface` | `#FFFFFF` | `#1E2126` | Cards, modais, topbar, formulários |
| `--sunken` | `#EDEFF2` | `#24282E` | Fundos rebaixados (thead, segmented, blocos internos) |
| `--border` | `#DDE1E6` | `#2C3036` | Bordas de cartão, divisores, linhas de tabela |
| `--border-strong` | `#C4C9D0` | `#3A3F47` | Bordas de inputs e contornos com mais peso |
| `--ink` | `#1C2024` | `#E8EAED` | Texto principal |
| `--muted` | `#5B6270` | `#9098A3` | Texto secundário, labels, placeholders |
| `--graphite` | `#22262B` | `#101216` | Sidebar, botões graphite, painel de login |
| `--graphite-hi` | `#2C3138` | `#1A1D22` | Item ativo da sidebar, realce sobre graphite |
| `--shadow` | `0 1px 2px rgba(20,25,35,.04), 0 1px 3px rgba(20,25,35,.03)` | `0 1px 2px rgba(0,0,0,.3)` | Elevação de cartões |
| `--ph` | `repeating-linear-gradient(45deg, #E7E9ED, #E7E9ED 10px, #EDEFF2 10px, #EDEFF2 20px)` | idem com `#24282E`/`#2C3036` | Placeholder hachurado (cards sem foto) |

### Tokens de marca

| Token | Claro | Escuro | Uso |
|---|---|---|---|
| `--brand` | `#E09915` | `#F0A93C` | Cor primária: botões, destaques, bordas ativas, ícones de header |
| `--brand-hover` | `#C8830B` | `#F5BC5E` | Hover da cor primária |
| `--brand-soft` | `#FBEFD3` | `#33291A` | Fundo suave laranja (ex.: botão Editar de linha) |

### Cores Semânticas (status) — pares `--x` / `--x-bg`

Cada família de status tem uma cor de texto (`--x`) e um fundo suave (`--x-bg`), usados juntos nas badges/pills e realces.

| Família | Token texto (claro / escuro) | Token fundo (claro / escuro) | Uso |
|---|---|---|---|
| `ok` | `#1F7A4D` / `#4FB07E` | `#E3F3EA` / `#16281F` | Pago, ocupado, ativo (positivo) |
| `danger` | `#C0392B` / `#E0685A` | `#FBE7E4` / `#2A1917` | Atrasado, vago, rescindido, exclusão |
| `info` | `#1F6FB2` / `#5BA3D8` | `#E4F0F9` / `#15222D` | Contrato ativo/em vigência, informativo, links |
| `warn` | `#B5730E` / `#E0A044` | `#FBEFD3` / `#2A2113` | Pendente, atenção, manutenção |
| `neu` | `#5B6270` / `#9098A3` | `#EDEFF2` / `#24282E` | Encerrado, arquivado, inativo, neutro |

### Fundamentos do sistema de tokens

- **Anti-FOUC:** um script inline no `<head>` de `base.html` lê `localStorage['shelterTheme']` e aplica `data-theme="dark"` no `<html>` **antes do primeiro paint**, evitando flash de tema claro.
- **Persistência:** a escolha do tema é gravada em `localStorage` (chave `shelterTheme`) por `static/js/theme.js`.
- **Overrides Bootstrap:** o Bootstrap 5.3 (CSS + JS) foi **mantido**; `shelter.css` redefine as CSS vars nativas do Bootstrap (`--bs-body-*`, `--bs-btn-*`, `--bs-table-*`, `--bs-modal-bg`, `--bs-toast-bg`, `--bs-alert-*` etc.) apontando para os tokens Shelter — **zero `!important`** no arquivo. O dark mode do Flatpickr também é coberto.

---

## 3. Tipografia

**Fonte principal:** **Inter** (Google Fonts, pesos 400/500/600/700/800), carregada via `<link>` em `base.html`. O global aplica `font-feature-settings: 'tnum' 1` (algarismos tabulares — alinhamento consistente de números em KPIs, tabelas e valores). Montserrat/Gotham foram descontinuadas no app web (permanecem apenas no legado do Login, até o módulo 03).

| Elemento | Peso | Tamanho | Observações |
|---|---|---|---|
| Títulos de página (topbar) | 700 | 18px | Alguns com ícone laranja à esquerda |
| Header de cartão | 700 | 14px | Ícone laranja opcional |
| Valor de KPI card | 800 | 34px | Algarismos tabulares |
| Corpo de texto | 400 | ~0.9rem | — |
| Labels de formulário | 700 | 11.5px | Caixa alta, `letter-spacing` ~.04–.05em, cor `--muted` |
| Cabeçalho de tabela (th) | 700 | 11px | Caixa alta, cor `--muted` |
| Badges / status (pills) | 700 | 11.5px | — |
| Rótulo de grupo da sidebar | 700 | 10.5px | Caixa alta, cor `#6B727C` |

---

## 4. Layout Geral

### Estrutura de Página
```
┌─────────────────────────────────────────────┐
│                  TOPBAR                      │
├──────────┬──────────────────────────────────┤
│          │                                  │
│ SIDEBAR  │        CONTEÚDO PRINCIPAL        │
│          │                                  │
│          │                                  │
└──────────┴──────────────────────────────────┘
```

| Elemento | Largura / Altura |
|---|---|
| Sidebar | 260px (fixa) |
| Topbar | 64px (fixa no topo) |
| Conteúdo | `margin-left: 260px`, `margin-top: 64px` |
| Padding interno do conteúdo | `1.75rem` |

Superfícies e bordas usam os tokens da seção 2 (`--canvas` no fundo geral, `--surface` nos cartões/topbar, `--border` nos divisores), reagindo automaticamente ao tema claro/escuro.

---

## 5. Sidebar

A sidebar é **sempre expandida no desktop** (o colapso introduzido na Rodada 2 foi removido; não há botão de toggle nem persistência em `localStorage` para desktop — apenas o toggle hamburger no mobile, ver seção 12).

### Especificações
- **Fundo:** `--graphite` (`#22262B` claro / `#101216` escuro)
- **Largura:** 260px fixa; sticky, altura `100vh`
- **Header (64px):** logo `Shelter_LOGO_white.svg` centralizada (`width: 90%`, `object-fit: contain`), sobre o fundo `--graphite`.
- **Texto:** branco / claro sobre o graphite
- **Ícones:** Bootstrap Icons
- **Rótulos de grupo:** caixa alta, `10.5px`, peso 700, cor `#6B727C`

### Estado Ativo
- Fundo: `--graphite-hi` (`#2C3138` claro / `#1A1D22` escuro)
- Borda esquerda: `3px solid var(--brand)`
- Texto: branco

### Estado Hover
- Realce sutil sobre o graphite; texto branco

### Seções do Menu
```
[  Shelter  ]    (logo Shelter_LOGO_white.svg)

  Dashboard

─── Cadastros ───
  Imóveis
  Proprietários
  Inquilinos

─── Operações ───
  Contratos
  Laudos de Vistoria
  Financeiro
  Recibos

─── Documentos ───
  GED — Documentos

─── Administração ─── (somente is_staff)
  Painel Admin
```

---

## 6. Topbar

- **Fundo:** `--surface`
- **Borda inferior:** `1px solid var(--border)`
- **Altura:** `64px` (sticky, `z-index: 5`)
- **Esquerda:** título da página (`18px`/700), alguns com ícone laranja (`--brand`).
- **Direita:** **toggle de tema** + sino de notificações + info do usuário + botão logout.
  - **Toggle de tema (`#theme-toggle`):** botão `.icon-btn` que alterna `data-theme` no `<html>` entre `""` (claro) e `"dark"`. Ícone alterna `bi-moon-stars` (no claro, oferece o escuro) ↔ `bi-sun` (no escuro). Lógica em `static/js/theme.js`: persiste em `localStorage['shelterTheme']`, atualiza o ícone e dispara o evento `shelter:theme-changed` no `document` a cada troca (consumido pelos gráficos, ver seção 13).
  - **Sino de notificações (`#notifDropdown`):** botão `.icon-btn` que abre um dropdown Bootstrap (`.notif-dropdown`) com as últimas notificações do usuário logado (`ultimas_notificacoes_usuario`, via context processor). Cada item usa `.notif-{nivel}` (`success`/`error`/`warning`/`info`) para a borda esquerda colorida (tokens `--ok`/`--danger`/`--warn`/`--info`). Sem badge de contagem não-lida, sem paginação.

---

## 7. Botões

Tokens do redesign "Shelter" (`static/css/shelter.css`); os overrides
redefinem as variáveis `--bs-btn-*` do Bootstrap, então os estados
(hover/active/disabled/focus) reagem ao tema claro/escuro via `data-theme`.

### Botão Principal laranja (`.btn-primary`)
- Fundo: `var(--brand)`
- Texto: `var(--brand-contrast)`, peso `700`
- Hover: fundo `var(--brand-hover)`

### Botão Grafite (ação primária escura — `.btn-graphite` / `.btn-secondary` / `.btn-dark`)
- Fundo: `var(--graphite)`
- Texto: `#FFFFFF`
- Hover: fundo `var(--graphite-hi)`
- Uso: **Salvar** nos formulários CRUD (§8.1)

### Botão Secundário / outline neutro (`.btn-outline-secondary`)
- Fundo: `var(--surface)`
- Borda: `1px solid var(--border-strong)`
- Texto: `var(--ink)`
- Hover: fundo `var(--sunken)`
- Uso: **Voltar** / **Cancelar** / ação de linha "Ver"

### Botão de Perigo (`.btn-danger`) e Outline Perigo (`.btn-outline-danger`)
- Sólido: fundo `var(--danger)`, texto `#FFFFFF`
- Outline: borda/texto `var(--danger)`, hover preenche com `var(--danger)`

---

## 8. Formulários

Tokens do redesign "Shelter" (`static/css/shelter.css`); reagem ao tema
claro/escuro via `data-theme` no `<html>`.

- **Inputs e selects:** fundo `var(--surface)`, borda `1px solid
  var(--border-strong)`, border-radius `8px`, altura mínima `42px`
- **Focus:** borda `2px solid var(--brand)` + halo `0 0 0 3px
  var(--focus-ring)` (padding compensado em `-1px` para o conteúdo não pular)
- **Labels:** `.form-label` uppercase, `700`, `letter-spacing:.045em`,
  `0.72rem`, cor `var(--muted)`
- **Asterisco de campo obrigatório:** `*` envolto em
  `<span class="text-danger">` (cor `var(--danger)`), logo após o texto do label
- **Placeholders:** cor `var(--muted)`
- **Textarea:** mesmas regras dos inputs, `resize: vertical`

### 8.1. Padrão de formulário CRUD

Os 9 formulários de card único (imóvel, notificação, inquilino, proprietário,
contrato, renovação, distrato, recibo, lançamento) seguem a mesma receita
(brief §3.5): link **Voltar** no topo; um ou mais `.section-card` "Dados de
…" com grid de campos renderizados via `{{ form.campo }}`; erros de validação
em `.alert-danger`; footer alinhado à direita com **Cancelar** (outline,
`.btn-outline-secondary`, leva à listagem/detalhe) + **Salvar** (grafite,
`.btn-graphite`, submit). Exceções semânticas: **Renovação** usa `.btn-info`
("Registrar Renovação") e **Distrato** usa `.btn-danger` ("Confirmar
Distrato"), acompanhando o código de cor dessas operações nas action bars de
detalhe. Datepicker (Flatpickr) e máscaras (IMask) continuam via atributos
`data-flatpickr`/`data-mask` definidos em `imoveis/forms.py` — o reskin não
altera o markup do campo em si.

---

## 9. Cards e Superfícies

Superfícies do redesign "Shelter"; reagem ao tema via `data-theme` no `<html>`.

### Section Card (container padrão)
- Fundo: `var(--surface)`
- Border-radius: `12px`
- Sombra: `var(--shadow)`
- Borda: `1px solid var(--border)`
- **Header:** borda inferior `1px solid var(--border)`, Inter, cor `var(--ink)`
- **Body:** padding interno confortável

### KPI Cards (Dashboard)
- Fundo: `var(--surface)`, borda `1px solid var(--border)`, sombra `var(--shadow)`
- Borda esquerda colorida por variante (`4px solid`)
- Hover: `transform: translateY(-2px)`, sombra levemente maior
- Estrutura: ícone (fundo colorido suave) + valor numérico + label

| Variante | Cor da borda / ícone | Fundo do ícone |
|---|---|---|
| `kpi-gold` | `var(--brand)` | `var(--brand-soft)` |
| `kpi-green` | `var(--ok)` | `var(--ok-bg)` |
| `kpi-red` | `var(--danger)` | `var(--danger-bg)` |
| `kpi-neutral` | `var(--neu)` | `var(--neu-bg)` |
| `kpi-info` | `var(--info)` | `var(--info-bg)` |

---

## 10. Tabelas

Tokens do redesign "Shelter"; reagem ao tema via `data-theme` no `<html>`.

- **Cabeçalho:** fundo `var(--sunken)`, texto `var(--muted)` Inter `700`, `0.78rem`, caixa alta
- **Borda inferior do cabeçalho:** `2px solid var(--border)`
- **Células:** padding `0.7rem 1rem`, borda `1px solid var(--border)`
- **Hover de linha:** fundo `var(--sunken)`
- **Texto de células:** `0.88rem`, cor `var(--ink)`

### 10.1. Vista Tabela de Imóveis (alternativa aos Cards)

A listagem de Imóveis (`imovel_list.html`) oferece duas visualizações da mesma
listagem, alternadas por um *segmented control* Cards/Tabela na result bar
(preferência persistida em `localStorage`, chave `shelterImovelView`, via
`static/js/imovel-view-toggle.js`). A vista Cards é a padrão; a vista Tabela
tem as colunas: **Endereço** (link para o detalhe), **Bairro/Cidade**,
**Tipo**, **Proprietário**, **Status** (badge) e **Ações** (Ver / Editar /
Excluir). Ambas as vistas iteram o mesmo queryset `imoveis` e compartilham o
mesmo modal de exclusão; nenhuma consulta nova é feita.

---

## 11. Badges de Status

Padrão: pill arredondado (`border-radius: 999px`), padding `0.25rem 0.65rem`,
Inter `700` `0.74rem`. As cores vêm dos pares de token semânticos
(`--x-bg` / `--x`), portanto reagem ao tema claro/escuro via `data-theme`.

| Classe | Par de token (fundo / texto) | Uso |
|---|---|---|
| `badge-ocupado`, `badge-pago` | `--ok-bg` / `--ok` | Imóvel ocupado · Lançamento pago |
| `badge-vago`, `badge-atrasado`, `badge-rescindido` | `--danger-bg` / `--danger` | Imóvel vago · Lançamento atrasado · Contrato rescindido |
| `badge-manutencao`, `badge-pendente` | `--warn-bg` / `--warn` | Em manutenção · Lançamento pendente |
| `badge-ativo` | `--info-bg` / `--info` | Contrato ativo |
| `badge-encerrado` | `--neu-bg` / `--neu` | Contrato encerrado |

---

## 12. Responsividade (Mobile)

- **Breakpoint mobile:** `max-width: 768px`
- Sidebar oculta por padrão: `transform: translateX(-260px)`
- Sidebar aberta via classe `.show`: `transform: translateX(0)`
- Overlay escuro ao abrir sidebar: `rgba(0, 0, 0, 0.45)`, z-index abaixo da sidebar
- Topbar ocupa largura total (`left: 0`) no mobile
- Conteúdo sem `margin-left` no mobile
- Toggle hamburger visível apenas no mobile (`d-md-none`)

> **Redesign "Shelter":** o **comportamento** do overlay e da sidebar off-canvas no mobile **não mudou** — apenas o visual foi atualizado (tokens de cor, tema claro/escuro). O overlay, a classe `.show` e o toggle hamburger seguem funcionando como antes.

---

## 13. Gráficos (Dashboard Imobiliário e Indicadores Financeiros)

Os gráficos hoje estão divididos em duas telas — Dashboard Imobiliário (`/dashboard/`, `templates/imoveis/dashboard_imobiliario.html`) e Indicadores Financeiros (embutidos em `/financeiro/`, `templates/financeiro/lancamento_list.html`). Regras de negócio por trás de cada métrica em `docs/03_regras_de_negocio.md` §9.

- **Biblioteca:** Chart.js 4.4.4
- **Cores lidas de tokens:** os gráficos não usam hex fixos — leem as CSS vars via `getComputedStyle` (`--ok`, `--danger`, `--warn`, `--info`, `--brand`, `--surface`, `--border`, `--muted`), de modo a acompanharem os temas claro/escuro.
- **Redesenho no toggle de tema:** os gráficos são **destruídos e recriados** ao receber o evento `shelter:theme-changed` disparado por `static/js/theme.js`, relendo os tokens do tema recém-aplicado.

### 13.1 Dashboard Imobiliário (`/dashboard/`)
- **Filtros em pills** (`.dash-filterbar` + `.filter-pill`): "Filtrar por" seguido de dois selects compactos — Tipo e Status —, cada um submetendo o form (`onchange="this.form.submit()"`) assim que muda; sem filtro de imóvel nem de período na barra (removidos no redesign visual).
- **KPI cards** (`.kpi-card-alt` + `.kpi-icon`): ícone quadrado colorido à esquerda (`.kpi-icon-{brand|ok|danger|info|warn}`, fundo `*-bg`/`-soft`, cor do token) + valor/label à direita. 6 cards, todos com dado real: total de imóveis, ocupados/vagos, taxa de vacância, contratos ativos, contratos que precisam de atenção, tempo médio de vacância (ver `docs/03_regras_de_negocio.md` §9.1 — nenhum é mais placeholder).
- **Donut — distribuição por situação do imóvel:** ocupado / vago / manutenção (`--ok`, `--danger`, `--warn`; borda entre fatias em `--surface`, `cutout: 68%`)
- **Donut — distribuição por tipo de imóvel:** uma cor por tipo cadastrado (`--brand`, `--warn`, `--ok`, `--muted`, `--danger`, `--info`)
- **Legenda customizada** (`.chart-legend`, ao lado do donut, não embaixo): lista com bolinha colorida + label + valor numérico, renderizada em JS (`renderLegend`) a partir dos mesmos dados do dataset — a legenda nativa do Chart.js fica desligada (`legend: { display: false }`).
- **Valor central do donut** (`.chart-donut-center`, sobreposto via `position: absolute`): percentual da maior fatia + seu label, calculado em JS (`renderCenter`).
- **Linha do tempo de status** (`.dash-timeline-select`): card sempre visível (não é mais drill-down condicional). Header com o título à esquerda e, à direita, um `<select name="timeline_imovel_id">` próprio (`onchange="this.form.submit()"`) que troca só a timeline, preservando os filtros de Tipo/Status via inputs hidden no mesmo mini-form — não afeta KPIs/donuts. Sem seleção, mostra o primeiro imóvel cadastrado.

### 13.2 Indicadores Financeiros (`/financeiro/`)
- **Gráfico de barras — evolução mensal (ganhos vs. despesas):** *period-aware* — últimos 6 meses fixos sem filtro de data, ou todos os meses do intervalo filtrado quando há data início/fim (título do card indica qual modo está ativo)
  - Ganhos: `--ok`; Despesas: `--danger`
  - Eixo Y: formatado como `R$ valor` (com sufixo `k` para milhares)
- **Donut — composição de despesas por categoria:** uma cor por `Lancamento.tipo` presente (`--info`, `--warn`, `--brand`, `--danger`, `--muted`, `--ok`)
- KPI cards (ganhos/despesas/saldo do período, total pendente, ticket médio de aluguel, % de inadimplência), ranking de rentabilidade por imóvel (barra de progresso) e tabela de lançamentos pendentes mais antigos — todos usando o componente `.card`, com empty-state (`bi-inbox`) quando não há dados.

---

## 14. Modais de Confirmação

- Padrão Bootstrap 5
- Tamanho: `modal-sm`
- Título em vermelho (`var(--danger)`) para ações destrutivas
- Dois botões: cancelar (outline secundário) + confirmar (danger)
- Sem bordas no header e footer (`border-0`)

---

## 15. Bibliotecas Frontend

| Biblioteca | Versão | Uso |
|---|---|---|
| Bootstrap | 5.3.3 | Framework CSS base |
| Bootstrap Icons | 1.11.3 | Ícones do sistema |
| Chart.js | 4.4.4 | Gráficos do dashboard |
| Gotham | — | Tipografia ⚠️ licença pendente |

---

## 16. Página de Login (redesign — módulo 03)

- Layout **dedicado** (fora do `base.html`, sem sidebar/topbar); referencia `static/css/shelter.css` (tokens) + fonte Inter, com o CSS específico da tela num `<style>` local que consome os tokens.
- **Card central:** `max-width: 1040px`, `min-height: 560px`, `border-radius: 18px`, grid de **2 colunas**, centralizado sobre fundo `--canvas`.
- **Painel esquerdo:** fundo `--graphite`, texto branco, círculos decorativos laranja translúcidos (`--brand` com baixa opacidade), logo "S" (quadradinho laranja) + wordmark "Shelter", headline "Bem-vindo(a) de volta!", parágrafo e rodapé "© {ano} Shelter · Gestão Imobiliária" (`{% now "Y" %}`).
- **Painel direito:** fundo `--surface`; título "Entrar na conta" + subtítulo; campo Usuário (ícone `bi-person`) e campo Senha (ícone `bi-lock` + toggle `bi-eye`/`bi-eye-slash` via `togglePassword()`); inputs de ~50px de altura; botão "Entrar →" full-width graphite.
- **Responsivo:** no mobile (`max-width: 767px`) o painel esquerdo some e apenas o formulário é exibido (card em coluna única).
- Lógica de autenticação Django preservada: `form`, `next` (hidden), mensagem de erro (`{% if form.errors %}`), ids/names `username`/`password`.

---

## 17. Documentos PDF Gerados (Rodada 4)

Os três PDFs gerados pelo sistema (Contrato, Laudo de Vistoria, Recibo) foram redesenhados para replicar 1:1 os mockups estáticos em `docs/pdf-models/` (`contrato_locacao.html`, `laudo_vistoria.html`, `recibo_pagamento.html`), mantendo o motor **xhtml2pdf**.

- **Logo:** sempre `{% static 'assets/Shelter_LOGO.jpg' %}` (versão rasterizada compatível com xhtml2pdf).
- **Cabeçalho:** usa `{{ objeto.pk }}` + data de criação (não há campo de "número de documento" formatado nos models).
- **CSS comum em `base_pdf.html`:** `.doc-header`, `.doc-logo`, `.doc-meta`, `.brand-rule`, `.doc-title-wrap`/`.doc-title`/`.doc-title-underline` (+ `.doc-title-underline-table`), `.sec`, `.fields`/`.flabel`/`.fval`, `.cards`/`.card-label`/`.card-value`, `.note-box`, `.sign-table`/`.sign-cell`/`.sign-line`/`.sign-role`, `.doc-footer`, `.avoid-break`. A classe `.card` (wrapper singular) **não existe mais**: o `border`/`padding` do cartão vive agora em `.cards td` (o xhtml2pdf desenhava uma borda por filho block-level quando a borda ficava no `<div class="card">`, produzindo efeito de grade — mover para a `<td>` usa o comando `BOX` do `TableStyle` e trata a célula como caixa única).
- **Limitações do xhtml2pdf tratadas nos templates:** `text-transform: uppercase` é ignorado pelo motor — os textos estáticos são escritos literalmente em CAIXA ALTA e os valores dinâmicos usam o filtro `|upper`; as regras CSS `text-transform` permanecem como documentação da intenção. `margin: ... auto ...` também não é suportado — a barra `.doc-title-underline` é centralizada via `<table align="center">` em vez de `margin: auto`.
- **CSS exclusivo por documento (no template filho):**
  - Laudo: `.data-table`, `.badge`/`.badge-bom`/`.badge-reg`/`.badge-ruim`, `.row-alt`.
  - Recibo: caixa de destaque da quantia.
- **Paleta dos PDFs:** cores de marca já documentadas (seção 2) — `#F2B441`, `#3A3A3A`, `#F7F3EA`, `#888888`, `#E0E0E0`, `#2E7D32` (estado bom), `#C62828` (estado ruim) — mais o tom `#9A6B00` para detalhes de marca sobre fundo claro.
- **Fora de escopo:** valor por extenso no recibo (sem `num2words`).
