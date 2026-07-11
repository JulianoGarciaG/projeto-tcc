# Histórico de Entregas
> Sistema Integrado de Gestão Imobiliária (GED e BI) — "Shelter"

Registro cronológico do **"porquê"** de cada rodada de implementação — não repete o "o quê" (isso é a referência viva em `docs/01_visao_geral.md`, `docs/02_modelagem_dados.md`, `docs/03_regras_de_negocio.md`, `docs/04_design_ui_ux.md`). Cada entrada mapeia para o diretório correspondente em `planner-docs/` (plano completo, decisões e módulos) e, quando aplicável, para o plano antigo consolidado aqui.

---

## Rodada 1 — Geração automática de documentos PDF

Plano original: (consolidado aqui, antes em `docs/PLANO_GERACAO_DOCUMENTOS.md`).

O sistema só armazenava documentos via upload manual — nenhuma geração de PDF pelo servidor. Esta rodada introduziu:

- Biblioteca `xhtml2pdf` para renderizar templates HTML/CSS como PDF.
- Novos models: `Recibo`, `ComodoTemplate`, `ItemVistoriaTemplate`, `ItemVistoria`, `TestemunhaLaudo`.
- `LaudoVistoria.contrato` passa a existir (opcional nesta rodada); `local_assinatura`/`data_assinatura`/`documento_gerado` novos.
- `Contrato.documento_gerado` novo (PDF gerado, sem sobrescrever upload manual).
- Catálogo de vistoria semeado (5 cômodos, 32 itens) — migração `0004_seed_vistoria_catalog`.
- CRUD completo de Recibo.
- **Decisão desta rodada (revertida na Rodada 2):** PDF era gerado **automaticamente ao salvar** o formulário (create/edit), com download imediato na resposta do POST.

## Rodada 2 — Ajustes pós-uso (25 itens de backlog)

Plano original: (consolidado aqui, antes em `docs/PLANO_AJUSTES_RODADA2.md`).

Após uso real do sistema da Rodada 1, backlog de 25 ajustes: bugs de UI/UX, mudança de comportamento na geração de PDF, simplificação de cadastros, máscaras/validações consistentes. Principais mudanças:

- **PDF deixa de ser automático:** create/edit voltam ao padrão PRG (redirect + toast); só as views `*_gerar_pdf` (botão "Regerar PDF") geram/baixam PDF — convenção mantida até hoje.
- **Tratamento de `ProtectedError`** em `contrato_delete` (generalizado às demais entidades só na rodada `avisos-exclusao-dependencias`, ver abaixo).
- **IMask + Flatpickr via CDN** — máscaras de telefone/moeda e datepicker dd/mm/yyyy, com init centralizada em `static/js/masks.js`.
- **Validação de CPF/CNPJ/RG** — `imoveis/validators.py` criado/expandido; aplicado retroativamente a `Inquilino.cpf/cnpj`.
- **Simplificações de cadastro:** removidos `Imovel.valor_aluguel` (agora derivado do contrato ativo), `Proprietario.endereco`, `Recibo.proveniente_sitio`, `Contrato.arquivo` (upload manual — mantido só `documento_gerado`), módulo `Entrada`/`Saida` do imóvel (substituído por `Lancamento` como único model financeiro), tipo `periodica` de `LaudoVistoria` (reclassificado para `entrada`).
- **Novos campos:** `Imovel.numero`/`complemento`, `Inquilino.faixa_renda` (substitui `renda_mensal` livre, em faixas de R$) e `Inquilino.observacoes`, `Recibo.periodo_inicio`/`periodo_fim` (substitui `periodo_referente`), `Recibo.imovel`/`contrato` tornam-se obrigatórios (`PROTECT`).
- **Checklist do laudo:** corrigido bug de renderização (`extra=len(catalogo)` em vez de `extra=0`) — armadilha registrada em `CLAUDE.md`.
- **Select dependente:** `LaudoVistoriaForm.contrato` passa a depender do imóvel escolhido (endpoint `contratos_por_imovel_json`); `LaudoVistoria.contrato` passa a **obrigatório** (`PROTECT`).
- **UI geral:** colapso de sidebar desktop introduzido nesta rodada (posteriormente **removido** — ver `remover-colapso-sidebar-e-ajustar-logo` abaixo) e toasts padronizados.

