# Objetivo

Reescrever `templates/documentos/recibo_pdf.html` REPLICANDO FIELMENTE (1:1) o layout de
`docs/pdf-models/recibo_pagamento.html` (destaque da quantia recebida, dados
do recibo, composição do valor, assinatura), preservando a regra de "exibir
apenas campos preenchidos" já implementada.

---

# Arquivos afetados

- `templates/documentos/recibo_pdf.html` (reescrita completa)

---

## Documentação relacionada

- docs/03_modelagem_dados.md
  Sem impacto (nenhum campo novo).
- docs/04_regras_de_negocio.md
  Sem impacto.
- docs/07_design_ui_ux.md
  Sem impacto direto (tratado no módulo 01).

---

# Dependências

- `01-base-pdf-fundacao.md` — usa `.sec`, `.fields`, `doc_meta`, além de um
  bloco de destaque específico do recibo (a caixa "Quantia recebida" com
  barra lateral dourada e valor em fonte grande) — se esse componente não for
  genérico o bastante para reaproveitar em outro documento, declarar como
  estilo local neste template (mesma lógica do módulo 03 para `.data-table`).

---

# Contexto passado pela view (não alterar)

`imoveis/views.py::_gerar_pdf_recibo` → `{'recibo': recibo}`
(`recibo` vem com `select_related('imovel', 'contrato__inquilino')`).

# Mapeamento de variáveis

| Seção do mockup | Variáveis Django |
|---|---|
| Cabeçalho (`doc_meta`) | `recibo.pk`, `recibo.criado_em` |
| Título | `"Recibo"` + `{% if recibo.parcela_atual and recibo.parcela_total %} — Parcela {{ recibo.parcela_atual }}/{{ recibo.parcela_total }}{% endif %}` (igual ao atual) |
| Quantia recebida (destaque) | `recibo.quantia` (`|brl`), **condicional** — só renderizar a caixa se `recibo.quantia` existir (igual ao comportamento atual) |
| Dados do recibo | `recibo.imovel.endereco/numero/complemento/cidade` (condicional em `recibo.imovel`), `recibo.quem_pagou` (condicional), `recibo.periodo_inicio`/`periodo_fim` (condicional — só se ambos preenchidos), `recibo.vencido_em` (condicional) |
| Composição do Valor | Seção inteira condicional a `recibo.valor_aluguel or recibo.valor_impostos or recibo.valor_seguros or recibo.valor_condominio`; cada linha (Aluguel/Impostos/Seguros/Condomínio) condicional ao respectivo campo; linha final `recibo.somatorio` (método/property, `|brl`) |
| Assinatura | `recibo.data_assinatura` (condicional, texto "Local, dd de mês de aaaa" — **atenção**: não existe campo de "local" no `Recibo`, apenas `data_assinatura`; manter o comportamento atual, que não usa cidade fixa) `recibo.assinante_nome` (fallback "Assinatura"), `recibo.assinante_cpf` (condicional). Seção só aparece se `assinante_nome or assinante_cpf or data_assinatura` (igual ao atual) |

# Ponto de atenção — texto do label de período

O template atual usa o rótulo "Correspondente ao Período" com o valor
formatado como `de dd/mm/aaaa a dd/mm/aaaa`. O mockup usa o rótulo "Período
correspondente" com o valor `dd/mm/aaaa a dd/mm/aaaa` (sem o prefixo "de").
Adotar o texto do mockup — isso afeta um assert de teste (ver módulo 05).

# Fora de escopo (não implementar)

- "Valor por extenso" (ex.: "Dois mil e quinhentos reais") — não existe
  infraestrutura (`num2words` não é dependência do projeto, não há método no
  model). Omitir essa linha do layout ou deixá-la fora da caixa de destaque.

---

# Critérios de aceite

- [ ] Caixa de "Quantia recebida" só aparece se `recibo.quantia` estiver
      preenchido.
- [ ] Cada linha de "Composição do Valor" (Aluguel/Impostos/Seguros/Condomínio)
      só aparece se o respectivo campo estiver preenchido; a seção inteira só
      aparece se houver ao menos um valor preenchido.
- [ ] "Somatório" sempre reflete `recibo.somatorio` (nunca recalculado no
      template).
- [ ] Bloco de assinatura só aparece se houver `assinante_nome`, `assinante_cpf`
      ou `data_assinatura`.
- [ ] Nenhuma referência a valor por extenso.
- [ ] Nenhuma alteração em `imoveis/views.py`.

---

# Riscos

- Mudança do texto "Correspondente ao Período" → "Período correspondente"
  quebra o assert existente em `imoveis/tests.py` — tratado no módulo 05, mas
  o Engineer deve avisar/confirmar antes de trocar o texto se preferir manter
  o rótulo atual por estabilidade dos testes (decisão de produto, não técnica).
