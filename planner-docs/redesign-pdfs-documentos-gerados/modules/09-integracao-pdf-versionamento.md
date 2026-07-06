# Objetivo

Alterar a camada de geração de PDF (`imoveis/pdf.py`) e as views
`*_gerar_pdf` (`imoveis/views.py`) para que cada geração crie uma nova
versão em `DocumentoGerado` (em vez de apenas sobrescrever o `FileField` do
próprio registro), calculando o hash do arquivo e o próximo número de
versão, e registrando o usuário autor.

---

# Arquivos afetados

- `imoveis/pdf.py` (`gerar_e_anexar`, `save_pdf_to_field` — revisar
  assinatura e comportamento)
- `imoveis/views.py` (`_gerar_pdf_contrato`, `_gerar_pdf_laudo`,
  `_gerar_pdf_recibo`, e as views `contrato_gerar_pdf`, `laudo_gerar_pdf`,
  `recibo_gerar_pdf` — precisam passar `request.user` para o helper, hoje
  elas só passam o objeto)
- Migration de dados (`0010_migrar_documentos_existentes.py` — ver estratégia
  de convivência abaixo) para registrar retroativamente os PDFs já existentes
  como versão 1 de cada origem que já tenha `documento_gerado`/`arquivo`
  preenchido.

---

## Documentação relacionada

- docs/04_regras_de_negocio.md
  Atualizar a regra "PDF nunca é gerado ao salvar" para deixar explícito que,
  a partir desta mudança, "regerar" cria uma nova versão (não sobrescreve) e
  os campos `documento_gerado`/`arquivo` passam a refletir sempre a última
  versão.
- docs/03_modelagem_dados.md
  Documentar que `Contrato.documento_gerado`, `LaudoVistoria.documento_gerado`
  e `Recibo.arquivo` continuam existindo como espelho de leitura da última
  versão, mas a fonte de verdade passa a ser `DocumentoGerado`.

---

# Dependências

- `07-model-documento-gerado.md`, `08-storage-s3-ready.md` — precisa do model
  e do storage prontos.
- `02-contrato-pdf.md`, `03-laudo-pdf.md`, `04-recibo-pdf.md` — o HTML/PDF
  gerado por essas views é o que passa a alimentar o `DocumentoGerado`; não
  há dependência técnica direta (a lógica de versionamento é agnóstica ao
  layout), mas faz sentido implementar depois da réplica visual estar pronta
  para não gerar 2 rodadas de versões "de teste" com o layout antigo.

---

# Estratégia de convivência com os campos legados

**Decisão**: manter `Contrato.documento_gerado`, `LaudoVistoria.documento_gerado`
e `Recibo.arquivo` como estão (não remover, não depreciar formalmente nesta
rodada), mas redefinir seu papel: a partir desta mudança, eles são
**espelhos de leitura da última versão** de `DocumentoGerado` para aquela
origem, atualizados automaticamente pela própria função de geração. Motivo:
minimiza o raio de impacto — todo template/link existente que lê
`objeto.documento_gerado.url` continua funcionando sem alteração imediata
(o módulo 10 os atualiza para também listar o histórico, mas isso é uma
melhoria incremental, não uma correção obrigatória para não quebrar nada).

Migração de dados dos PDFs já existentes: para cada `Contrato`/`LaudoVistoria`
com `documento_gerado` preenchido e cada `Recibo` com `arquivo` preenchido,
criar um `DocumentoGerado` com `numero_versao=1`, `gerado_por=None` (autor
desconhecido, dado histórico), `gerado_em` copiado de `criado_em` do objeto
de origem (aproximação razoável, já que não há timestamp real da geração do
PDF hoje) e `hash_sha256` calculado a partir do arquivo já salvo. Implementar
como `RunPython` na migration de dados, lendo o arquivo do storage atual
(sem re-gerar o PDF).

# Alterações em `imoveis/pdf.py`

