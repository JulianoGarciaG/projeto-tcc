# Objetivo

Checklist de validacao manual final do redesign completo: todas as telas,
nos dois temas (claro/escuro) e nos dois breakpoints (desktop/mobile), mais
confirmacao de que nenhum model/view/form/signal/migration foi alterado.
Nao ha codigo novo neste modulo -- e a etapa de QA que fecha a rodada,
seguindo o mesmo padrao usado em
`planner-docs/fix-visual-pdfs-gerados/modules/05-validacao-visual-manual.md`.

---

# Arquivos afetados

Nenhum (apenas validacao manual no navegador + comandos de verificacao).

---

## Documentacao relacionada

- CLAUDE.md
  Apos a validacao, atualizar a secao "ESTADO ATUAL" com um novo item de
  rodada (ex. "Redesign Visual UI") resumindo a mudanca de paleta/tokens,
  a decisao de manter Bootstrap, a introducao de `shelter.css` e o dark
  mode -- seguindo o formato das rodadas anteriores ja documentadas.

- docs/07_design_ui_ux.md
  Revisao final de consistencia: confirmar que todas as secoes (2, 3, 4,
  5, 6, 8, 9, 10, 11, 12, 13, 14, 16) foram atualizadas pelos modulos
  anteriores e nao ficaram tokens antigos (`--color-primary`, Montserrat,
  `#F2B441` etc.) mencionados como atuais.

---

# Dependencias

- Depende de TODOS os modulos 01 a 13 estarem implementados.

---

# Criterios de aceite

- [ ] `venv/Scripts/python manage.py check` sem erros.
- [ ] `venv/Scripts/python manage.py test imoveis` com a suite completa
      passando (nenhuma regressao funcional).
- [ ] `git diff` (ou `git status`) confirma que apenas arquivos em
      `templates/**` e `static/css|js/**` foram alterados -- nenhum arquivo
      `.py` de `imoveis/` (models/views/forms/signals/admin) nem migration
      nova.
- [ ] Tema claro: percorrer manualmente Login, Dashboard, uma listagem
      padrao (ex. Contratos), a listagem de Imoveis nas duas vistas
      (Cards e Tabela), um Detalhe (Contrato), o formulario de Laudo
      (criacao e edicao) e a tela GED -- conferindo contra os mockups do
      `DESIGN_BRIEF.md`.
- [ ] Tema escuro: repetir o mesmo percurso acima com o toggle de tema
      ativado, conferindo contraste/legibilidade de texto, badges, tabelas,
      inputs, popup do Flatpickr, modais de exclusao e toasts.
- [ ] Persistencia do tema: recarregar a pagina e trocar de rota com o
      tema escuro ativo -- confirmar que nao ha flash de tema claro e que
      a preferencia permanece apos fechar/reabrir o navegador
      (localStorage).
- [ ] Dashboard: alternar o tema com os graficos na tela e confirmar que
      ambos (donut e barras) sao redesenhados com as cores corretas, sem
      duplicar canvases.
- [ ] Listagem de Imoveis: alternar Cards/Tabela, recarregar a pagina e
      confirmar que a preferencia foi mantida (localStorage).
- [ ] Responsividade mobile (largura <= 768px): sidebar oculta por
      padrao, abre via hamburguer com overlay, topbar ocupa largura total
      -- comportamento identico ao anterior ao redesign, so com o novo
      visual.
- [ ] Formulario de Laudo: criar um laudo novo (conferir que o checklist
      completo aparece) e editar um laudo existente com itens ja
      preenchidos (conferir que o segmented reflete o estado salvo);
      adicionar e remover uma testemunha dinamicamente.
- [ ] Modais de exclusao (Bootstrap) abrem e fecham corretamente em todas
      as listagens, em ambos os temas.
- [ ] Encoding: `git diff` dos templates editados nao mostra caracteres
      corrompidos (confirma que nenhum arquivo foi tocado com
      Get-Content/Set-Content do PowerShell).

---

# Riscos

- Validacao manual e sujeita a esquecimento de algum fluxo condicional
  (ex.: contrato com fiador + renovacao + distrato simultaneos, imovel
  rural vs. urbano) -- usar os criterios de aceite dos modulos 08-11 como
  checklist auxiliar de casos de teste.
- Nao ha suite automatizada de UI (Selenium/Playwright) no projeto -- toda
  a validacao visual e manual; recomenda-se anotar prints antes/depois
  para o registro da rodada, mas isso e opcional e nao bloqueia o
  fechamento do modulo.
