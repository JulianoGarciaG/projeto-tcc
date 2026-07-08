# Objetivo

Exibir a contagem de `dependentes_cascata` (property criada no módulo
`02-models-dependentes-cascata`) dentro do `modal-body` dos modais de
confirmação de exclusão já existentes, nas 4 listagens afetadas. Só
renderizar o aviso quando a lista não estiver vazia (ou seja, quando
houver pelo menos um dependente com `count > 0`).

Não alterar a estrutura do modal (tamanho, header, footer, botões) — ver
padrão documentado em `docs/07_design_ui_ux.md` §14. O aviso é um bloco de
texto adicional dentro do `modal-body`, entre a pergunta de confirmação
existente e o fechamento da div.

---

# Arquivos afetados

- `templates/imoveis/imovel_list.html` — **dois** modais (`modalExcluir{{ im.pk }}`
  vista Cards, `modalExcluirTb{{ im.pk }}` vista Tabela) iterando o mesmo
  `im` — adicionar o aviso nos dois.
- `templates/contratos/contrato_list.html` — modal `del{{ c.pk }}`.
- `templates/laudos/laudo_list.html` — modal `del{{ l.pk }}`.
- `templates/recibos/recibo_list.html` — modal `del{{ r.pk }}`.

---

# Dependências

Depende do módulo `02-models-dependentes-cascata` (usa a property
`dependentes_cascata` de `Imovel`, `Contrato`, `LaudoVistoria`, `Recibo`).
Implemente `02` antes deste módulo (ou na mesma janela, ver afinidade de
cache em `plan.md`).

---

# Leituras adicionais

Nenhuma.

---

# Detalhamento

Bloco padrão a inserir no `modal-body`, logo após a pergunta de
confirmação existente (`Deseja excluir...?` / `Excluir...?`). Adapte a
variável de loop (`im`, `c`, `l`, `r`) para cada template:

```html
{% with im.dependentes_cascata as deps %}
{% if deps %}
<div class="small text-warning mt-2">
  <i class="bi bi-exclamation-triangle me-1"></i>Também serão excluídos:
  {% for label, n in deps %}{{ n }} {{ label }}{% if not forloop.last %}, {% endif %}{% endfor %}.
</div>
{% endif %}
{% endwith %}
```

Aplicar esse bloco (trocando `im` por `c`, `l`, `r` conforme o template) em
cada modal listado em "Arquivos afetados". Em `imovel_list.html`, inserir
o bloco **nos dois** modais (Cards e Tabela) — ambos iteram a mesma
variável `im` do mesmo `{% for im in imoveis %}`, então o trecho é
idêntico nos dois lugares.

Classe `text-warning` já é coberta pelos tokens de tema (`--warn`) via
overrides do Bootstrap em `shelter.css` — não é necessário criar CSS novo.

---

# Critérios de aceite

- [ ] Os 4 templates listados exibem o aviso de cascata apenas quando
      `dependentes_cascata` não está vazia.
- [ ] `imovel_list.html` tem o aviso nos dois modais (Cards e Tabela).
- [ ] Nenhuma mudança na estrutura/tamanho/botões do modal — só o texto
      adicional dentro do `modal-body`.
- [ ] Testado visualmente (ou ao menos revisado) nos temas claro e escuro
      (classe `text-warning` deve permanecer legível em ambos).
- [ ] `venv/Scripts/python manage.py check` roda sem erros.

---

# Riscos

- Esquecer de replicar o bloco em um dos dois modais de `imovel_list.html`
  (Cards/Tabela) deixaria a vista Tabela sem o aviso.
- Se o módulo `02` usar nomes de property diferentes do combinado
  (`dependentes_cascata`), o template quebra silenciosamente (Django
  engolindo erro de atributo como vazio) — confirmar o nome exato lendo
  `imoveis/models.py` antes de escrever os templates.
