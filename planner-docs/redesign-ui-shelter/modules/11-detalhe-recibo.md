# Objetivo

Reskin de `templates/recibos/recibo_detail.html` conforme o padrao Detalhe
do `DESIGN_BRIEF.md` (secao 3.4), adaptado ao dominio do recibo: action
bar (Voltar, Editar, Regerar PDF, download do PDF gerado quando existir) e
card de Informacoes com os campos do recibo (imovel, contrato, periodo,
quem pagou, valor, versoes do GED).

---

# Arquivos afetados

- `templates/recibos/recibo_detail.html`

---

## Documentacao relacionada

- docs/03_modelagem_dados.md
  Sem impacto (nenhum campo novo exibido).

---

# Dependencias

- Modulo 01 (fundacoes).
- Modulo 02 (chrome).

---

# Criterios de aceite

- [ ] Action bar preservada (Voltar, Editar, Regerar Recibo/PDF, link do
      PDF gerado quando existir).
- [ ] Card de Informacoes com `<dl>` label-valor: imovel, contrato,
      quem pagou, periodo (`periodo_inicio`/`periodo_fim`), valor,
      demais campos ja exibidos hoje.
- [ ] Lista de versoes do GED versionado (`recibo.documentos_gerados.all`)
      se ja exibida hoje, preservada com o padrao visual de "versoes do
      PDF gerado" usado no modulo 09 (mesma convencao de card).
- [ ] Nenhuma view, url, form, model ou signal alterada.

---

# Riscos

- Baixo -- template simples, sem formsets nem uploads adicionais alem do
  PDF gerado.
