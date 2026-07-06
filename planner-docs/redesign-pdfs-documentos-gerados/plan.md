# Plano - Redesign dos PDFs gerados + GED versionado (S3-ready)

## Objetivo

1. Replicar FIELMENTE (1:1) o layout visual definido em
   docs/pdf-models/*.html nos tres documentos PDF gerados pelo sistema -
   Contrato, Laudo de Vistoria e Recibo - mantendo o motor xhtml2pdf e sem
   perder nenhum dado dinamico atualmente exibido.
2. Introduzir uma camada de GED versionado: cada geracao de PDF passa a criar
   um registro imutavel (DocumentoGerado), com numero de versao sequencial
   por origem, hash do arquivo e autor, sobre uma abstracao de storage
   pronta para migrar para S3 no futuro sem mudar codigo de aplicacao.

## Estado atual

- PDFs renderizados por xhtml2pdf a partir de templates/documentos/base_pdf.html
  (layout compartilhado com blocks titulo_doc/conteudo) + 3 templates filhos:
  contrato_pdf.html, laudo_pdf.html, recibo_pdf.html.
- Geracao so ocorre nas views _gerar_pdf_contrato / _gerar_pdf_laudo /
  _gerar_pdf_recibo (imoveis/views.py), chamadas pelas views *_gerar_pdf
  (padrao PRG - nunca ao salvar). Toda a logica de conversao HTML-PDF vive em
  imoveis/pdf.py (gerar_e_anexar, save_pdf_to_field, pdf_download_response,
  link_callback).
- Hoje o PDF gerado SOBRESCREVE o FileField do proprio registro
  (Contrato.documento_gerado, LaudoVistoria.documento_gerado, Recibo.arquivo)
  - nao existe historico de versoes, nem hash, nem autor.
- Os mockups em docs/pdf-models/ sao HTML standalone (sem Django template
  tags, dados ficticios, logo referenciado por caminho absoluto do Windows),
  mas foram escritos EXCLUSIVAMENTE em CSS 2.1 + tabelas - nada de flexbox,
  grid, border-radius, box-shadow ou position: fixed. Foram deliberadamente
  escritos para serem compativeis com o xhtml2pdf.
- O mockup ja usa exatamente a paleta de marca documentada em
  docs/07_design_ui_ux.md (#F2B441, #3A3A3A, #F7F3EA, #888888, #E0E0E0,
  #2E7D32, #C62828), com uma cor nova nao documentada: #9A6B00.
- Storage hoje e 100% FileSystemStorage implicito (padrao Django); nao ha
  configuracao STORAGES em core/settings.py. O padrao ja estabelecido no
  projeto para infraestrutura plugavel via .env e o de DB_ENGINE
  (core/settings.py, linhas 54-75) - o storage deve seguir o mesmo padrao.
- Templates que hoje leem documento_gerado/arquivo diretamente (revistos no
  modulo de GED): templates/contratos/contrato_detail.html,
  templates/laudos/laudo_detail.html, templates/recibos/recibo_detail.html,
  templates/ged/documentos.html (view documentos em imoveis/views.py).
- Ultima migration existente: 0008_alter_contrato_dia_vencimento_alter_fiador_rg_cpf_and_more.py
  - a nova migration deste plano sera 0009.

## Resumo dos modulos

| Modulo | Responsabilidade |
|---|---|
| 01-base-pdf-fundacao.md | Reescrever base_pdf.html com o CSS COMUM aos 3 mockups (header, brand-rule, doc-title, .sec, .fields/.flabel/.fval, .cards/.card, .note-box, .sign-table, .doc-footer, .avoid-break) - replica 1:1 |
| 02-contrato-pdf.md | Reescrever contrato_pdf.html replica fiel do mockup, com as variaveis de contexto atuais |
| 03-laudo-pdf.md | Reescrever laudo_pdf.html replica fiel do mockup (tabelas por comodo, badges, cards de resumo, testemunhas) - CSS especifico (.data-table, .badge*, .row-alt) local ao template |
| 04-recibo-pdf.md | Reescrever recibo_pdf.html replica fiel do mockup (destaque da quantia, composicao do valor) - CSS especifico do destaque local ao template |
| 05-ajuste-testes.md | Atualizar asserts de imoveis/tests.py que dependem de classes CSS/textos substituidos pelo redesign |
| 06-validacao-manual.md | Checklist de geracao e inspecao visual dos 3 PDFs, incluindo os 2 pontos de risco real do pisa (letter-spacing+uppercase; border-collapse em tabelas aninhadas) |
| 07-model-documento-gerado.md | Novo model DocumentoGerado (versoes imutaveis) + migration 0009 + admin |
| 08-storage-s3-ready.md | Configuracao STORAGES plugavel via .env (padrao analogo ao DB_ENGINE), upload_to deterministico, sem adicionar boto3/django-storages agora |
| 09-integracao-pdf-versionamento.md | Alterar imoveis/pdf.py e as views *_gerar_pdf para criar uma versao de DocumentoGerado a cada geracao; estrategia de convivencia com os campos legados documento_gerado/arquivo |
| 10-ged-listagem-versoes.md | Atualizar templates/ged/documentos.html, contrato_detail.html, laudo_detail.html, recibo_detail.html e a view documentos para listar todas as versoes (nao so a ultima) |
| 11-testes-ged-versionado.md | Testes da nova camada: criacao de versao, incremento sequencial por origem, hash, imutabilidade, storage plugavel |

## Ordem de implementacao

1. 01-base-pdf-fundacao.md
2. 02-contrato-pdf.md, 03-laudo-pdf.md, 04-recibo-pdf.md (paralelos entre si, dependem so de 01)
3. 05-ajuste-testes.md (depende de 02, 03, 04)
4. 06-validacao-manual.md (depende de 05)
5. 07-model-documento-gerado.md (independente da parte visual - pode comecar em paralelo ao passo 1, listado depois por clareza narrativa)
6. 08-storage-s3-ready.md (depende de 07 - o FileField de DocumentoGerado precisa existir para apontar para o storage configuravel)
7. 09-integracao-pdf-versionamento.md (depende de 07, 08 e da reescrita visual 02/03/04, pois e o ponto em que a geracao do PDF final passa a alimentar o novo model)
8. 10-ged-listagem-versoes.md (depende de 09)
9. 11-testes-ged-versionado.md (depende de 07, 08, 09 - roda por ultimo, junto com 05, antes do fechamento do plano)

> Observacao: os modulos 01-06 (visual) e 07-08 (fundacao do GED) sao
> trilhas independentes e podem ser implementadas em paralelo por
> engenheiros diferentes. Elas convergem no modulo 09.

## Dependencias entre modulos

- 02, 03, 04 dependem de 01.
- 05 depende de 02, 03, 04.
- 06 depende de 05.
- 08 depende de 07.
- 09 depende de 07, 08, e de 02/03/04 (o PDF final gerado e o que vira DocumentoGerado).
- 10 depende de 09.
- 11 depende de 07, 08, 09.

## Estrategia recomendada (parte visual)

REPLICAR os 4 templates 1:1 a partir dos mockups - nao "adaptar" ou
"aproximar". Os mockups ja foram escritos em CSS 2.1 + tabelas
especificamente para rodar no xhtml2pdf, entao nao ha necessidade de
reinterpretar layout, apenas de:

- Transcrever as mesmas classes CSS, cores, espacamentos e estrutura de
  tabelas dos mockups para os templates Django.
- Substituir os dados estaticos ficticios dos mockups pelas variaveis de
  contexto reais ja fornecidas pelas views (nenhuma view muda por causa da
  parte visual).
- Extrair para base_pdf.html apenas o CSS realmente comum aos 3 mockups
  (comparacao linha a linha confirma que .doc-header, .doc-logo, .doc-meta,
  .brand-rule, .doc-title-wrap/.doc-title/.doc-title-underline, .sec,
  .fields/.fields td/.flabel/.fval, .cards/.card/.card-label/.card-value,
  .note-box, .sign-table/.sign-cell/.sign-line/.sign-role, .doc-footer,
  .avoid-break sao identicos ou quase identicos nos 3 arquivos) - detalhes
  no modulo 01.
- Manter no template filho apenas o CSS EXCLUSIVO daquele documento: laudo
  (.data-table, .badge/.badge-bom/.badge-reg/.badge-ruim, .row-alt) e recibo
  (a caixa de destaque da quantia, que so existe nesse mockup).
- Unica ressalva tecnica remanescente (nao e "adaptacao de design", e
  validacao de compatibilidade real do pisa): confirmar no PDF gerado de
  fato (nao so no preview HTML) que (a) letter-spacing combinado com
  text-transform: uppercase renderiza igual ao mockup, e (b)
  border-collapse: collapse funciona nas tabelas aninhadas (.fields dentro
  de .card, .data-table dentro do bloco de comodo). Caso algo nao renderize
  fielmente, o fallback e documentado no modulo 06 (nunca mudar a estrutura
  de tabelas, so ajustar a propriedade CSS pontual que falhar).

## Estrategia recomendada (GED versionado)

- Novo model DocumentoGerado - um registro por geracao de PDF (imutavel),
  nunca atualizado apos criado. "Documento atual" = ultima versao
  (numero_versao mais alto) para aquela origem.
- Os campos legados documento_gerado (Contrato, LaudoVistoria) e arquivo
  (Recibo) sao MANTIDOS por compatibilidade, mas passam a ser espelhos
  automaticos da ultima versao (sincronizados pela propria funcao de
  geracao) - nao sao a fonte de verdade a partir de agora, apenas um atalho
  de leitura para nao quebrar templates/links existentes imediatamente. Ver
  modulo 09 para a decisao detalhada e a migracao dos PDFs ja existentes
  (registrados retroativamente como versao 1).
- Storage: usar a chave STORAGES do Django (padrao desde Django 4.2),
  configuravel por variavel de ambiente (STORAGE_BACKEND=filesystem|s3),
  seguindo o mesmo padrao de DB_ENGINE ja usado no projeto. Em dev,
  FileSystemStorage (nenhuma mudanca de comportamento). Documentar (sem
  implementar) o passo futuro de trocar para S3 via django-storages.
- HA MIGRATION nesta rodada (modulo 07, 0009_documentogerado.py) - a
  afirmacao de "nenhuma migration necessaria" do plano anterior valia
  APENAS para a parte visual (modulos 01-06); a parte de GED versionado
  exige model novo.

## Observacoes gerais

- Nao existe campo de "numero de documento" formatado (ex.: 2025-0142,
  VS-2026-0088, RC-2026-0451) nos models de negocio - esses numeros sao
  ficticios dos mockups. Confirmado como fora de escopo: usar
  {{ objeto.pk }} + {{ objeto.criado_em|date:"d/m/Y" }} no cabecalho do PDF.
  (O DocumentoGerado do modulo 07 tem seu proprio numero_versao sequencial,
  que e uma coisa diferente - nao e o "numero de contrato/laudo/recibo" do
  mockup, e o numero da versao do arquivo gerado.)
- Valor por extenso do recibo ("Dois mil e quinhentos reais") confirmado
  como fora de escopo - sem infraestrutura (num2words) no projeto.
- Logo: usar sempre {% static 'assets/Shelter_LOGO.jpg' %} - nunca o
  caminho absoluto do Windows usado nos arquivos de docs/pdf-models/.
- Encoding: todos os templates devem ser editados com a ferramenta Edit,
  nunca com Get-Content/Set-Content do PowerShell.
- A cor #9A6B00 nao esta na paleta documentada em docs/07_design_ui_ux.md -
  tratar como token novo especifico de PDF (modulo 01) e avaliar
  formalizacao na documentacao.
- boto3/django-storages NAO devem ser adicionados a requirements.txt/ambiente
  nesta rodada - apenas a arquitetura deve ficar pronta para a troca futura
  (modulo 08).
