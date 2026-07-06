# Objetivo

Reskin de `templates/laudos/laudo_form.html`, o formulario mais complexo
do sistema, conforme `DESIGN_BRIEF.md` secao 3.5: card "Dados do Laudo"
(incluindo o select de Contrato dependente do Imovel, via
`contratos_por_imovel_json`), card "Comodos e Itens Vistoriados" com o
segmented control visual Bom/Regular/Ruim sobreposto ao `<select>` de
estado ja existente, e card "Testemunhas" com o formset dinamico. Toda a
logica JS/Django existente (fetch de contratos, delete de formset,
management_form) e preservada -- o segmented e uma camada visual sobre o
`<select>` do Django, nao uma substituicao de campo.

---

# Arquivos afetados

- `templates/laudos/laudo_form.html`

---

## Documentacao relacionada

- docs/04_regras_de_negocio.md
  Sem impacto (nenhuma regra de dependencia contrato/imovel muda -- so o
  visual do select).

- docs/07_design_ui_ux.md
  Documentar o novo componente "segmented sobre select" (se quem implementar
  decidir registrar o padrao) na secao de componentes reutilizaveis.

---

# Dependencias

- Modulo 01 (fundacoes -- classe `.segmented`).
- Modulo 02 (chrome).
- Modulo 12 (reaproveita a convencao de card + footer sticky de
  formulario).

---

# Criterios de aceite

- [ ] Card "Dados do Laudo": grid 2 colunas com Imovel (select), Contrato
      (select, disabled ate escolher imovel, com hint "Filtrado pelo
      imovel selecionado"), Tipo, Data, Responsavel, Observacoes
      (textarea full-width) -- preservando EXATAMENTE o script JS atual
      que faz `fetch(urlBase...)` para `contratos_por_imovel_json` e
      popula o `<select>` de contrato (nao reescrever essa logica, apenas
      o CSS ao redor).
- [ ] Card "Comodos e Itens Vistoriados": aviso informativo preservado
      ("Selecione o estado apenas dos itens vistoriados..."); itens
      agrupados por comodo (`{% ifchanged f.comodo.value %}` preservado);
      cada item com um segmented visual Bom(ok)/Regular(warn)/Ruim(danger)
      que reflete e atualiza o `<select>` real do formset (`f.estado`) --
      o `<select>` pode ficar visualmente oculto (`sr-only`/`hidden`) mas
      deve continuar existindo no DOM e sendo submetido normalmente; a
      opcao "sem estado" (item nao vistoriado) deve continuar possivel de
      representar (nenhum segmento selecionado = valor vazio).
- [ ] **Progressive enhancement:** o `<select>` real so e ocultado DEPOIS de
      o JS construir o segmented com sucesso (ex.: JS adiciona uma classe no
      container que dispara o `hidden` via CSS). Sem JS / se o script falhar,
      o `<select>` nativo do Django permanece visivel e utilizavel -- o
      formulario nunca fica sem forma de preencher o estado. O segmented
      escreve no `<select>` via `.value` + `dispatchEvent(new Event('change'))`
      para manter qualquer listener e a validacao do Django intactos.
- [ ] Checkbox `f.DELETE` de cada item (quando `f.instance.pk`) preservado
      visualmente no padrao do brief.
- [ ] `{{ item_formset.management_form }}` preservado sem alteracao.
- [ ] Card "Testemunhas": header com botao "Adicionar" (linhas dinamicas do
      formset ja existente `testemunha_formset`), campos Nome/CPF/remover
      preservados, `{{ testemunha_formset.management_form }}` preservado.
- [ ] Bloco de erros (`form.errors`/`item_formset.errors`/
      `testemunha_formset.errors`) preservado, com o novo estilo de
      alerta.
- [ ] Footer com Cancelar/Salvar no padrao do modulo 12.
- [ ] Testado manualmente: criar um laudo novo (checklist completo
      renderiza todos os itens do catalogo -- `extra=len(catalogo)`,
      conforme convencao do projeto) e editar um laudo existente
      (segmented reflete o estado ja salvo de cada item).
- [ ] Nenhuma view, url, form, model ou signal alterada.

---

# Riscos

- **Alto**: o segmented control precisa ser sincronizado via JS com um
  `<select>` nativo do Django sem quebrar o submit do formset (nomes
  `form-N-estado` gerados dinamicamente pelo Django) -- testar
  exaustivamente com o formset management form (adicionar/remover linhas
  de testemunha nao deve desalinhar os indices dos itens de vistoria, que
  sao formsets independentes).
- Regressao critica ja documentada no projeto (memoria): `extra=0` no
  formset de itens faz o checklist sumir -- garantir que o reskin nao
  mexa no `item_formset_factory(extra=len(catalogo))` da view.
- Alto acoplamento com o script de contrato-dependente-de-imovel -- validar
  que o hint "Filtrado pelo imovel selecionado" e o estado `disabled`
  inicial do select de contrato continuam corretos apos o reskin.
