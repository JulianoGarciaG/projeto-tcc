# Objetivo

Fazer todos os `ModelChoiceField` dos formulários que exibem Imóvel, Contrato
ou Laudo em dropdown usarem `rotulo_curto` (em vez do `label_from_instance`
padrão, que cai em `str(obj)`), e ajustar o endpoint JSON do select dependente
de laudo (`contratos_por_imovel_json`) para o mesmo padrão.

Recibo não aparece em nenhum select (não é FK de nenhum outro model) — não há
o que ajustar para ele aqui.

---

# Arquivos afetados

- `imoveis/forms.py`:
  - Novas classes `ImovelChoiceField`, `ContratoChoiceField`,
    `LaudoChoiceField` (subclasses de `forms.ModelChoiceField`), definidas uma
    vez perto dos widgets no topo do arquivo (após `_telefone_attrs`, linha
    27).
  - `ContratoForm.imovel` (Meta.fields linha 128, widget linha 133) — declarar
    o campo explicitamente na classe para trocar a classe do field.
  - `LaudoVistoriaForm.imovel` e `.contrato` (linhas 183-208) — mesma troca;
    manter a lógica de queryset dinâmico do `__init__` (194-208) intacta,
    só troca a classe do field declarado.
  - `ReciboForm.imovel` e `.contrato` (linhas 328-340).
  - `LancamentoForm.contrato` (linha 259-261).
  - `NotificacaoForm.imovel` (linha 278-280).
  - `DistratoForm.laudo_saida` (linha 312-316).
- `imoveis/views.py` — `contratos_por_imovel_json` (linha 621-627): trocar o
  `label` montado manualmente por `c.rotulo_curto`.

---

# Dependências

Depende de `01-identidade-core` (usa `rotulo_curto`).

---

# Leituras adicionais

Nenhuma.

---

# Especificação

## Classes de campo reutilizáveis (`imoveis/forms.py`, topo do arquivo)

```python
class ImovelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.rotulo_curto


class ContratoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.rotulo_curto


class LaudoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.rotulo_curto
```

Três classes quase idênticas (não uma genérica) porque cada uma tipa o campo
para o model correto e deixa explícito, em cada `ModelForm`, qual entidade
está sendo escolhida — consistente com o restante do arquivo, que já declara
um widget por campo em vez de abstrações genéricas.

## Padrão de uso — declarar o campo explicitamente no `ModelForm`

Exemplo em `ContratoForm` (o `queryset` replica o que o `ModelForm` geraria
sozinho a partir da FK — `Imovel.objects.all()` — só que agora com a classe de
field customizada):

```python
class ContratoForm(forms.ModelForm):
    imovel = ImovelChoiceField(queryset=Imovel.objects.all(), widget=forms.Select(attrs=_sel))

    class Meta:
        model = Contrato
        fields = [...]  # continua listando 'imovel' — Meta não muda
        widgets = {...}  # remover a entrada 'imovel' de widgets (o field
                         # explícito já define o widget)
```

Aplicar o mesmo padrão a:
- `LaudoVistoriaForm.imovel` (`ImovelChoiceField`, `queryset=Imovel.objects.all()`)
- `LaudoVistoriaForm.contrato` (`ContratoChoiceField`) — **atenção**: o
  `__init__` atual (194-208) reatribui `self.fields['contrato'].queryset`
  dinamicamente conforme o imóvel escolhido. Ao declarar o campo
  explicitamente na classe, o `queryset` inicial pode ser
  `Contrato.objects.none()` (o `__init__` sempre sobrescreve antes de
  renderizar) — não alterar a lógica de filtragem existente, só a classe do
  field.
- `ReciboForm.imovel` (`ImovelChoiceField`), `ReciboForm.contrato`
  (`ContratoChoiceField`)
- `LancamentoForm.contrato` (`ContratoChoiceField`)
- `NotificacaoForm.imovel` (`ImovelChoiceField`)
- `DistratoForm.laudo_saida` (`LaudoChoiceField`, e é `required=False` —
  preservar isso no field explícito, já que hoje vem do model
  `null=True, blank=True`: `LaudoChoiceField(queryset=LaudoVistoria.objects.all(), required=False, widget=forms.Select(attrs=_sel))`)

## `contratos_por_imovel_json` (`imoveis/views.py`)

Trocar:

```python
dados = [{'id': c.pk, 'label': f'Contrato #{c.pk} — {c.inquilino.nome} ({c.get_status_display()})'}
         for c in contratos]
```

por:

```python
dados = [{'id': c.pk, 'label': c.rotulo_curto} for c in contratos]
```

O `select_related('inquilino')` já existente na queryset (linha 624) continua
necessário porque `Contrato.rotulo_curto` acessa `self.inquilino.nome`.

---

# Critérios de aceite

- [ ] Os 3 subclasses de `ModelChoiceField` existem em `imoveis/forms.py` e
      usam `rotulo_curto`.
- [ ] Todos os selects listados em "Arquivos afetados" renderizam
      `rotulo_curto` no HTML (inspecionar o `<option>` gerado ou testar via
      `str(form['campo'])`).
- [ ] `LaudoVistoriaForm` continua filtrando `contrato` pelo `imovel`
      escolhido (comportamento de `__init__`, linhas 194-208, inalterado).
- [ ] `contratos_por_imovel_json` retorna `label` = `rotulo_curto` do
      contrato.
- [ ] `DistratoForm.laudo_saida` continua opcional (`required=False`).

---

# Riscos

- **Meta.widgets órfão**: ao declarar um campo explicitamente na classe do
  `ModelForm`, a entrada correspondente em `Meta.widgets` fica sem efeito
  (Django ignora silenciosamente) — remover essas entradas para não confundir
  quem ler o form depois.
- **Campo `required`/`empty_label` implícitos do model**: ao declarar o field
  manualmente, atributos que o `ModelForm` inferia sozinho (ex.: `required`
  vindo de `blank=True/False` do model) precisam ser replicados manualmente —
  conferir `blank`/`null` de cada FK antes de fixar `required=True/False`
  (`DistratoForm.laudo_saida` é o único opcional entre os listados).
