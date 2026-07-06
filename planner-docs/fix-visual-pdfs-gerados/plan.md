# Plano — Fix visual dos PDFs gerados (Contrato / Laudo / Recibo)

## Objetivo

Corrigir divergências visuais entre os 3 PDFs gerados pelo sistema
(`templates/documentos/{contrato,laudo,recibo}_pdf.html`, motor **xhtml2pdf**) e os
mockups de referência (`docs/pdf-models/*.html`), sem alterar models, views,
lógica de geração/versionamento (GED) ou dados. Escopo 100% CSS/HTML dos
templates de PDF.

O CSS dos templates de PDF já é **textualmente idêntico** ao CSS dos mockups
(comparação linha a linha confirmou isso). A divergência visual não vem de CSS
diferente, e sim de **propriedades CSS que o xhtml2pdf não suporta ou suporta
de forma diferente de um navegador**. Este plano identifica, com evidência
empírica (renders de teste reais gerados localmente com o xhtml2pdf 0.2.17
instalado no projeto, mais leitura do código-fonte da lib em
`venv/Lib/site-packages/xhtml2pdf`), quais problemas são reais bugs de
renderização e qual o CSS/HTML de substituição comprovado.

## Estado atual (investigação)

- **`text-transform` não existe na lista de propriedades suportadas pelo
  xhtml2pdf** (`xhtml2pdf/parser.py:attrNames`). É silenciosamente ignorado.
  Todo texto que depende de `text-transform: uppercase` (título do documento,
  cabeçalhos de seção `.sec`, labels `.flabel`/`.card-label`, cabeçalhos de
  tabela `.data-table th`, alguns rótulos inline do laudo/recibo) renderiza em
  case normal no PDF, mesmo com a regra CSS presente.
- **`letter-spacing` É suportado** (`context.py`/`reportlab_paragraph.py` via
  `setCharSpace`) — confirmado visualmente no PDF real
  (`media/contratos/gerados/contrato_10.pdf`) e em testes isolados. Não requer
  correção.
- **`margin: ... auto ...` não é suportado** — o parser (`util.py:getSize`)
  trata o token `auto` como `0`. Isso quebra especificamente
  `.doc-title-underline` (barra decorativa sob o título), que depende de
  `margin: 10px auto 0 auto` para centralizar. Confirmado empiricamente: em um
  render isolado, a barra **não aparece em lugar nenhum** (nem à esquerda, nem
  centralizada) — o PDF real (`contrato_10.pdf`) confirma a mesma ausência
  total abaixo do título.
- **`background-color`/`border` em `<div>` de bloco funcionam corretamente**
  quando o `<div>` contém um único nó de texto direto (confirmado no PDF real:
  `.sec` e `.note-box` renderizam faixa de fundo cheia + barra lateral,
  largura total, sem problema). **Não é um bug** — a percepção de "fundo fraco"
  relatada vem majoritariamente da ausência do uppercase (item acima), não de
  falha de background.
- **Bug real confirmado por teste**: quando um `<div>` com `border` envolve
  **múltiplos filhos block-level** (ex.: `.card` envolvendo `.card-label` +
  `.card-value`), o xhtml2pdf desenha **uma borda separada para cada filho**
  em vez de uma única caixa ao redor de todo o conteúdo — produzindo o efeito
  de "grade de tabela genérica" relatado pelo usuário. Testado e reproduzido
  isoladamente. A correção comprovada é aplicar `border`/`padding`
  diretamente na `<td>` da tabela `.cards` (célula de tabela tem tratamento de
  borda próprio no xhtml2pdf — `tables.py`, comando `BOX` do `TableStyle` — e
  não sofre esse problema), eliminando o `<div class="card">` wrapper.
- Todas as correções abaixo foram **validadas com renders de teste reais**
  (PDF gerado localmente via `xhtml2pdf.pisa.CreatePDF`) antes de entrarem
  neste plano — não são apenas hipóteses de leitura de código.

## Resumo dos módulos

| Módulo | Escopo | Depende de |
|---|---|---|
| `01-base-pdf-fundamentos.md` | `base_pdf.html`: padrão de sublinhado do título (tabela centralizada), reestruturação de `.cards`/`.card`/`.card-label`/`.card-value`, convenção de uppercase literal (documentada como comentário CSS) | — |
| `02-contrato-pdf-uppercase-e-cards.md` | `contrato_pdf.html`: aplicar uppercase literal nos títulos/seções/labels estáticos e via filtro `\|upper` nos dinâmicos; adaptar markup do bloco "Condições da Locação" ao novo padrão de `.cards` | 01 |
| `03-laudo-pdf-uppercase-e-cards.md` | `laudo_pdf.html`: idem contrato + cabeçalhos de `.data-table` + card com borda colorida do "Resumo da Vistoria" + rótulo "Testemunhas" | 01 |
| `04-recibo-pdf-uppercase.md` | `recibo_pdf.html`: título, "Composição do Valor", rótulo "Quantia recebida" e labels de campo | 01 |
| `05-validacao-visual-manual.md` | Checklist de comparação visual PDF-real × mockup, por documento, após os módulos 01–04 implementados | 01, 02, 03, 04 |

## Ordem de implementação

1. `01-base-pdf-fundamentos.md` (obrigatório primeiro — os outros 3 módulos dependem da nova estrutura de `.cards`)
2. `02`, `03`, `04` — podem ser feitos em qualquer ordem entre si (arquivos independentes)
3. `05-validacao-visual-manual.md` — só faz sentido depois de 01–04 implementados

## Observações gerais

- Nenhum model, view, form, signal, migration ou lógica de `imoveis/pdf.py`
  é alterado. Only `templates/documentos/*.html`.
- Os testes automatizados de PDF em `imoveis/tests.py` (classe
  `DocumentoGeradoTests` e afins) fazem apenas asserts estruturais (existência
  de PDF, hash, versão) — não fazem assert de CSS/pixel, portanto não devem
  quebrar com estas mudanças. Ainda assim, rodar a suíte completa depois de
  cada módulo é recomendado (`venv/Scripts/python manage.py test imoveis`).
- **Risco de encoding**: os textos ficarão com muitos acentos maiúsculos em
  português (Á, Ç, Ã, Õ, É). CLAUDE.md já proíbe editar templates com
  `Get-Content`/`Set-Content` do PowerShell 5.1 (corrompe UTF-8) — usar
  sempre a ferramenta de edição (Edit tool), nunca comandos de shell para
  reescrever esses arquivos.
- `docs/07_design_ui_ux.md` (seção 17, linha ~305) lista as classes CSS atuais
  dos PDFs, incluindo `.card` — essa lista precisa ser atualizada após o
  módulo 01 (a classe `.card` deixa de existir, vira `.cards td`).
