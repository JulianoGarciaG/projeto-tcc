# Plano: Remoção do colapso da sidebar + correção do dimensionamento da logo

## Objetivo
Remover completamente a funcionalidade de colapso da sidebar (desktop) introduzida na Rodada 2 (item G1), fazendo com que a sidebar permaneça **sempre expandida**, e corrigir o CSS da logo dentro da sidebar para que ela preencha corretamente a largura disponível.

## Estado atual
- O colapso da sidebar é implementado em 3 pontos:
  - `templates/base.html` — script inline no `<head>` que lê `localStorage.getItem('sidebarCollapsed')` e aplica a classe `sidebar-collapsed` no `<html>` antes do paint; botão `#sidebar-collapse-toggle` na topbar; script inline no final do body que alterna a classe e persiste no `localStorage`.
  - `static/css/custom.css` — bloco `@media (min-width: 769px) { html.sidebar-collapsed { ... } }` (linhas ~80-97) com todas as regras de estado colapsado, e o elemento `.brand-compact` (marca reduzida "S") usado apenas nesse estado.
  - Não há arquivo JS dedicado ao colapso — toda a lógica está inline em `base.html`. `static/js/masks.js` não participa disso.
- Nenhuma outra página/template depende do estado colapsado (busca `sidebar-collapsed`/`sidebarCollapsed` restrita a `CLAUDE.md`, `static/css/custom.css`, `templates/base.html`, `PLANO_AJUSTES_RODADA2.md`).
- A logo (`#sidebar .sidebar-brand img`) usa `width: 100%; height: 100%; object-fit: contain; object-position: left center;` dentro de um container `.sidebar-brand` com `padding: .75rem 1rem` e `height: 72px`. Como o SVG tem proporção mais larga que a altura disponível, `object-fit: contain` limita o tamanho pela altura e `object-position: left center` ancora a imagem à esquerda, deixando espaço vazio à direita — por isso a logo não preenche visualmente a largura da sidebar.
- `docs/07_design_ui_ux.md` (seção 5 e 12) não documenta o colapso desktop; não requer remoção de conteúdo, mas pode registrar a decisão de sidebar sempre expandida se aplicável.

## Resumo dos módulos
1. **01-remover-toggle-e-script.md** — Remove o botão de colapso da topbar e os dois trechos de JS inline (`head` e final do `body`) em `templates/base.html`.
2. **02-remover-css-colapso.md** — Remove o bloco CSS de estado colapsado e a marca compacta (`brand-compact`) em `static/css/custom.css` e no HTML de `base.html`.
3. **03-ajustar-css-logo.md** — Corrige o dimensionamento da logo na sidebar (`.sidebar-brand` / `.sidebar-brand img`) para preencher a largura disponível.

## Ordem de implementação
1. Módulo 01 (remove gatilhos de UI e JS)
2. Módulo 02 (remove CSS e HTML remanescente do estado colapsado) — depende do 01 para remover a referência ao `brand-compact` de forma coerente
3. Módulo 03 (independente — pode ser feito em paralelo, mas é listado por último por ser um ajuste visual isolado)

## Dependências entre módulos
- Módulo 02 depende do Módulo 01 apenas na ordem lógica de remoção (evitar remover CSS de um elemento HTML que ainda está referenciado por JS ativo); tecnicamente podem ser feitos na mesma alteração de `base.html`/`custom.css`.
- Módulo 03 é independente dos módulos 01 e 02.

## Observações gerais
- Nenhuma migration, model, view ou form é afetado — mudança é 100% front-end (template + CSS).
- `docs/07_design_ui_ux.md` deve ser revisado após a implementação (ver cada módulo) para remover/atualizar qualquer menção futura ao estado colapsado e registrar a especificação final da logo, caso a documentação venha a ser atualizada por outro fluxo (o Planner não edita a documentação).
- `CLAUDE.md`, na seção "Rodada 2", menciona o colapso da sidebar como convenção estabelecida; após a remoção, essa menção deve ser revista por quem mantém o CLAUDE.md (fora do escopo do Planner/Engineer deste plano, mas registrado como observação).
- Testes automatizados (`imoveis/tests.py`) não cobrem sidebar/CSS — não são afetados.