```python
def registrar_versao(instance, tipo, pdf_bytes, usuario=None):
    """Cria uma nova versão imutável em DocumentoGerado e atualiza o campo
    legado (documento_gerado/arquivo) do objeto de origem para apontar
    para a última versão."""
    proximo_numero = (
        DocumentoGerado.objects.filter(**{tipo: instance})
        .aggregate(m=Max('numero_versao'))['m'] or 0
    ) + 1
    hash_arquivo = hashlib.sha256(pdf_bytes).hexdigest()
    versao = DocumentoGerado(
        tipo=tipo, numero_versao=proximo_numero,
        hash_sha256=hash_arquivo, gerado_por=usuario,
        **{tipo: instance},
    )
    nome = f'{tipo}_{instance.pk}_v{proximo_numero}.pdf'
    versao.arquivo.save(nome, ContentFile(pdf_bytes), save=True)
    return versao
```

`gerar_e_anexar` passa a:
1. Renderizar o PDF (sem mudança).
2. Chamar `registrar_versao(...)` para criar a nova versão.
3. Continuar chamando `save_pdf_to_field` (campo legado) apontando para o
   **mesmo arquivo físico** da versão recém-criada (reaproveitar
   `versao.arquivo.name`/bytes, não gerar um segundo arquivo redundante no
   storage).
4. Assinatura de `gerar_e_anexar` precisa aceitar `usuario` (novo parâmetro
   opcional, default `None` — mantém retrocompatibilidade de chamada onde
   não houver `request`, embora hoje todo caller tenha `request.user`).

# Alterações em `imoveis/views.py`

`_gerar_pdf_contrato`, `_gerar_pdf_laudo`, `_gerar_pdf_recibo` passam a
receber também o `usuario` (vindo de `request.user`) e repassá-lo para
`gerar_e_anexar`. As views públicas `contrato_gerar_pdf`, `laudo_gerar_pdf`,
`recibo_gerar_pdf` já têm `request` disponível — só precisam passar
`request.user` adiante.

---

# Critérios de aceite

- [ ] Cada chamada às views `*_gerar_pdf` cria uma nova linha em
      `DocumentoGerado` com `numero_versao` incrementado corretamente para
      aquela origem (nunca reaproveita número de versão já usado).
- [ ] `hash_sha256` da versão criada corresponde ao hash real do arquivo
      salvo.
- [ ] `gerado_por` é preenchido com o usuário autenticado que gerou o PDF.
- [ ] Campos legados (`documento_gerado`/`arquivo`) continuam funcionando nos
      templates existentes, sempre refletindo a última versão criada.
- [ ] Migration de dados registra retroativamente como versão 1 todos os
      documentos já existentes antes desta mudança, sem re-gerar PDFs.
- [ ] Nenhum arquivo duplicado físico é criado para a mesma geração (campo
      legado e `DocumentoGerado.arquivo` apontam para o mesmo conteúdo,
      idealmente o mesmo path).
- [ ] `manage.py test imoveis` passa (ajustes de teste ficam no módulo 11,
      mas nenhum teste de geração de PDF existente deve regredir por causa
      desta mudança).

---

# Riscos

- Gravar o arquivo físico duas vezes (uma em `DocumentoGerado.arquivo`, outra
  no campo legado) duplicaria espaço em disco/S3 desnecessariamente — a
  recomendação é fazer o campo legado apontar para o **mesmo path** do
  arquivo da versão mais recente (usando o mesmo `FieldFile.name`) em vez de
  chamar `.save()` duas vezes com os mesmos bytes. Detalhar essa
  implementação com cuidado para não quebrar o storage plugável do módulo 08
  (evitar assumir `FileSystemStorage` especificamente).
- A migration de dados que le arquivos existentes do storage pode falhar se
  algum arquivo referenciado no banco não existir mais fisicamente
  (arquivo órfão) — tratar com `try/except` e logar/pular esses casos em vez
  de interromper a migration inteira.
- Mudar a assinatura de `gerar_e_anexar`/helpers privados é uma mudança
  interna, mas deve ser conferida contra todos os call sites (só existem 3
  hoje, listados em "Arquivos afetados") para não deixar nenhuma chamada sem
  o novo parâmetro.
