# Brief + Prompt — Redesign visual do Shelter

> Cole tudo isto no Claude (claude.ai) e **anexe as imagens** nos pontos marcados com `[INSERIR IMAGEM: ...]`.
> A Parte 1 é a instrução (o "prompt"). A Parte 2 é o contexto (o "brief"). Não precisa editar nada — só trocar os placeholders de imagem.

---

## PARTE 1 — PROMPT (instrução para o Claude)

Você é um designer de produto sênior especializado em sistemas web B2B (ferramentas internas / back-office). Vou te dar o design system atual e o inventário de telas de um sistema de gestão imobiliária chamado **Shelter**, mais screenshots das telas reais. Quero que você proponha um **novo visual** para o sistema.

**Objetivo:** modernizar a identidade visual mantendo o sistema utilizável e denso (é uma ferramenta de trabalho, não uma landing page). Não é um redesign de fluxo/UX — a estrutura de navegação e o conteúdo de cada tela permanecem. É um redesign de **linguagem visual**: cor, tipografia, espaçamento, componentes, hierarquia, "sensação".

**O que eu quero que você entregue, nesta ordem:**

1. **Diagnóstico** (curto) — o que enfraquece o visual atual, olhando os screenshots.
2. **Direção de design** — 1 conceito visual recomendado (não 3), descrito em palavras: personalidade, paleta proposta (com hex), tipografia, tratamento de superfícies/sombras/bordas, densidade. Se fizer sentido, proponha suporte a **modo escuro**.
3. **Mockups em HTML** — gere as telas prioritárias como **artefatos HTML autocontidos** (CSS inline, sem dependências externas exceto se necessário). Comece por, nesta ordem: **(a) Dashboard, (b) Listagem, (c) Detalhe**. Depois Login e Formulário. Cada mockup deve ser fiel ao conteúdo real descrito no brief — mesmos KPIs, mesmas colunas, mesmos campos — só com a nova roupagem.
4. **Guia de aplicação** — como traduzir isso de volta para o stack (Bootstrap 5.3 + CSS custom via variáveis). Liste as variáveis CSS a alterar e os componentes afetados.

**Restrições técnicas (importante — o mockup tem que ser implementável no stack real):**
- Stack: **Django templates + Bootstrap 5.3 + Bootstrap Icons + CSS custom com variáveis** (`--color-*`). **Sem build system, sem framework JS** (só Chart.js para gráficos). Nada de Tailwind, React, Sass.
- O tema é controlado por variáveis CSS em `:root`. Prefira soluções que virem troca de variáveis + ajustes de componente, não reescrita total.
- Fonte atual: Montserrat (Google Fonts) como substituta da Gotham. Pode propor outra fonte do Google Fonts se justificar.
- Densidade de ferramenta interna: tabelas com muitas linhas, formulários longos. Não sacrifique densidade por "respiro" decorativo.
- Português (pt-BR) em toda a interface.

**Formato:** vá por partes. Entregue diagnóstico + direção primeiro e **pergunte se aprovo antes de gerar os mockups HTML**.

---

## PARTE 2 — BRIEF (contexto do sistema)

### O produto
**Shelter** — Sistema Integrado de Gestão Imobiliária (GED + BI) para uma administradora de imóveis. Ferramenta interna usada por funcionários, gestores, vistoriadores (em campo, mobile) e auditores. Faz CRUD de imóveis/pessoas/contratos, gestão documental (GED versionado), lançamentos financeiros e um dashboard de indicadores. É um sistema Django server-rendered, responsivo (usado também no celular em vistorias).

### Chassi (presente em todas as telas exceto Login)
- **Sidebar fixa** 260px, fundo grafite escuro, sempre expandida no desktop; no mobile vira drawer com overlay (hamburger na topbar). Logo Shelter no topo. Seções: Cadastros (Imóveis, Proprietários, Inquilinos) · Operações (Contratos, Laudos, Financeiro, Recibos) · Documentos (GED) · Administração (só is_staff).
- **Topbar fixa** 60px: título da página à esquerda, info do usuário + logout à direita, mensagens flash (toasts).
- **Conteúdo**: fundo bege claro, padding 1.75rem.

### Design system atual (a substituir/evoluir)
**Paleta:**
| Papel | Hex |
|---|---|
| Primária (dourado) | `#F2B441` |
| Secundária (grafite) | `#3A3A3A` |
| Background | `#F7F3EA` |
| Surface (cards) | `#F7F7F7` |
| Texto muted | `#888888` |
| Borda | `#E0E0E0` |
| Sucesso / Perigo / Info | `#2E7D32` / `#C62828` / `#1565C0` |

**Tipografia:** Montserrat. Títulos 1.5–2rem bold; corpo 0.9rem; labels 0.87rem medium; badges 0.74rem bold.

**Componentes-chave:** section-card (header com borda inferior + body), KPI cards (borda esquerda colorida 4px + ícone em círculo suave), tabelas (cabeçalho bege caixa-alta, hover dourado suave), badges pill de status (ocupado/vago/ativo/pago/pendente/atrasado etc.), botões (primário dourado com texto grafite, secundário outline grafite, perigo vermelho), inputs (borda cinza, focus dourado com halo), modais de confirmação Bootstrap.

