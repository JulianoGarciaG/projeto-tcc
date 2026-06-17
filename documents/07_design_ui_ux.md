# 07 — Design & UI/UX
> Sistema Integrado de Gestão Imobiliária

---

## 1. Identidade Visual

⚠️ Inserir: diretrizes de aplicação da logo (sidebar, login, topbar, favicon)

### Personalidade
O sistema deve transmitir uma experiência **moderna e limpa** — interface sem ruído visual, foco no conteúdo, espaçamento generoso e hierarquia clara.

---

## 2. Paleta de Cores

| Variável | Hex | Uso |
|---|---|---|
| `--color-primary` | `#F2B441` | Botões principais, destaques, bordas ativas, badges |
| `--color-secondary` | `#3A3A3A` | Texto principal, sidebar, elementos escuros |
| `--color-background` | `#F7F3EA` | Background geral das páginas |
| `--color-surface` | `#F7F7F7` | Cards, modais, sidebar, formulários |
| `--color-text-light` | `#FFFFFF` | Texto sobre fundos escuros ou dourados |
| `--color-text-muted` | `#888888` | Textos secundários, labels, placeholders |
| `--color-border` | `#E0E0E0` | Bordas de inputs, divisores, separadores |

### Cores Semânticas (status)
| Variável | Hex | Uso |
|---|---|---|
| `--color-success` | `#2E7D32` | Pago, ocupado, ativo |
| `--color-warning` | `#F2B441` | Pendente, atenção (reutiliza primária) |
| `--color-danger` | `#C62828` | Atrasado, vago, rescindido, exclusão |
| `--color-neutral` | `#757575` | Encerrado, arquivado, inativo |
| `--color-info` | `#1565C0` | Informativo, links |

---

## 3. Tipografia

| Elemento | Fonte | Peso | Tamanho |
|---|---|---|---|
| Fonte principal | Gotham | — | — |
| Títulos (h1–h2) | Gotham | Bold (700) | 1.5rem – 2rem |
| Subtítulos (h3–h4) | Gotham | Medium (500) | 1.1rem – 1.3rem |
| Corpo de texto | Gotham | Regular (400) | 0.9rem |
| Labels de formulário | Gotham | Medium (500) | 0.87rem |
| Texto auxiliar / muted | Gotham | Regular (400) | 0.78rem |
| Badges / status | Gotham | Bold (700) | 0.74rem |

> ⚠️ Gotham é uma fonte comercial licenciada (Hoefler & Co).
> Licença de uso pendente de definição.
> Enquanto não resolvida, utilizar **Montserrat** (Google Fonts) como substituta temporária — geometria e proporções similares.

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
| Topbar | 60px (fixa no topo) |
| Conteúdo | `margin-left: 260px`, `margin-top: 60px` |
| Padding interno do conteúdo | `1.75rem` |

---

## 5. Sidebar

### Especificações
- **Fundo:** `#3A3A3A`
- **Texto:** `#FFFFFF` com opacidade `0.75`
- **Ícones:** Bootstrap Icons, tamanho `1rem`, largura fixa `1.2rem`
- **Itens:** ícone + texto, padding `0.6rem 1.5rem`
- **Seções (labels):** texto em caixa alta, tamanho `0.68rem`, opacidade `0.35`

### Estado Ativo
- Borda esquerda: `3px solid #F2B441`
- Fundo: `rgba(255, 255, 255, 0.08)` (levemente iluminado)
- Texto: `#FFFFFF` opacidade `1`
- Padding esquerdo compensado: `calc(1.5rem - 3px)`

### Estado Hover
- Fundo: `rgba(255, 255, 255, 0.05)`
- Texto: `#FFFFFF` opacidade `1`

### Seções do Menu
```
[Logo / Nome da empresa]   ⚠️ Inserir

─── Cadastros ───
  Imóveis
  Proprietários
  Inquilinos

─── Operações ───
  Contratos
  Laudos de Vistoria
  Financeiro

─── Documentos ───
  GED — Documentos

─── Administração ─── (somente is_staff)
  Painel Admin
```

---

## 6. Topbar

- **Fundo:** `#F7F7F7`
- **Borda inferior:** `1px solid #E0E0E0`
- **Altura:** `60px`
- **Conteúdo:** título da página (esquerda) + mensagens flash + info do usuário + botão logout (direita)
- **Título:** fonte Gotham Medium, `0.95rem`, cor `#3A3A3A`
- **Info do usuário:** fonte `0.85rem`, cor `#888888`

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

---

## 13. Gráficos (Dashboard)

- **Biblioteca:** Chart.js 4.4.4
- **Gráfico de rosca:** ocupação dos imóveis (ocupado / vago / manutenção)
  - Cores: `#2E7D32`, `#C62828`, `#F2B441`
  - Borda entre fatias: `2px solid #F7F3EA`
- **Gráfico de barras:** recebimentos vs. pendências (últimos 6 meses)
  - Recebido: `rgba(46, 125, 50, 0.75)`
  - Pendente/Atrasado: `rgba(198, 40, 40, 0.65)`
  - Border-radius das barras: `5px`
  - Eixo Y: formatado como `R$ valor`

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

## 16. Página de Login

- Layout **split**: dois painéis lado a lado
- **Painel esquerdo:** fundo `#3A3A3A`, elementos decorativos (blobs, grade de pontos), texto de boas-vindas, logo da empresa ⚠️ Inserir
- **Painel direito:** fundo `#F7F7F7`, formulário centralizado com inputs estilizados
- Border-radius do container: `8px` (desktop), sem radius (mobile)
- No mobile: apenas o painel direito (formulário) é exibido
