# Objetivo

Adicionar a `Contrato` os campos `finalidade` (residencial/comercial —
usado no título do PDF e na cláusula que trata da finalidade da
locação), `local_assinatura` e `data_assinatura` (mesmo padrão já usado
em `LaudoVistoria`).

---

# Arquivos afetados

- `imoveis/models.py` (classe `Contrato`)
- `imoveis/migrations/0011_*.py` (nova migration — **coordenar com o
  módulo 04**, ver Dependências)
- `imoveis/forms.py` (`ContratoForm`)
- `templates/contratos/contrato_form.html`
- `templates/contratos/contrato_detail.html`

---

# Especificação do model

Em `Contrato`, adicionar (posicionar perto de `tipo_contrato`/`status`
para `finalidade`, e perto de `observacoes` para os campos de
assinatura — mesma ordem lógica de `LaudoVistoria`):

```python
FINALIDADE_CHOICES = [
    ('residencial', 'Residencial'),
    ('comercial', 'Comercial'),
]

finalidade = models.CharField(max_length=12, choices=FINALIDADE_CHOICES,
                              default='residencial', verbose_name='Finalidade')
local_assinatura = models.CharField(max_length=200, blank=True,
                                    verbose_name='Local da Assinatura')
data_assinatura = models.DateField(null=True, blank=True,
                                   verbose_name='Data da Assinatura')
```

`finalidade` segue o padrão de `Imovel.categoria`
(`default='urbano'` já existente) — tem `default`, não precisa ser
opcional no form. `local_assinatura`/`data_assinatura` replicam
exatamente os campos homônimos de `LaudoVistoria`.

---

# Especificação do form (`ContratoForm`)

Adicionar `'finalidade'`, `'local_assinatura'`, `'data_assinatura'` a
`Meta.fields`. Widgets:

```python
'finalidade': forms.Select(attrs=_sel),
'local_assinatura': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Cidade da assinatura'}),
```

No `__init__`, adicionar `self.fields['data_assinatura'].widget = _date_widget()`
junto das já existentes `data_inicio`/`data_fim` (mesmo padrão de
`LaudoVistoriaForm.__init__`).

---

# Especificação dos templates de tela

- `templates/contratos/contrato_form.html`: adicionar 3 novos campos no
  bloco "Dados do Contrato" (`form.finalidade`, `form.local_assinatura`,
  `form.data_assinatura`), mesmo padrão visual das colunas já existentes
  (`col-md-4`/`col-md-6`).
- `templates/contratos/contrato_detail.html`: exibir os 3 campos novos
  na seção de dados do contrato, com `local_assinatura`/`data_assinatura`
  condicionais (`{% if %}`) — mesmo padrão de exibição já usado em
  `templates/laudos/laudo_detail.html` para os campos homônimos.

---

## Documentação relacionada

- docs/03_modelagem_dados.md
  Atualizar a seção 2.5 (Contrato) com as 3 novas linhas da tabela de
  campos (`finalidade`, `local_assinatura`, `data_assinatura`) e as
  choices de `finalidade`.
- docs/04_regras_de_negocio.md
  Documentar que `finalidade` determina o título do PDF gerado
  ("CONTRATO DE LOCAÇÃO RESIDENCIAL"/"COMERCIAL") — cobrir junto da
  documentação do módulo 05, sem duplicar.
- docs/07_design_ui_ux.md
  Sem impacto (campos de formulário seguem os padrões já documentados
  de `_date_widget()`/`_sel`).

---

# Dependências

- Nenhuma dependência de código de outro módulo.
- **Coordenação de migration:** este módulo e o módulo
  `04-fiador-model-form-qualificacao-completa.md` devem ter os campos de
  model prontos ANTES de rodar `makemigrations` — gerar a migration
  `0011` uma única vez cobrindo os dois conjuntos de alterações (mesmo
  padrão da migration `0008`, que combinou `Contrato.dia_vencimento` e
  `Fiador.rg_cpf` num arquivo só).

---

# Critérios de aceite

- [ ] `Contrato.finalidade`/`local_assinatura`/`data_assinatura`
      criados exatamente como especificado.
- [ ] Migration `0011` criada e aplicada sem erros
      (`python manage.py makemigrations && python manage.py migrate`).
- [ ] `ContratoForm` aceita os 3 campos novos; `data_assinatura` usa
      Flatpickr (`data-flatpickr`) e aceita `dd/mm/aaaa`.
- [ ] `contrato_form.html` e `contrato_detail.html` atualizados e
      renderizando sem erro (`python manage.py check`).
- [ ] Contratos existentes (fixture `criar_base()` em `imoveis/tests.py`,
      que não define `finalidade`) continuam válidos com o `default`
      `'residencial'` — nenhum teste existente quebra por causa do novo
      campo obrigatório-com-default.

---

# Riscos

- `finalidade` tem `default='residencial'` para não quebrar os
  contratos existentes na migration — confirmar que esse é realmente o
  padrão desejado (contratos residenciais são a maioria do portfólio);
  se a maioria for comercial, ajustar o `default` antes de aplicar a
  migration em produção (dado já existente vira `residencial`
  silenciosamente).
- `local_assinatura`/`data_assinatura` ficam `blank=True`/`null=True` —
  se o cliente exigir esses campos preenchidos como pré-condição para
  gerar o PDF, essa validação de negócio (bloquear geração do PDF sem
  esses campos) não está coberta por este módulo nem pelo módulo 06;
  avaliar se é necessário antes de fechar o plano.
