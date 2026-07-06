# 07 — Design & UI/UX
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
| Favicon | Símbolo isolado | Exportar apenas o elemento gráfico dourado (ainda não implementado) |

> Os arquivos da logo estão em `static/assets/` (`Shelter_LOGO.svg`, `Shelter_LOGO_white.svg`, `Shelter_LOGO.jpg`, `Shelter_LOGO_white.jpg`).
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
  - **Sino de notificações:** restilizado como `.icon-btn`.

---

## 7. Botões

### Botão Principal (ação primária)
- Fundo: `#F2B441`
- Texto: `#3A3A3A`, Gotham Medium
- Border-radius: `6px`
- Padding: `0.5rem 1.1rem`
- Hover: opacidade `0.88` ou leve escurecimento do fundo

### Botão Secundário (outline)
- Fundo: transparente
- Borda: `1px solid #3A3A3A`
- Texto: `#3A3A3A`
- Hover: fundo `#3A3A3A`, texto `#FFFFFF`

### Botão de Perigo (exclusão)
- Fundo: `#C62828`
- Texto: `#FFFFFF`
- Hover: leve escurecimento

### Botão Outline Perigo
- Borda: `1px solid #C62828`
- Texto: `#C62828`
- Hover: fundo `#C62828`, texto `#FFFFFF`

---

## 8. Formulários

- **Inputs e selects:** fundo `#FFFFFF`, borda `1px solid #E0E0E0`, border-radius `6px`
- **Focus:** borda `#F2B441`, box-shadow `0 0 0 3px rgba(242, 180, 65, 0.15)`
- **Labels:** Gotham Medium, `0.87rem`, cor `#3A3A3A`
- **Placeholders:** cor `#888888`
- **Textarea:** mesmas regras dos inputs, `resize: vertical`

---

## 9. Cards e Superfícies

### Section Card (container padrão)
- Fundo: `#F7F7F7`
- Border-radius: `6px`
- Sombra: `0 1px 3px rgba(0, 0, 0, 0.06)`
- **Header:** padding `1rem 1.25rem`, borda inferior `1px solid #E0E0E0`, Gotham Medium, cor `#3A3A3A`
- **Body:** padding `1.25rem`

### KPI Cards (Dashboard)
- Fundo: `#F7F7F7`
- Border-radius: `6px`
- Sombra: `0 1px 3px rgba(0, 0, 0, 0.06)`
- Borda esquerda colorida por variante (`4px solid`)
- Hover: `transform: translateY(-2px)`, sombra levemente maior
- Estrutura: ícone (fundo colorido suave) + valor numérico + label

| Variante | Cor da borda | Fundo do ícone | Cor do ícone |
|---|---|---|---|
| `kpi-gold` | `#F2B441` | `rgba(242,180,65,0.12)` | `#F2B441` |
| `kpi-green` | `#2E7D32` | `rgba(46,125,50,0.10)` | `#2E7D32` |
| `kpi-red` | `#C62828` | `rgba(198,40,40,0.10)` | `#C62828` |
| `kpi-neutral` | `#757575` | `rgba(117,117,117,0.10)` | `#757575` |
| `kpi-info` | `#1565C0` | `rgba(21,101,192,0.10)` | `#1565C0` |

---

## 10. Tabelas

- **Cabeçalho:** fundo `#F7F3EA`, texto `#3A3A3A` Gotham Medium, `0.78rem`, caixa alta
- **Borda inferior do cabeçalho:** `2px solid #E0E0E0`
- **Células:** padding `0.7rem 1rem`, borda `1px solid #E0E0E0`
- **Hover de linha:** fundo `rgba(242, 180, 65, 0.05)`
- **Texto de células:** `0.88rem`, cor `#3A3A3A`

---

## 11. Badges de Status

Padrão: pill arredondado (`border-radius: 999px`), padding `0.25rem 0.65rem`, Gotham Bold `0.74rem`.

| Classe | Fundo | Texto | Uso |
|---|---|---|---|
| `badge-ocupado` | `rgba(46,125,50,0.12)` | `#2E7D32` | Imóvel ocupado |
| `badge-vago` | `rgba(198,40,40,0.12)` | `#C62828` | Imóvel vago |
| `badge-manutencao` | `rgba(242,180,65,0.15)` | `#B8860B` | Em manutenção |
| `badge-ativo` | `rgba(21,101,192,0.12)` | `#1565C0` | Contrato ativo |
| `badge-encerrado` | `rgba(117,117,117,0.12)` | `#757575` | Contrato encerrado |
| `badge-rescindido` | `rgba(198,40,40,0.12)` | `#C62828` | Contrato rescindido |
| `badge-pago` | `rgba(46,125,50,0.12)` | `#2E7D32` | Lançamento pago |
| `badge-pendente` | `rgba(242,180,65,0.15)` | `#B8860B` | Lançamento pendente |
| `badge-atrasado` | `rgba(198,40,40,0.12)` | `#C62828` | Lançamento atrasado |

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

## 13. Gráficos (Dashboard)

- **Biblioteca:** Chart.js 4.4.4
- **Cores lidas de tokens:** desde o redesign "Shelter", os gráficos não usam mais hex fixos — leem as CSS vars via `getComputedStyle` (`--ok`, `--danger`, `--warn`, `--surface`, `--border`, `--muted`), de modo a acompanharem os temas claro/escuro.
- **Redesenho no toggle de tema:** os gráficos são **destruídos e recriados** ao receber o evento `shelter:theme-changed` disparado por `static/js/theme.js`, relendo os tokens do tema recém-aplicado.
- **Gráfico de rosca (donut):** ocupação dos imóveis (ocupado / vago / manutenção)
  - `cutout: 64%`, legenda embaixo
  - Cores: `--ok`, `--danger`, `--warn`; borda entre fatias em `--surface`
- **Gráfico de barras:** recebimentos vs. pendências (últimos 6 meses)
  - Recebido: `--ok`; Pendente/Atrasado: `--danger`
  - Eixo Y: formatado como `R$ valor`
- **KPI cards / demais componentes do dashboard:** a barra de filtros e a tabela de últimos lançamentos passaram a usar o componente `.card`; a tabela tem empty-state com ícone `bi-inbox`. A **view do dashboard e os nomes de contexto permanecem inalterados** (mudança 100% de template/CSS/JS).

---

## 14. Modais de Confirmação

- Padrão Bootstrap 5
- Tamanho: `modal-sm`
- Título em vermelho (`#C62828`) para ações destrutivas
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