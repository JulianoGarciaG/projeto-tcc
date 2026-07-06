# Objetivo

Reskin de `templates/login.html` (layout dedicado, sem sidebar/topbar)
conforme `DESIGN_BRIEF.md` secao 3.1: card central ate 1040px, grid de duas
colunas, painel esquerdo graphite com elementos decorativos e mensagem de
boas-vindas, painel direito com o formulario de autenticacao. Preserva
100% a logica de autenticacao Django (`form`, `next`, mensagens de erro) e
o toggle de mostrar/ocultar senha ja existente.

---

# Arquivos afetados

- `templates/login.html`

---

## Documentacao relacionada

- docs/07_design_ui_ux.md secao 16 (Pagina de Login)
  Atualizar com as novas medidas (max-width 1040px, min-height 560px,
  border-radius 18px) e tokens de cor.

---

# Dependencias

- Modulo 01 (fundacoes) -- consome tokens/classes de `shelter.css`.
- Independente do modulo 02 (login nao estende `base.html`).

---

# Criterios de aceite

- [ ] `login.html` referencia `static/css/shelter.css` no lugar de
      `custom.css`, mais a fonte Inter.
- [ ] Card central com `max-width: 1040px`, `border-radius: 18px`, grid de
      2 colunas, `min-height: 560px`.
- [ ] Painel esquerdo com fundo `--graphite`, circulos decorativos laranja
      translucidos, logo "S" + wordmark Shelter, headline
      "Bem-vindo(a) de volta!", paragrafo e rodape com o ano corrente
      (mantendo o `{% now "Y" %}` ja usado).
- [ ] Painel direito com titulo "Entrar na conta" + subtitulo, campo
      Usuario com icone `bi-person`, campo Senha com icone `bi-lock` +
      toggle `bi-eye`/`bi-eye-slash` (mantendo a funcao JS
      `togglePassword()` ja existente), botao "Entrar" full-width
      graphite.
- [ ] Mensagem de erro de credenciais invalidas (`{% if form.errors %}`)
      preservada, com o novo estilo de alerta.
- [ ] `input type="hidden" name="next"` preservado.
- [ ] Layout responsivo: no mobile, some o painel esquerdo (comportamento
      ja existente via `@media max-width: 767px`), mantido.
- [ ] Fluxo de login funcional testado manualmente (usuario/senha validos
      redirecionam para o dashboard; invalidos mostram a mensagem).

---

# Riscos

- Nenhum -- template isolado, sem dependencia de outras telas, baixo risco
  de regressao. Unico ponto de atencao e nao quebrar o `id`/`name` dos
  campos `username`/`password` usados pelo Django auth.
