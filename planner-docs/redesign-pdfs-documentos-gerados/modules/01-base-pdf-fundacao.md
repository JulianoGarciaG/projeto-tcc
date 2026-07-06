# Objetivo

Reescrever `templates/documentos/base_pdf.html` para conter o CSS **comum**
aos 3 mockups (`docs/pdf-models/*.html`) — cabeçalho (logo + nº do documento
+ data de emissão), régua de marca, título, seções, "cards", tabela de campos
rotulados, caixa de nota/destaque, tabela de assinaturas e rodapé —, servindo
de base para os templates filhos (módulos 02, 03, 04) sem duplicar CSS.

Este módulo é uma **réplica fiel** do CSS/HTML dos mockups, não uma
reinterpretação: os 3 arquivos em `docs/pdf-models/` foram escritos
deliberadamente em CSS 2.1 puro + tabelas (nenhum flexbox, grid,
`border-radius`, `box-shadow` ou `position: fixed`) para já serem
compatíveis com o `xhtml2pdf`. O trabalho aqui é transcrever, não adaptar.

---

# Arquivos afetados

- `templates/documentos/base_pdf.html` (reescrita completa)

---

## Documentação relacionada

- docs/07_design_ui_ux.md
  Avaliar se a paleta/tokens usados nos PDFs (em especial `#9A6B00`, cor de
  texto ainda não documentada, usada em badges/destaques dourados sobre fundo
  claro) devem ser adicionados à tabela de paleta de cores ou a uma seção
  específica de "tokens de PDF". Se a equipe decidir não formalizar, registrar
  a decisão em comentário no CSS do template.
- docs/03_modelagem_dados.md
  Sem impacto (nenhum campo de model é criado/alterado nesta parte visual).
- docs/04_regras_de_negocio.md
  Sem impacto (regra "PDF só via botão" não muda).

---

# Dependências

Nenhuma (módulo raiz — 02, 03 e 04 dependem dele).

---

# Detalhamento técnico

## Comparação linha a linha dos 3 mockups — o que é comum

Confirmado por inspeção direta de `docs/pdf-models/contrato_locacao.html`,
`laudo_vistoria.html` e `recibo_pagamento.html`: as classes abaixo são
idênticas (ou têm apenas diferenças triviais de `font-size`/`margin`) nos
três arquivos e devem migrar para `base_pdf.html`:

- `.doc-header`, `.doc-header td`, `.doc-logo`, `.doc-meta`, `.doc-meta strong`
- `.brand-rule`
- `.doc-title-wrap`, `.doc-title`, `.doc-title-underline` (recibo não usa o
  underline — ver nota abaixo)
- `.sec`, `.sec .sec-note` (o `.sec-note` só é usado no contrato, mas é uma
  variação trivial da mesma classe — manter no base)
- `.fields`, `.fields td`, `.fields td.pad`, `.flabel`, `.fval`
- `.cards`, `.cards td`, `.card`, `.card-label`, `.card-value`
- `.note-box`
- `.sign-table`, `.sign-cell`, `.sign-line`, `.sign-role`
- `.doc-footer`
- `.avoid-break`
- `@page { size: A4; margin: 2cm; }` e o `body { ... }` base (fonte, tamanho,
  cor, `line-height`)

Nota sobre `.doc-title-underline`: no mockup do recibo o título não tem a
barra inferior (`recibo_pagamento.html` linha 39-41 não inclui a
`<div class="doc-title-underline">`). Manter a classe no CSS base (é
inofensiva se não usada), mas o bloco de título do recibo (módulo 04) não a
renderiza — replicar exatamente como no mockup, não "padronizar" adicionando
algo que o mockup do recibo não tem.

## O que NÃO vai para o base (é específico de um único documento)

- `.data-table`, `.badge`/`.badge-bom`/`.badge-reg`/`.badge-ruim`, `.row-alt`
  — usados só em `laudo_vistoria.html`. Ficam declarados dentro de
  `laudo_pdf.html` (módulo 03), não em `base_pdf.html`.
- A caixa de destaque "Quantia recebida" (tabela com barra lateral dourada de
  5px e tipografia grande para o valor) — usada só em `recibo_pagamento.html`.
  Fica declarada dentro de `recibo_pdf.html` (módulo 04).

## Estrutura de blocks a manter/criar