## Redesign UI "Shelter" (`planner-docs/redesign-ui-shelter/`)

Reskin completo da camada de template/CSS do app web (sidebar, topbar, login, dashboard, listagens, detalhes, formulários), introduzindo o sistema de **tokens** (CSS custom properties) com temas claro/escuro (`data-theme`), substituindo a paleta antiga (`custom.css`, `--color-*`). Fora de escopo: models/views/forms/signals e os PDFs gerados (`templates/documentos/`). Fonte de verdade visual: `planner-docs/redesign-ui-shelter/DESIGN_BRIEF.md`. Resultado documentado em `docs/04_design_ui_ux.md` (paleta/tokens em toda a extensão do documento).

## Rodada 4 — Redesign dos PDFs gerados + GED versionado (`planner-docs/redesign-pdfs-documentos-gerados/`)

Duas entregas em paralelo:

1. **Redesign visual dos 3 PDFs** (Contrato, Laudo, Recibo) para replicar 1:1 os mockups em `docs/pdf-models/*.html`, mantendo o motor xhtml2pdf.
2. **GED versionado (`DocumentoGerado`):** cada geração de PDF passa a criar um registro **imutável**, com `numero_versao` sequencial por origem, `sha256` e autor (`gerado_por`). Os campos legados (`Contrato.documento_gerado`, `LaudoVistoria.documento_gerado`, `Recibo.arquivo`) passam a ser espelhos automáticos da última versão. Introduzida também a config `STORAGES` plugável (`STORAGE_BACKEND=filesystem`/`s3`, S3 preparado mas não ativado).

Detalhado, à época, em `docs/05_ged_documentos_versionados.md` (documento descontinuado — ver entrada "Reversão do GED versionado" abaixo).

## Fix visual dos PDFs gerados (`planner-docs/fix-visual-pdfs-gerados/`)

Correção de divergências visuais entre os PDFs gerados e os mockups de referência, causadas por limitações reais do motor xhtml2pdf 0.2.17 (não por CSS divergente): `text-transform` é silenciosamente ignorado (textos estáticos passam a ser escritos literalmente em CAIXA ALTA, valores dinâmicos usam `|upper`); `margin: auto` não é suportado (centralização via `<table align="center">`); borda/padding de cartão em `<div>` com múltiplos filhos block-level produzia grade indesejada (movido para `<td>`). Armadilhas registradas em `CLAUDE.md` e `docs/04_design_ui_ux.md` §17.

## Remoção do colapso de sidebar (`planner-docs/remover-colapso-sidebar-e-ajustar-logo/`)

Reverte a feature de colapso de sidebar desktop introduzida na Rodada 2 (nunca totalmente adotada) — a sidebar volta a ser **sempre expandida** no desktop (só show/hide mobile permanece). Ajuste adicional no dimensionamento da logo dentro da sidebar. Documentado em `docs/04_design_ui_ux.md` §5.

## Melhorias de validação e visualização de documentos (`planner-docs/melhorias-validacao-visualizacao-documentos/`)

Cinco melhorias pontuais agrupadas por terem sido pedidas na mesma rodada:

1. Validador `validate_rg_cpf` para `Fiador.rg_cpf` (fechando a última lacuna de validação de documento).
2. Validador `validate_telefone` para `Proprietario`/`Inquilino.telefone` (antes só mascarado no front).
3. `MinValueValidator`/`MaxValueValidator` em `Contrato.dia_vencimento` (antes só restrito via atributos HTML, bypassável por POST direto).
4. Filtro de período do Dashboard migrado para Flatpickr dd/mm/aaaa via `DashboardFiltroForm` (único datepicker do sistema fora do padrão até então).
5. Preview de `Imovel.planta_projeto` na tela de detalhe (antes só visível editando).
6. Aumento do espaço de assinatura no PDF do laudo (`.assinatura-laudo`).
7. Documentos GED do contrato (`comprovante_renda`/`contrato_social`/`recibo_chaves`/`comprovante_anual`) migrados do formulário de criação para upload na tela de detalhe (`contrato_anexar_documento`) — mesmo padrão já usado por `laudo_anexar_arquivo`.

