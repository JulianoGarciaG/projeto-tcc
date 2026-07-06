# Objetivo

Ampliar `Fiador` com os dados exigidos pela cláusula XX do contrato
jurídico: RG e CPF discretos, endereço completo e dados do cônjuge
(nome/RG/CPF), preservando compatibilidade com o campo já existente
`rg_cpf`.

---

# Arquivos afetados

- `imoveis/models.py` (classe `Fiador`)
- `imoveis/migrations/0011_*.py` (nova migration — **coordenar com o
  módulo 03**, ver Dependências)
- `imoveis/forms.py` (`FiadorForm`)
- `templates/contratos/contrato_form.html` (bloco `fiador-row`)
- `templates/contratos/contrato_detail.html` (bloco de exibição de
  fiadores)

---

# Especificação do model

Em `Fiador`, manter `rg_cpf` inalterado (compatibilidade — ver Riscos) e
adicionar:

```python
rg = models.CharField(max_length=20, blank=True, validators=[validate_rg],
                      verbose_name='RG')
cpf = models.CharField(max_length=14, blank=True, validators=[validate_cpf],
                       verbose_name='CPF')
endereco = models.CharField(max_length=300, blank=True,
                            verbose_name='Endereço Completo')
conjuge_nome = models.CharField(max_length=200, blank=True,
                                verbose_name='Nome do Cônjuge')
conjuge_rg = models.CharField(max_length=20, blank=True, validators=[validate_rg],
                              verbose_name='RG do Cônjuge')
conjuge_cpf = models.CharField(max_length=14, blank=True, validators=[validate_cpf],
                               verbose_name='CPF do Cônjuge')
```

`validate_rg`/`validate_cpf` já existem em `imoveis/validators.py` e já
são importados em `imoveis/models.py` (reutilizar, não duplicar).

Ajustar também o `help_text` de `qualificacao` (campo já existente) para
`'Estado civil, profissão, nacionalidade'` — mesmo texto de
`Inquilino.qualificacao` — deixando explícito que esse campo já cobre o
"estado civil" citado na decisão do usuário (ver `plan.md`,
"Observações gerais", ambiguidade resolvida). Não criar um campo
`estado_civil` novo.

---

# Especificação do form (`FiadorForm`)

Adicionar `'rg'`, `'cpf'`, `'endereco'`, `'conjuge_nome'`, `'conjuge_rg'`,
`'conjuge_cpf'` a `Meta.fields`, com widgets `TextInput` seguindo o
padrão já usado (`{**_ctrl, 'placeholder': ...}`). Sugestão de
placeholders: `'RG'`, `'CPF'`, `'Endereço completo'`, `'Nome do cônjuge'`,
`'RG do cônjuge'`, `'CPF do cônjuge'`.

Não tornar `rg`/`cpf` obrigatórios a nível de model (permanecem
`blank=True`, mesmo padrão de `Inquilino.rg`) — a obrigatoriedade fica a
critério do form apenas se o usuário decidir endurecer a regra depois;
este módulo não adiciona `clean()` customizado.

---

# Especificação dos templates de tela

- `templates/contratos/contrato_form.html`: o bloco `fiador-row` (linha
  de formset) cresce de 5 para 11 campos — reorganizar em duas linhas
  por fiador (uma com identificação: nome/qualificação/RG/CPF/garantia;
  outra com endereço e dados do cônjuge), mantendo a estrutura
  `{% for ff in fiador_formset %}` e o botão de exclusão (`ff.DELETE`)
  já existente.
- `templates/contratos/contrato_detail.html`: exibir os campos novos no
  card "Fiador(es)", condicionalmente (`{% if f.rg %}`, etc.), sem
  quebrar o layout atual para fiadores antigos que não tenham esses
  campos preenchidos.

---

## Documentação relacionada

- docs/03_modelagem_dados.md
  Atualizar a seção 2.6 (Fiador) com as 6 novas linhas da tabela de
  campos e a nota sobre `qualificacao` cobrir "estado civil".
- docs/04_regras_de_negocio.md
  Sem impacto em automação/signal — só dado cadastral novo; mencionar
  apenas se a documentação central do contrato jurídico (módulo 05)
  precisar referenciar de onde vêm os dados da cláusula XX.
- docs/07_design_ui_ux.md
  Sem impacto.

---

# Dependências

- Nenhuma dependência de código de outro módulo.
- **Coordenação de migration:** ver `03-contrato-model-form-finalidade-assinatura.md`
  — os campos de model dos módulos 03 e 04 devem estar prontos antes de
  rodar `makemigrations` uma única vez (migration `0011`).

---

# Critérios de aceite

- [ ] 6 campos novos criados em `Fiador` exatamente como especificado;
      `rg_cpf` permanece sem alterações de schema.
- [ ] `help_text` de `qualificacao` atualizado.
- [ ] Migration `0011` aplicada sem erros.
- [ ] `FiadorForm`/`FiadorFormSet` aceitam os campos novos; formset
      continua funcionando com `extra=1`/`can_delete=True`.
- [ ] Admin (`imoveis/admin.py::FiadorInline`) não precisa de alteração —
      `TabularInline` sem `fields` explícito já exibe todos os campos do
      model automaticamente (confirmar rodando `python manage.py check`
      e abrindo o admin do Contrato).
- [ ] Fiadores criados antes desta migration (só `rg_cpf` preenchido)
      continuam válidos — nenhum teste existente quebra.

---

# Riscos

- **Retrocompatibilidade de fiadores antigos:** registros criados antes
  desta migration têm `rg`/`cpf` vazios (só `rg_cpf` preenchido). O
  template jurídico (módulo 05) precisa de um fallback explícito para
  esse caso — especificado no módulo 05, não implementar aqui. Não é
  escopo deste módulo migrar/dividir os dados de `rg_cpf` para `rg`/`cpf`
  automaticamente (nenhuma forma confiável de separar "qual é RG e qual
  é CPF" a partir do valor único salvo).
- `endereco`/dados de cônjuge sendo todos opcionais pode gerar cláusula
  XX com trechos em branco se o operador não preencher — mitigar apenas
  na validação visual manual (módulo 08), não há regra de negócio
  bloqueante prevista neste plano.
