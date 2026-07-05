# Plano: Validacao de campos, datepickers dd/mm/yyyy, visualizacao de planta, espaco de assinatura no laudo e migracao dos documentos GED do contrato

## Objetivo
Implementar cinco melhorias pontuais e independentes entre si (agrupadas em um unico plano por terem sido solicitadas na mesma rodada):

1. Fechar lacunas de validacao de documentos/contato ainda sem validator (CPF/CNPJ/RG/telefone/faixas numericas).
2. Garantir que todo datepicker do sistema use o formato dd/mm/aaaa (Flatpickr).
3. Exibir a Planta/Projeto do imovel diretamente na tela de visualizacao (hoje so e visivel editando o registro).
4. Aumentar o espaco acima da linha de assinatura no PDF do Laudo de Vistoria, para assinatura manuscrita.
5. Mover os campos "Documentos (GED)" do formulario de criacao do Contrato para uma secao de upload na tela de visualizacao (mesmo padrao de "adicionar depois, na tela de detalhe" ja usado por Lancamentos e pelo anexo do Laudo).

## Estado atual (investigacao)

### 1. Validacao de inputs
- imoveis/validators.py ja expoe validate_cpf, validate_cnpj, validate_cpf_cnpj e validate_rg, todos reutilizados corretamente em Proprietario.cpf_cnpj, Inquilino.cpf/cnpj/rg, TestemunhaLaudo.cpf e Recibo.assinante_cpf (imoveis/models.py).
- Todos os campos EmailField (Proprietario.email, Inquilino.email) ja validam formato de e-mail nativamente (Django) e usam forms.EmailInput.
- Lacunas confirmadas (unicos campos "relevantes" sem validacao adequada no projeto inteiro):
  - Fiador.rg_cpf (imoveis/models.py:169) -- CharField sem nenhum validator, apesar de o rotulo ser "RG/CPF".
  - Proprietario.telefone e Inquilino.telefone -- so tem mascara de front-end (IMask, static/js/masks.js); nao ha validacao de formato no backend (bypassavel via POST direto).
  - Contrato.dia_vencimento (imoveis/models.py:141) -- PositiveSmallIntegerField sem limite superior; o form restringe 1-31 so via atributos HTML (min/max), que nao impedem POST direto com valor fora da faixa.
- Nao ha nenhum outro forms.Form/CharField avulso no projeto (login usa AuthenticationForm padrao do Django, fora de escopo) nem outros campos de documento sem validator.

### 2. Datepickers dd/mm/yyyy
- imoveis/forms.py define _date_widget() (Flatpickr, dateFormat igual a d/m/Y em static/js/masks.js:42) e todo DateField de todo ModelForm do app ja usa esse widget (ImovelForm, ContratoForm, LaudoVistoriaForm, LancamentoForm, NotificacaoForm, RenovacaoContratoForm, DistratoForm, ReciboForm) -- confirmado campo a campo em imoveis/forms.py.
- Unica excecao encontrada: o filtro de periodo do Dashboard (templates/dashboard.html linhas 33 e 37) usa input type=date nativo do navegador (fora de qualquer Django Form), que nao segue o padrao Flatpickr/dd-mm-aaaa e cujo valor e interpretado em imoveis/views.py linhas 73-86 como string ISO (yyyy-mm-dd) direto no filtro do ORM.

### 3. Planta/Projeto do imovel
- Imovel.planta_projeto (FileField, so para categoria=urbano) e editavel em imovel_form.html:104, mas imovel_detail.html nao exibe nem linka o arquivo -- hoje so se ve entrando em Editar.

### 4. Espaco de assinatura no laudo (PDF)
- templates/documentos/base_pdf.html linhas 76-78 ja tem uma classe .assinatura-laudo com margin-top de 80px, criada na Rodada 2 (item L5) especificamente para este fim, aplicada so em laudo_pdf.html (nao afeta contrato/recibo). O espaco nunca foi validado visualmente (checklist de validacao manual da Rodada 2 ficou pendente) -- a solicitacao atual e para aumentar ainda mais esse espaco.

