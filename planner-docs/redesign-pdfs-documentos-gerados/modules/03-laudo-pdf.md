# Objetivo

Reescrever `templates/documentos/laudo_pdf.html` REPLICANDO FIELMENTE (1:1) o layout de
`docs/pdf-models/laudo_vistoria.html` (identificação, legenda de badges,
tabelas por cômodo, cards de resumo, observações gerais, assinaturas e
testemunhas), preservando todas as variáveis de contexto atuais.

---

# Arquivos afetados

- `templates/documentos/laudo_pdf.html` (reescrita completa)

---

## Documentação relacionada

- docs/03_modelagem_dados.md
  Sem impacto (nenhum campo novo).
- docs/04_regras_de_negocio.md
  Sem impacto (regra de resumo automático via `resumo_vistoria()` não muda).
- docs/07_design_ui_ux.md
  Sem impacto direto (cores dos badges — bom/regular/ruim — já usam tokens
  `#2E7D32`/`#9A6B00`/`#C62828`, avaliados no módulo 01).

---

# Dependências

- `01-base-pdf-fundacao.md` — usa `.sec`, `.fields`, `.cards`, `.note-box`,
  `.sign-table`, `doc_meta`, além de novas classes específicas deste
  documento: `.data-table`, `.badge`/`.badge-bom`/`.badge-reg`/`.badge-ruim`,
  `.row-alt` (definir se ficam no CSS base — reutilizáveis só aqui — ou no
  próprio `laudo_pdf.html`; como só o laudo usa, recomenda-se declarar essas
  classes localmente neste template, dentro de um `{% block %}` de estilo
  extra ou repetidas no próprio arquivo, para não poluir o CSS base com
  classes de uso único).

---

# Contexto passado pela view (não alterar)

`imoveis/views.py::_gerar_pdf_laudo` →
```
{'laudo': laudo, 'grupos': _itens_agrupados(laudo), 'resumo': laudo.resumo_vistoria(), 'testemunhas': laudo.testemunhas.all()}
```
`_itens_agrupados` (mesmo arquivo) já agrupa os itens por cômodo, preservando
a ordem — **não precisa mudar**, o novo layout consome a mesma estrutura
(`grupos` é uma lista de `{'comodo': str, 'itens': [ItemVistoria, ...]}`).

# Mapeamento de variáveis

| Seção do mockup | Variáveis Django |
|---|---|
| Cabeçalho (`doc_meta`) | `laudo.pk`, `laudo.criado_em` |
| Título | `laudo.get_tipo_display` |
| Identificação | `laudo.get_tipo_display`, `laudo.data` (`|date:"d/m/Y"`), `laudo.imovel.endereco/numero/complemento/bairro/cidade` (mesma correção de endereço do módulo 02), `laudo.locador_nome` (método), `laudo.locatario_nome` (método), `laudo.responsavel` |
| Legenda de badges | Estático (BOM/REGULAR/RUIM) — sem dado dinâmico |
| Tabelas por cômodo | `{% for grupo in grupos %}` → `grupo.comodo` (título), `{% for item in grupo.itens %}` → `item.item`, `item.estado` (mapear para classe do badge — ver abaixo), `item.get_estado_display`, `item.observacao` (condicional) |
| Resumo da Vistoria (cards) | `resumo.total`, `resumo.bom`, `resumo.regular`, `resumo.ruim` |
| Observações Gerais | `laudo.observacoes` (condicional, `linebreaksbr`) |
| Data/local antes das assinaturas | `laudo.local_assinatura` / `laudo.data_assinatura` (condicional, igual ao template atual) |
| Assinaturas | `laudo.locador_nome`, `laudo.locatario_nome` |
| Testemunhas | `{% for t in testemunhas %}` → `t.nome`, `t.cpf` (condicional). Quantidade é variável (0 a N) — mockup mostra exatamente 2 lado a lado; usar `{% for %}` com `{% cycle %}`/agrupamento de 2 em 2 numa tabela, **ou** simplificar para uma linha por testemunha se o agrupamento em pares tornar o template complexo demais (decisão do Engineer, desde que suporte 0, 1 ou N testemunhas sem quebrar) |

# Mapeamento estado → badge

Como o `xhtml2pdf` renderiza templates Django normalmente (não é o pisa que
limita isso, é puro Django Template Language), usar:
```
{% if item.estado == 'bom' %}badge-bom{% elif item.estado == 'regular' %}badge-reg{% else %}badge-ruim{% endif %}
```
Aplicar o mesmo mapeamento na borda esquerda colorida de cada `<td>` do item
(`border-left: 3px solid <cor>`), como no mockup.

# Pontos de atenção herdados de testes existentes (ver módulo 05 para o ajuste)

- `imoveis/tests.py::LaudoTests.test_pdf_laudo_condicionais` hoje verifica:
  - `'1 item vistoriado'` (frase textual do resumo) — o novo layout substitui
    essa frase por cards numéricos (`Total de itens: 1`, etc.). **Este texto
    exato vai deixar de existir** — decisão registrada no módulo 05.
  - `'assinatura-laudo'` (classe CSS do espaçamento extra acima da linha de
    assinatura do laudo, para assinatura manuscrita). Preservar esse
    comportamento visual (espaço maior que o do contrato/recibo) na nova
    tabela `.sign-table` do laudo — pode-se manter a classe adicional
    `assinatura-laudo` no elemento correspondente (ex.:
    `<table class="sign-table avoid-break assinatura-laudo">`) só para não
    quebrar o teste, ou atualizar o teste (módulo 05 decide).

---

# Critérios de aceite

- [ ] Todas as condicionais do template atual são preservadas (observações
      gerais só se preenchidas; local/data de assinatura só se preenchidos;
      testemunhas só se existirem).
- [ ] Endereço do imóvel exibe `numero`/`complemento`.
- [ ] Badges de estado usam cor correta para `bom`/`regular`/`ruim` em 100%
      dos itens (incluindo bordas de item da tabela).
- [ ] Resumo (cards) reflete exatamente `resumo_vistoria()` sem recalcular
      nada no template.
- [ ] Suporta 0, 1 ou N testemunhas sem erro de template.
- [ ] Laudos com muitos itens/cômodos continuam paginando corretamente
      (validação real no módulo 06 — `page-break-inside: avoid` nos blocos por
      cômodo).

---

# Riscos

- Tabela por cômodo com `page-break-inside: avoid` pode forçar cômodos
  inteiros para a página seguinte de forma indesejada se o cômodo tiver muitos
  itens — validar com um laudo real de 5 cômodos/32 itens (catálogo seed da
  migração 0004) no módulo 06.
- Agrupar testemunhas em pares (2 colunas) complica o template quando a
  contagem é ímpar; se o Engineer optar por lista single-column, o resultado
  visual diverge levemente do mockup — aceitável, documentar a decisão no
  código (comentário no template).
