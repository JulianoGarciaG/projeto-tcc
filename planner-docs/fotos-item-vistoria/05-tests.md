# Objetivo

Cobrir a feature de fotos por item de vistoria e garantir, com testes de
regressão explícitos, que PDF do laudo e central GED continuam intocados
(RF4/RF5).

---

# Arquivos afetados

- `imoveis/tests.py`

---

# Dependências

Depende de `01-model-foto-item-vistoria`, `02-form-widget-multiplo-arquivo`,
`03-views-laudo` e `04-templates-laudo` já implementados.

---

# Leituras adicionais

- `imoveis/tests.py:542` (`test_laudo_create_salva_apenas_itens_com_estado`)
  — usar como referência do payload de POST do formset de itens (mesmo
  `TOTAL_FORMS`/`INITIAL_FORMS`/prefixo `itens-`), para não reinventar a
  montagem dos dados de teste.
- `imoveis/tests.py:467` (`test_laudo_anexar_arquivo`) — referência de como
  o projeto já testa upload de arquivo (`SimpleUploadedFile`).

---

# Casos de teste a implementar

Adicionar à classe `LaudoTests` (ou nova classe `FotoItemVistoriaTests`,
seguindo o padrão de classes já existente em `imoveis/tests.py`):

1. **Criação com foto e estado preenchido** — POST em `laudo_create` com uma
   linha do formset de itens tendo `estado` preenchido e um arquivo em
   `itens-0-fotos` (`SimpleUploadedFile` de imagem, ex. PNG 1x1 mínimo).
   Assert: laudo criado, `ItemVistoria` criado, `FotoItemVistoria.objects
   .filter(item=item).count() == 1`, `item.fotos.first().imagem` não vazio.

2. **Múltiplas fotos na mesma linha** — mesmo payload do caso 1, mas com 2+
   arquivos no mesmo campo (`request.FILES` com múltiplos valores para a
   mesma key `itens-0-fotos`, via `client.post(..., data)` com uma lista de
   arquivos no dicionário). Assert: `FotoItemVistoria.objects.filter(item=item).count() == 2`.

3. **Foto sem estado — validação esperada (não silenciosa)** — POST em
   `laudo_create` com uma linha tendo **apenas** foto anexada e `estado`
   vazio. Assert: `resp.status_code == 200` (form re-renderizado, não
   redirect), nenhum `LaudoVistoria`/`ItemVistoria`/`FotoItemVistoria` criado
   no banco (o POST inteiro falha, conforme risco documentado no módulo
   `03-views-laudo`).

4. **Edição — adicionar foto a item existente** — criar laudo com item já
   persistido (`estado` preenchido), depois POST em `laudo_edit` reenviando
   os mesmos dados do item (mesmo `estado`) + um arquivo novo em
   `itens-0-fotos`. Assert: `FotoItemVistoria` criado vinculado ao item
   existente (mesma PK).

5. **Detalhe do laudo exibe as fotos agrupadas por item** — criar item com
   2 fotos, GET em `laudo_detail`, assert `resp.context['grupos']` contém o
   item com `item.fotos.count() == 2` (ou `assertContains` verificando a
   tag `<img` no HTML da página).

6. **Regressão — PDF não contém fotos.** Gerar o PDF do laudo
   (`laudo_gerar_pdf`) de um laudo com item que tem foto e assert que o PDF
   é gerado normalmente (`resp.content.startswith(b'%PDF-')`) — não é
   possível (nem necessário) inspecionar visualmente o PDF em teste
   automatizado; o teste de regressão real é **negativo**: confirmar que o
   contexto passado para `documentos/laudo_pdf.html` em
   `_gerar_pdf_laudo` (`imoveis/views.py:50-59`) não inclui nenhuma chave
   relacionada a `fotos`/`FotoItemVistoria` (inspecionar as chaves do dict
   de contexto construído, ex. via mock/spy de `gerar_e_anexar`, ou
   simplesmente reafirmar por leitura de código que `_gerar_pdf_laudo` não
   foi alterado pelos módulos anteriores — se o diff de `03-views-laudo`
   tiver mexido nessa função, este teste deve falhar e sinalizar regressão).

7. **Regressão — central GED não lista fotos de item.** GET em `documentos`
   (view `imoveis/views.py:805`) com um laudo tendo itens com fotos; assert
   que o contexto da resposta não tem nenhuma chave nova relacionada a
   `FotoItemVistoria` e que `resp.context` permanece com as mesmas chaves de
   hoje (`contratos_gerados`, `laudos`, `laudos_gerados`, `comprovantes`,
   `contratos_recibo`, `contratos_anual`, `recibos`).

---

# Critérios de aceite

- [ ] Todos os 7 casos acima implementados e passando.
- [ ] `venv/Scripts/python manage.py test imoveis` passa sem quebrar nenhum
      teste existente (em especial
      `test_laudo_create_salva_apenas_itens_com_estado`,
      `test_laudo_create_renderiza_checklist_do_catalogo`,
      `test_laudo_gerar_pdf_view`, `test_pdf_laudo_condicionais`).
- [ ] Arquivos de imagem de teste são limpos ao final (seguir o padrão já
      usado no arquivo, ex. `limpar_arquivos_gerados()`/`.delete(save=False)`
      conforme a classe base de teste utilizada).

---

# Riscos

- Montar uma imagem válida mínima para os testes (PNG 1x1) é necessário
  porque `ImageField`/Pillow rejeita bytes arbitrários — usar um PNG real
  minúsculo em base64/bytes fixos no teste (não usar apenas
  `b'fake image content'`, que falha na validação de `ImageField`).
- Testar upload de múltiplos arquivos na mesma key via Django test client
  exige montar `request.FILES` corretamente (dicionário com lista de
  `SimpleUploadedFile` na mesma chave) — validar a sintaxe aceita pela
  versão do Django test client usada no projeto (Django 6.0) antes de
  finalizar o teste 2.
