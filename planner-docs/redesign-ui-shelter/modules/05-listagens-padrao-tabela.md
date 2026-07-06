# Objetivo

Reskin dos 6 templates de listagem que usam apenas a vista Tabela (nenhum
tem vista Cards), conforme `DESIGN_BRIEF.md` secao 3.3 (barra de filtros +
result bar + tabela + badges + modal de confirmacao de exclusao). Mesma
receita visual aplicada nos 6 arquivos, cada um com seus proprios campos
de filtro e colunas ja existentes -- nenhuma coluna, filtro ou action e
adicionada/removida, apenas o visual.

---

# Arquivos afetados

- `templates/contratos/contrato_list.html`
- `templates/inquilinos/inquilino_list.html`
- `templates/proprietarios/proprietario_list.html`
- `templates/laudos/laudo_list.html`
- `templates/recibos/recibo_list.html`
- `templates/financeiro/lancamento_list.html`

---

## Documentacao relacionada

- docs/07_design_ui_ux.md secao 10 (Tabelas) e secao 11 (Badges de Status)
  Atualizar com os novos tokens de cor/tipografia das tabelas e badges.

- docs/07_design_ui_ux.md secao 14 (Modais de Confirmacao)
  Atualizar paleta do modal de exclusao (cabecalho `--danger`, botoes).

---

# Dependencias

- Modulo 01 (fundacoes).
- Modulo 02 (chrome -- todos os 6 templates estendem `base.html`).

---

# Criterios de aceite

Para cada um dos 6 arquivos:
- [ ] Barra de filtros (card) com os campos de busca/filtro ja existentes
      de cada tela, restilizada (label uppercase, input com icone quando
      aplicavel) + botoes Filtrar (graphite ou brand conforme brief) e
      Limpar (icone x).
- [ ] Result bar com contador "N encontrado(s)" (texto ja existente,
      quando houver) e botao primario laranja "Novo <Entidade>" levando a
      view de criacao ja existente.
- [ ] Tabela com header `background: var(--sunken)`, `th` uppercase 11px
      `--muted`, linhas com `border-top: 1px solid var(--border)`,
      mantendo exatamente as mesmas colunas de cada tela hoje.
- [ ] Badges de status usando as classes do modulo 01 mapeadas para as
      variantes corretas (ok/danger/info/warn/neu) preservando os mesmos
      `get_status_display`/valores de status usados hoje.
- [ ] Botoes de acao de linha (Ver/Editar/Excluir) com os estilos
      neutro/laranja-soft/danger-soft do brief.
- [ ] Modal Bootstrap de confirmacao de exclusao (`data-bs-toggle="modal"`)
      preservado functionalmente, com o novo visual (`.modal-content`
      herdado do `shelter.css`, titulo em `--danger`).
- [ ] Empty state (`{% empty %}` de cada listagem) usando o padrao
      `bi-inbox` + texto muted centralizado.
- [ ] Nenhuma view, url, form, model ou signal alterada; nenhuma coluna,
      filtro ou acao adicionada/removida.

---

# Riscos

- Sao 6 arquivos quase identicos em estrutura -- risco de inconsistencia
  se um deles for esquecido ou receber tratamento diferente; usar a
  checklist por arquivo acima para garantir paridade.
- `lancamento_list.html`, `inquilino_list.html`, `proprietario_list.html`,
  `laudo_list.html` e `recibo_list.html` tem modais de exclusao com
  `id="del{{ pk }}"` -- confirmar que o novo CSS de `.modal` nao quebra o
  `data-bs-target` (ids continuam iguais, so estilo).
