# Objetivo

Remover o botão de colapso da sidebar (desktop) e toda a lógica JavaScript inline associada (leitura/gravação de `localStorage` e toggle de classe), mantendo intocado o comportamento do menu mobile (botão hamburguer/overlay).

---

# Arquivos afetados

- `templates/base.html`
  - Remover o `<script>` inline no `<head>` (linhas 9-14 no estado atual) que aplica `document.documentElement.classList.add('sidebar-collapsed')` a partir do `localStorage`.
  - Remover o botão `#sidebar-collapse-toggle` na topbar (bloco "Botão de colapso da sidebar (desktop)", linhas 111-115 no estado atual).
  - Remover, dentro do `<script>` no final do `<body>`, o bloco "Colapso desktop (G1)" (linhas 175-179 no estado atual): o `addEventListener('click', ...)` que alterna `sidebar-collapsed` e grava em `localStorage`.
  - Manter integralmente o script de sidebar mobile (`sidebar-toggle`, `sidebar-overlay`, `openSidebar`/`closeSidebar`) e o script de toasts.

---

## Documentação relacionada

- `docs/07_design_ui_ux.md`
  Sem impacto direto (o documento já não descreve o colapso desktop). Nenhuma atualização necessária neste módulo.

- `CLAUDE.md`
  A seção "ESTADO ATUAL > Consolidado > Rodada 2" cita "colapso da sidebar no desktop (persistido em localStorage)" como funcionalidade entregue. Após a remoção completa (módulos 01-03), esse trecho deve ser revisto para refletir que a sidebar é sempre expandida. Fora do escopo de edição deste plano (Planner não altera documentação/CLAUDE.md); apenas sinalizar para revisão humana.

---

# Dependências

Nenhuma. Este módulo pode ser implementado isoladamente.

---

# Critérios de aceite

- [ ] O botão de colapso (`#sidebar-collapse-toggle`) não existe mais no HTML renderizado.
- [ ] Nenhum script no `base.html` lê ou grava a chave `sidebarCollapsed` no `localStorage`.
- [ ] Nenhum script adiciona/remove a classe `sidebar-collapsed` em `<html>`.
- [ ] O menu hamburguer mobile (`#sidebar-toggle`) e o overlay continuam funcionando normalmente (sem alteração de comportamento).
- [ ] Toasts continuam funcionando normalmente (script não afetado).
- [ ] `python manage.py check` não acusa erros (mudança é só em template, mas validar que não há template tag quebrada).

---

# Riscos

- Baixo: se o Engineer remover acidentalmente o script de sidebar mobile por estar próximo do bloco de colapso no mesmo `<script>` tag — revisar o diff cuidadosamente antes de salvar.
- Nenhum outro template referencia `sidebar-collapse-toggle` ou `sidebarCollapsed` (confirmado por busca no repositório), portanto não há risco de quebra em outras páginas.