**Sensação pretendida hoje:** "moderna e limpa, sem ruído visual, foco no conteúdo, hierarquia clara". Avalie se o resultado atual entrega isso.

---

### Inventário de telas (7 arquétipos)

O sistema tem ~40 rotas, mas se resumem a 7 padrões visuais. Redesenhar um representante de cada cobre tudo.

**1. Login** — layout split de dois painéis. Painel esquerdo escuro com logo branca + decoração + texto de boas-vindas; painel direito claro com o formulário (usuário/senha) centralizado. No mobile só o painel do formulário.

**2. Dashboard / BI** (tela `/`) — a mais rica em dados:
- Barra de filtros: Imóvel (select), Data início, Data fim, Status (select), botões Filtrar/Limpar.
- **5 KPI cards**: Total de Imóveis (dourado), Ocupados (verde), Vagos + % vacância (vermelho), Contratos Ativos (azul), Inadimplentes (cinza). Cada um: ícone + número grande + label.
- **2 gráficos** (Chart.js): rosca "Ocupação dos imóveis" (ocupado/vago/manutenção) + barras "Recebimentos vs. Pendências — últimos 6 meses".
- **Tabela** "Últimos Lançamentos Financeiros": colunas Inquilino, Imóvel, Tipo, Vencimento, Valor, Status (badge).

**3. Listagem** (representante: Imóveis `/imoveis/`) — nota: Imóveis é a única listagem em **cards com foto**; as demais (Proprietários, Inquilinos, Contratos, Laudos, Recibos, Financeiro) são **tabelas**. Considere ambos os formatos.
- Barra de filtros em card (busca por texto + selects de status/tipo + Filtrar/Limpar).
- Linha de contagem de resultados + botão "Novo".
- Grid de cards: foto do imóvel, endereço (link), badge de status, bairro/cidade, tipo/categoria, proprietário, e botões ver/editar/excluir. Estado vazio com ícone.
- Modal de confirmação de exclusão.
- (Para o representante em tabela: linhas com dados + badge de status + ações ver/editar/excluir por linha.)

**4. Detalhe** (representante: Contrato `/contratos/<pk>/`) — a tela mais complexa:
- Barra de ações no topo: Voltar, Editar, **Regerar PDF**, baixar PDF gerado, Renovar, Distrato (condicionais ao status).
- Coluna esquerda: card "Informações" (lista de campos label/valor + badge de status no header: tipo, inquilino, imóvel, início/término, valor mensal, dia de vencimento, observações); card "Documentos" (GED) — lista de versões do PDF gerado + 4 blocos de anexo (Comprovante de Renda [PF], Contrato Social [PJ], Recibo de Chaves, Comprovante Anual), cada um com link "ver arquivo" e um mini-form de upload inline; card "Fiadores"; cards condicionais "Renovação" e "Distrato".
- Coluna direita: card "Lançamentos Financeiros" (tabela: tipo, vencimento, valor, status, comprovante + botão "Novo"); card "Laudos de Vistoria" (tabela: tipo, data, responsável, arquivo + botão "Novo").

**5. Formulário simples** (representante: Inquilino `/inquilinos/novo/`) — campos de texto com **máscaras** (CPF/CNPJ, RG, telefone, moeda) e **datepicker** (dd/mm/aaaa). Labels acima dos inputs, foco dourado com halo, botões Salvar/Cancelar no rodapé. Formulários costumam ser longos (muitos campos) — pense em agrupamento/seções.

**6. Formulário complexo** (representante: Laudo de Vistoria `/laudos/novo/`) — além dos campos normais: um **checklist de vistoria** (formset: ~32 itens em 5 cômodos, cada item com estado bom/regular/ruim), um **select dependente** (contrato filtrado pelo imóvel escolhido) e uma lista dinâmica de testemunhas. É a tela mais desafiadora de organizar visualmente.

**7. GED — Central de Documentos** (`/documentos/`) — grade/lista de todos os PDFs gerados pelo sistema (contratos, laudos, recibos) com versionamento: tipo, origem, número da versão, data, quem gerou, link de download.

**Fora de escopo:** os 3 PDFs gerados (contrato/laudo/recibo). São outro meio (impressão, renderizados por xhtml2pdf com restrições próprias) e já têm design definido — não misturar com o visual web.

---

### Imagens das telas reais

> Anexe os screenshots correspondentes abaixo (rodar `venv/Scripts/python manage.py runserver` e capturar).

- [INSERIR IMAGEM: Dashboard]
- [INSERIR IMAGEM: Listagem de Imóveis]
- [INSERIR IMAGEM: Detalhe de Contrato]
- [INSERIR IMAGEM: Login]
- [INSERIR IMAGEM: Formulário (Inquilino ou Laudo)]
- [INSERIR IMAGEM: Sidebar/Topbar em detalhe (opcional)]

---

### Prioridade de entrega
1. Dashboard · 2. Listagem · 3. Detalhe de Contrato → depois Login e Formulários.
Comece pelo diagnóstico + direção de design e aguarde aprovação antes dos mockups HTML.
