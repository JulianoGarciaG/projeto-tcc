# Objetivo

Adicionar um campo de upload múltiplo de imagens (não-model) a
`ItemVistoriaForm`, para que cada linha do formset de itens do laudo aceite
0..N arquivos de foto.

---

# Arquivos afetados

- `imoveis/forms.py` — novo widget/campo (perto dos helpers `_date_widget`/
  `_moeda_widget`, `imoveis/forms.py:13-24`) e alteração em
  `ItemVistoriaForm` (`imoveis/forms.py:233-244`).

---

# Dependências

Nenhuma dependência de código (o campo não referencia `FotoItemVistoria`
diretamente — só devolve uma lista de arquivos via `cleaned_data`). O módulo
`03-views-laudo` é quem usa o resultado para criar os registros do model do
módulo `01`.

---

# Leituras adicionais

Nenhuma.

---

# Especificação

Django não tem upload múltiplo nativo em um único campo (`ClearableFileInput`
não aceita `multiple`). Criar um widget e um campo dedicados:

```python
class MultiplaImagemInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultiplaImagemField(forms.FileField):
    """Campo não-model: aceita 0..N imagens, sempre opcional (o item só
    passa a exigir `estado` se o usuário efetivamente mudar algo na linha —
    ver risco documentado no módulo 03-views-laudo)."""
    widget = MultiplaImagemInput

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('required', False)
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if not data:
            return []
        arquivos = data if isinstance(data, list) else [data]
        return [super(MultiplaImagemField, self).clean(f, initial) for f in arquivos]
```

Ajustar `ItemVistoriaForm`:

```python
class ItemVistoriaForm(forms.ModelForm):
    fotos = MultiplaImagemField(
        widget=MultiplaImagemInput(attrs={'class': 'form-control form-control-sm', 'accept': 'image/*', 'multiple': True}),
    )

    class Meta:
        model = ItemVistoria
        fields = ['comodo', 'item', 'estado', 'observacao', 'ordem']
        widgets = {
            # ... (inalterado)
        }
```

Notas importantes:
- `fotos` **não** entra em `Meta.fields` — é campo de formulário, não de
  model; `ModelForm.save()` o ignora automaticamente, então nenhuma
  alteração é necessária em `item_vistoria_formset_factory`
  (`imoveis/forms.py:246-254`).
- `accept="image/*"` restringe a apenas imagens no seletor do navegador
  (suposição validada do objetivo: jpg/png, sem PDF escaneado). Não há
  validação server-side de tipo/tamanho nesta rodada — ver risco abaixo.
- O campo é sempre `required=False`: anexar foto é opcional em qualquer
  linha, inclusive nas que não têm `estado` selecionado. A obrigatoriedade
  cruzada (estado) é tratada na camada de view/detecção de linha alterada —
  ver `03-views-laudo`, não aqui.

---

# Critérios de aceite

- [ ] `MultiplaImagemInput`/`MultiplaImagemField` implementados conforme
      especificação (ou equivalente funcional).
- [ ] `ItemVistoriaForm` expõe `fotos` como campo extra, sem quebrar
      `Meta.fields` existente.
- [ ] `python manage.py shell` (ou teste rápido) confirma que
      `ItemVistoriaForm(data, files).fields['fotos']` aceita lista vazia e
      lista com múltiplos arquivos sem erro.
- [ ] Nenhuma mudança em `item_vistoria_formset_factory`/`ItemVistoriaFormSet`.

---

# Riscos

- **Sem validação de tipo/tamanho/quantidade de imagem no servidor** (só
  `accept` no HTML, que é apenas sugestão de UI). Registrar como risco
  aceito nesta rodada — se necessário, trabalho futuro pode adicionar
  `validate_image_file_extension`/limite de tamanho.
- `MultiplaImagemField.clean` chama `FileField.clean` por arquivo — garantir
  que cada imagem individual ainda passe pela validação padrão de
  `ImageField`/Pillow (arquivo corrompido, etc.) quando for de fato salva
  como `FotoItemVistoria` no módulo `03` (o `ItemVistoriaForm.fotos` não é
  `ImageField`, então a validação de "é uma imagem válida" só ocorre quando
  o model `FotoItemVistoria` for instanciado e salvo — ponto de atenção para
  o módulo de views tratar erros de imagem inválida sem quebrar a transação
  do laudo inteiro).
