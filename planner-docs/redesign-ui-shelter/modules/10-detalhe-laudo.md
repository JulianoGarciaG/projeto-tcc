# Objetivo

Reskin de `templates/laudos/laudo_detail.html` conforme o padrao Detalhe
do `DESIGN_BRIEF.md` (secao 3.4), adaptado ao dominio do laudo de
vistoria: action bar, card de Informacoes, itens vistoriados por comodo
(com badges de estado bom/regular/ruim) e bloco de anexo do laudo
assinado. Preservar a logica de upload existente (`laudo_anexar_arquivo`).

---

# Arquivos afetados

- `templates/laudos/laudo_detail.html`

---

## Documentacao relacionada

- docs/03_modelagem_dados.md
  Sem impacto (nenhum campo novo exibido).

- docs/07_design_ui_ux.md secao 11 (Badges de Status)
  Confirmar mapeamento das badges de estado do item de vistoria
  (bom=ok, regular=warn, ruim=danger) com os novos tokens.

---

# Dependencias

- Modulo 01 (fundacoes).
- Modulo 02 (chrome).

---

# Criterios de aceite

- [ ] Action bar preservada (Voltar, Editar, Regerar PDF, download do PDF
      gerado quando existir, upload/anexo do laudo assinado).
- [ ] Card de Informacoes com `<dl>` label-valor: imovel, contrato, tipo,
      data, responsavel, observacoes -- mesmos campos de hoje.
- [ ] Lista de itens vistoriados agrupados por comodo, com badge de estado
      (bom/regular/ruim) usando as classes ok/warn/danger do modulo 01,
      preservando as mesmas observacoes por item.
- [ ] Testemunhas do laudo (quando existirem) listadas conforme hoje.
- [ ] Bloco de upload do arquivo assinado (`laudo_anexar_arquivo`) com o
      padrao de input file dashed + botao Enviar graphite, preservando o
      `action`/`enctype` do form.
- [ ] Nenhuma view, url, form, model ou signal alterada.

---

# Riscos

- Itens de vistoria agrupados por comodo dependem de ordenacao ja definida
  pela view/queryset -- nao alterar a ordem de exibicao ao restilizar.
