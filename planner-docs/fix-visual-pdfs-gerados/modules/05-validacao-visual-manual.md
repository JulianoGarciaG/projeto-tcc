# Objetivo

Validar visualmente, apos os modulos 01-04 implementados, que os 3 PDFs
gerados pelo sistema reproduzem fielmente os mockups de docs/pdf-models/,
usando um contrato/laudo/recibo real do banco de dev (ou dados de teste
representativos) para gerar os PDFs via fluxo normal do sistema (botao
"Regerar PDF"), e comparando lado a lado com o mockup correspondente.

Este modulo nao altera nenhum arquivo de template - e um checklist de
verificacao. Caso alguma divergencia seja encontrada, ela deve ser corrigida
no modulo correspondente (01-04) e o item deste checklist revalidado.

---

# Arquivos afetados

Nenhum (modulo de validacao, sem edicao de codigo).

---

## Documentacao relacionada

- docs/07_design_ui_ux.md
  Apos validacao ok, confirmar que a secao 17 (linha ~305) reflete a lista
  de classes CSS atualizada (.card removida, .cards td documentada) - ajuste
  de texto, sem mudanca de conteudo tecnico.

---

# Dependencias

Depende dos modulos 01, 02, 03 e 04 - so faz sentido executar depois que
todos os 4 estiverem implementados.

---

# Roteiro de validacao

Para cada um dos 3 documentos, gerar o PDF real pelo fluxo do sistema
(tela de detalhe do Contrato/Laudo/Recibo -> botao "Regerar PDF") usando um
registro com o maximo de campos preenchidos possivel (fiador, observacoes,
testemunhas, todas as parcelas de valor no recibo), e abrir o PDF resultante
lado a lado com o mockup HTML correspondente (aberto em um navegador) de
docs/pdf-models/.

## Checklist - Contrato (contrato_pdf.html vs docs/pdf-models/contrato_locacao.html)

- [ ] Titulo "CONTRATO DE LOCACAO DE IMOVEL" em caixa alta, centralizado,
      com a barra laranja centralizada logo abaixo.
- [ ] Cada header de secao (.sec) aparece em caixa alta, com fundo cream de
      largura total e barra lateral laranja.
- [ ] "(Pessoa Fisica)"/"(Pessoa Juridica)" ao lado de "INFORMACOES DO
      LOCATARIO" aparece em caixa alta e cor cinza (mais leve que o
      titulo da secao).
- [ ] Todos os labels de campo (.flabel) em caixa alta.
- [ ] Bloco "CONDICOES DA LOCACAO" com 4 cartoes separados por espaco
      visivel, cada um com borda propria, label pequeno em caixa alta no
      topo e valor grande em negrito.
- [ ] Bloco "Fiador"/"FIADORES" (plural correto quando ha mais de um
      fiador) segue o mesmo padrao dos demais campos.
- [ ] Bloco "OBSERVACOES" com fundo cream e barra lateral.
- [ ] Assinaturas alinhadas, com nome + papel (Locador/Locatario).

## Checklist - Laudo (laudo_pdf.html vs docs/pdf-models/laudo_vistoria.html)

- [ ] Titulo "LAUDO DE VISTORIA - ENTRADA" ou "- SAIDA" em caixa alta, com
      barra laranja centralizada abaixo.
- [ ] Headers de secao (.sec) em caixa alta.
- [ ] Labels da secao "IDENTIFICACAO" em caixa alta.
- [ ] Legenda BOM/REGULAR/RUIM com as cores corretas.
- [ ] Tabela de itens por comodo com cabecalho "ITEM"/"ESTADO"/"OBSERVACAO"
      em caixa alta, faixa lateral colorida por estado, linhas alternadas
      (row-alt) visiveis.
- [ ] Bloco "RESUMO DA VISTORIA" com 4 cartoes separados; os 3 cartoes
      Bom/Regular/Ruim com barra superior colorida (verde/dourado/vermelho)
      visivel junto com a borda cinza padrao dos outros lados.
- [ ] Bloco "OBSERVACOES GERAIS" com fundo cream.
- [ ] Rotulo "TESTEMUNHAS" em caixa alta antes do bloco de assinaturas de
      testemunhas (quando houver).

## Checklist - Recibo (recibo_pdf.html vs docs/pdf-models/recibo_pagamento.html)

- [ ] Titulo "RECIBO" ou "RECIBO - PARCELA X/Y" em caixa alta (sem barra
      decorativa abaixo - o recibo nao usa essa barra, conforme mockup).
- [ ] Caixa de destaque "QUANTIA RECEBIDA" em caixa alta, com valor grande
      em negrito.
- [ ] Labels de campo (Imovel, Recebemos de, Periodo correspondente,
      Vencimento) em caixa alta.
- [ ] Header de secao "COMPOSICAO DO VALOR" em caixa alta com fundo cream.
- [ ] Linha "Somatorio" com fundo cream e valor em negrito.
- [ ] Bloco de assinatura centralizado corretamente.

## Regressao geral

- [ ] venv/Scripts/python manage.py test imoveis - todos os 72 testes
      passam sem alteracao.
- [ ] Nenhuma quebra visual em documentos SEM fiador, SEM observacoes, SEM
      testemunhas (campos opcionais que somem condicionalmente) - gerar
      tambem um PDF de cada tipo com o minimo de campos preenchidos.

---

# Criterios de aceite

- [ ] Todos os itens dos 3 checklists acima marcados como corretos.
- [ ] Suite de testes automatizados (72 testes) passando.

---

# Riscos

- Validacao e subjetiva (comparacao visual olho a olho) - registrar prints
  de tela ou anotacoes de qualquer divergencia residual encontrada, para
  decidir se justifica um modulo de ajuste adicional fora deste plano.