Documentado em `docs/03_regras_de_negocio.md` §5, §9, §12 e `CLAUDE.md` (gotcha da tabela de modelos).

## Fotos por item do checklist de vistoria (`planner-docs/fotos-item-vistoria/`)

Permite anexar 0..N fotos a cada `ItemVistoria` (novo model `FotoItemVistoria`), enviadas no mesmo formset de itens do laudo. Fotos visíveis **só no detalhe** do laudo — nunca no PDF nem na central GED. Anexar foto conta como mudança do form, então uma linha nova com foto mas sem `estado` passa a exigir `estado` (extensão da regra "só o item vistoriado é salvo"). Documentado em `docs/02_modelagem_dados.md` (§2.10a) e `docs/03_regras_de_negocio.md` §6.

## Avisos de exclusão de dependências (`planner-docs/avisos-exclusao-dependencias/`)

Duas frentes:

1. **Bloqueios `PROTECT` sem tratamento amigável:** generaliza para `imovel_delete`, `proprietario_delete` e `inquilino_delete` o mesmo tratamento de `ProtectedError` que só `contrato_delete` tinha (Rodada 2) — mensagem orientando a excluir os vínculos primeiro, em vez de erro 500.
2. **Cascatas `CASCADE` silenciosas:** property `dependentes_cascata` (em `Imovel`, `Contrato`, `LaudoVistoria`, `Recibo`) calcula a contagem de dependentes que seriam apagados junto; o modal de confirmação de exclusão passa a exibir esse aviso, sem bloquear a exclusão.

Documentado em `docs/03_regras_de_negocio.md` §7.

## Histórico de notificações por usuário (`planner-docs/historico-notificacoes-usuario/`)

Persiste, por usuário, um histórico das mensagens que o sistema já emite via `django.contrib.messages` (sem alterar os 36+ pontos de chamada existentes). Novo model `NotificacaoUsuario` (distinto do model de negócio `Notificacao`, avisos de órgãos públicos). Captura centralizada via storage customizado (`MESSAGE_STORAGE = 'imoveis.message_storage.PersistentFallbackStorage'`); leitura via context processor (`ultimas_notificacoes_usuario`) injetada em todo template. Sino da topbar (antes decorativo) passa a abrir dropdown com as últimas 8 notificações. Sem estado de lida/não lida, sem paginação. Documentado em `docs/02_modelagem_dados.md` (§2.17) e `docs/03_regras_de_negocio.md` §15.

## Camada de identidade e nomenclatura de entidades (`planner-docs/identidade-nomenclatura-entidades/`)

Cria `imoveis/identidade.py` (`IdentificavelMixin`) para resolver dois sintomas: (1) dropdowns/listas mostravam `Contrato #17` sem contexto; (2) PDFs baixavam como `contrato_3.pdf`, indistinguíveis entre si. Solução **aditiva** (sem migração):

- `codigo` — `{PREFIXO}-{pk:04d}` (`IMV`/`CTR`/`LAU`/`REC`), derivado em runtime.
- `rotulo_curto`/`rotulo_longo` — rótulos legíveis para selects e cabeçalhos de detalhe.
- `nome_arquivo(instance, versao=None)` — nome determinístico de PDF (via `slugify`), usado tanto na versão do GED quanto no download.

`Imovel`, `Contrato`, `LaudoVistoria` e `Recibo` herdam o mixin; `__str__` de cada model permanece inalterado. Documentado em `docs/02_modelagem_dados.md` (§1, "Camada de identidade").

