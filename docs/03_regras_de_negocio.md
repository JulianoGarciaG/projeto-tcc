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

## 3. Unicidade de Renovação e Distrato

| Entidade | Regra |
|---|---|
| `RenovacaoContrato` | Apenas **uma** renovação por contrato (OneToOneField) |
| `Distrato` | Apenas **um** distrato por contrato (OneToOneField) |

**Comportamento na view:**
- Se o contrato já possui renovação → exibe aviso e redireciona para o detalhe do contrato, sem criar nova.
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

## 5a. Recibos Vinculados ao Contrato (card no detalhe)

- O detalhe do contrato (`contrato_detail`) exibe um card "Recibos" com todos os `Recibo` vinculados via `Recibo.contrato` (`related_name='recibos'`), cada linha linkando para `recibo_detail`.
- O botão "Novo Recibo" do card usa a rota dedicada `contratos/<int:contrato_pk>/recibos/novo/` (view `recibo_create_from_contrato`), que pré-seleciona `imovel`/`contrato` no `ReciboForm` a partir do contrato de origem — mesmo padrão de pré-preenchimento já usado por `notificacao_create` (parâmetro de rota, não querystring). A view genérica `recibo_create` (sem contrato pré-selecionado) continua existindo para o botão "+ Novo" da listagem de recibos.
- Este card é distinto da central GED (`DocumentoGerado` com `tipo='recibo'`, versões de PDF) — mostra os registros de negócio `Recibo`, não os PDFs gerados.

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
lançamentos, renovação/distrato, itens de vistoria, testemunhas, documentos
gerados) que são apagados junto quando o registro pai é excluído. A property
`dependentes_cascata` (em cada um desses models, `imoveis/models.py`) calcula
essa contagem, e o modal de confirmação de exclusão das respectivas listagens
exibe um aviso com a quantidade de cada tipo de dependente que também será
removido — sem bloquear a exclusão.

---

## 8. GED — Gestão Eletrônica de Documentos

A central de documentos (`/documentos/`), o versionamento de PDFs (`DocumentoGerado`) e o storage plugável (`STORAGE_BACKEND`) têm documento dedicado: **[docs/05_ged_documentos_versionados.md](05_ged_documentos_versionados.md)**.

---

## 9. Dashboard — Filtros e Métricas

O dashboard suporta filtros combinados aplicados simultaneamente:

| Filtro | Campo filtrado |
|---|---|
| Imóvel | `contrato__imovel_id` |
| Data início | `data_vencimento__gte` |
| Data fim | `data_vencimento__lte` |
| Status do lançamento | `status` |

O filtro de período (data início/fim) é validado e limpo por `DashboardFiltroForm` (`imoveis/forms.py`), um `forms.Form` com os campos opcionais `data_inicio`/`data_fim`, ambos com widget Flatpickr (formato dd/mm/aaaa).

**Métricas calculadas:**
- Total de imóveis, ocupados e vagos (com base no filtro de imóvel)
- Taxa de vacância: `(vagos / total) * 100`
- Contratos ativos (global, sem filtro)
- Inadimplentes: lançamentos com `status = 'atrasado'` (com filtros aplicados)
- Gráfico de barras: soma de valores pagos e pendentes/atrasados nos últimos 6 meses

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

## 14. GED Versionado e Storage Plugável (Rodada 4)

Ver documento dedicado: **[docs/05_ged_documentos_versionados.md](05_ged_documentos_versionados.md)** (versionamento de `DocumentoGerado`, storage plugável `STORAGE_BACKEND`).

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
- **Retrocompatibilidade do GED versionado:** PDFs de contrato já gerados antes desta mudança (`DocumentoGerado` existentes, `tipo='contrato'`) são imutáveis e **não são regerados nem migrados** — continuam permanentemente no layout antigo (resumo em cards). Só uma nova chamada a "Regerar PDF" produz uma versão nova no layout jurídico.
- **Paginação A4:** o CSS das cláusulas evita `page-break-inside: avoid` no corpo de texto das cláusulas (risco de página em branco no xhtml2pdf quando a cláusula é maior que o espaço restante) — apenas o número da cláusula fica inline (negrito) com o início do texto, nunca separado por quebra de página.
