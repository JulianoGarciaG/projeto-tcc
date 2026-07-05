# Objetivo

Adicionar validacao de formato ao numero de telefone (hoje so mascarado no front-end via IMask, sem checagem no backend) em `Proprietario.telefone` e `Inquilino.telefone`.

---

# Arquivos afetados

- `imoveis/validators.py`
  - Adicionar `validate_telefone(value)`: remove caracteres nao numericos e verifica se restam 10 ou 11 digitos (DDD + fixo de 8 digitos, ou DDD + celular de 9 digitos). Levanta `ValidationError` caso contrario. Aceita com ou sem mascara, no mesmo estilo de `validate_cpf`/`validate_cnpj`.

- `imoveis/models.py`
  - Import (linha 3): adicionar `validate_telefone`.
  - `Proprietario.telefone` (linha 11): adicionar `validators=[validate_telefone]`.
  - `Inquilino.telefone` (linha 103): adicionar `validators=[validate_telefone]`.

- `imoveis/migrations/` — gerar migration (`AlterField` para os dois campos). Ver observacao no `plan.md` sobre consolidar com os modulos 01 e 03.

- `imoveis/tests.py`
  - Import (linha 16): adicionar `validate_telefone`.
  - Nova classe `ValidateTelefoneTests` (ver Criterios de aceite).

---

## Documentacao relacionada

- `docs/03_modelagem_dados.md`
  Secoes 2.1 (Proprietario) e 2.4 (Inquilino), campo `telefone`: acrescentar nota de que o formato aceito e DDD + numero (10 ou 11 digitos), com ou sem mascara.

- `docs/04_regras_de_negocio.md`
  Sem impacto obrigatorio; candidato a mesma subsecao de validacoes sugerida no modulo 01, caso seja criada.

- `docs/07_design_ui_ux.md`
  Sem impacto (a mascara de front-end ja documentada em `CLAUDE.md`/`masks.js` nao muda; so passa a existir validacao equivalente no backend).

---

# Dependencias

Nenhuma. Modulo independente (pode ser feito na mesma migration do modulo 01 e 03, mas nao ha dependencia funcional).

---

# Criterios de aceite

- [ ] `validate_telefone` existe em `imoveis/validators.py`, aceita telefones com 10 ou 11 digitos (com ou sem mascara `(00) 0000-0000` / `(00) 00000-0000`), rejeita quantidades de digitos diferentes.
- [ ] `Proprietario.telefone` e `Inquilino.telefone` usam `validators=[validate_telefone]`.
- [ ] Campo continua opcional (`blank=True` mantido) — string vazia nao deve disparar o validator nem erro de "campo obrigatorio".
- [ ] Migration gerada e aplicada sem erros.
- [ ] Novos testes em `imoveis/tests.py` (classe `ValidateTelefoneTests`): telefone fixo valido (10 digitos, com e sem mascara) aceito; celular valido (11 digitos) aceito; numero curto (ex.: `123`) rejeitado; teste de modelo (`Proprietario(...).full_clean()` e/ou `Inquilino(...).full_clean()`) com telefone invalido levantando `ValidationError`; teste garantindo que telefone em branco (`""`) nao levanta erro (campo opcional).
- [ ] `python manage.py test imoveis` roda sem falhas.
- [ ] `python manage.py check` sem erros.

---

# Riscos

- Baixo/medio: telefones cadastrados anteriormente em formato fora do padrao (ex.: numeros internacionais, ramais, "sem DDD") passam a falhar validacao em edicoes futuras via formulario, ainda que o registro antigo continue salvo no banco (validator so roda em `full_clean()`/ModelForm, nao retroativamente). Comunicar essa mudanca de comportamento se houver dados legados fora do padrao brasileiro de 10/11 digitos.
