# Objetivo

Reescrever `ContratoPdfTests` (asserts do layout antigo não fazem mais
sentido) e acrescentar testes para os utilitários de extenso, os campos
novos de `Contrato`/`Fiador` e o novo contexto de
`_gerar_pdf_contrato`.

---

# Arquivos afetados

- `imoveis/tests.py`

---

# O que precisa mudar

## `ContratoPdfTests` (reescrever)

Os asserts atuais (`'PESSOA FÍSICA'`, `'PESSOA JURÍDICA'`,
`'RAZÃO SOCIAL'`, presença/ausência de `'Observações'`) referem-se ao
layout de cards antigo e deixam de ser válidos. Substituir por asserts
compatíveis com o layout jurídico (módulo 05), por exemplo:

- Presença dos títulos das 21 cláusulas (ou ao menos uma amostra
  representativa — ex.: `'CLÁUSULA I'`, `'CLÁUSULA XX'`,
  `'CLÁUSULA XXI'` — conferir a numeração romana exata usada no
  template).
- Dados fixos do locador aparecem sempre (`SHELTER_LOCADOR['razao_social']`,
  `SHELTER_LOCADOR['cnpj']`), independentemente do `Proprietario`
  cadastrado do imóvel.
- Título muda conforme `contrato.finalidade`
  (`'RESIDENCIAL'`/`'COMERCIAL'`).
- PF vs PJ do locatário continua condicional (adaptar os testes
  `test_pf_exibe_cpf_e_nao_cnpj`/`test_pj_exibe_cnpj` já existentes para
  o novo texto em vez dos rótulos de card antigos).
- Fiador com apenas `rg_cpf` legado (sem `rg`/`cpf` discretos) ainda
  aparece no PDF (teste do fallback do módulo 05).
- Fiador com `rg`/`cpf`/cônjuge preenchidos aparece com os dados
  completos.

## Testes novos — `imoveis/extenso.py` (módulo 01)

Classe nova, por exemplo `ExtensoTests`, cobrindo cada função pura
isoladamente (sem precisar de banco/fixtures):

- `valor_por_extenso`: valor redondo (ex.: `Decimal('1500.00')`), valor
  com centavos, `None`/vazio.
- `meses_entre`: mesmo dia (`2026-01-01` a `2027-01-01` = 12), com ajuste
  de dia (`2026-01-15` a `2027-01-10` = 11).
- `meses_por_extenso`: singular (`1` → contém `'mês'`), plural.
- `dia_ordinal_extenso`: extremos (`1`, `31`) e valor redondo (`10`).

## Testes novos — `Contrato` (módulo 03)

- `criar_base()` (fixture existente) continua funcionando sem definir
  `finalidade` — `Contrato.objects.create(...)` sem o campo assume
  `'residencial'`.
- Teste dedicado de contrato `finalidade='comercial'` (pode reaproveitar
  o padrão do teste PJ já existente).
- `ContratoForm` aceita `local_assinatura`/`data_assinatura` em
  `dd/mm/aaaa` (mesmo padrão de `test_contrato_create_redireciona_sem_pdf`,
  que já testa `data_inicio`/`data_fim` em `dd/mm/aaaa`).

## Testes novos — `Fiador` (módulo 04)

- `Fiador` com os campos novos preenchidos passa em `full_clean()`.
- `Fiador` só com `rg_cpf` legado (campos novos vazios) continua válido
  (retrocompatibilidade).
- `FiadorForm`/`FiadorFormSet` aceitam os campos novos.

## `GeracaoPdfViewTests.test_contrato_gerar_pdf_view` (revisar, não reescrever)

Continua validando `Content-Type`, `%PDF-` e que
`contrato.documento_gerado` foi preenchido — nenhuma mudança esperada
aqui além de garantir que o `tearDown`/`limpar_arquivos_gerados()`
continua limpando os arquivos do novo template também (mesmo mecanismo,
não muda).

---

## Documentação relacionada

- docs/03_modelagem_dados.md
  Sem impacto (testes não são documentação de modelagem).
- docs/04_regras_de_negocio.md
  Sem impacto direto.
- docs/07_design_ui_ux.md
  Sem impacto.

---

# Dependências

- `01-utilitarios-extenso-num2words.md`
- `02-constantes-locador-shelter.md`
- `03-contrato-model-form-finalidade-assinatura.md`
- `04-fiador-model-form-qualificacao-completa.md`
- `05-reescrita-contrato-pdf-clausulas.md`
- `06-view-context-gerar-pdf.md`

Este módulo depende de todos os anteriores — só pode ser concluído
depois deles.

---

# Critérios de aceite

- [ ] `imoveis.tests.ContratoPdfTests` totalmente reescrito e verde.
- [ ] Novos testes de `imoveis/extenso.py` cobrindo as 4 funções.
- [ ] Novos testes de `Contrato`/`Fiador` para os campos do módulo 03/04.
- [ ] Suíte completa (`python manage.py test imoveis`) 100% verde ao
      final — nenhuma regressão nos outros 60+ testes existentes.
- [ ] `limpar_arquivos_gerados()` continua sendo chamado nos `tearDown`
      relevantes (nenhum PDF de teste sobra no `media/`).

---

# Riscos

- Se os módulos 01-06 sofrerem ajustes tardios (ex.: mudança de nome de
  filtro, mudança na estrutura das cláusulas), os testes deste módulo
  são o ponto que absorve o retrabalho — escrevê-los só depois que o
  template (módulo 05) estiver considerado estável evita reescrita
  duplicada.
- Testar a presença literal de trechos do texto jurídico transcrito
  torna os testes sensíveis a qualquer ajuste de redação futuro no
  texto das cláusulas — preferir asserts sobre estrutura (títulos das
  cláusulas, presença de variáveis) a asserts sobre frases inteiras do
  corpo jurídico, quando possível.
