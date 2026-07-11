# 03 — Regras de Negócio
> Sistema Integrado de Gestão Imobiliária (GED e BI)

---

## 1. Status do Imóvel (Automático via Signal)

O status do imóvel é **gerenciado automaticamente** pelo sistema, nunca manualmente pelo usuário.

**Lógica:**
- Se o imóvel possui **ao menos um contrato com `status = 'ativo'`** → `status = 'ocupado'`
- Se o imóvel **não possui contratos ativos** → `status = 'vago'`

**Gatilhos:**
- `post_save` no modelo `Contrato` → atualiza o imóvel vinculado
- `post_delete` no modelo `Contrato` → atualiza o imóvel vinculado

**Exceção:**
- O status `'manutencao'` não é gerenciado por signal — deve ser definido manualmente pelo usuário.

---

## 2. Distrato — Encerramento Automático do Contrato

Ao salvar um `Distrato`, o sistema **encerra automaticamente o contrato vinculado**.

**Lógica (método `save` do modelo `Distrato`):**
```
distrato.save() → contrato.status = 'encerrado' → contrato.save()
```

**Consequência:** após o distrato, o signal de status do imóvel é acionado e o imóvel passa para `'vago'` (se não houver outro contrato ativo).

---

## 3. Renovação e Distrato

| Entidade | Regra |
|---|---|
| `RenovacaoContrato` | **Múltiplas** renovações por contrato (ForeignKey), acumuladas como histórico. Registro permitido **somente enquanto o contrato está ativo**. Sem campo de valor — reajuste de valor é feature separada (`Contrato.valor_vigente`). |
| `Distrato` | Apenas **um** distrato por contrato (OneToOneField) |

**Comportamento na view:**
- Renovação: o botão "Renovar" fica sempre disponível para contrato **ativo**; a ação `renovacao_create` só cria o registro se `contrato.status == 'ativo'` (contrato não-ativo → aviso e redireciona para o detalhe, defesa contra acesso direto por URL). O detalhe do contrato exibe todas as renovações em formato de histórico.
- Se o contrato já possui distrato → exibe aviso e redireciona para o detalhe do contrato, sem criar novo.

---

## 4. Campos Condicionais por Categoria do Imóvel

Os campos do imóvel variam conforme a `categoria`:

| Categoria | Campos exclusivos |
|---|---|
| `urbano` | `cadastro_prefeitura`, `planta_projeto` |
| `rural` | `nirf`, `incra`, `car` |

**Comportamento na interface:**
- O formulário exibe/oculta os campos dinamicamente via JavaScript conforme a categoria selecionada.
- Campos da categoria não selecionada ficam ocultos e não devem ser preenchidos.

---

## 5. Campos Condicionais por Tipo de Contrato

Os documentos do contrato variam conforme o `tipo_contrato`:

| Tipo | Campo exclusivo |
|---|---|
| `PF` (Pessoa Física) | `comprovante_renda` |
| `PJ` (Pessoa Jurídica) | `contrato_social` |

**Comportamento na interface:**
- Esses campos (e `recibo_chaves`, `comprovante_anual`) **não fazem parte** do formulário de criação/edição de contrato (`ContratoForm`) — são anexados individualmente na tela de detalhe do contrato via `contrato_anexar_documento` (mesmo padrão do anexo de laudo assinado).

---

## 5.1. Documentos Pessoais do Contrato (anexo múltiplo)

