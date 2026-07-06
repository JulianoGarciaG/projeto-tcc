# Objetivo

Reskin de `templates/ged/documentos.html`: grid de 5 cards (Laudos de
Vistoria, Comprovantes de Pagamento, Contratos Gerados, Laudos Gerados,
Recibos Gerados), cada um com contador no header e tabela interna,
reaproveitando os componentes `card`/`table`/`badge`/empty-state do modulo
01. Esta tela nao corresponde a nenhum dos 5 arquetipos do brief -- e
tratada como variacao do padrao de listagem em tabela.

**Importante (dados aninhados sem mockup):** como o DESIGN_BRIEF nao tem
mockup do GED, a FONTE DE LAYOUT desta tela e a **estrutura ja existente**
de `templates/ged/documentos.html` -- quem implementar NAO deve inventar um
arranjo novo. O trabalho e puramente de reskin: manter a mesma arvore de
blocos (grid de cards -> card por origem -> tabela interna de versoes/itens),
apenas trocando classes/estilos pelos componentes do modulo 01. O padrao
visual de referencia para "card com tabela interna" e a secao Documentos do
Detalhe de Contrato (modulo 09), que o brief cobre; reaproveitar aquela
linguagem (header de card + lista de versoes com data/hora/usuario) aqui.

---

# Arquivos afetados

- `templates/ged/documentos.html`

---

## Documentacao relacionada

- docs/04_regras_de_negocio.md
  Sem impacto (nenhuma regra de GED muda, apenas o visual da tela).

- docs/07_design_ui_ux.md
  Sem impacto direto (nao ha secao dedicada ao GED hoje; se quem implementar
  decidir documentar o padrao "grid de cards com tabela interna", registrar
  como nova sub-secao em Cards e Superficies).

---

# Dependencias

- Modulo 01 (fundacoes).
- Modulo 02 (chrome).

---

# Criterios de aceite

- [ ] Grid de 5 `card`s (2 colunas), cada um com header contendo icone +
      titulo + badge de contagem (`{{ x.count }}`), preservando os 5
      blocos ja existentes: Laudos de Vistoria, Comprovantes de Pagamento,
      Contratos Gerados (Sistema), Laudos Gerados (Sistema), Recibos
      Gerados.
- [ ] Tabelas internas com as mesmas colunas de hoje em cada bloco
      (incluindo `numero_versao`/`gerado_em` nos blocos de GED versionado),
      restilizadas com o padrao de tabela do modulo 01.
- [ ] Empty state (`{% empty %}`) de cada tabela usando `bi-inbox` +
      texto muted.
- [ ] Links "Abrir" para os arquivos preservados (`target="_blank"`).
- [ ] Nenhuma mudanca na view que alimenta esta tela nem nos nomes de
      contexto (`laudos`, `comprovantes`, `contratos_gerados`,
      `laudos_gerados`, `recibos`).

---

# Riscos

- Baixo -- tela somente leitura, sem formularios nem JS de comportamento
  alem dos links; risco de regressao restrito ao CSS.
