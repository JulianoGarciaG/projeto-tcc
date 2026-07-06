# Objetivo

Reescrever `templates/documentos/contrato_pdf.html` REPLICANDO FIELMENTE (1:1) o layout de
`docs/pdf-models/contrato_locacao.html`, preservando todas as variáveis de
contexto atualmente usadas (nenhuma mudança em `imoveis/views.py`).

---

# Arquivos afetados

- `templates/documentos/contrato_pdf.html` (reescrita completa)

---

## Documentação relacionada

- docs/03_modelagem_dados.md
  Sem impacto (nenhum campo novo; endereço já documentado com `numero`/`complemento`).
- docs/04_regras_de_negocio.md
  Sem impacto.
- docs/07_design_ui_ux.md
  Sem impacto direto (tratado no módulo 01).

---

# Dependências

- `01-base-pdf-fundacao.md` — usa os blocks/classes CSS definidos ali
  (`.sec`, `.fields`, `.flabel`/`.fval`, `.cards`/`.card`, `.note-box`,
  `.sign-table`, `doc_meta`).

---

# Contexto passado pela view (não alterar)

`imoveis/views.py::_gerar_pdf_contrato` → `{'contrato': contrato}`
(`contrato` vem com `select_related('imovel', 'inquilino')`).

# Mapeamento de variáveis (contexto atual → seção do novo layout)

| Seção do mockup | Variáveis Django a usar |
|---|---|
| Cabeçalho (`doc_meta`) | `contrato.pk`, `contrato.criado_em` |
| Informações do Imóvel | `contrato.imovel.get_tipo_display`, `contrato.imovel.endereco`, `contrato.imovel.numero`, `contrato.imovel.complemento`, `contrato.imovel.bairro`, `contrato.imovel.cidade`, `contrato.imovel.area_m2` (condicional), `contrato.imovel.matricula` (condicional), `contrato.imovel.proprietario.nome`, `contrato.imovel.proprietario.cpf_cnpj` |
| Informações do Locatário | `contrato.get_tipo_contrato_display`, `contrato.inquilino.nome`, `contrato.inquilino.cpf`/`cnpj` (condicional por `tipo_contrato`), `contrato.inquilino.rg` (condicional), `contrato.inquilino.qualificacao` (condicional), `contrato.inquilino.telefone` (condicional), `contrato.inquilino.email` (condicional) |
| Condições da Locação (cards) | `contrato.valor_mensal` (filtro `|brl`), `contrato.dia_vencimento`, `contrato.data_inicio`/`data_fim` (`|date:"d/m/Y"`) |
| Fiador(es) | `contrato.fiadores.all` — **loop**, o mockup mostra só 1 fiador mas o model permite múltiplos (`related_name='fiadores'`); manter `{% for f in contrato.fiadores.all %}` como no template atual, repetindo o bloco "Fiador" completo para cada um. Campos: `f.nome`, `f.rg_cpf`, `f.qualificacao` (condicional), `f.garantia` (condicional). Seção inteira só aparece `{% if contrato.fiadores.all %}` |
| Observações | `contrato.observacoes` (condicional, `linebreaksbr`) |
| Assinaturas | `contrato.imovel.proprietario.nome` + `contrato.imovel.proprietario.cpf_cnpj`; `contrato.inquilino.nome` + `contrato.inquilino.cpf` (ou `cnpj` se PJ, seguir mesma lógica condicional de exibição do documento) |

# Correção a aplicar (fora do escopo visual, mas na mesma reescrita)

- Endereço deve incluir `numero`/`complemento` (hoje ausente em
  `contrato_pdf.html`, presente em `recibo_pdf.html`). Formato sugerido:
  `{{ endereco }}{% if numero %}, {{ numero }}{% endif %}{% if complemento %} — {{ complemento }}{% endif %}{% if bairro %}, {{ bairro }}{% endif %}{% if cidade %} — {{ cidade }}{% endif %}`.

---

# Critérios de aceite

- [ ] Todas as condicionais existentes no template atual são preservadas:
      observações só aparecem se preenchidas; CPF vs CNPJ/RG conforme
      `tipo_contrato`; campos opcionais do imóvel (`area_m2`, `matricula`) só
      aparecem se preenchidos; seção de fiador só aparece se houver ao menos um.
- [ ] Múltiplos fiadores continuam sendo listados (não travar em 1 fiador fixo
      como no mockup).
- [ ] Endereço exibe `numero`/`complemento` nas 3 seções onde aparece
      (Informações do Imóvel).
- [ ] Nenhuma alteração em `imoveis/views.py`.
- [ ] `python manage.py test imoveis.tests.ContratoPdfTests` — ver módulo 05
      para ajustes de assert necessários; o objetivo final é 100% verde.

---

# Riscos

- O mockup assume 1 fiador; garantir que o loop com múltiplos fiadores não
  quebre visualmente (cada fiador deve repetir o bloco de 2 linhas, não
  empilhar tudo em uma única tabela sem separação clara).
- Texto "Garantia oferecida" no mockup é específico de um cenário com imóvel
  em garantia — o campo real `Fiador.garantia` é um `CharField` livre; manter
  o rótulo genérico "Garantia" (como já é hoje) e não impor formato.
