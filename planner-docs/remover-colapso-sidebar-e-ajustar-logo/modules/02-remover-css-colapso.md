# Objetivo

Remover as regras CSS do estado "sidebar colapsada" e o elemento de marca compacta (`brand-compact`, o "S" exibido apenas quando colapsado), garantindo que a sidebar permaneça sempre na largura total (`260px`) e a logo completa (`brand-full`) sempre visível.

---

# Arquivos afetados

- `static/css/custom.css`
  - Remover integralmente o bloco `/* ---------- Colapso desktop da sidebar (G1) ---------- */` e a media query `@media (min-width: 769px) { html.sidebar-collapsed { ... } }` (linhas ~80-97 no estado atual), incluindo todas as regras aninhadas (`.nav-text`, `.nav-section-label`, `.nav-link`, `.nav-link.active`, `.brand-full`, `.brand-compact`).
  - Remover o bloco de estilo de `.sidebar-brand .brand-compact` (linhas ~67-78 no estado atual), já que o elemento correspondente deixará de existir no HTML.
  - Manter a variável `--sidebar-width: 260px` em `:root` sem alterações (ela já representa a largura fixa desejada).

- `templates/base.html`
  - Remover o `<span class="brand-compact" aria-hidden="true">S</span>` dentro de `.sidebar-brand` (linha 29 no estado atual).
  - Opcional/recomendado: remover a classe `brand-full` da tag `<img>` caso não tenha outro uso além de diferenciar do estado colapsado (verificar módulo 03 antes de decidir — se o módulo 03 mantiver o seletor `.brand-full` para estilização, manter a classe; caso contrário, pode ser simplificada para `class="sidebar-logo"` ou similar). Este módulo deve apenas remover o `<span class="brand-compact">`; a decisão sobre renomear `brand-full` fica a critério do módulo 03.

---

## Documentação relacionada

- `docs/07_design_ui_ux.md`
  Seção 5 (Sidebar): nenhuma menção ao colapso/estado compacto existe atualmente, portanto sem impacto de atualização decorrente deste módulo.

---

# Dependências

- Depende do Módulo `01-remover-toggle-e-script.md` ter sido aplicado antes (ou na mesma alteração), para que não reste JavaScript funcional tentando manipular uma classe CSS (`sidebar-collapsed`) que deixou de existir.

---

# Critérios de aceite

- [ ] A classe `html.sidebar-collapsed` e todas as suas regras aninhadas não existem mais em `custom.css`.
- [ ] O seletor `.sidebar-brand .brand-compact` não existe mais em `custom.css`.
- [ ] O elemento `<span class="brand-compact">` não existe mais em `base.html`.
- [ ] A sidebar renderiza sempre com `width: 260px` (`--sidebar-width`) em qualquer largura de viewport desktop (>= 769px).
- [ ] Inspeção visual: nenhum texto de item de menu (`nav-text`, `nav-section-label`) some em nenhuma condição desktop.

---

# Riscos

- Baixo: garantir que a remoção do bloco CSS não deixe chaves `{}` órfãs ou quebre a cascata de outras regras próximas (revisar o arquivo após edição).
- Se o módulo 03 alterar nomes de classe da logo, sincronizar a ordem de aplicação para não reintroduzir referências quebradas a `brand-full`/`brand-compact`.