## Card de recibos vinculados no detalhe do contrato (`planner-docs/card-recibos-vinculados-contrato/`)

Adiciona ao `contrato_detail` um card listando os `Recibo` vinculados via `Recibo.contrato`, com botão "Novo Recibo" que pré-seleciona `imovel`/`contrato` (rota dedicada `recibo_create_from_contrato`, mesmo padrão de pré-preenchimento já usado por `notificacao_create`). Documentado em `docs/03_regras_de_negocio.md` §5a.

## Split e merge do dashboard financeiro

Duas mudanças em sequência no dashboard único original (ocupação de imóveis + indicadores financeiros na mesma tela):

1. **Split:** o dashboard foi separado em duas telas — **Dashboard Imobiliário** (assume a rota raiz `/`, view `dashboard_imobiliario`, KPIs/donuts de ocupação e vacância) e um **Dashboard Financeiro** com rota própria (`/financeiro/dashboard/`).
2. **Merge (commit `3c0557d`, "feat(financeiro): merge dashboard into lancamentos page"):** a rota `/financeiro/dashboard/` foi removida; os KPIs, gráficos e o ranking de rentabilidade passaram a ser renderizados diretamente na página de listagem de Lançamentos (`/financeiro/`), via `_dashboard_financeiro_context(request)` (`imoveis/views.py`), chamada dentro de `lancamento_list`. Não existe mais uma tela de dashboard financeiro separada.

Nesse mesmo período, o gráfico de evolução mensal (ganhos vs. despesas) passou a ser *period-aware*: sem filtro de data, mostra os últimos 6 meses fixos; com filtro de data início/fim, mostra todos os meses do intervalo informado.

Documentado em `docs/01_visao_geral.md` §7/§8.3, `docs/03_regras_de_negocio.md` §9 e `docs/04_design_ui_ux.md` §13.

## Contrato jurídico completo (`planner-docs/contrato-juridico-completo/`)

Reescrita total do PDF de Contrato: de um resumo em cards para um **instrumento particular de locação juridicamente completo** — preâmbulo + 21 cláusulas fixas (I a XXI) transcritas de um modelo jurídico fornecido pelo cliente, com variáveis do sistema injetadas no texto corrido. Principais mudanças:

- **Locador fixo (Shelter):** o locador do contrato deixa de ser `imovel.proprietario` — passa a ser sempre a Shelter, com dados fixos em `settings.SHELTER_LOCADOR`. O `Proprietario` cadastrado continua existindo normalmente no resto do sistema.
- **Campos novos em `Contrato`:** `finalidade` (residencial/comercial), `local_assinatura`, `data_assinatura`.
- **Campos novos em `Fiador`:** `rg`, `cpf`, `endereco`, `conjuge_nome`, `conjuge_rg`, `conjuge_cpf` (qualificação jurídica completa; `rg_cpf` legado mantido).
- **Número por extenso:** novo módulo `imoveis/extenso.py` (dependência `num2words`) — valor monetário, quantidade de meses e ordinal do dia de vencimento por extenso. Datas por extenso **não** usam `num2words` (o filtro nativo `date` do Django com `LANGUAGE_CODE='pt-br'` já resolve).
- **Retrocompatibilidade:** PDFs de contrato já gerados antes desta mudança permanecem no layout antigo (GED versionado é imutável); só uma nova geração usa o layout jurídico novo.

Documentado em `docs/02_modelagem_dados.md` (`Contrato`, `Fiador`) e `docs/03_regras_de_negocio.md` §16.

## Perfis de usuário Admin/Owner/Comum (`planner-docs/perfis-usuario-admin-owner-comum/`)

Substitui o modelo binário `is_staff`/autenticado por 3 perfis efetivos de acesso, via `Group` do Django:

- **Admin** (`is_superuser=True` + `is_staff=True`): irrestrito, incluindo `/admin/`.
- **Owner** (Group "Owner"): tudo, exceto `/admin/`.
- **Comum** (Group "Comum", ou nenhum Group/superuser): tudo, exceto Dashboard, Financeiro (CRUD de `Lancamento`) e `/admin/`.

