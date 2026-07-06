# Design Brief — Redesign Visual "Shelter"

> Fonte: projeto Claude Design `24aef7be-6a13-4ef5-94ce-43fefb42df3e` ("Redesign Visual — Shelter").
> 5 telas de referência: Login, Dashboard, Listagem, Detalhe (Contrato), Formulário (Laudo).
> **Escopo:** reskin da camada de template/CSS do app web. Models/views/forms/signals **não mudam**.
> Os PDFs gerados (`templates/documentos/`) **não** fazem parte deste redesign.

---

## 1. Fundações (tokens) — idênticas em todas as telas

Fonte: **Inter** (Google Fonts, pesos 400/500/600/700/800), `font-feature-settings:'tnum' 1` para números tabulares.

### Tema claro (`:root`)
```
--canvas:#F4F5F7; --surface:#FFFFFF; --sunken:#EDEFF2;
--border:#DDE1E6; --border-strong:#C4C9D0;
--ink:#1C2024; --muted:#5B6270;
--brand:#E09915; --brand-hover:#C8830B; --brand-soft:#FBEFD3;
--graphite:#22262B; --graphite-hi:#2C3138;
--ok:#1F7A4D; --ok-bg:#E3F3EA; --danger:#C0392B; --danger-bg:#FBE7E4;
--info:#1F6FB2; --info-bg:#E4F0F9; --warn:#B5730E; --warn-bg:#FBEFD3;
--neu:#5B6270; --neu-bg:#EDEFF2;
--shadow:0 1px 2px rgba(20,25,35,.04),0 1px 3px rgba(20,25,35,.03);
```

### Tema escuro (`[data-theme="dark"]`)
```
--canvas:#16181C; --surface:#1E2126; --sunken:#24282E;
--border:#2C3036; --border-strong:#3A3F47;
--ink:#E8EAED; --muted:#9098A3;
--brand:#F0A93C; --brand-hover:#F5BC5E; --brand-soft:#33291A;
--graphite:#101216; --graphite-hi:#1A1D22;
--ok:#4FB07E; --ok-bg:#16281F; --danger:#E0685A; --danger-bg:#2A1917;
--info:#5BA3D8; --info-bg:#15222D; --warn:#E0A044; --warn-bg:#2A2113;
--neu:#9098A3; --neu-bg:#24282E;
--shadow:0 1px 2px rgba(0,0,0,.3);
```

Placeholder hachurado (cards sem foto):
`--ph:repeating-linear-gradient(45deg,#E7E9ED,#E7E9ED 10px,#EDEFF2 10px,#EDEFF2 20px)`
(dark: `#24282E`/`#2C3036`).

### Primitivas de forma
- Raio de cartão: 10px; inputs/botões: 8px; badges/pills: 100px; segmented: 6–7px.
- Sidebar: 260px fixa. Topbar/header: 64px de altura.
- Inputs: altura 40–42px (48–50px no Login), `border:1px solid var(--border-strong)`.
- Foco de input (destaque): `border:2px solid var(--brand)` + `box-shadow:0 0 0 3px rgba(224,153,21,.16)`.
- Labels: 11–12px, 700, `letter-spacing:.04–.05em`, `text-transform:uppercase`, cor `--muted`.

---

## 2. Chrome comum (Sidebar + Topbar)

### Sidebar (graphite, 260px, sticky, altura 100vh)
- Header 64px: quadradinho laranja "S" (logo) + wordmark "Shelter" branco.
- Nav com grupos rotulados (uppercase 10.5px, cor `#6B727C`):
  - **(topo)** Dashboard
  - **Cadastros:** Imóveis · Proprietários · Inquilinos
  - **Operações:** Contratos · Laudos de Vistoria · Financeiro · Recibos
  - **Documentos:** GED — Documentos
  - **Administração:** Painel Admin
- Item ativo: `background:var(--graphite-hi)`, texto branco, `border-left:3px solid var(--brand)`.
- Ícones Bootstrap Icons (já usados no projeto).

### Topbar (surface, 64px, sticky, z-index 5)
- Esquerda: título da página (18px/700), alguns com ícone laranja.
- Direita: **toggle de tema** (lua/sol), sino de notificações, avatar (círculo laranja com inicial) + nome/role, botão **Sair**.