Manter os blocks existentes para minimizar o diff nos filhos:
- `{% block titulo_doc %}` — título principal do documento (ex.: "Contrato de
  Locação de Imóvel").
- `{% block conteudo %}` — corpo específico de cada documento.

Adicionar um novo block para o cabeçalho:
- `{% block doc_meta %}{% endblock %}` — conteúdo da célula direita do
  cabeçalho (ex.: `CONTRATO Nº 42<br>Emitido em 05/07/2026`). Cada filho
  sobrescreve com seu próprio rótulo/objeto. Default vazio (não quebra se um
  filho não sobrescrever).

## Cabeçalho com nº do documento + data de emissão

Os mockups fixam textos como `CONTRATO Nº 2025-0142` — não existe esse campo
nos models (confirmado fora de escopo no `plan.md`). Cada filho deve
sobrescrever `{% block doc_meta %}` assim:

- Contrato: `CONTRATO Nº {{ contrato.pk }}<br>Emitido em {{ contrato.criado_em|date:"d/m/Y" }}`
- Laudo: `LAUDO Nº {{ laudo.pk }}<br>Emitido em {{ laudo.criado_em|date:"d/m/Y" }}`
- Recibo: `RECIBO Nº {{ recibo.pk }}<br>Emitido em {{ recibo.criado_em|date:"d/m/Y" }}`

(Implementação real do texto de cada um fica nos módulos 02/03/04 — este
módulo só precisa garantir que o block existe e tem fallback vazio.)

## Única ressalva técnica (não é adaptação de layout, é validação de motor)

Os mockups já são 100% CSS 2.1 + tabelas, então não há decisão de design a
tomar aqui. Existem apenas 2 combinações que precisam ser confirmadas no PDF
real gerado pelo pisa (não só no preview em navegador), porque implementações
de subconjunto de CSS podem ter bugs específicos de renderização mesmo para
propriedades "suportadas":

1. `letter-spacing` combinado com `text-transform: uppercase` em `.doc-title`,
   `.sec`, `.flabel`, `.card-label` — presente em todos os 3 mockups.
2. `border-collapse: collapse` em tabelas aninhadas (`.fields` dentro de uma
   célula de `.cards`, e — no laudo — `.data-table` dentro do bloco de
   cômodo).

Essas 2 combinações são testadas no módulo 06. Caso alguma não renderize
como no mockup, o ajuste é pontual (ex.: reduzir `letter-spacing` ou remover
`border-collapse` de uma tabela específica), nunca uma reestruturação do
layout.

## Logo

Sempre usar `{% static 'assets/Shelter_LOGO.jpg' %}` (como já é feito hoje em
`base_pdf.html`), resolvido por `link_callback` em `imoveis/pdf.py` (já
existente, não mexer) — nunca o caminho absoluto do Windows usado nos
arquivos de `docs/pdf-models/` (esses são mockups locais, não templates
funcionais).

---

# Critérios de aceite

- [ ] `base_pdf.html` não contém mais o CSS antigo (`.cabecalho`, `h1.titulo-doc`,
      `h2.secao`, `table.dados`, `table.grade`, `.destaque`, `.assinatura`,
      `.linha-assinatura`, `.rodape`) — substituído pela réplica do CSS comum
      dos mockups.
- [ ] Todas as classes listadas em "o que é comum" estão presentes e com os
      mesmos valores de cor/espaçamento dos mockups (comparação lado a lado).
- [ ] Nenhuma classe específica de um único documento (`.data-table`,
      `.badge*`, `.row-alt`, caixa de destaque do recibo) foi incluída no
      `base_pdf.html`.
- [ ] Logo continua carregada via `{% static %}` (não usar caminho absoluto).
- [ ] Block `doc_meta` existe com corpo vazio por padrão.
- [ ] `@page { size: A4; margin: 2cm; }` mantido, idêntico ao mockup.
- [ ] `python manage.py check` roda sem erros após a alteração.

---

# Riscos

- Classes CSS renomeadas quebram testes que fazem `assertIn`/`assertNotIn` em
  texto ou classe (ex.: `assinatura-laudo`) — mitigado no módulo 05, mas o
  nome exato das classes usadas aqui deve ser comunicado nos módulos 02/03/04
  para consistência (a recomendação é usar exatamente os nomes dos mockups,
  já que a réplica é 1:1).
- `letter-spacing` + `text-transform: uppercase` e `border-collapse` em
  tabelas aninhadas podem ter comportamento sutilmente diferente no pisa real
  em relação ao preview em navegador — validar no PDF de fato (módulo 06)
  antes de considerar o layout "pronto", mesmo que o HTML pareça correto.
