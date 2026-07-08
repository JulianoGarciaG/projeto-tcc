# Objetivo

Trocar `#{{ obj.pk }}` cru e trechos de `__str__` pouco legíveis nos
templates de lista/detalhe das 4 entidades por `codigo`/`rotulo_longo`
(`imoveis/identidade.py`, módulo `01-identidade-core`). CRUD de exibição —
sem lógica de negócio, propriedades já resolvidas no model.

---

# Arquivos afetados

- `templates/contratos/contrato_detail.html` — linhas 3-4 (`{% block title
  %}`/`{% block page_title %}`): trocar `Contrato #{{ contrato.pk }}` por
  `{{ contrato.codigo }}` (mantendo o texto ao redor, ex.: `Contrato
  {{ contrato.codigo }}`).
- `templates/contratos/renovacao_form.html` — linha 18: trocar
  `Contrato #{{ contrato.pk }} — {{ contrato.inquilino.nome }} / {{ contrato.imovel.endereco|truncatechars:40 }}`
  por `{{ contrato.rotulo_curto }}`.
- `templates/contratos/contrato_list.html` — avaliar se vale adicionar uma
  coluna/badge com `{{ c.codigo }}` (hoje a lista já mostra
  `{{ c.inquilino.nome }}` como link principal — acrescentar o código como
  texto secundário, sem remover o nome do inquilino).
- `templates/recibos/recibo_detail.html` — linhas 3-4 (`Recibo #{{ recibo.pk
  }}` → `{{ recibo.codigo }}`); linha 24 (`#{{ recibo.contrato.pk }} —
  {{ recibo.contrato.inquilino.nome }}` → `{{ recibo.contrato.rotulo_curto }}`).
- `templates/recibos/recibo_list.html` — linha 39 (`#{{ r.pk }}` →
  `{{ r.codigo }}`); linha 51 (mesma troca no texto do modal de exclusão).
- `templates/laudos/laudo_detail.html` — linhas 2-3 (`Laudo #{{ laudo.pk }}`
  → `{{ laudo.codigo }}`).
- `templates/laudos/laudo_list.html` — linha 41: já mostra
  `{{ l.imovel.endereco|truncatechars:35 }}` como link — acrescentar
  `{{ l.codigo }}` como texto secundário (ex.: badge/small ao lado).
- `templates/imoveis/imovel_detail.html` — linha 3 (`{% block title %}
  {{ imovel }}` → `{{ imovel.rotulo_longo }}`); avaliar cabeçalho do card de
  informações (linha ~44-55) para incluir `{{ imovel.codigo }}` visível.
- `templates/imoveis/imovel_list.html` — linhas 86 e 148: já mostram
  `{{ im.endereco|truncatechars:40 }}` como link — acrescentar
  `{{ im.codigo }}` como texto secundário.
- `templates/ged/documentos.html` — nas 5 tabelas (Laudos, Comprovantes,
  Contratos Gerados, Laudos Gerados, Recibos Gerados), adicionar uma coluna
  `Código` usando `{{ l.codigo }}` / `{{ d.contrato.codigo }}` /
  `{{ d.laudo.codigo }}` / `{{ d.recibo.codigo }}` conforme a tabela — hoje
  essas listas não têm nenhum identificador curto, só endereço/nome truncado.

---

# Dependências

Depende de `01-identidade-core` (propriedades `codigo`/`rotulo_curto`/
`rotulo_longo` acessíveis diretamente no template, sem template tag
adicional — Django resolve atributos/properties de objeto nativamente).

---

# Leituras adicionais

Nenhuma.

---

# Critérios de aceite

- [ ] Nenhum template de lista/detalhe das 4 entidades mostra `#{{ obj.pk }}`
      cru (buscar por `#{{` nos arquivos afetados após a mudança).
- [ ] `contrato_detail.html`, `recibo_detail.html`, `laudo_detail.html`
      mostram `codigo` no título/cabeçalho.
- [ ] `imovel_detail.html` usa `rotulo_longo` no `<title>`.
- [ ] As 5 tabelas de `ged/documentos.html` mostram uma coluna de código.
- [ ] Encoding permanece UTF-8 íntegro (acentos/travessões não corrompidos)
      após a edição.

---

# Riscos

- **Encoding no Windows**: editar estes `.html` **somente** com a ferramenta
  Edit — nunca `Get-Content`/`Set-Content` do PowerShell 5.1, que corrompe
  UTF-8 (regra já registrada em CLAUDE.md e na memória do projeto).
- **`truncatechars` já aplicado ao endereço**: ao acrescentar `codigo` como
  texto secundário nas listas, não remover o `truncatechars` existente no
  nome/endereço principal — é o comportamento responsivo já validado.
- **`rotulo_longo`/`rotulo_curto` acessam relações** (`imovel.proprietario`,
  `contrato.inquilino`, etc.) — nas listas, confirmar que a view já faz
  `select_related`/`prefetch_related` adequado (a maioria já faz, pois os
  templates atuais já exibem `inquilino.nome`/`imovel.endereco`); se notar N+1
  novo introduzido especificamente pela troca, reportar ao final da
  implementação do módulo, mas não é esperado — os campos usados por
  `rotulo_curto`/`rotulo_longo` já eram acessados por esses templates antes.