### 5. Documentos GED do contrato
- Hoje comprovante_renda, contrato_social, recibo_chaves e comprovante_anual sao campos de ContratoForm (imoveis/forms.py linhas 118-139) preenchidos na tela de criacao/edicao (templates/contratos/contrato_form.html linhas 32-55), com toggle JS PF/PJ (linhas 99-116 do mesmo template).
- O padrao ja estabelecido no projeto para anexar arquivo depois de criado o registro, pela tela de detalhe, e o laudo_anexar_arquivo (imoveis/views.py linhas 566-577, testado em imoveis/tests.py linhas 363-374): um POST simples com request.FILES.get(arquivo), sem ModelForm dedicado, redirecionando de volta ao detail. Este plano replica esse padrao para os 4 campos de documento do Contrato.
- contrato_detail.html linhas 52-67 ja tem uma secao "Documentos" somente de leitura (links); ela sera estendida com os formularios de upload.
- A central GED (views.documentos, templates/ged/documentos.html) le os mesmos campos do model e nao precisa de nenhuma alteracao.

## Resumo dos modulos

| # | Modulo | Resumo |
|---|---|---|
| 01 | 01-validador-documento-fiador.md | Novo validator validate_rg_cpf (CPF com DV ou RG alfanumerico) aplicado a Fiador.rg_cpf |
| 02 | 02-validador-telefone.md | Novo validator validate_telefone aplicado a Proprietario.telefone e Inquilino.telefone |
| 03 | 03-validador-dia-vencimento.md | MinValueValidator(1) e MaxValueValidator(31) em Contrato.dia_vencimento |
| 04 | 04-dashboard-filtro-data-dd-mm-yyyy.md | Filtro de datas do Dashboard passa a usar Flatpickr dd/mm/aaaa via DashboardFiltroForm |
| 05 | 05-imovel-preview-planta-projeto.md | Exibicao da Planta/Projeto na tela de detalhe do imovel |
| 06 | 06-laudo-pdf-espaco-assinatura.md | Aumento do margin-top de .assinatura-laudo no PDF do laudo |
| 07 | 07-contrato-documentos-backend.md | Remove os 4 campos de documento do ContratoForm; cria view/URL contrato_anexar_documento (padrao laudo_anexar_arquivo) |
| 08 | 08-contrato-documentos-template.md | Remove a secao Documentos (GED) e o JS de toggle PF/PJ de contrato_form.html; adiciona os uploads em contrato_detail.html |

## Ordem de implementacao
Os modulos 01-06 sao totalmente independentes entre si e podem ser feitos em qualquer ordem (inclusive em paralelo por Engineers diferentes). Ordem sugerida, apenas para agrupar por area:

1. Modulo 01 -- validador Fiador
2. Modulo 02 -- validador telefone
3. Modulo 03 -- validador dia de vencimento
4. Modulo 04 -- datepicker do dashboard
5. Modulo 05 -- preview da planta
6. Modulo 06 -- espaco de assinatura do laudo
7. Modulo 07 -- backend dos documentos do contrato
8. Modulo 08 -- template dos documentos do contrato (depende do 07)

## Dependencias entre modulos
- Modulo 08 depende do Modulo 07 (usa a URL contrato_anexar_documento criada nele).
- Todos os demais modulos (01-06) nao dependem uns dos outros nem dos modulos 07/08.

## Observacoes gerais
- Migrations: os modulos 01, 02 e 03 alteram validators em campos existentes, o que exige "makemigrations imoveis" (Django inclui validators no estado deconstruido do field -- confirmado nas migrations 0005/0006 da Rodada 2). Os modulos 07/08 e os demais (04, 05, 06) nao exigem migration. Recomenda-se ao Engineer rodar makemigrations uma unica vez apos concluir os modulos 01-03, gerando uma migration consolidada (ex.: 0007), em vez de 3 migrations separadas.
- Nenhum modulo altera o signal de status do imovel (imoveis/signals.py) nem os modelos Recibo/Lancamento/LaudoVistoria alem do ja descrito.
- Nenhum modulo remove ou renomeia campos de model -- apenas adiciona validators (01-03) ou reorganiza onde/como um campo ja existente e preenchido na UI (07-08).
- A suite atual tem 48 testes em imoveis/tests.py, todos passando; cada modulo abaixo especifica os testes novos a adicionar, e rodar "python manage.py test imoveis" ao final e obrigatorio em todo modulo.
- docs/03_modelagem_dados.md ja esta desatualizado em relacao ao estado atual do projeto (cita Saida/Entrada, valor_aluguel, Contrato.arquivo e Inquilino.renda_mensal, todos removidos em rodadas anteriores). Os modulos abaixo apontam apenas os trechos pontualmente afetados por esta rodada; a reconciliacao geral do documento esta fora do escopo deste plano.
