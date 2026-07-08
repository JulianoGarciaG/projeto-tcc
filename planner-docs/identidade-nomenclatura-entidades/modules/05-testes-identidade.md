# Objetivo

Cobrir com testes automatizados (`imoveis/tests.py`) a nova camada de
identidade: `codigo`, `rotulo_curto`/`rotulo_longo`, `nome_arquivo`, labels de
select e o nome de arquivo real devolvido pelas views `*_gerar_pdf`.

---

# Arquivos afetados

- `imoveis/tests.py` — novas classes de teste (ver "Especificação"); ajuste
  das 3 asserções existentes em `GeracaoPdfViewTests` (linhas 483-513) que
  hoje não checam o nome do arquivo.

---

# Dependências

Depende de `01-identidade-core`, `02-forms-labels-select` e
`03-pdf-nomes-arquivo` já implementados (não há o que testar antes disso).

---

# Leituras adicionais

Nenhuma. Usar os helpers de fixture já existentes no arquivo (`criar_base()`,
`limpar_arquivos_gerados()` — conferir no início de `imoveis/tests.py` antes
de escrever os testes novos, para reaproveitá-los em vez de duplicar setup).

---

# Especificação — o que cobrir

## `codigo` (nova classe `IdentidadeCodigoTests`)

- `Imovel`, `Contrato`, `Recibo`, `LaudoVistoria` recém-criados retornam
  `codigo` no formato `PREFIXO-0001` (zero-padded a 4 dígitos) — um teste por
  entidade, usando o prefixo correto (`IMV`/`CTR`/`REC`/`LAU`).
- Um objeto não salvo (`Imovel()`, sem `.save()`) não levanta exceção ao
  acessar `.codigo` (retorna o placeholder, ex.: `IMV-????`).

## `rotulo_curto` / `rotulo_longo` (mesma classe ou `IdentidadeRotulosTests`)

- `Recibo.rotulo_curto` com `periodo_inicio`/`parcela_atual`/`parcela_total`
  preenchidos inclui mês/ano abreviado e "parcela N/M".
- `Recibo.rotulo_curto` **sem** esses campos (só `imovel`/`contrato`
  obrigatórios) não quebra e ainda mostra `codigo` + quem pagou/inquilino.
- `Contrato.rotulo_curto` inclui `inquilino.nome`, endereço do imóvel, período
  abreviado (`mm/aa–mm/aa`) e `get_status_display()`.
- `LaudoVistoria.rotulo_curto` inclui `get_tipo_display()`, endereço do
  imóvel e `locatario_nome()`.
- `Imovel.rotulo_curto` usa `bairro` quando presente e cai para `cidade`
  quando `bairro` está vazio.

## `nome_arquivo` (nova classe `NomeArquivoTests`, sem precisar de banco —
testar diretamente a função pura com instâncias construídas em memória, no
estilo de `imoveis/extenso.py`/testes existentes)

- Nome de arquivo de Contrato/Laudo/Recibo não contém acentos nem caracteres
  fora de `[A-Za-z0-9._-]` (usar um nome com acento, ex. inquilino "João
  Sá", e assertar que o resultado não contém "ã"/"ç"/etc — regressão direta
  do requisito "slugify sem acento, seguro no Windows").
- Passar `versao=2` inclui o sufixo `_v2` no nome; `versao=None` (ou omitido)
  não inclui sufixo de versão.
- Endereço/nome muito longo (ex.: 200 caracteres) resulta em nome de arquivo
  truncado — não deve estourar um teto razoável (ex.: menor que 150
  caracteres no total).

## Labels de select (nova classe `LabelSelectTests`, ou adicionar aos testes
de forms existentes)

- `ContratoForm().fields['imovel'].label_from_instance(imovel)` retorna
  `imovel.rotulo_curto` (idem para os demais campos trocados no módulo 02:
  `LaudoVistoriaForm.imovel`/`.contrato`, `ReciboForm.imovel`/`.contrato`,
  `LancamentoForm.contrato`, `NotificacaoForm.imovel`,
  `DistratoForm.laudo_saida`).
- `test_contratos_por_imovel_json` (já existe, linha 437) — estender a
  asserção existente para conferir que o `label` retornado é
  `contrato.rotulo_curto` em vez do formato antigo.

## Nome de arquivo real nas views `*_gerar_pdf` (ajustar
`GeracaoPdfViewTests`, linhas 474-518)

- `test_contrato_gerar_pdf_view`: além do que já é checado, assertar que o
  header `Content-Disposition` da resposta contém o `codigo` do contrato
  (ex.: `self.assertIn(self.contrato.codigo, resp['Content-Disposition'])`) e
  termina em `_v1.pdf` na primeira geração.
- Gerar o mesmo contrato duas vezes (chamando a view de novo) e assertar que a
  segunda resposta tem `_v2.pdf` no `Content-Disposition` — cobre
  `_proxima_versao` incrementando corretamente entre chamadas.
- Mesmo padrão para `test_laudo_gerar_pdf_view` e `test_recibo_gerar_pdf_view`.

---

# Critérios de aceite

- [ ] `venv/Scripts/python manage.py test imoveis` passa sem falhas nem
      warnings novos.
- [ ] Todas as bullets de "Especificação" viraram pelo menos um teste.
- [ ] Testes de `nome_arquivo` não dependem de banco de dados (instância em
      memória basta, sem `.save()`, exceto onde `codigo` exigir pk — nesse
      caso, usar `criar_base()`/fixtures já existentes).

---

# Riscos

- **Testes de arquivo/versão dependem de limpeza**: gerar PDF duas vezes no
  mesmo teste cria 2 `DocumentoGerado` — usar `limpar_arquivos_gerados()` (já
  usado em `tearDown` de outras classes) para não deixar lixo em `media/`
  entre execuções.
- **Acoplamento com `slugify`**: não assertar o texto exato slugificado (pode
  variar sutilmente entre versões do Django) — assertar propriedades (sem
  acentos, contém substring esperada, termina com sufixo esperado) em vez de
  igualdade exata de string completa.
