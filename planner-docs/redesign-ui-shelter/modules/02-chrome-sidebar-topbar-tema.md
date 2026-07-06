# Objetivo

Reskin do chrome comum (`templates/base.html`): sidebar graphite 260px e
topbar 64px conforme `DESIGN_BRIEF.md` secao 2, incluindo o novo botao de
toggle de tema (lua/sol) com persistencia em localStorage. Troca o `<link>`
de `custom.css` para `static/css/shelter.css` e adiciona a fonte Inter.
Preserva 100% do comportamento existente: overlay mobile da sidebar,
toasts Bootstrap, blocos `nav_*` de cada template filho, links do menu e
condicional `is_staff` do Painel Admin.

---

# Arquivos afetados

- `templates/base.html`
- `static/js/theme.js` (novo arquivo)

---

## Documentacao relacionada

- docs/07_design_ui_ux.md
  Reescrever secoes 4 (Layout Geral), 5 (Sidebar) e 6 (Topbar) com as novas
  medidas/cores/tokens e o comportamento do toggle de tema.

- docs/07_design_ui_ux.md secao 12 (Responsividade)
  Confirmar que o comportamento do overlay mobile nao mudou (so o visual).

---

# Dependencias

- Modulo 01 (fundacoes) -- consome as classes/tokens de `shelter.css`.

---

# Criterios de aceite

- [ ] `base.html` referencia `static/css/shelter.css` no lugar de
      `custom.css`, mais o link da fonte Inter (Google Fonts).
- [ ] Script inline no `<head>` le `localStorage` (chave dedicada, ex.
      `shelterTheme`) e aplica `data-theme="dark"` no elemento `<html>`
      antes do primeiro paint (sem flash de tema errado).
- [ ] Sidebar com fundo `--graphite`, item ativo com
      `background: var(--graphite-hi)`, `border-left: 3px solid var(--brand)`
      e texto branco -- mantendo os mesmos grupos/labels/icones/links
      atuais (Dashboard; Cadastros: Imoveis/Proprietarios/Inquilinos;
      Operacoes: Contratos/Laudos de Vistoria/Financeiro/Recibos;
      Documentos: GED; Administracao: Painel Admin condicional a
      `user.is_staff`).
- [ ] Topbar 64px, fundo `--surface`, com titulo da pagina a esquerda e, a
      direita: novo botao de toggle de tema (icone `bi-moon-stars` claro /
      `bi-sun` escuro), sino de notificacoes, avatar+nome/role e botao
      Sair -- todos os elementos ja existentes preservados.
- [ ] `static/js/theme.js` implementa: leitura inicial do tema,
      toggle no clique do botao, troca do icone, persistencia em
      localStorage, e disparo de um evento customizado
      (ex. `shelter:theme-changed`) no `document` a cada troca, para que
      o modulo 04 (dashboard) possa redesenhar os graficos.
- [ ] Toasts Bootstrap continuam funcionando (auto-dismiss 5s) com o novo
      visual herdado do `shelter.css` do modulo 01.
- [ ] Overlay mobile da sidebar (`#sidebar-overlay`, classes `.show`)
      continua funcional, sem mudanca de comportamento -- so o visual.
- [ ] Todas as paginas que estendem `base.html` continuam renderizando sem
      erro (`venv/Scripts/python manage.py test imoveis` passando).
- [ ] Nenhuma view, url, form, model ou signal foi alterada.

---

# Riscos

- Script de aplicacao do tema no `<head>` precisa rodar de forma sincrona
  e o mais cedo possivel para evitar flash de tema claro antes de escurecer
  -- colocar como `<script>` inline logo apos `<meta charset>`, nunca como
  arquivo externo assincrono.
- Se o evento customizado de troca de tema nao for disparado corretamente,
  o dashboard (modulo 04) nao vai redesenhar os graficos -- validar a
  integracao ao implementar o modulo 04.
