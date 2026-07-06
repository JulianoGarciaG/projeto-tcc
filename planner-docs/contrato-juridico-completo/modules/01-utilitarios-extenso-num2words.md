# Objetivo

Adicionar a dependência `num2words` e criar utilitários puros para
"número por extenso" usados no PDF jurídico do contrato: valor monetário
por extenso, prazo em meses por extenso e dia de vencimento ordinal.
Datas por extenso NÃO fazem parte deste módulo (ver nota abaixo).

---

# Arquivos afetados

- `requirements.txt` (adicionar `num2words`)
- `imoveis/extenso.py` (novo arquivo)
- `imoveis/templatetags/imoveis_tags.py` (novos filtros)

---

## Nota — datas por extenso já funcionam sem código novo

O Planner validou que o filtro nativo `date` do Django já produz datas
por extenso no formato desejado, usando `core/settings.py` como está
(`LANGUAGE_CODE = 'pt-br'`, sem `LocaleMiddleware`, sem
`translation.activate()`):

```
{{ contrato.data_inicio|date:"j \d\e F \d\e Y" }}
```

produz `"1 de Junho de 2026"` (mês com inicial maiúscula, como o
catálogo de tradução pt-br do próprio Django já retorna). Usar esse
filtro diretamente no template do módulo 05 — não criar função própria
para isso.

---

# Especificação de `imoveis/extenso.py`

Funções puras (sem dependência de Django models/views — testáveis
isoladamente, mesmo padrão de `Recibo.somatorio()`/`LaudoVistoria.resumo_vistoria()`):

- `valor_por_extenso(valor: Decimal) -> str`
  Usa `num2words(valor, lang='pt_BR', to='currency', currency='BRL')`
  (ou equivalente da API instalada — validar a assinatura exata da
  versão de `num2words` resolvida pelo `pip install`, pois a API de
  `to='currency'` varia entre versões). Deve tratar `Decimal` convertendo
  para `float`/`int` conforme a função exigir. Retornar a string já
  pronta para uso em texto corrido (ex.: `"mil e quinhentos reais"`).
  Tratar `None`/valor vazio retornando string vazia (mesmo padrão de
  `imoveis_tags.brl` do projeto, que retorna o valor original se não
  converter).

- `meses_entre(data_inicio: date, data_fim: date) -> int`
  Calcula o total de meses inteiros entre duas datas
  (`(fim.year - inicio.year) * 12 + (fim.month - inicio.month)`,
  ajustando -1 se `fim.day < inicio.day`). Não depende de bibliotecas
  externas (`dateutil` não está no projeto — não adicionar).

- `meses_por_extenso(quantidade: int) -> str`
  Usa `num2words(quantidade, lang='pt_BR')` (cardinal) e retorna a frase
  completa, ex.: `"doze meses"` (singular `"um mês"` se `quantidade == 1`).

- `dia_ordinal_extenso(dia: int) -> str`
  Retorna a palavra ordinal do dia de vencimento, ex.: `"primeiro"`,
  `"décimo"`. Usar `num2words(dia, lang='pt_BR', to='ordinal')` se a
  versão instalada suportar `to='ordinal'` para `pt_BR`; validar durante
  a implementação (risco listado abaixo). O template (módulo 05) compõe
  o formato final `"1º (primeiro)"` combinando `contrato.dia_vencimento`
  (numeral) com este filtro (palavra).

---

# Filtros de template (`imoveis/templatetags/imoveis_tags.py`)

Adicionar ao arquivo existente (que já tem o filtro `brl`), sem remover
nada:

- `@register.filter def valor_extenso(value)` → `extenso.valor_por_extenso(value)`
- `@register.filter def meses_extenso(value)` → `extenso.meses_por_extenso(value)`
- `@register.filter def dia_extenso(value)` → `extenso.dia_ordinal_extenso(value)`

Todos devem tratar exceções/entrada inválida retornando o valor original
(mesmo padrão defensivo do filtro `brl` já existente).

---

## Documentação relacionada

- docs/03_modelagem_dados.md
  Sem impacto (não é campo de model, é utilitário de apresentação).
- docs/04_regras_de_negocio.md
  Adicionar uma nota curta sobre a dependência `num2words` e o uso de
  valores por extenso no PDF do contrato (pode entrar na mesma seção que
  documentar o módulo 05, junto com a atualização feita por aquele
  módulo — não duplicar aqui se já for cobrir lá).
- docs/07_design_ui_ux.md
  Sem impacto direto.

---

# Dependências

Nenhuma — módulo independente, primeiro da cadeia.

---

# Critérios de aceite

- [ ] `num2words` presente em `requirements.txt` e instalado no `venv`.
- [ ] `imoveis/extenso.py` criado com as 4 funções especificadas, sem
      importar nada de `django.db`/`imoveis.models` (utilitário puro).
- [ ] Os 3 filtros novos registrados em `imoveis_tags.py` e funcionando
      em um template de teste simples (`{{ valor|valor_extenso }}` etc.).
- [ ] `valor_por_extenso(None)` e `dia_ordinal_extenso(None)` não geram
      exceção (retornam string vazia ou o valor original).

---

# Riscos

- A API de `num2words` para `to='currency'` e `to='ordinal'` varia entre
  versões da lib — validar contra a versão realmente instalada
  (`pip show num2words`) antes de fixar o formato de saída; não assumir
  a assinatura sem testar interativamente.
- `num2words(..., to='ordinal')` pode não ter cobertura completa para
  todos os dias de 1 a 31 em `pt_BR` nas versões mais antigas da lib —
  testar especificamente os extremos (1, 31) e valores redondos (10, 20).
- Plural/singular de "mês"/"meses" e "real"/"reais" deve ser tratado
  manualmente na função (num2words normalmente não pluraliza a unidade
  sozinho para `to='cardinal'`).