### Toggle de tema (comportamento)
- Alterna `data-theme` no `<html>` entre `""` (claro) e `"dark"`.
- Ícone alterna `bi-moon-stars` ↔ `bi-sun`.
- **Persistir** a escolha (localStorage) e reaplicar no load — os mockups só guardam em state, mas produção deve persistir.
- Charts precisam ser redesenhados ao trocar tema (lêem CSS vars).

---

## 3. Telas

### 3.1 Login
- Fundo `--canvas`, card central `max-width:1040px`, `border-radius:18px`, grid 2 colunas, `min-height:560px`.
- **Esquerda** (`--graphite`, texto branco): círculos decorativos laranja translúcidos; logo "S"+Shelter; headline "Bem-vindo(a) de volta!"; parágrafo; rodapé "© 2026 Shelter · Gestão Imobiliária".
- **Direita:** título "Entrar na conta" + subtítulo; campo Usuário (ícone `bi-person`); campo Senha (ícone `bi-lock` + toggle `bi-eye`); botão "Entrar →" full-width graphite.
- Login **não tem** sidebar/topbar (layout próprio, provavelmente `registration/login.html` fora do `base.html`).

### 3.2 Dashboard
- **Barra de filtros** (card): Imóvel (select), Data início, Data fim (Flatpickr dd/mm/aaaa), Status (select), botões Filtrar (graphite) + Limpar (ícone x).
- **5 KPI cards** (grid 5 col): Total de Imóveis, Ocupados, Vagos, Contratos Ativos, Inadimplentes. Cada um: label uppercase + bolinha colorida de status, número 34px/800, linha auxiliar com ícone.
- **2 gráficos Chart.js** (grid 1fr 1.4fr): donut "Ocupação dos imóveis" (cutout 64%, legenda embaixo) + barras "Recebimentos vs. Pendências · últimos 6 meses". Cores lidas de CSS vars; redesenhar no toggle de tema.
- **Tabela** "Últimos Lançamentos Financeiros": Inquilino, Imóvel (link info), Tipo, Vencimento, Valor (right, bold), Status (badge pill). Header "Ver todos".

### 3.3 Listagem (ex.: Imóveis)
- **Barra de filtros:** Buscar (input com ícone lupa), Status, Tipo, botões Filtrar + Limpar.
- **Result bar:** contador "N imóvel(is) encontrado(s)" + **segmented toggle Cards/Tabela** + botão primário laranja "Novo Imóvel".
- **Vista Cards** (grid 3 col): imagem/placeholder hachurado + badge de status no canto; endereço (link), local (geo), chips tipo/categoria, dono; rodapé com 3 botões de ação (Ver = neutro, Editar = laranja soft, Excluir = danger soft).
- **Vista Tabela:** Endereço, Bairro/Cidade, Tipo, Proprietário, Status (badge), Ações (3 ícones). Alterna via toggle (state no cliente).
- **Nota:** a vista Cards é específica de Imóveis (tem foto). As demais listagens (proprietários, inquilinos, contratos, etc.) usam a **vista Tabela** como padrão.

### 3.4 Detalhe (ex.: Contrato #10)
- **Action bar:** Voltar (esq) · spacer · Editar (graphite) · Regerar Contrato (PDF) · Contrato Gerado (PDF) · Renovar (info) · Distrato (danger). Botões condicionais conforme o domínio atual.
- **Grid 2 colunas:**
  - **Esquerda:** card **Informações** (header com badge de status; linhas label→valor); card **Documentos** (link "última versão", lista de **versões do PDF gerado** com data/hora/usuário — GED versionado; separador; blocos de upload GED com badge PF/PJ: Comprovante de Renda, Contrato Social, Recibo de Chaves, Comprovante Anual — cada um input dashed + botão Enviar); card **Fiador(es)** (bloco sunken por fiador com nome/estado civil, RG-CPF, garantia, link certidão).
  - **Direita:** card **Lançamentos Financeiros** (header com botão Novo; tabela Tipo/Vencimento/Valor/Status/Comprov.; empty state com ícone inbox); card **Laudos de Vistoria** (header botão Novo; tabela Tipo/Data/Responsável/Arquivo; empty state).
