# Objetivo

Trocar os nomes de arquivo improvisados (`contrato_3.pdf`, `laudo_5.pdf`,
`recibo_9.pdf`) pelo padrão determinístico de `nome_arquivo()`
(`imoveis/identidade.py`, módulo `01-identidade-core`), tanto na versão
imutável do GED (`DocumentoGerado`) quanto no download do PDF — sem alterar o
caminho interno do GED (`ged/{tipo}/{pk}/v{n}/`, que já é determinístico e não
depende do nome do arquivo).

---

# Arquivos afetados

- `imoveis/pdf.py`:
  - `registrar_documento_gerado()` (linha 69-97) — extrair o cálculo de `tipo`
    (hoje inline, if/elif isinstance, linhas 77-84) para um helper privado
    `_tipo_de(instance)`, reutilizado também por `gerar_e_anexar`. Aceitar um
    parâmetro opcional `versao` para não recalcular a query duas vezes por
    geração.
  - `gerar_e_anexar()` (linha 100-106) — **muda a assinatura**: remove o
    parâmetro `filename` (agora calculado internamente via `nome_arquivo`) e
    passa a retornar `(pdf_bytes, filename)` em vez de só `pdf_bytes`.
- `imoveis/views.py` — `_gerar_pdf_contrato` (29-39), `_gerar_pdf_laudo`
  (52-62), `_gerar_pdf_recibo` (65-69): remover a linha `filename = f'...'`
  manual e adaptar a chamada a `gerar_e_anexar` para o novo retorno em tupla.

---

# Dependências

Depende de `01-identidade-core` (usa `nome_arquivo`).

---

# Leituras adicionais

Nenhuma.

---

# Especificação

## `imoveis/pdf.py`

```python
def _tipo_de(instance):
    """'contrato' | 'laudo' | 'recibo' a partir da classe da instância."""
    from .models import Contrato, LaudoVistoria, Recibo
    if isinstance(instance, Contrato):
        return 'contrato'
    if isinstance(instance, LaudoVistoria):
        return 'laudo'
    if isinstance(instance, Recibo):
        return 'recibo'
    raise ValueError(f'Origem não suportada: {type(instance).__name__}')


def _proxima_versao(instance, tipo):
    from .models import DocumentoGerado
    ultima = (DocumentoGerado.objects.filter(**{tipo: instance})
              .aggregate(m=Max('numero_versao'))['m']) or 0
    return ultima + 1


def registrar_documento_gerado(instance, pdf_bytes, filename, usuario=None, versao=None):
    from .models import DocumentoGerado
    tipo = _tipo_de(instance)
    versao = versao or _proxima_versao(instance, tipo)
    doc = DocumentoGerado(
        tipo=tipo,
        numero_versao=versao,
        sha256=hashlib.sha256(pdf_bytes).hexdigest(),
        gerado_por=usuario if getattr(usuario, 'is_authenticated', False) else None,
        **{tipo: instance},
    )
    doc.arquivo.save(filename, ContentFile(pdf_bytes), save=False)
    doc.save()
    return doc


def gerar_e_anexar(instance, template_name, context, field_name, usuario=None):
    """Gera o PDF, registra a versão no GED e espelha no FileField legado.

    Retorna (pdf_bytes, filename) — filename já inclui o número de versão,
    para o chamador reaproveitar no download (Content-Disposition).
    """
    from .identidade import nome_arquivo

    pdf_bytes = render_pdf(template_name, context)
    tipo = _tipo_de(instance)
    versao = _proxima_versao(instance, tipo)
    filename = nome_arquivo(instance, versao=versao)
    registrar_documento_gerado(instance, pdf_bytes, filename, usuario, versao=versao)
    save_pdf_to_field(instance, field_name, pdf_bytes, filename)
    return pdf_bytes, filename
```

`_proxima_versao` fica exposta separada para não duplicar a query dentro de
`gerar_e_anexar` e `registrar_documento_gerado` — `gerar_e_anexar` já sabe a
versão antes de chamar `registrar_documento_gerado`, e passa explicitamente.

## `imoveis/views.py` — as 3 funções `_gerar_pdf_*`

Trocar, por exemplo em `_gerar_pdf_contrato`:

```python
def _gerar_pdf_contrato(contrato, usuario=None):
    contexto = {
        'contrato': contrato,
        'locador': settings.SHELTER_LOCADOR,
        'prazo_meses': meses_entre(contrato.data_inicio, contrato.data_fim),
    }
    pdf_bytes, filename = gerar_e_anexar(contrato, 'documentos/contrato_pdf.html',
                                        contexto, 'documento_gerado', usuario=usuario)
    return pdf_download_response(pdf_bytes, filename)
```

(remove a linha `filename = f'contrato_{contrato.pk}.pdf'`; mesmo padrão para
`_gerar_pdf_laudo` e `_gerar_pdf_recibo` — só muda o nome da variável de
contexto e o `field_name`.)

---

# Critérios de aceite

- [ ] `gerar_e_anexar` não recebe mais `filename` como parâmetro e retorna
      `(pdf_bytes, filename)`.
- [ ] As 3 views `_gerar_pdf_*` não montam mais `filename` manualmente.
- [ ] Baixar um contrato/laudo/recibo gera um arquivo com o padrão
      `{Tipo}_{codigo}_..._v{n}.pdf` (verificar o header
      `Content-Disposition` da resposta).
- [ ] `DocumentoGerado.arquivo` e o FileField legado (`documento_gerado`/
      `arquivo`) recebem o mesmo nome de arquivo novo.
- [ ] Gerar duas vezes o mesmo contrato produz `_v1` e depois `_v2` no nome do
      arquivo (sem duplicar a query de versão nem gerar números conflitantes).

---

# Riscos

- **Mudança de assinatura pública**: `gerar_e_anexar` é chamada só pelas 3
  funções em `imoveis/views.py` (confirmado por grep) — não há outros
  chamadores a atualizar, mas se algum teste futuro instanciar
  `gerar_e_anexar` diretamente com a assinatura antiga, quebra (ver módulo
  `05-testes-identidade`).
- **Retrocompatibilidade dos FileFields legados**: registros já existentes
  mantêm o filename antigo salvo no banco (ex.: `contrato_3.pdf`) — isso é
  esperado e não deve ser "corrigido" retroativamente; só novas gerações usam
  o nome novo.
- **PDF nunca é gerado ao salvar**: este módulo não toca em `*_create`/
  `*_edit` — só nas 3 funções `_gerar_pdf_*`, que já são exclusivas dos
  botões "Gerar/Regerar PDF". Não introduzir geração de PDF em outro lugar.