Principais mudanças:

- Novo model `PermissaoTela` (`managed=False`, sem tabela própria) — existe só para ancorar as permissões customizadas `pode_acessar_dashboard`/`pode_acessar_financeiro`, sem acoplar a um model de negócio (migração `0014_permissaotela`).
- Migração de dados `0015_cria_grupos_e_reclassifica_usuarios` cria os Groups Owner/Comum e reclassifica usuários existentes (`is_staff` → `is_superuser`; demais → Comum).
- Views de Dashboard e Financeiro protegidas por `permission_required(..., raise_exception=True)` — acesso direto por URL sem permissão retorna **403** (`templates/403.html`), nunca stack trace.
- Sidebar (`templates/base.html`) oculta os itens Dashboard/Financeiro por perfil — complementar à proteção de view, nunca a única camada.
- Usuário pertencente a Owner **e** Comum simultaneamente tem acesso de Owner (permissões efetivas são a união dos Groups; Comum não revoga nada).
- Não há tela de gestão de perfis no sistema — atribuição de Group é feita só via `/admin/`.

Documentado em `docs/01_visao_geral.md` §4 e `docs/03_regras_de_negocio.md` §10.

## Lançamento indexado por imóvel com ciclo ganho/despesa

Substitui o `Lancamento` vinculado só a `Contrato` por um lançamento **indexado por `Imovel`** (obrigatório, `PROTECT`), tratando cada imóvel como unidade financeira independente do contrato vigente. Principais mudanças no model `Lancamento` (migração `0016_lancamento_ganho_despesa`):

- Campo novo `natureza` (`ganho`/`despesa`), obrigatório.
- `contrato` passa de obrigatório/`CASCADE` para **opcional**/`SET_NULL` — só preenchido quando o lançamento se origina de um contrato/recibo.
- Campo novo `recibo` (FK opcional, `CASCADE`) — presente só nos ganhos criados automaticamente.
- `status` (`pendente`/`efetivado`) passa a se aplicar **só a `natureza='ganho'`**; despesas ficam com `status=null` (`CheckConstraint`). Os antigos choices `pago`/`atrasado` saem — "atrasado" deixa de ser um status gravado.
- Property `vencido` (`natureza='ganho' and status='pendente' and data_vencimento < hoje`) calculada em runtime — substitui o status `atrasado` armazenado; a inadimplência do dashboard passa a ser calculada na query, não a partir de um campo desatualizável.
- Novo sinal (`recibo_salvo`, `imoveis/signals.py`): criar um `Recibo` cria automaticamente um ganho pendente no `Imovel` correspondente, sincronizando valor/vencimento enquanto o ganho está pendente e "congelando" quando ele é efetivado.
- Dashboard ganha uma tabela de rentabilidade por imóvel (ganhos efetivados menos despesas).

Documentado em `docs/02_modelagem_dados.md` (`Lancamento`, diagrama de relacionamentos) e `docs/03_regras_de_negocio.md` §9.

## Reversão do GED versionado

Reverte o versionamento imutável de PDFs introduzido na **Rodada 4** (`redesign-pdfs-documentos-gerados`). O sistema volta ao modelo "só a versão mais recente": `Contrato.documento_gerado`, `LaudoVistoria.documento_gerado` e `Recibo.arquivo` voltam a ser a **única** fonte de verdade dos PDFs gerados — cada nova geração sobrescreve o arquivo anterior (banco e storage físico), sem histórico.