- Empty state padrão: ícone `bi-inbox` grande + texto muted centralizado.

### 3.5 Formulário (ex.: Novo Laudo)
- **Voltar** no topo; `max-width:1100px`.
- Card **Dados do Laudo:** grid 2 col — Imóvel (select), Contrato (select **disabled** até escolher imóvel, com hint "Filtrado pelo imóvel selecionado" — endpoint `contratos_por_imovel_json` atual), Tipo, subgrid Data (Flatpickr) + Responsável, Observações (textarea full-width). Asteriscos `*` danger nos obrigatórios.
- Card **Cômodos e Itens Vistoriados:** aviso info; por cômodo um bloco com header sunken + grid de itens (Item / Estado / Observação). **Estado** = segmented Bom(ok)/Regular(warn)/Ruim(danger). Reproduz o formset do checklist atual.
- Card **Testemunhas:** header com botão Adicionar; linhas dinâmicas (Nome / CPF / remover) — formset dinâmico.
- **Footer sticky** (bottom): Cancelar (outline) + Salvar (graphite).

---

## 4. Padrões reutilizáveis a extrair (para o CSS/partials)

- **Card:** `background:var(--surface);border:1px solid var(--border);border-radius:10px;box-shadow:var(--shadow)`; header interno `padding:14px 18px;border-bottom:1px solid var(--border);font-weight:700;font-size:14px` (ícone laranja opcional).
- **Badge/pill de status:** `padding:3px 11px;border-radius:100px;font-size:11.5px;font-weight:700` + par `--x-bg`/`--x`. Mapear: Ocupado/Pago/ok=ok; Vago/atrasado=danger; Ativo/em vigência=info; pendente=warn; neutro=neu.
- **Botão primário laranja:** `background:var(--brand);color:#22262B;font-weight:700`.
- **Botão graphite** (ação principal escura): `background:var(--graphite);color:#fff`.
- **Botão outline:** `border:1px solid var(--border-strong);background:var(--surface);color:var(--ink)`.
- **Botões de ação de linha** (Ver/Editar/Excluir): neutro / `border+bg` laranja-soft / danger-soft.
- **Segmented control:** wrapper `background:var(--sunken);border:1px solid var(--border);border-radius:7px;padding:3px`; item ativo `background:var(--surface);box-shadow:var(--shadow)`.
- **Input file dashed** (upload GED): `border:1px dashed var(--border-strong)` + botão Enviar graphite.
- **Table:** header `background:var(--sunken)`, th uppercase 11px muted; linhas `border-top:1px solid var(--border)`.
- **Empty state:** `bi-inbox` + texto muted centralizado.

---

## 5. Decisões de arquitetura a resolver no plano

1. **Bootstrap 5.3 fica ou sai?** O redesign é 100% CSS custom com tokens próprios. Opções: (a) remover Bootstrap e reescrever `base.html`+partials com o novo CSS; (b) manter Bootstrap para JS (toasts, modais, collapse) e sobrepor visual. Avaliar impacto nos componentes que hoje dependem de classes Bootstrap.
2. **Inline styles dos mockups → classes CSS.** Os `.dc.html` usam style inline; produção deve consolidar em `static/css/` (ex.: `custom.css` ou novo `shelter.css`) com as CSS vars + classes utilitárias/componentes.
3. **Dark mode:** adicionar `data-theme` no `<html>`, script de toggle + persistência (localStorage), garantir que Flatpickr, selects nativos e Chart.js herdem/reajam.
4. **Chart.js:** hoje o dashboard passa dados como contexto; ver como os gráficos são renderizados atualmente e migrar para os dois gráficos do mock (donut + barras) lendo CSS vars.
5. **Toggle Cards/Tabela** na listagem de Imóveis: precisa de JS leve (sem framework) + persistência opcional.
6. **Fidelidade de domínio:** casar cada elemento visual com o model/view/campo real (status vago/ocupado por signal, GED versionado com histórico, laudo dependente de imóvel, faixas de renda, etc.). Não inventar campos.
7. Login provavelmente sai do `base.html` (layout dedicado sem sidebar).
8. Encoding: editar templates **só com o Edit tool** (nunca Set-Content/Get-Content do PowerShell) — regra do projeto.