Além dos quatro campos de documento fixos (1 arquivo cada), o contrato aceita anexos pessoais avulsos em quantidade livre (`DocumentoContrato`, ver [modelagem 2.5.1](02_modelagem_dados.md#251-documentocontrato)) — documentação diversa do inquilino/fiador, de formatos variados.

- **Anexar (upload múltiplo):** bloco "Documentos Pessoais" na seção Documentos do detalhe. Um único input `type="file" multiple` envia vários arquivos de uma vez para `contrato_documento_pessoal_upload`, que cria uma linha `DocumentoContrato` por arquivo (guardando o nome original como rótulo). Sem arquivo selecionado → mensagem de erro, nada é criado.
- **Listar:** cada arquivo aparece como um item da lista, com link "Ver arquivo" e botão "Remover".
- **Remover (individual):** `contrato_documento_pessoal_delete` apaga o arquivo físico (`arquivo.delete(save=False)`) e o registro daquela linha **apenas** — os demais anexos permanecem. O `doc_pk` é validado como pertencente ao contrato da rota (404 caso contrário).
- Tolerância de formato idêntica aos demais anexos (`accept="application/pdf,image/*"`, sem validação restritiva no backend). Não integra a central GED — vive só no detalhe do contrato.

---

## 5a. Recibos Vinculados ao Contrato (card no detalhe)

- O detalhe do contrato (`contrato_detail`) exibe um card "Recibos" com todos os `Recibo` vinculados via `Recibo.contrato` (`related_name='recibos'`), cada linha linkando para `recibo_detail`.
- O botão "Novo Recibo" do card usa a rota dedicada `contratos/<int:contrato_pk>/recibos/novo/` (view `recibo_create_from_contrato`), que pré-seleciona `imovel`/`contrato` no `ReciboForm` a partir do contrato de origem — mesmo padrão de pré-preenchimento já usado por `notificacao_create` (parâmetro de rota, não querystring). A view genérica `recibo_create` (sem contrato pré-selecionado) continua existindo para o botão "+ Novo" da listagem de recibos.
- Este card é distinto da central GED (documentos gerados/anexados do tipo recibo) — mostra os registros de negócio `Recibo`, não os PDFs gerados.

---

## 6. Laudo de Vistoria Vinculado ao Distrato

- O `Distrato` pode referenciar um `LaudoVistoria` do tipo `saida` como laudo de saída.
- O vínculo é **opcional** (`null=True`, `blank=True`).
- Na view de distrato, o queryset de laudos é filtrado para exibir **somente os laudos do imóvel vinculado ao contrato**.

### Fotos por item do checklist
- Cada linha do checklist (`ItemVistoria`) aceita 0..N fotos (`FotoItemVistoria`), enviadas no **mesmo** formset de itens do laudo (create/edit). As views passam `request.FILES` ao formset e gravam as fotos via `_salvar_fotos_itens()` **após** `item_formset.save()` (precisa do PK do item). As fotos aparecem **só no detalhe** do laudo — nunca no PDF nem na central GED.
- Anexar foto marca a linha como alterada: uma linha nova (create) com foto mas **sem `estado`** passa a exigir `estado` e falha a validação (extensão natural da regra "só o item vistoriado é salvo").

---

## 7. Proteção Contra Exclusão de Registros Vinculados

| Entidade protegida | Protege contra exclusão de | Tratamento |
|---|---|---|
| `Proprietario` | Possui imóveis (`PROTECT`) | `proprietario_delete` captura `ProtectedError` e exibe mensagem orientando a excluir os imóveis primeiro |
| `Imovel` | Possui contratos ou recibos (`PROTECT`) | `imovel_delete` captura `ProtectedError` e exibe mensagem orientando a excluir os vínculos primeiro |
| `Inquilino` | Possui contratos (`PROTECT`) | `inquilino_delete` captura `ProtectedError` e exibe mensagem orientando a excluir os contratos primeiro |
| `Contrato` | Possui laudos de vistoria ou recibos vinculados (`PROTECT`) | `contrato_delete` captura `ProtectedError` e exibe mensagem orientando a excluir os vínculos primeiro |

Além do bloqueio por `PROTECT`, os modelos `Imovel`, `Contrato`, `LaudoVistoria`
e `Recibo` têm relacionamentos `CASCADE` (fotos, notificações, fiadores,
lançamentos, renovação/distrato, itens de vistoria, testemunhas) que são
apagados junto quando o registro pai é excluído. A property
`dependentes_cascata` (em cada um desses models, `imoveis/models.py`) calcula
essa contagem, e o modal de confirmação de exclusão das respectivas listagens
exibe um aviso com a quantidade de cada tipo de dependente que também será
removido — sem bloquear a exclusão.

---

## 8. GED — Gestão Eletrônica de Documentos

- Todos os documentos do sistema são armazenados digitalmente, eliminando a dependência de pastas físicas.
- A central GED (`/documentos/`) agrega os documentos agrupados por tipo (view `documentos` em `imoveis/views.py`), lendo diretamente os campos legados dos models de negócio — não há versionamento: cada tipo de documento tem no máximo **um** arquivo vigente por origem.
  - **PDFs gerados pelo sistema:** `Contrato.documento_gerado`, `LaudoVistoria.documento_gerado`, `Recibo.arquivo` — listados a partir dos registros com o campo preenchido (`Contrato.objects.exclude(documento_gerado='')` etc.).
  - **Anexos manuais:** `LaudoVistoria.arquivo` (assinado), `Lancamento.comprovante`, `Contrato.recibo_chaves`, `Contrato.comprovante_anual`.
- Um documento só aparece na central GED se o campo de arquivo **não estiver vazio**.
- **Sem histórico de versões:** cada geração de PDF (botão "Regerar PDF") sobrescreve o arquivo anterior — tanto o registro no banco quanto o arquivo físico no storage (`imoveis/pdf.py:save_pdf_to_field` apaga o arquivo antigo antes de salvar o novo). Não há como consultar PDFs gerados anteriormente; para "corrigir" um documento, basta gerar de novo.
- **Storage plugável (`STORAGE_BACKEND`):** o armazenamento de arquivos usa a config `STORAGES` do Django 4.2+ (`core/settings.py`), controlada pela variável de ambiente `STORAGE_BACKEND`, seguindo o mesmo padrão já usado para `DB_ENGINE`: `filesystem` (default) → `FileSystemStorage`; `s3` → preparado, mas não ativado (setar sem as libs instaladas levanta `ImproperlyConfigured`). `boto3`/`django-storages` não foram adicionados ao projeto — apenas a arquitetura está pronta.

---

## 9. Dashboard Imobiliário e Indicadores Financeiros

Os indicadores do sistema estão divididos em **duas telas independentes** (o dashboard único original foi separado; o financeiro depois teve sua rota própria removida e mesclado na listagem de Lançamentos — ver `docs/historico_entregas.md`):

### 9.1 Dashboard Imobiliário (`/dashboard/`, view `dashboard_imobiliario`)

Filtros de Tipo e Status (`tipo`/`status`), aplicados sobre `Imovel.objects` e refletidos em todos os KPIs e donuts:

| Filtro | Campo filtrado |
|---|---|
| Tipo de imóvel | `tipo` |
| Status do imóvel | `status` |

Não há filtro de imóvel nem de período na barra superior — a janela usada pelo KPI de tempo médio de vacância e pela linha do tempo é fixa: últimos 90 dias a partir de hoje.

**Métricas calculadas:**
- Total de imóveis, ocupados, vagos e em manutenção (com base nos filtros de tipo/status)
- Taxa de vacância: `(vagos / total) * 100`
- Contratos ativos (global, sem filtro)
- Donut de distribuição por situação do imóvel (ocupado/vago/manutenção) e donut de distribuição por tipo de imóvel
- **Contratos que Precisam de Atenção:** contratos ativos com `precisa_atencao=True`; listados na tabela ao final da página. A elegibilidade depende **somente** do status `ativo` — nenhuma condição de período bloqueia o aviso, então um contrato ativo com fim de vigência **já vencido** aparece normalmente (a estadia pode seguir por renovação sem novo contrato). A janela de disparo vai de **30 dias antes a 7 dias depois** (inclusive) de uma data de referência, para duas âncoras: **fim de vigência** (`data_fim`, motivo "Fim de vigência") e **aniversário anual** de `data_inicio` (motivo "Aniversário de reajuste"). Contratos com renovação registrada continuam usando `data_inicio`/`data_fim` do contrato **original** como referência — a renovação não desloca aniversário nem fim de vigência. Ver [§14 — Indicador de Atenção e Reajuste de Valor](#14-indicador-de-atenção-e-reajuste-de-valor) para a regra completa, incluindo a supressão do aviso de aniversário após o reajuste.
- **Tempo Médio de Vacância:** média em dias dos períodos de vacância concluídos (`HistoricoStatusImovel` com `status='vago'` e `data_fim` preenchida) iniciados nos últimos 90 dias, respeitando os filtros de tipo/status. Sem períodos concluídos no intervalo, o KPI exibe "—".
- **Linha do tempo de status:** card sempre visível, com **seletor de imóvel próprio** (`timeline_imovel_id`, independente dos filtros de Tipo/Status — não afeta KPIs/donuts). Sem seleção explícita, mostra o primeiro imóvel cadastrado (ordenado por endereço). O `<select>` exibe `Imovel.endereco_filtro` (endereço + número + complemento) para desambiguar imóveis de endereço parecido. Lista o histórico de status (`HistoricoStatusImovel`) do imóvel escolhido dentro da janela de 90 dias, com badges coloridos por status e duração em dias.

Essas três métricas usam dados reais desde o lançamento da feature de histórico de status — não são mais placeholder.

### 9.1.1 Histórico de Status no detalhe do imóvel (`imovel_detail`)

Abaixo da lista de Laudos de Vistoria, a tela de detalhe do imóvel (`imoveis/views.py:imovel_detail`) exibe o histórico completo de status daquele imóvel — mesmo model (`HistoricoStatusImovel`) e mesma UI de badges/duração da linha do tempo do dashboard, mas com duas diferenças deliberadas:

- **Sem janela de 90 dias**: lista todo o histórico do imóvel (`historico_status.order_by('data_inicio')`), sem filtro por `data_inicio`/`data_fim`.
- **Sem seletor de imóvel**: o imóvel já é fixado pelo `pk` da URL; não há `timeline_imovel_id`.

**KPIs agregados** (dias acumulados por status, ao longo de toda a história do imóvel): soma de `HistoricoStatusImovel.duracao_dias` de cada período, agrupada por `status` (`vago`/`ocupado`/`manutencao`). Como `duracao_dias` usa `timezone.now()` como fim quando `data_fim` é nulo, o período em aberto (status atual) **conta** no total até o momento da consulta — mesmo critério que o dashboard já usa implicitamente ao exibir "atual" com duração calculada até hoje.

Essa timeline e seus KPIs são independentes da timeline de 90 dias do dashboard: não compartilham contexto, não se afetam mutuamente.

### 9.2 Indicadores Financeiros (embutidos em `/financeiro/`, função `_dashboard_financeiro_context` chamada por `lancamento_list`)

Não existe mais uma tela de dashboard financeiro separada — os KPIs, gráficos e ranking abaixo são renderizados na própria página de listagem de Lançamentos, acima da tabela e dos filtros de listagem.

Filtros combinados, aplicados sobre `Lancamento.objects`:

| Filtro | Campo filtrado |
|---|---|
| Imóvel | `imovel_id` (dropdown exibe `Imovel.endereco_filtro` — endereço + número + complemento) |
| Data início | `data_caixa__gte` |
| Data fim | `data_caixa__lte` |

**Regime de caixa (não mais competência):** `data_caixa` é uma anotação `Coalesce(data_pagamento, data_vencimento)` — reflete quando o dinheiro efetivamente entrou/saiu, com fallback para `data_vencimento` enquanto o lançamento não foi efetivado (`data_pagamento` nulo). Na prática: lançamento `efetivado` → indexado por `data_pagamento`; lançamento `pendente` (e despesa, que nunca preenche `data_pagamento` hoje) → indexado por `data_vencimento`. Essa mesma `data_caixa` alimenta o filtro de período, os KPIs do período e o gráfico de evolução mensal — os três usam o queryset `lancamentos_qs` já anotado/filtrado. O filtro de período (data início/fim) é validado e limpo por `DashboardFiltroForm` (`imoveis/forms.py`), um `forms.Form` com os campos opcionais `data_inicio`/`data_fim`, ambos com widget Flatpickr (formato dd/mm/aaaa).

**Fora da regra híbrida (permanecem em `data_vencimento`):** a property `Lancamento.vencido` e o % de inadimplência (que se baseia na mesma regra) — ambos existem para decidir se um pendente está atrasado, não para indexar por período, então não mudam com a migração para regime de caixa.

**Métricas calculadas:**
- Ganhos do período (`natureza='ganho'`, `status='efetivado'`), despesas do período e saldo (ganhos − despesas)
- Total pendente (`natureza='ganho'`, `status='pendente'`)
- Ticket médio de aluguel: média de `valor` dos lançamentos `natureza='ganho'`, `tipo='aluguel'`
- % de inadimplência: **calculado em runtime**, nunca gravado — proporção de ganhos com `status='pendente'` e `data_vencimento < hoje` sobre o total de ganhos (mesma regra da property `Lancamento.vencido`; não usa `data_caixa`)
- **Gráfico de evolução mensal (ganhos vs. despesas) é period-aware:**
  - Sem filtro de data início/fim: últimos 6 meses fixos a partir do mês atual.
  - Com filtro de data início e/ou fim: todos os meses do intervalo informado (mínimo 1 mês), usando a data informada (ou a outra ponta, se só uma for preenchida) como limite.
  - O título do card ("· últimos 6 meses" ou "· período filtrado") reflete qual dos dois modos está ativo.
  - Os meses são calculados por `data_caixa__year`/`data_caixa__month`, não `data_vencimento`.
- Ranking de rentabilidade por imóvel: para cada imóvel com lançamentos, soma de ganhos `efetivado` menos soma de despesas, ordenado do maior para o menor saldo
- Donut de composição de despesas por categoria (`Lancamento.tipo`, apenas naturezas `despesa`)
- Tabela dos 5 lançamentos pendentes mais antigos (`natureza='ganho'`, `status='pendente'`), ordenada e com dias de atraso calculados por `data_vencimento` (para pendentes, `data_caixa` coincide com `data_vencimento`, já que `data_pagamento` ainda é nulo)

**Lançamento (`imoveis/models.py`) — ganho/despesa por imóvel:**
- `Lancamento.imovel` é obrigatório; `Lancamento.contrato` é opcional (preenchido só quando o lançamento se origina de um contrato/recibo).
- `natureza` distingue `ganho` de `despesa`. O ciclo `pendente` → `efetivado` (campo `status`) só existe em ganhos — uma `CheckConstraint` garante que despesa nunca tem `status` preenchido.
- O `tipo` é **restrito pela `natureza`** (`Lancamento.TIPOS_POR_NATUREZA`): `ganho` → `aluguel`/`arrendamento`/`venda`/`outros`; `despesa` → `condominio`/`iptu`/`manutencao`/`multa`/`outros`. Ao contrário do gate de `status`, essa regra vive **só na UI/form** — `LancamentoForm.clean` rejeita combinações inválidas e o dropdown de tipo é filtrado por JS ao trocar a natureza; **não** há `CheckConstraint` de banco (decisão explícita). Registros legados que não respeitavam a regra foram apagados na introdução dela, sem rota de migração.
- Criar um `Recibo` dispara um `post_save` (`imoveis/signals.py:recibo_salvo`) que cria automaticamente um `Lancamento` ganho `pendente` apontando pro `imovel` do recibo (preservando `contrato` e a referência `recibo` de origem). Editar o recibo depois sincroniza valor/vencimento do ganho **enquanto ele ainda estiver pendente**; um ganho já `efetivado` não é mais tocado pelo signal.
- A view `lancamento_efetivar` marca um ganho `pendente` como `efetivado` (preenchendo `data_pagamento` se vazia) — é a única forma de fechar o ciclo, não existe efetivação automática por data.

---

## 10. Autenticação e Controle de Acesso

- Todas as views exigem autenticação (`@login_required`).
- Usuários não autenticados são redirecionados para `/login/`.
- O painel administrativo Django (`/admin/`) é restrito a usuários com `is_staff = True`.
- Após login bem-sucedido, o usuário é redirecionado para `/` (dashboard).
- Após logout, o usuário é redirecionado para `/login/`.

**Perfis de usuário** (Group do Django, atribuídos somente via `/admin/` — não há tela de gestão de perfis no sistema):

| Perfil | Como é identificado | Acesso |
|---|---|---|
| Admin | `is_superuser=True` + `is_staff=True` | Irrestrito, incluindo `/admin/` |
| Owner | Group "Owner" | Tudo, exceto `/admin/` |
| Comum | Group "Comum", ou nenhum Group/superuser | Tudo, exceto Dashboard, Financeiro (CRUD de `Lancamento`) e `/admin/` |

- As permissões customizadas `imoveis.pode_acessar_dashboard` e `imoveis.pode_acessar_financeiro` são ancoradas em um model "permission-only" sem tabela (`PermissaoTela`, `managed=False` em `imoveis/models.py`), desacoplado de qualquer model de negócio.
- As views de Dashboard e Financeiro (CRUD de `Lancamento`) são protegidas por `permission_required(..., raise_exception=True)` — acesso direto por URL sem a permissão retorna 403 (`templates/403.html`), nunca stack trace.
- A sidebar (`templates/base.html`) oculta os itens Dashboard e Financeiro para quem não tem a permissão correspondente — complementar à proteção de view, nunca a única camada.
- Um usuário pertencente a Owner e Comum simultaneamente tem acesso de Owner (permissões efetivas são a união das permissões de todos os Groups do usuário; Comum não possui permissões próprias para revogar nada).

---

## 11. Alimentação em Tempo Real

- Todas as operações CRUD (criação, edição, exclusão) refletem imediatamente no banco de dados.
- O status do imóvel é recalculado a cada alteração de contrato (via signal), sem necessidade de ação manual.

---

## 12. Validações de Documentos e Campos (`imoveis/validators.py`)

Todos os validadores customizados aceitam o valor com ou sem máscara e removem os não-dígitos antes de validar.

| Validador | Campos que o utilizam | Regra |
|---|---|---|
| `validate_cpf` | `Inquilino.cpf`, `TestemunhaLaudo.cpf`, `Recibo.assinante_cpf` | 11 dígitos + dígitos verificadores válidos |
| `validate_cnpj` | `Inquilino.cnpj` | 14 dígitos + dígitos verificadores válidos |
| `validate_cpf_cnpj` | `Proprietario.cpf_cnpj` | 11 dígitos → valida como CPF; 14 dígitos → valida como CNPJ; caso contrário, erro |
| `validate_rg` | `Inquilino.rg` | Aceita apenas letras, números, "." e "-" (sem dígito verificador nacional) |
| `validate_rg_cpf` | `Fiador.rg_cpf` | Se restarem exatamente 11 dígitos numéricos, valida como CPF (dígitos verificadores); caso contrário, valida o formato como RG |
| `validate_telefone` | `Proprietario.telefone`, `Inquilino.telefone` | Exige 10 dígitos (fixo com DDD) ou 11 dígitos (celular com DDD), com ou sem máscara |

**Dia de vencimento do contrato:** `Contrato.dia_vencimento` usa `MinValueValidator(1)` e `MaxValueValidator(31)` (django.core.validators), restringindo o valor ao intervalo de 1 a 31.

---

## 13. Acesso Mobile (Vistoriadores em Campo)

- A interface é responsiva e permite que vistoriadores realizem consultas e atualizações diretamente do local do imóvel via dispositivos móveis.
- A sidebar é ocultada no mobile e acessada via toggle hamburger.

---

## 14. Indicador de Atenção e Reajuste de Valor

Dois predicados de `Contrato` (`imoveis/models.py`) governam este fluxo, compartilhando a mesma **janela de disparo** mas com finalidades distintas:

- **`precisa_atencao`** — o **aviso**: alimenta o badge "Precisa de atenção" (detalhe e listagem de contratos), o filtro `?atencao=sim|nao` da listagem e a tabela "Contratos que Precisam de Atenção" do dashboard.
- **`pode_reajustar`** — a **elegibilidade do ajuste**: alimenta o botão "Reajustar" no detalhe e o gate da view `contrato_reajuste` (que bloqueia o POST de `valor_vigente` quando `not pode_reajustar`).

**Janela de disparo (comum aos dois):** 30 dias **antes** a 7 dias **depois** (inclusive nos dois extremos) de uma data de referência, ou seja `-7 <= (referência - hoje).days <= 30`. Duas âncoras: (1) **fim de vigência** = `data_fim`; (2) **aniversário anual** de `data_inicio` (ocorrência mais próxima de hoje; `29/02` em ano não-bissexto recua para `28/02`). Basta uma âncora cair na janela.

**Elegibilidade base (ambos):**
- **Somente status** — o contrato precisa estar `ativo`. Nenhuma condição de período bloqueia: contrato ativo cujo **fim de vigência já venceu** (fora do período do documento original) recebe aviso e permite ajuste normalmente. Isso cobre estadias mantidas por renovação, que juridicamente dispensam novo contrato para até 30 meses.
- **Renovação não desloca a referência** — as properties leem apenas `data_inicio`/`data_fim` do contrato **original**; uma `RenovacaoContrato` registrada não altera aniversário nem fim de vigência para efeito desta regra.
- Contrato com status diferente de `ativo` (encerrado, distratado etc.) nunca é elegível, independentemente da data.

**Divergência após o reajuste (aniversário anual):** realizar o reajuste carimba `data_ultimo_reajuste = hoje` (na view `contrato_reajuste`). Quando esse carimbo cai **dentro da janela do aniversário atual**, o aviso da âncora de aniversário é **suprimido** (`precisa_atencao` → `False`), mas `pode_reajustar` permanece `True` enquanto a janela estiver aberta — o botão "Reajustar" continua disponível para novos ajustes no mesmo ciclo. A supressão vale **só para o aniversário**: a âncora de **fim de vigência** não é afetada pelo reajuste e segue avisando até sair da janela. No ciclo seguinte (próximo aniversário), como `data_ultimo_reajuste` do ano anterior cai fora da nova janela, o aviso **reaparece** normalmente.

O valor contratual original (`valor_mensal`) nunca muda no reajuste — só `valor_vigente` é gravado, e `valor_cobranca` passa a devolvê-lo; o PDF jurídico continua exibindo `valor_mensal`.

---

## 15. Histórico de Notificações por Usuário

- Toda mensagem disparada via `django.contrib.messages` (`success`/`error`/`warning`/`info`) é persistida em `NotificacaoUsuario` para o usuário autenticado que gerou a request, sem alterar os 36+ pontos de chamada existentes em `imoveis/views.py`.
- **Captura centralizada:** `MESSAGE_STORAGE = 'imoveis.message_storage.PersistentFallbackStorage'` (`core/settings.py`) substitui o storage padrão do Django. `PersistentFallbackStorage.add()` mantém o comportamento normal (toast efêmero em `base.html`) e adicionalmente cria um `NotificacaoUsuario` quando `request.user.is_authenticated`; para usuário anônimo, só o toast é exibido (sem persistência).
- **Leitura via context processor:** `imoveis.context_processors.notificacoes_usuario` (registrado em `TEMPLATES[0]['OPTIONS']['context_processors']`) injeta `ultimas_notificacoes_usuario` (últimas 8, slicing simples sem `Paginator`, mesmo precedente do dashboard) em todo template renderizado com `render()`. Para usuário anônimo, retorna dict vazio.
- **Sem estado de lida/não lida, sem paginação, sem link para o objeto de origem** — histórico é somente leitura, append-only, exibido no dropdown do sino da topbar.

---

## 16. Contrato Jurídico Completo (PDF)

O PDF de Contrato (`templates/documentos/contrato_pdf.html`) foi reescrito como instrumento particular de locação juridicamente completo — preâmbulo + 21 cláusulas fixas (I a XXI) transcritas de um modelo jurídico fornecido pelo cliente, com variáveis do sistema injetadas no texto corrido. Mantém o motor xhtml2pdf e o padrão A4 de `base_pdf.html`.

- **Locador fixo (Shelter):** o locador exibido no PDF **não é** mais `contrato.imovel.proprietario` — é sempre a própria Shelter, com dados fixos em `settings.SHELTER_LOCADOR` (`core/settings.py`): `razao_social`, `cnpj`, `representante_nome`, `representante_rg`, `representante_cpf`, `endereco`, `telefone`, `pix_chave`, `foro`. O `Proprietario` cadastrado do imóvel continua existindo e sendo usado normalmente no resto do sistema (cadastro, listagens); deixa apenas de ser "quem assina como locador" no contrato gerado. A view `_gerar_pdf_contrato` (`imoveis/views.py`) passa `locador=settings.SHELTER_LOCADOR` e `prazo_meses=meses_entre(contrato.data_inicio, contrato.data_fim)` no contexto do template.
- **Finalidade do contrato:** `Contrato.finalidade` (`residencial`/`comercial`) determina o texto de "CONTRATO DE LOCAÇÃO RESIDENCIAL/COMERCIAL" no título e a redação da Cláusula VI (uso do imóvel).
- **Qualificação completa do fiador:** `Fiador` ganhou campos discretos `rg`, `cpf`, `endereco`, `conjuge_nome`, `conjuge_rg`, `conjuge_cpf` (além do `rg_cpf` legado) para a qualificação jurídica completa no contrato — todos opcionais.
- **Local/data de assinatura:** `Contrato.local_assinatura`/`data_assinatura` (mesmo padrão já existente em `LaudoVistoria`) alimentam o fechamento do contrato no PDF.
- **Número por extenso (`imoveis/extenso.py`):** módulo puro (sem dependência de models/views) baseado em `num2words` (pt-BR), com três funções usadas via filtros de template (`imoveis/templatetags/imoveis_tags.py`):
  - `valor_por_extenso(valor)` — valor monetário por extenso (ex.: `Decimal('1500.00')` → "mil e quinhentos reais").
  - `meses_por_extenso(quantidade)` — quantidade de meses por extenso (ex.: 12 → "doze meses").
  - `dia_ordinal_extenso(dia)` — ordinal por extenso do dia de vencimento (ex.: 10 → "décimo").
  - `meses_entre(data_inicio, data_fim)` — cálculo puro de meses inteiros entre duas datas (sem `dateutil`), usado para `prazo_meses`.
  - **Datas por extenso não usam `num2words`** — o filtro nativo `date` do Django, com `LANGUAGE_CODE = 'pt-br'`, já produz o formato desejado via `{{ valor|date:"j \d\e F \d\e Y" }}` (ex.: "1 de Junho de 2026").
- **Sem regeração automática:** o PDF de contrato já gerado antes desta mudança permanece no layout antigo até que alguém clique novamente em "Regerar PDF" — só então o arquivo é sobrescrito pelo layout jurídico novo.
- **Paginação A4:** o CSS das cláusulas evita `page-break-inside: avoid` no corpo de texto das cláusulas (risco de página em branco no xhtml2pdf quando a cláusula é maior que o espaço restante) — apenas o número da cláusula fica inline (negrito) com o início do texto, nunca separado por quebra de página.
