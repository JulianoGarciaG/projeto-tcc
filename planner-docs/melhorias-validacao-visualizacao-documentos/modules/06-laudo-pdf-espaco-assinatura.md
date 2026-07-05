# Objetivo

Aumentar o espaco em branco acima da linha de assinatura no PDF do Laudo de Vistoria, para viabilizar assinatura manuscrita apos impressao.

---

# Arquivos afetados

- `templates/documentos/base_pdf.html`
  - Classe `.assinatura-laudo` (linhas 76-78): aumentar o valor de `margin-top` de `80px` para um valor maior (recomendado: entre `130px` e `150px`). Atualizar o comentario acima da regra (linha 75) para refletir o novo valor/motivo.
  - Nao alterar a classe base `.assinatura` (linhas 71-74, `margin-top: 40px`), que e usada por `contrato_pdf.html` e `recibo_pdf.html` — a mudanca deve ficar restrita a `.assinatura-laudo`, aplicada apenas em `laudo_pdf.html` (linhas 50 e 53 desse template).

---

## Documentacao relacionada

- `docs/07_design_ui_ux.md`
  Sem impacto (documento nao detalha valores de CSS de PDFs).

- `docs/03_modelagem_dados.md` / `docs/04_regras_de_negocio.md`
  Sem impacto.

---

# Dependencias

Nenhuma. Modulo independente — alteracao isolada de uma unica regra CSS.

---

# Criterios de aceite

- [ ] `.assinatura-laudo` tem `margin-top` maior que o valor atual (80px), suficiente para assinatura manuscrita (recomendado 130-150px).
- [ ] `.assinatura` (base) permanece com `margin-top: 40px`, sem alteracao.
- [ ] Gerar/baixar um PDF de laudo de teste (`laudo_gerar_pdf`) e conferir visualmente que ha espaco maior acima de cada linha de assinatura (locador e locatario), sem que o conteudo do laudo seja cortado ou empurrado para uma pagina extra em laudos curtos.
- [ ] Teste existente `test_pdf_laudo_condicionais` (`imoveis/tests.py`, verifica apenas a presenca da classe `assinatura-laudo` no HTML, nao o valor em px) continua passando sem alteracao.
- [ ] `python manage.py test imoveis` roda sem falhas.

---

# Riscos

- Baixo: espaco excessivo pode empurrar as testemunhas (bloco seguinte, `laudo_pdf.html` linhas 57-64) para uma segunda pagina em laudos com muitos itens vistoriados. Validar visualmente com um laudo "cheio" (32 itens do catalogo, ver seed da migracao 0004) antes de finalizar o valor exato de `margin-top`.
