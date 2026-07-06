# Objetivo

Ajustar `imoveis/views.py` para que a geração do PDF do contrato passe
ao template os dados do locador fixo (Shelter) e o prazo em meses
calculado, sem alterar nenhuma outra view.

---

# Arquivos afetados

- `imoveis/views.py` (`_gerar_pdf_contrato`)

---

# Especificação

Adicionar `from django.conf import settings` no topo de `imoveis/views.py`
(ainda não importado) e `from .extenso import meses_entre` (módulo 01).

Alterar `_gerar_pdf_contrato`:

```python
def _gerar_pdf_contrato(contrato, usuario=None):
    filename = f'contrato_{contrato.pk}.pdf'
    contexto = {
        'contrato': contrato,
        'locador': settings.SHELTER_LOCADOR,
        'prazo_meses': meses_entre(contrato.data_inicio, contrato.data_fim),
    }
    pdf_bytes = gerar_e_anexar(contrato, 'documentos/contrato_pdf.html',
                               contexto, 'documento_gerado', filename,
                               usuario=usuario)
    return pdf_download_response(pdf_bytes, filename)
```

Não alterar a assinatura da função nem a view pública `contrato_gerar_pdf`
(continua chamando `_gerar_pdf_contrato(contrato, request.user)` sem
mudanças).

---

## Documentação relacionada

- docs/03_modelagem_dados.md
  Sem impacto (não é campo de model).
- docs/04_regras_de_negocio.md
  Cobrir junto do módulo 05 (a regra de negócio é "o locador exibido é
  sempre a Shelter" — este módulo só implementa o encanamento técnico).
- docs/07_design_ui_ux.md
  Sem impacto.

---

# Dependências

- `01-utilitarios-extenso-num2words.md` — função `meses_entre`.
- `02-constantes-locador-shelter.md` — `settings.SHELTER_LOCADOR`.

---

# Critérios de aceite

- [ ] `_gerar_pdf_contrato` passa `locador` e `prazo_meses` no contexto,
      sem remover `contrato` do contexto.
- [ ] Nenhuma outra view (`_gerar_pdf_laudo`, `_gerar_pdf_recibo`,
      `contrato_gerar_pdf`, `contrato_create`, `contrato_edit`) é
      alterada.
- [ ] `python manage.py test imoveis.tests.GeracaoPdfViewTests` continua
      100% verde.

---

# Riscos

- `meses_entre` chamado com `contrato.data_fim` menor que
  `contrato.data_inicio` (dado inconsistente) pode retornar um número
  negativo — não há validação de negócio hoje impedindo
  `data_fim < data_inicio` no `ContratoForm`; se isso for um problema
  real, é uma validação de formulário fora do escopo deste módulo
  (registrar como observação, não bloquear a entrega).