- **Model removido:** `DocumentoGerado` (e `documento_gerado_upload_to`) saem de `imoveis/models.py`; `DocumentoGeradoAdmin` sai de `imoveis/admin.py`. `dependentes_cascata` de `Contrato`/`LaudoVistoria` deixa de referenciar `documentos_gerados`; `Recibo.dependentes_cascata` passa a retornar sempre `[]`.
- **`imoveis/pdf.py`:** `gerar_e_anexar(instance, template_name, context, field_name)` simplificado — sem parâmetro `usuario`, sem versão/hash/registro em GED. `save_pdf_to_field` passa a apagar o arquivo antigo do campo (`field.delete(save=False)`) antes de salvar o novo.
- **`imoveis/identidade.py`:** `nome_arquivo(instance, versao=None)` mantido como está — o parâmetro `versao` não é mais usado por `pdf.py`, mas a função continua aceitando-o.
- **`imoveis/views.py`:** a view `documentos()` (rota `/documentos/`, central GED) passa a listar o documento vigente direto dos campos legados (`Contrato.objects.exclude(documento_gerado='')...` etc.), não mais versões de `DocumentoGerado`.
- **Templates:** blocos "Versões do PDF gerado" removidos de `templates/ged/documentos.html`, `templates/contratos/contrato_detail.html`, `templates/laudos/laudo_detail.html`, `templates/recibos/recibo_detail.html`.
- **Migração `0017_remove_documentogerado`:** apaga fisicamente do storage os arquivos extras que só existiam por causa do versionamento (árvore `ged/...`), preservando os arquivos que os campos legados ainda referenciam, depois remove o model.
- **Fora de escopo:** a arquitetura de storage plugável (`STORAGES`/`STORAGE_BACKEND`, S3 preparado não ativado) não foi tocada — é ortogonal a essa mudança e continua usada pelos anexos manuais. Anexos manuais não-versionados (`comprovante_renda`, `contrato_social`, `recibo_chaves`, `comprovante_anual`, `laudo.arquivo` assinado) também não mudaram.

`docs/05_ged_documentos_versionados.md` foi descontinuado (conteúdo vigente sobre GED e storage plugável passou para `docs/03_regras_de_negocio.md` §8). A entrada da Rodada 4 acima **não foi reescrita** — registra o que foi entregue naquela época; esta entrada documenta a reversão.

## Documentos Pessoais do Contrato (anexo múltiplo)

Os contratos só tinham os quatro campos de documento fixos (`comprovante_renda`/`contrato_social`/`recibo_chaves`/`comprovante_anual`), cada um aceitando **um** arquivo. Faltava espaço para documentação pessoal diversa do inquilino/fiador — vários arquivos, formatos variados. Esta rodada introduz o primeiro padrão **multi-arquivo por linha** do sistema:

- **Model novo `DocumentoContrato`** (migração `0023_documentocontrato`): FK `CASCADE` para `Contrato` (`related_name='documentos_pessoais'`), uma linha por arquivo, com `nome_original` guardando o nome do upload como rótulo. Ver `docs/02_modelagem_dados.md` §2.5.1.
- **Upload múltiplo sem formset:** input único `type="file" multiple` no detalhe do contrato → `contrato_documento_pessoal_upload` itera `request.FILES.getlist('arquivos')` e cria uma linha por arquivo. Optou-se por iterar o `getlist` em vez de um `FileField` custom multi-arquivo em formset — evita a armadilha do `has_changed` (registrada na memória do projeto) e mantém o mesmo padrão "upload no detail" dos anexos fixos.
- **Remoção individual:** `contrato_documento_pessoal_delete` apaga só o arquivo físico + registro da linha alvo (`arquivo.delete(save=False)`), validando que o `doc_pk` pertence ao contrato da rota (404 caso contrário) — os demais anexos ficam intactos.
- **Sem GED:** decidido manter os documentos pessoais apenas no detalhe do contrato (fora da central `/documentos/`), fiel ao escopo pedido. Tolerância de formato idêntica aos demais anexos.
- Inline `DocumentoContratoInline` no admin do `Contrato`; testes em `ContratoDocumentoTests` (upload múltiplo, upload vazio, delete individual preservando o resto, 404 cross-contrato).

Documentado em `docs/02_modelagem_dados.md` (§2.5.1 e diagrama) e `docs/03_regras_de_negocio.md` §5.1.
