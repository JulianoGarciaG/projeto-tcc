# Objetivo

Remover a secao "Documentos (GED)" e o toggle JS PF/PJ associado do formulario de criacao/edicao do contrato, e adicionar os formularios de upload (um por documento) na secao "Documentos" ja existente na tela de detalhe do contrato.

Depende do modulo 07 (usa a URL `contrato_anexar_documento` e pressupoe que `ContratoForm` ja nao expoe os 4 campos).

---

# Arquivos afetados

- `templates/contratos/contrato_form.html`
  - Remover por completo o bloco "Documentos GED" (linhas 32-55: `<div class="section-card mb-4">...Comprovante de Renda...Contrato Social...Recibo de Entrega de Chaves...Comprovante Anual...</div>`).
  - Remover por completo o `{% block extra_js %}...{% endblock %}` (linhas 99-116): esse script so existia para alternar a visibilidade de `comprovante_renda`/`contrato_social` conforme `tipo_contrato`; sem esses campos no formulario, o script fica sem utilidade (nenhum outro campo do formulario depende dele — confirmado que `campo-pf`/`campo-pj` so eram usados nesse bloco removido).
  - Manter `enctype="multipart/form-data"` no `<form>` (linha 11): ainda e necessario por causa do upload de `certidao_onus` no formset de Fiadores.

- `templates/contratos/contrato_detail.html`
  - Secao "Documentos GED" (linhas 52-67): manter a lista de links existente (`documento_gerado`, `comprovante_renda`, `contrato_social`, `recibo_chaves`, `comprovante_anual`) e adicionar, logo abaixo, ate 3 mini-formularios de upload (`method="post"`, `enctype="multipart/form-data"`, `{% csrf_token %}`, um `<input type="file" name="arquivo">` e um botao), cada um apontando para `{% url "contrato_anexar_documento" contrato.pk "<campo>" %}`:
    - Um formulario para `comprovante_renda`, exibido apenas se `contrato.tipo_contrato == "PF"`.
    - Um formulario para `contrato_social`, exibido apenas se `contrato.tipo_contrato == "PJ"` (substitui a antiga logica de toggle via JS — aqui e resolvido no servidor, sem JS, pois `tipo_contrato` ja e um dado fixo do contrato salvo).
    - Um formulario para `recibo_chaves` (sempre visivel).
    - Um formulario para `comprovante_anual` (sempre visivel).
  - Seguir o mesmo estilo visual ja usado no upload do laudo (`templates/laudos/laudo_detail.html` linhas 66-70): `class="d-flex gap-2"`, `form-control form-control-sm` no input, `btn btn-outline-primary btn-sm` no botao.

---

## Documentacao relacionada

- `docs/04_regras_de_negocio.md`
  Ja apontado no modulo 07 (secoes 5 e 8) — este modulo e quem efetivamente implementa a mudanca de UI que a documentacao precisa refletir. Nao duplicar a atualizacao; ela e unica e cobre os dois modulos (07 backend + 08 template).

- `docs/07_design_ui_ux.md`
  Sem impacto obrigatorio; se o mantenedor documentar o padrao "upload pela tela de detalhe" (ja usado por laudo e agora por contrato), este e o local apropriado para uma nota curta sobre o padrao de UI reutilizado.

- `docs/03_modelagem_dados.md`
  Sem impacto.

---

# Dependencias

Depende do Modulo 07 (`07-contrato-documentos-backend.md`): a URL `contrato_anexar_documento` e a remocao dos campos do `ContratoForm` precisam existir antes de alterar os templates.

---

# Criterios de aceite

- [ ] A tela de criacao de contrato (`contrato_create`) nao exibe mais nenhum campo de documento (comprovante de renda, contrato social, recibo de chaves, comprovante anual).
- [ ] A tela de edicao de contrato (`contrato_edit`) tambem nao exibe mais esses campos (mesmo `ContratoForm` usado nos dois fluxos).
- [ ] O toggle JS PF/PJ foi removido de `contrato_form.html` e nao ha erros no console do navegador ao abrir a tela de criacao/edicao.
- [ ] A tela de detalhe do contrato (`contrato_detail`) exibe, na secao "Documentos", um upload para Comprovante de Renda quando `tipo_contrato == "PF"`, ou para Contrato Social quando `tipo_contrato == "PJ"` (nunca os dois ao mesmo tempo), alem dos uploads sempre visiveis de Recibo de Chaves e Comprovante Anual.
- [ ] Apos enviar um arquivo em qualquer um dos uploads, a pagina recarrega no proprio detalhe do contrato, com o link do documento recem-enviado aparecendo na lista de documentos.
- [ ] Nenhuma quebra visual nas demais secoes de `contrato_detail.html` (Informacoes, Fiadores, Renovacao, Distrato, Lancamentos, Laudos).
- [ ] `python manage.py test imoveis` roda sem falhas (inclui os testes de view do modulo 07, que exercitam o fluxo completo).
- [ ] `python manage.py check` sem erros.

---

# Riscos

- Baixo: encoding — este template usa caracteres acentuados (ex.: "Recibo de Entrega de Chaves"); seguir a convencao do `CLAUDE.md` de nunca editar templates com `Get-Content`/`Set-Content` do PowerShell (usar a ferramenta de edicao adequada) para nao corromper o UTF-8 do arquivo.
- Baixo: se o Engineer remover o bloco `extra_js` inteiro de `contrato_form.html` sem conferir se havia outro script alem do toggle PF/PJ, revisar o diff — neste arquivo, na versao atual, o unico conteudo desse bloco e o toggle (confirmado nas linhas 99-116).
