# Objetivo

Reskin de `templates/contratos/contrato_detail.html` conforme
`DESIGN_BRIEF.md` secao 3.4, a tela de referencia do padrao Detalhe.
Action bar com os botoes condicionais existentes (Voltar, Editar, Regerar
Contrato/PDF, Contrato Gerado/PDF, Renovar, Distrato); cards de
Informacoes, Documentos (GED versionado + os 4 blocos de upload) e
Fiador(es) na coluna esquerda; Lancamentos Financeiros e Laudos de
Vistoria na coluna direita. E o template mais proximo 1:1 do mockup do
brief -- foco em fidelidade de classe/token, sem redesenhar a estrutura.

---

# Arquivos afetados

- `templates/contratos/contrato_detail.html`

---

## Documentacao relacionada

- docs/03_modelagem_dados.md
  Sem impacto (nenhum campo novo exibido).

- docs/04_regras_de_negocio.md
  Sem impacto direto -- confirmar apenas que a descricao do GED versionado
  (versoes listadas com data/hora/usuario) continua compativel com o texto
  já documentado.

---

# Dependencias

- Modulo 01 (fundacoes).
- Modulo 02 (chrome).

---

# Criterios de aceite

- [ ] Action bar com Voltar, Editar, "Regerar Contrato (PDF)" e, quando
      `contrato.documento_gerado` existir, "Contrato Gerado (PDF)";
      Renovar (quando `contrato.status == 'ativo'` e `not renovacao`) e
      Distrato (quando `not distrato`) -- todas as condicoes preservadas
      exatamente.
- [ ] Card "Informacoes" com badge de status no header e `<dl>` label-valor
      com todos os campos atuais (tipo, inquilino, qualificacao
      condicional, imovel, datas, valor mensal, dia de vencimento,
      observacoes condicional).
- [ ] Card "Documentos": link da ultima versao (`contrato.documento_gerado`),
      lista de "Versoes do PDF gerado" (`contrato.documentos_gerados.all`,
      com `numero_versao`/`gerado_em`/`gerado_por`) e os 4 blocos de upload
      GED (Comprovante de Renda com badge PF, Contrato Social com badge PJ,
      Recibo de Entrega de Chaves, Comprovante Anual de Pagamento) --
      cada um com input file dashed + botao Enviar graphite, mantendo os
      4 `action="{% url 'contrato_anexar_documento' contrato.pk '<campo>' %}"`
      exatamente como hoje.
- [ ] Card "Fiador(es)" (quando `fiadores` existir): bloco por fiador com
      nome/qualificacao, RG-CPF, garantia condicional, link da certidao de
      onus condicional.
- [ ] Cards condicionais de Renovacao e Distrato (quando existirem),
      preservando os campos `<dl>` atuais.
- [ ] Coluna direita: card "Lancamentos Financeiros" (tabela + botao
      "+ Novo" + empty-state) e card "Laudos de Vistoria" (tabela + botao
      "+ Novo" + empty-state).
- [ ] Nenhuma view, url, form, model ou signal alterada.

---

# Riscos

- E o template com mais logica condicional de toda a tela de detalhe
  (renovacao/distrato/fiadores/4 uploads GED) -- alto risco de perder um
  bloco `{% if %}` durante o reskin; validar manualmente com um contrato
  que tenha fiador, renovacao E distrato simultaneamente, alem de um
  contrato "limpo" sem nenhum desses.
