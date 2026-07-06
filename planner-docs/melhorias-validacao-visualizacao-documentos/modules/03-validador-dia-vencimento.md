# Objetivo

Impedir, no backend, que `Contrato.dia_vencimento` receba um valor fora do intervalo 1-31 (hoje so restrito pelos atributos HTML `min`/`max` do widget, que nao protegem contra POST direto).

---

# Arquivos afetados

- `imoveis/models.py`
  - Import (linha 1): adicionar `from django.core.validators import MinValueValidator, MaxValueValidator` (novo import; nao usar `imoveis/validators.py` para isso, pois sao validators genericos ja prontos no Django).
  - `Contrato.dia_vencimento` (linha 141): adicionar `validators=[MinValueValidator(1), MaxValueValidator(31)]`.

- `imoveis/migrations/` — gerar migration (`AlterField` de `Contrato.dia_vencimento`). Ver observacao no `plan.md` sobre consolidar com os modulos 01 e 02.

- `imoveis/tests.py`
  - Nova classe `ContratoDiaVencimentoTests` (ver Criterios de aceite). Reaproveitar o helper `criar_base()` ja existente (linha 25) para obter um contrato base e alterar `dia_vencimento` antes de `full_clean()`.

---

## Documentacao relacionada

- `docs/03_modelagem_dados.md`
  Secao 2.5 (Contrato), campo `dia_vencimento`: acrescentar nota "Intervalo permitido: 1 a 31".

- `docs/04_regras_de_negocio.md`
  Sem impacto obrigatorio; candidato a mesma subsecao de validacoes sugerida no modulo 01, caso seja criada.

---

# Dependencias

Nenhuma. Modulo independente.

---

# Criterios de aceite

- [ ] `Contrato.dia_vencimento` usa `validators=[MinValueValidator(1), MaxValueValidator(31)]`.
- [ ] Migration gerada e aplicada sem erros.
- [ ] Novos testes em `imoveis/tests.py`: `dia_vencimento=45` e `dia_vencimento=0` levantam `ValidationError` em `full_clean()`; `dia_vencimento=1` e `dia_vencimento=31` sao aceitos; `dia_vencimento` default (`10`) continua funcionando sem erro.
- [ ] `python manage.py test imoveis` roda sem falhas.
- [ ] `python manage.py check` sem erros.

---

# Riscos

- Muito baixo: contratos ja existentes com `dia_vencimento` fora do intervalo (nao deveria haver, pois o form ja restringia via HTML) so seriam bloqueados se alguem os editar e salvar novamente. Nenhum impacto em leitura/listagem.
