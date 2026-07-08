# Objetivo

Criar o model `FotoItemVistoria` — 0..N fotos por `ItemVistoria` — e a
migration correspondente.

---

# Arquivos afetados

- `imoveis/models.py` (novo model, logo após `class ItemVistoria` —
  `imoveis/models.py:341-362` — e antes de `class TestemunhaLaudo`).
- Migration nova (`imoveis/migrations/00XX_fotoitemvistoria.py`), gerada por
  `makemigrations` — não escrever manualmente.

---

# Dependências

Nenhuma (primeiro módulo da feature).

---

# Leituras adicionais

Nenhuma (o necessário já está em `imoveis/models.py:341-362` e em
`docs/03_modelagem_dados.md` seção 2.10, referenciado no plan.md).

---

# Especificação do model

```python
def foto_item_vistoria_upload_to(instance, filename):
    """itens_vistoria/{item_id}/{filename} — usa instance.item_id (FK id),
    sem precisar carregar o ItemVistoria nem o LaudoVistoria relacionado."""
    return f'itens_vistoria/{instance.item_id}/{filename}'


class FotoItemVistoria(models.Model):
    """Foto anexada a um item do checklist de vistoria. Visível apenas no
    detalhe do laudo — nunca no PDF nem na central GED."""
    item = models.ForeignKey(ItemVistoria, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(upload_to=foto_item_vistoria_upload_to)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Foto do Item de Vistoria'
        verbose_name_plural = 'Fotos do Item de Vistoria'
        ordering = ['criado_em']

    def __str__(self):
        return f'Foto de {self.item} ({self.criado_em:%d/%m/%Y})'
```

Notas:
- `on_delete=CASCADE`: apagar o `ItemVistoria` (ex. via `DELETE` no formset,
  `can_delete=True` já existente) apaga as fotos junto — comportamento
  esperado, mesmo padrão de `FotoImovel`/`Imovel`.
- `ImageField` exige `Pillow`, já é dependência do projeto (`FotoImovel`).
- Não adicionar `legenda`/ordenação customizada — fora de escopo (galeria
  simples por `criado_em`, conforme suposição validada no objetivo da
  feature).
- Não registrar em `imoveis/admin.py` nesta rodada — não é requisito
  funcional; se quiser inline no admin de `LaudoVistoria`, tratar como item
  de trabalho futuro.

---

# Critérios de aceite

- [ ] Model `FotoItemVistoria` criado exatamente como especificado acima.
- [ ] `venv/Scripts/python manage.py makemigrations imoveis` gera uma
      migration nova sem alterar nenhum outro model.
- [ ] `venv/Scripts/python manage.py migrate` aplica sem erro.
- [ ] `venv/Scripts/python manage.py check` sem warnings novos.

---

# Riscos

- Nenhum risco relevante isolado — o model é aditivo e não altera nenhum
  model existente. O risco de integração (upload dentro do formset) está
  nos módulos `02`/`03`.
