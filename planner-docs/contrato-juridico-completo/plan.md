# Plano — Contrato jurídico completo (PDF de Contrato — reescrita total)

## Objetivo

Substituir o PDF de Contrato atual (resumo em campos/cards, layout de
`docs/pdf-models/contrato_locacao.html`) por uma **reescrita completa**:
um instrumento particular de locação juridicamente completo, com
**21 cláusulas fixas (I a XXI)** transcritas do modelo fornecido pelo
cliente (`modelo-contrato.pdf`, fora do repositório), com variáveis do
sistema injetadas no meio do texto corrido. Mantém o motor **xhtml2pdf**
e o padrão A4 (`@page` já definido em `base_pdf.html`).

## Estado atual

- `templates/documentos/contrato_pdf.html` estende `templates/documentos/base_pdf.html`
  e renderiza um resumo em seções/cards (Imóvel, Locatário, Condições,
  Fiador, Observações, Assinaturas). É o layout entregue na Rodada 4
  (`planner-docs/redesign-pdfs-documentos-gerados/`) e ajustado na
  correção visual (`planner-docs/fix-visual-pdfs-gerados/`).
- Geração de PDF só ocorre via `contrato_gerar_pdf` (`imoveis/views.py`),
  que chama `_gerar_pdf_contrato()` → `imoveis/pdf.py:gerar_e_anexar()`.
  O contexto atual é só `{'contrato': contrato}`.
- Hoje o "locador" exibido no PDF é `contrato.imovel.proprietario` (dono
  cadastrado do imóvel). **Isso muda**: o locador jurídico passa a ser
  sempre a Shelter (dados fixos), independente do proprietário cadastrado
  do imóvel — o proprietário continua existindo normalmente no cadastro,
  só deixa de ser "quem assina como locador" no contrato gerado.
- `Contrato` (`imoveis/models.py`) não tem campos de finalidade
  (residencial/comercial) nem de local/data de assinatura — só
  `LaudoVistoria` tem `local_assinatura`/`data_assinatura` hoje.
- `Fiador` (`imoveis/models.py`) só tem `nome`, `qualificacao` (texto
  livre), `rg_cpf` (campo único validado por `validate_rg_cpf`),
  `certidao_onus` e `garantia` — não há RG/CPF discretos, endereço nem
  dados de cônjuge.
- Não há biblioteca de "número por extenso" no projeto (`num2words` não
  está em `requirements.txt` nem instalado no `venv`).
- **Investigação já feita (não repetir):** validado neste planejamento
  que o filtro `date` nativo do Django, com `LANGUAGE_CODE = 'pt-br'` já
  configurado em `core/settings.py` (sem `LocaleMiddleware`, sem
  `translation.activate()` explícito), já renderiza datas por extenso
  com mês maiúsculo exatamente no formato pedido.
  **Não é necessário nenhum código novo para data por extenso** — só
  `num2words` é necessário para valor monetário, quantidade de meses e
  ordinal do dia de vencimento (módulo 01).
- Última migration: `0010_documentogerado_retroativo.py`. A migration
  deste plano será `0011`.
- Suíte de testes: 72 testes em `imoveis/tests.py`, incluindo
  `ContratoPdfTests` (asserts específicos do layout atual, que serão
  totalmente reescritos no módulo 07).
- Exemplo validado: `{{ contrato.data_inicio|date:"j \d\e F \d\e Y" }}` produz `"1 de Junho de 2026"`.

## Resumo dos módulos

| Módulo | Responsabilidade |
|---|---|
| `01-utilitarios-extenso-num2words.md` | Dependência `num2words`; módulo `imoveis/extenso.py` com valor por extenso, quantidade de meses por extenso e dia de vencimento ordinal; filtros de template correspondentes |
| `02-constantes-locador-shelter.md` | Constantes fixas do locador (Shelter) em `core/settings.py`, disponibilizadas ao contexto do PDF |
| `03-contrato-model-form-finalidade-assinatura.md` | Campos novos em `Contrato`: `finalidade` (residencial/comercial), `local_assinatura`, `data_assinatura` — migration, form, templates de tela (form/detail) |
| `04-fiador-model-form-qualificacao-completa.md` | Campos novos em `Fiador`: RG/CPF discretos, endereço completo, dados do cônjuge — migration, form, templates de tela (form/detail) |
| `05-reescrita-contrato-pdf-clausulas.md` | Reescrita total de `templates/documentos/contrato_pdf.html`: preâmbulo + 21 cláusulas (I–XXI), variáveis injetadas, CSS de paginação A4 |
| `06-view-context-gerar-pdf.md` | Ajustar `_gerar_pdf_contrato`/`contrato_gerar_pdf` (`imoveis/views.py`) para passar `locador` e `prazo_meses` ao contexto do template |
| `07-atualizacao-testes.md` | Reescrever `ContratoPdfTests` e acrescentar testes de `imoveis/extenso.py`, `Fiador` e `Contrato` (campos novos) |
| `08-checklist-validacao-visual-manual.md` | Checklist de geração e inspeção visual do PDF final frente ao `modelo-contrato.pdf`, incluindo paginação A4 e retrocompatibilidade dos PDFs já gerados no GED |

