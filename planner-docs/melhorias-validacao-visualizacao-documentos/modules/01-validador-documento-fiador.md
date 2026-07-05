# Objetivo

Adicionar validacao ao campo `Fiador.rg_cpf` (hoje sem nenhum validator), aceitando tanto CPF (com digito verificador) quanto RG (formato alfanumerico), reutilizando os validators ja existentes em `imoveis/validators.py` em vez de duplicar logica.

---

# Arquivos afetados

- `imoveis/validators.py`
  - Adicionar, ao final do arquivo, a funcao `validate_rg_cpf(value)`: remove caracteres nao numericos; se sobrarem 11 digitos, delega para `validate_cpf(value)`; caso contrario, delega para `validate_rg(value)` (aceita letras, numeros, "." e "-").

- `imoveis/models.py`
  - Import (linha 3): adicionar `validate_rg_cpf` ao import de `.validators`.
  - `Fiador.rg_cpf` (linha 169): adicionar `validators=[validate_rg_cpf]`.

- `imoveis/migrations/` — gerar nova migration (`makemigrations imoveis`) com o `AlterField` de `Fiador.rg_cpf`. Ver observacao no `plan.md` sobre consolidar com os modulos 02 e 03 em uma unica migration, se forem implementados na mesma sessao.

- `imoveis/tests.py`
  - Import (linha 16): adicionar `validate_rg_cpf` ao import de `.validators`.
  - Nova classe `ValidateRgCpfTests` (ver Criterios de aceite).

---

## Documentacao relacionada

- `docs/03_modelagem_dados.md`
  Secao 2.6 (Fiador), linha do campo `rg_cpf`: atualizar a coluna "Observacoes" para citar que o campo aceita CPF valido (com digito verificador) ou RG em formato livre (letras, numeros, "." e "-").

- `docs/04_regras_de_negocio.md`
  Nenhuma secao atual trata de validacao de documentos; se o mantenedor da documentacao optar por registrar as regras de validacao do sistema, este e um bom candidato a nova subsecao dentro do documento existente (nao criar arquivo novo).

- `docs/07_design_ui_ux.md`
  Sem impacto (mudanca e so de backend/model).

---

# Dependencias

Nenhuma. Modulo independente.

---

# Criterios de aceite

- [ ] `validate_rg_cpf` existe em `imoveis/validators.py`, aceita CPF valido (com ou sem mascara) e RG alfanumerico (com "." e "-"), e rejeita CPF com digito verificador invalido.
- [ ] `Fiador.rg_cpf` usa `validators=[validate_rg_cpf]`.
- [ ] Migration gerada e aplicada sem erros (`python manage.py makemigrations imoveis` e `python manage.py migrate`).
- [ ] Novos testes em `imoveis/tests.py` (classe `ValidateRgCpfTests`), cobrindo: CPF valido com e sem mascara aceito; CPF com digito verificador errado rejeitado (`ValidationError`); RG alfanumerico simples (ex.: `12.345.678-9`) aceito; string com caracteres invalidos (ex.: `!!!`) rejeitada; teste de modelo (`Fiador(...).full_clean()`) com CPF invalido levantando `ValidationError`, no mesmo estilo de `test_inquilino_cpf_invalido_bloqueado`.
- [ ] `python manage.py test imoveis` roda sem falhas (48 testes existentes + novos).
- [ ] `python manage.py check` sem erros.

---

# Riscos

- Baixo: fiadores ja cadastrados no banco com `rg_cpf` em formato que nao passa nem como CPF nem como RG valido (ex.: valor vazio de fiadores antigos criados antes desta regra) nao sao afetados retroativamente — o validator so roda em `full_clean()`/formularios, nunca em dados ja salvos.
- Atencao ao nao quebrar o caso de RG que comeca com digitos e por acaso tem 11 caracteres numericos (ex.: RG de 11 digitos sem letra) — nesse caso o validator tentara valida-lo como CPF e pode rejeitar um RG legitimo. Documentar essa limitacao conhecida no docstring da funcao (mesma limitacao que ja existe em `validate_cpf_cnpj`).
