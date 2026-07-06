# Objetivo

Atualizar os asserts de `imoveis/tests.py` que dependem de texto/classes CSS
substituídos pelo redesign dos módulos 02, 03 e 04, garantindo que a suíte
completa volte a passar 100% sem reduzir a cobertura/intenção original de
cada teste.

---

# Arquivos afetados

- `imoveis/tests.py` (apenas os métodos listados abaixo — não alterar
  `setUp`/fixtures/outros testes não relacionados a PDF)

---

## Documentação relacionada

- Nenhum documento de `/docs` é impactado por este módulo (mudança é
  exclusivamente de teste automatizado).

---

# Dependências

- `02-contrato-pdf.md`, `03-laudo-pdf.md`, `04-recibo-pdf.md` — precisa saber
  o texto/classe final escolhido em cada um antes de ajustar os asserts.

---

# Testes a revisar (mapeamento exato)

## `ReciboPdfTests` / `RecibosTests` (classe com `test_pdf_endereco_completo_e_periodo`, linha ~171-182 hoje)

- `self.assertIn('de 01/06/2026 a 30/06/2026', html)` — se o módulo 04 adotar
  o texto do mockup (sem prefixo "de"), trocar para
  `self.assertIn('01/06/2026 a 30/06/2026', html)`.
- `self.assertNotIn('Correspondente ao Período', html)` — se o rótulo mudar
  para "Período correspondente", trocar a string do assert mantendo a mesma
  intenção (garantir que o rótulo some quando `periodo_fim` é `None`).

## `ContratoPdfTests` (linhas ~185-210 hoje)

- Sem mudança de texto esperada (labels "Observações", "Pessoa Física",
  "Pessoa Jurídica", "Razão Social" devem ser mantidos literalmente nos
  módulos 02) — apenas rodar e confirmar que passam; se o Engineer alterar
  algum desses rótulos no módulo 02, atualizar aqui também.

## `LaudoTests.test_pdf_laudo_condicionais` (linhas ~267-288 hoje)

- `self.assertIn('1 item vistoriado', html)` — essa frase deixa de existir
  (resumo agora é feito via cards numéricos). Substituir por asserts que
  validem os números do resumo através do card, por exemplo:
  ```python
  self.assertIn('Total de itens', html)
  # resumo.total == 1 no cenário do teste
  ```
  Manter a verificação de que o número correto (`1`) aparece associado ao
  card de total — se o valor "1" for genérico demais para `assertIn` (pode
  aparecer em outros lugares do HTML, ex.: no nome do laudo), preferir
  `assertIn('>1<', html)` ou verificar `resumo['total'] == 1` topicamente já
  garantido por `test_resumo_vistoria_calculado` (outro teste) — neste teste
  específico o foco deve ser confirmar que a seção de resumo aparece com os
  rótulos certos, não recontar o número.
- `self.assertIn('assinatura-laudo', html)` — manter esse assert **sem
  alteração** se o módulo 03 decidir preservar a classe `assinatura-laudo` no
  novo `.sign-table` do laudo (opção recomendada, menor diff). Caso o
  Engineer prefira renomear a classe, atualizar este assert para o novo nome
  e deixar registrado no commit o motivo da mudança de nome.

# Execução obrigatória

Após os ajustes, rodar:
```
venv/Scripts/python manage.py test imoveis
```
e confirmar que todos os testes (48 atuais + quaisquer novos) passam.

---

# Critérios de aceite

- [ ] `venv/Scripts/python manage.py test imoveis` sem falhas.
- [ ] Nenhum teste foi removido ou teve sua asserção enfraquecida a ponto de
      deixar de testar o comportamento original (ex.: condicional "só aparece
      se preenchido" continua sendo verificada, mesmo que o texto mude).
- [ ] Nenhuma mudança em testes fora do escopo de PDF (formulários, models,
      signals, views não relacionadas).

---

# Riscos

- Enfraquecer um assert (trocar `assertIn(texto_especifico)` por algo genérico
  demais) pode mascarar uma regressão futura — revisar cada troca com atenção
  ao que o teste original realmente validava (presença condicional de dado,
  não só o texto em si).