## Ordem de implementação

1. `01-utilitarios-extenso-num2words.md` e `02-constantes-locador-shelter.md`
   — independentes entre si, podem ser feitos em paralelo.
2. `03-contrato-model-form-finalidade-assinatura.md` e
   `04-fiador-model-form-qualificacao-completa.md` — independentes entre
   si; gerar a migration `0011` uma única vez, após os dois módulos
   terem seus campos de model prontos (mesmo padrão da migration `0008`,
   que já combinou alterações de `Contrato` e `Fiador` num único arquivo).
3. `05-reescrita-contrato-pdf-clausulas.md` — depende de 01, 02, 03 e 04
   (usa os filtros de extenso, as constantes do locador e todos os
   campos novos de `Contrato`/`Fiador`).
4. `06-view-context-gerar-pdf.md` — depende de 01 (para `prazo_meses`) e
   02 (para `locador`); pode ser feito em paralelo ao módulo 05, mas a
   validação final do PDF só faz sentido com os dois prontos.
5. `07-atualizacao-testes.md` — depende de 01, 02, 03, 04, 05, 06.
6. `08-checklist-validacao-visual-manual.md` — depende de 05, 06 e 07
   (só faz sentido com testes automatizados verdes).

## Dependências entre módulos

- `05` depende de `01`, `02`, `03`, `04`.
- `06` depende de `01`, `02`.
- `07` depende de `01`, `02`, `03`, `04`, `05`, `06`.
- `08` depende de `05`, `06`, `07`.
- `03` e `04` são independentes entre si em termos de código, mas
  compartilham a geração da migration `0011` — coordenar para não gerar
  duas migrations concorrentes.

## Observações gerais

- Ambiguidade resolvida — "estado civil/qualificação" do Fiador: a
  decisão do usuário lista "estado civil/qualificação" entre os campos
  novos do Fiador. Este plano não cria um campo `estado_civil` novo —
  o campo `Fiador.qualificacao` (já existente, texto livre) já cobre
  esse dado (mesmo padrão de `Inquilino.qualificacao`, cujo `help_text`
  é "Estado civil, profissão, nacionalidade"). O módulo 04 apenas ajusta
  o `help_text` de `Fiador.qualificacao` para deixar isso explícito. Caso
  o cliente queira um campo estruturado separado, é uma decisão de
  produto a ser levantada antes da implementação do módulo 04.
- Texto jurídico das cláusulas não é reproduzido neste plano. O módulo
  05 apenas estrutura onde cada variável entra; a transcrição literal do
  preâmbulo e das 21 cláusulas deve ser feita a partir do
  `modelo-contrato.pdf` fornecido pelo cliente (fora do repositório —
  confirmar que o Engineer terá acesso a esse arquivo antes de iniciar o
  módulo 05).
- Locador deixa de ser `imovel.proprietario` no PDF. O `Proprietario`
  cadastrado do imóvel continua existindo e sendo usado normalmente no
  resto do sistema — a mudança é só na exibição do contrato gerado, que
  passa a sempre mostrar a Shelter como locador jurídico (módulo 02).
- Retrocompatibilidade do GED versionado: PDFs de contrato já gerados
  (`DocumentoGerado` existentes, tipo `contrato`) são imutáveis e não são
  regerados nem migrados — continuam no layout antigo (resumo em cards)
  para sempre. Só uma nova chamada a "Regerar PDF" produz uma versão
  nova no layout jurídico (módulo 08).
- `num2words` não instalado ainda — módulo 01 adiciona a
  `requirements.txt`; rodar `venv/Scripts/pip install -r requirements.txt`
  antes de escrever `imoveis/extenso.py`.
- Risco transversal de paginação A4: cláusulas longas não devem usar
  `page-break-inside: avoid` no corpo inteiro (pode gerar página em
  branco se a cláusula for maior que o espaço restante) — só o título
  da cláusula deve ficar colado ao início do texto (módulo 05, validado
  no módulo 08).
- `CLAUDE.md` (raiz do projeto) não é atualizado pelo Planner — após a
  implementação, a tabela "Modelos principais" (`Contrato`, `Fiador`), a
  seção "Convenções obrigatórias" e "ESTADO ATUAL" devem ser atualizadas
  manualmente com uma nova entrada de rodada — fora do escopo deste plano.
