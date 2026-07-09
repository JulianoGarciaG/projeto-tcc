# Objetivo

Tornar o sino da topbar clicável, expandindo um dropdown com as últimas N
notificações do usuário (`ultimas_notificacoes_usuario`, já populado pelo
context processor do módulo 3). Sem badge de contagem não-lida (não há
conceito de lida/não lida neste escopo).

---

# Arquivos afetados

- `templates/base.html` — substituir o `<span class="icon-btn">` do sino
  (linhas 124-126 atualmente) por um dropdown Bootstrap.
- `static/css/shelter.css` — estilos do dropdown de notificações.

---

# Dependências

Depende do módulo `03-context-processor-sino` (consome
`ultimas_notificacoes_usuario` no template).

---

# Leituras adicionais

Nenhuma (padrão de tokens de cor — `--ok`/`--danger`/`--warn`/`--info` e
pares `-bg` — já usado pelos badges em `shelter.css:740-752`, referenciado em
plan.md).

---

# Implementação

Bootstrap 5.3 (já carregado via CDN, bundle com JS de dropdown incluso) —
não é necessário JS customizado.

Trocar o bloco atual:

```html
<span class="icon-btn" title="Notificações" aria-label="Notificações">
  <i class="bi bi-bell"></i>
</span>
```

por:

```html
<div class="dropdown notif-dropdown">
  <button class="icon-btn" type="button" id="notifDropdown" data-bs-toggle="dropdown"
          aria-expanded="false" title="Notificações" aria-label="Notificações">
    <i class="bi bi-bell"></i>
  </button>
  <ul class="dropdown-menu dropdown-menu-end notif-menu" aria-labelledby="notifDropdown">
    <li><h6 class="dropdown-header">Notificações</h6></li>
    {% for n in ultimas_notificacoes_usuario %}
    <li>
      <div class="notif-item notif-{{ n.nivel }}">
        <div class="notif-msg">{{ n.mensagem }}</div>
        <div class="notif-time">{{ n.criado_em|date:"d/m/Y H:i" }}</div>
      </div>
    </li>
    {% empty %}
    <li><span class="dropdown-item-text text-muted">Nenhuma notificação.</span></li>
    {% endfor %}
  </ul>
</div>
```

Mapear `nivel` para cor usando as classes de badge já existentes como
referência (não reutilizar `.badge-*` diretamente pois são para status de
negócio — criar classes próprias `.notif-success/.notif-error/.notif-warning/
.notif-info` em `shelter.css`, com a mesma lógica de tokens):

```css
.notif-dropdown .dropdown-menu { min-width: 320px; max-height: 400px; overflow-y: auto; }
.notif-item { padding: .5rem .75rem; border-left: 3px solid transparent; }
.notif-success { border-left-color: var(--ok); }
.notif-error   { border-left-color: var(--danger); }
.notif-warning { border-left-color: var(--warn); }
.notif-info    { border-left-color: var(--info); }
.notif-msg  { font-size: .875rem; color: var(--ink); }
.notif-time { font-size: .75rem; color: var(--neu); }
```

Testar em ambos os temas (`data-theme` claro/escuro) — `var(--ink)`/
`var(--neu)` já são tokens que respondem ao tema, então não deve exigir
override adicional, mas conferir visualmente.

---

# Critérios de aceite

- [ ] Clicar no sino abre um dropdown Bootstrap (sem JS customizado).
- [ ] Dropdown lista as notificações de `ultimas_notificacoes_usuario`,
      mais recente primeiro (já garantido pela `Meta.ordering` do model).
- [ ] Cada item mostra mensagem, nível (indicado por cor) e data/hora.
- [ ] Estado vazio ("Nenhuma notificação.") quando não há registros.
- [ ] Sem badge numérico de não-lidas (fora de escopo).
- [ ] Visual correto em tema claro e escuro.
- [ ] Responsivo/mobile: dropdown não estoura a viewport (usar
      `dropdown-menu-end` já presente no exemplo).

---

# Riscos

- `base.html` é estendido por todas as páginas — qualquer erro de sintaxe
  Django template quebra o sistema inteiro. Revisar com atenção antes de
  salvar.
- Seguir a nota de encoding do CLAUDE.md: nunca editar `base.html` com
  `Get-Content`/`Set-Content` do PowerShell — usar a ferramenta de edição
  (evita corromper UTF-8, ex: acentos em "Notificações").
