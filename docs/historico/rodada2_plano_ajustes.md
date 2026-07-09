# Plano de Ajustes — Rodada 2

> Arquivo histórico, movido de `docs/PLANO_AJUSTES_RODADA2.md`. Ver resumo em [docs/historico_entregas.md](../historico_entregas.md) ("Rodada 2"). Estado atual do sistema: `docs/02_modelagem_dados.md`, `docs/03_regras_de_negocio.md`, `docs/04_design_ui_ux.md`.

## Contexto

A Rodada 1 (ver `docs/historico/rodada1_plano_geracao_documentos.md`) implementou geração automática de PDF para Contrato/Laudo/Recibo, novos models (`Recibo`, `ComodoTemplate`, `ItemVistoriaTemplate`, `ItemVistoria`, `TestemunhaLaudo`) e o CRUD de Recibos. Em uso real, o usuário identificou um backlog de 25 ajustes: bugs de UI/UX, uma mudança de comportamento na geração de PDF (deixa de ser automática), simplificações de cadastro (remoção de campos e módulos) e necessidade de máscaras/validações consistentes em todo o sistema. Este documento cobre **apenas o planejamento** da Rodada 2 — nenhum código é alterado nesta etapa.

### Decisões de abordagem confirmadas com o usuário
1. **G1 (logo/sidebar):** não existe hoje nenhum colapso de sidebar no desktop (só show/hide mobile via overlay). Será **criada** uma feature real de colapso (ícone-only) no desktop, com a logo se adaptando (versão compacta).
2. **G5/G7 (máscaras/datepicker):** adicionar **IMask** (máscaras) e **Flatpickr** (datepicker dd/mm/yyyy) via CDN — mesmo padrão já usado para Bootstrap/Bootstrap Icons (sem npm/build).
3. **N1 (faixas de renda):** usar faixas por salário mínimo: até 2 SM · 2–4 SM · 4–6 SM · 6–10 SM · 10–20 SM · acima de 20 SM.

---

## 1. Estado atual investigado (por módulo)

### Geral / Layout (`templates/base.html`, `static/css/custom.css`)
- Sidebar (`#sidebar`) é `position:fixed`, `width:260px` fixo; só existe show/hide mobile (`.show` + overlay) via JS inline em `base.html` (linhas 139-149). **Não há colapso desktop.**
- Logo: `<img>` dentro de `.sidebar-brand` (altura fixa 72px), com `object-fit:contain` — já proporcional ao contêiner, mas o contêiner nunca muda de tamanho hoje. `base.html:20` referencia `Shelter_LOGO_white.svg` (existe em `static/assets/`, junto de `.jpg` e versões escuras).
- Mensagens: `{% if messages %}` renderizadas **inline na topbar** (`base.html:105-112`), ao lado do título da página — não é toast/alerta fixo. Cada página herda isso do `base.html` (a posição é sempre a mesma). O ícone de sino (`bi-bell`) ao lado do avatar é decorativo, sem dropdown funcional. **Reinterpretação:** "descentralizado" provavelmente se refere à baixa visibilidade/posição pouco destacada (comprimida na topbar, sem animação/empilhamento) — ver decisão G2.
- `LaudoVistoria.contrato` é `on_delete=models.PROTECT` (`imoveis/models.py:179`). `contrato_delete` (`imoveis/views.py:411-416`) chama `obj.delete()` sem `try/except` → `ProtectedError` não tratado = página de erro 500 do Django. **Confirma G3.**
- Geração automática de PDF ao salvar ocorre em `contrato_create/edit`, `laudo_create/edit`, `recibo_create/edit` (`imoveis/views.py`), todas retornando `_gerar_pdf_*(obj)` (a resposta HTTP de download) em vez de redirect. **G4 substitui esse fluxo.**
- Nenhuma lib de máscara/datepicker existe hoje (`static/js/` não existe; nenhum `mask`/`flatpickr`/`IMask` referenciado). Campos de data usam `forms.DateInput(attrs={'type':'date'})`; telefone/moeda são `TextInput`/`NumberInput` sem máscara.
- Validação de CPF já existe (`imoveis/validators.py::validate_cpf`), aplicada em `Recibo.assinante_cpf` e `TestemunhaLaudo.cpf`. **Não aplicada** a `Inquilino.cpf` nem a `Proprietario.cpf_cnpj`.

### Imóveis (`imoveis/models.py::Imovel`, `imoveis/forms.py::ImovelForm`, `templates/imoveis/*`)
- `Imovel.valor_aluguel` é `DecimalField` obrigatório, exibido em `imovel_form.html:57`, `imovel_detail.html:72-73`, e em `ImovelAdmin.list_display`.
- **"Contrato ativo" já é derivável:** `Contrato.status` tem choices `ativo/encerrado/rescindido` (`imoveis/models.py:111-115`) e o signal `imoveis/signals.py::_atualizar_status_imovel` já usa `imovel.contratos.filter(status='ativo').exists()`. **Não precisa de campo novo** — usar `imovel.contratos.filter(status='ativo').order_by('-data_inicio').first()`.
- Não existem campos "Número" nem "Complemento" — `Imovel.endereco` é um único `CharField(300)` de texto livre.
- **Módulo financeiro "Entradas/Saídas" do imóvel** = models `Entrada`/`Saida` (`imoveis/models.py:398-455`, distintos do `Lancamento` financeiro global e do tipo entrada/saída do `LaudoVistoria`). Usados em: `imovel_detail.html` (seções "Entradas"/"Saídas" com totais; contexto em `imovel_detail` linhas 180-193), views `entrada_*`/`saida_*` (`imoveis/views.py:684-763`), forms `EntradaForm`/`SaidaForm`, urls (`imoveis/urls.py:20-28`), admin (`SaidaAdmin`/`EntradaAdmin`). **Nenhuma outra tela depende deles** (dashboard usa só `Lancamento`; `distrato_form.html` referencia `laudo_saida`, FK para `LaudoVistoria`, não relacionado). Dados atuais: **1 registro em `Entrada` e 1 em `Saida`**.

### Proprietários (`imoveis/models.py::Proprietario`)
- `endereco = CharField(300, blank=True)` — usado só em `proprietario_form.html:20`; não aparece em nenhum PDF nem em outras telas.

### Inquilinos (`imoveis/models.py::Inquilino`, `imoveis/forms.py::InquilinoForm`)
- `renda_mensal = DecimalField(null=True, blank=True)` — campo livre, sem faixas.
- **Não existe** campo `observacoes` em `Inquilino` (existe em `Contrato`, `LaudoVistoria`, `Notificacao`, `Lancamento`, `Saida`, `Entrada`).

### Laudos de Vistoria (`imoveis/models.py::LaudoVistoria`, `imoveis/forms.py`, `imoveis/views.py`, `templates/laudos/*`)
- `LaudoVistoriaForm` (`imoveis/forms.py:144-159`) tem `contrato` como `forms.Select` **sem filtro** — lista todos os contratos, sem dependência do imóvel. Não há JS de filtro dinâmico.
- `TIPO_CHOICES` inclui `('periodica', 'Vistoria Periódica')` (`imoveis/models.py:172-176`). **Existe 1 registro com `tipo='periodica'`** (de 2 laudos totais).
- `arquivo` (upload manual) é exposto na criação (`laudo_form.html:25`; presente em `LaudoVistoriaForm.Meta.fields`). **Confirma L3.**
- Catálogo `ComodoTemplate`/`ItemVistoriaTemplate` **já está populado no banco**: a data migration `0004_seed_vistoria_catalog.py` foi aplicada na Rodada 1; a consulta ao banco confirma **5 cômodos e 32 itens** (Sala, Cozinha, Quarto, Banheiro, Área externa). **Porém o checklist aparece vazio na tela de "Novo Laudo"** — e a causa **não é falta de seed**, é um **bug de renderização do formset**: `ItemVistoriaFormSet = inlineformset_factory(..., extra=0)`. Em formsets de model/inline, o total de linhas exibidas é `max(len(queryset), min_num) + extra`; para um laudo novo o queryset é vazio → `max(0,0) + 0 = 0`. O `initial=_initial_itens_catalogo()` que a view passa **só preenche linhas "extra"**, e como `extra=0` nenhuma linha é criada. Reproduzido: `fs.total_form_count()` retorna **0** com 32 itens de `initial`. Os testes da Rodada 1 não pegaram isso porque o E2E montava o POST com as 32 linhas manualmente (management form), sem exercitar o GET. **L4 real = corrigir esse `extra`** (ver decisão).
- PDF (`base_pdf.html:71-74`): `.assinatura` usa `margin-top:40px` fixo. **Confirma L5** (aumentar o espaço acima da linha de assinatura do laudo).
- Não existe campo de anexo pós-vistoria no detail (`laudo_detail.html` não tem upload); o único `FileField` de upload manual do laudo é `arquivo` (o mesmo que sai da criação).

### Recibos (`imoveis/models.py::Recibo`, `imoveis/forms.py::ReciboForm`)
- `imovel`/`contrato` são `ForeignKey(..., on_delete=SET_NULL, null=True, blank=True)`. **Dado atual: 0 registros com esses campos nulos** (1 recibo total, ambos preenchidos) → migração para `NOT NULL` é segura sem correção de dados.
- `periodo_referente = CharField(200, blank=True)` — texto livre.
- `proveniente_sitio = CharField(300, blank=True)` — presente no form, no PDF (`recibo_pdf.html:16`) e no model.
- Endereço do imóvel no recibo: `recibo_pdf.html:14` já exibe `recibo.imovel.endereco` — falta número/complemento (só existirá após I2).

### Contratos (`imoveis/models.py::Contrato`)
- Dois campos de arquivo distintos confirmados:
  - `arquivo = FileField(upload_to='contratos/', ...)` — **upload manual original** (candidato à remoção, C1).
  - `documento_gerado = FileField(upload_to='contratos/gerados/', ...)` — **PDF gerado pelo sistema** (NÃO remover; destino do botão "Regerar PDF").
- Ambos aparecem em `contrato_form.html:38-39`, `contrato_detail.html:15-17,60-61` e `ged/documentos.html` (seção "Contratos com Arquivo" usa `arquivo`; "Contratos Gerados (Sistema)" usa `documento_gerado`).
- **Confirmado:** apenas `arquivo` é candidato à remoção; `documento_gerado` permanece intocado.

---

## 2. Decisões resolvidas

| # | Item | Decisão |
|---|---|---|
| G1 | Logo sidebar | Criar colapso desktop (ícone-only) com toggle; logo troca para versão compacta quando colapsada; estado persistido em `localStorage` |
| G2 | Notificações | Padronizar como toasts Bootstrap fixos (canto superior direito, empilháveis, auto-dismiss), substituindo o bloco inline atual na topbar |
| G3 | Erro ao deletar contrato com laudo | `contrato_delete` captura `ProtectedError`, mostra `messages.error` amigável e redireciona para `contrato_detail` |
| G4 | PDF deixa de ser automático | Remove chamada a `_gerar_pdf_*` de dentro de `*_create`/`*_edit`; essas views voltam ao padrão PRG (redirect + `messages.success`); o botão "Regerar PDF" (`*_gerar_pdf`) passa a ser o único gatilho, em todas as telas de detail |
| G5 | Máscaras | IMask via CDN. Campos: `telefone` (Proprietario/Inquilino) e valores monetários (`quantia`, `valor_*` do Recibo). Obs.: **não existe campo CEP** hoje, então máscara de CEP fica N/A |
| G6 | Validação CPF/CNPJ/RG/e-mail | CPF: aplicar `validate_cpf` também a `Inquilino.cpf` (retroativo — ver risco). CNPJ: criar `validate_cnpj` em `imoveis/validators.py` (dígitos verificadores), aplicar a `Inquilino.cnpj` e a `Proprietario.cpf_cnpj` (validação condicional: 11 dígitos→CPF, 14→CNPJ). RG: sem dígito verificador nacional único → validação apenas de formato genérico (alfanumérico, sem símbolos além de `.`/`-`), não bloqueante além disso. E-mail: `EmailField` já valida (Django nativo) — nenhuma ação nova |
| G7 | Datepicker dd/mm/yyyy | Flatpickr via CDN, `locale: "pt"`, `dateFormat: "d/m/Y"`, substituindo `type="date"` por `type="text"` com `data-flatpickr` e init JS centralizada |
| I1 | Valor do aluguel no imóvel | Remover `Imovel.valor_aluguel`; exibir no `imovel_detail.html` (somente leitura) o `valor_mensal` do contrato ativo mais recente; se não houver, não exibir a linha |
| I2 | Número/Complemento | Novos campos opcionais `Imovel.numero` (CharField 20, blank) e `Imovel.complemento` (CharField 100, blank) |
| I3 | Remover módulo Entradas/Saídas do imóvel | Remover models `Entrada`/`Saida`, forms, views, urls, admin, seções em `imovel_detail.html`; **sem relação com o tipo Entrada/Saída do Laudo** (mantido) nem com `Lancamento` (mantido) — ver pergunta em aberto sobre perda de dados |
| P1 | Remover endereço do proprietário | Remover `Proprietario.endereco` |
| N1 | Faixas de renda | `Inquilino.renda_mensal` (Decimal) → `Inquilino.faixa_renda` (CharField com choices): `ate_2sm`, `2_4sm`, `4_6sm`, `6_10sm`, `10_20sm`, `acima_20sm` |
| N2 | Observações do inquilino | Novo campo `Inquilino.observacoes = TextField(blank=True)` |
| L1 | Contrato dependente do imóvel | JS no `laudo_form.html`: campo `contrato` inicia `disabled`; ao selecionar `imovel`, fetch assíncrono (nova view `contratos_por_imovel_json`) popula as opções com os contratos daquele imóvel e habilita o campo |
| L2 | Remover "Vistoria Periódica" | Remover `('periodica', ...)` de `LaudoVistoria.TIPO_CHOICES`; data migration reatribui registros `periodica` → `entrada` (ver §3) |
| L3 | Remover upload manual na criação | Remover campo `arquivo` de `LaudoVistoriaForm.Meta.fields` (o model mantém o campo — ver L6) |
| L4 | Checklist do laudo aparece vazio | **NÃO é falta de seed** (banco já tem 5 cômodos/32 itens) — é bug de renderização: `inlineformset_factory(..., extra=0)` gera 0 linhas para laudo novo, ignorando o `initial`. Corrigir em `laudo_create` construindo a factory por request com `extra=len(catalogo)` (ou setando `item_formset.extra = len(catalogo)` antes de renderizar). POST não muda (contagem vem do management form). Sem alteração de dados/migração |
| L5 | Espaço de assinatura no PDF | Classe modificadora `.assinatura-laudo` (margin-top ~80px) só no `laudo_pdf.html`, sem afetar contrato/recibo |
| L6 | Anexo pós-assinatura no detail | **Reaproveita `LaudoVistoria.arquivo`** (mesmo campo removido da criação em L3) — passa a ser editável só no detail/edição, com upload dedicado em `laudo_detail.html` (form próprio, POST para nova view `laudo_anexar_arquivo` ou `laudo_edit`) |
| R1 | Imóvel/contrato obrigatórios no recibo | `Recibo.imovel`/`contrato` → `on_delete=PROTECT`, `null=False, blank=False` (sem órfãos hoje — migração direta, sem `RunPython`) |
| R2 | Endereço completo no recibo | `recibo_pdf.html` exibe `imovel.endereco`, `imovel.numero`, `imovel.complemento` (depende de I2) |
| R3 | Dois datepickers no período | `Recibo.periodo_referente` (CharField) → `periodo_inicio` + `periodo_fim` (`DateField`, `null=True, blank=True`); PDF exibe "de X a Y" só se ambos preenchidos |
| R4 | Remover "Proveniente do Sítio" | Remover `Recibo.proveniente_sitio` (model, form, template PDF) |
| C1 | Remover upload manual do contrato | Remover `Contrato.arquivo` (model, form, `contrato_form.html`/`contrato_detail.html`/`ged/documentos.html`); **manter `documento_gerado` intacto** |

---

## 3. Estratégia de migração de dados

| Risco | Situação encontrada | Estratégia |
|---|---|---|
| `Recibo.imovel`/`contrato` → obrigatórios (R1) | 0 registros nulos (1 recibo total, ambos preenchidos) | Migração de schema direta (`null=False`), sem `RunPython` — sem prompt interativo do Django |
| Remoção da opção periódica (L2) | 1 laudo com `tipo='periodica'` (de 2) | Data migration `RunPython` **antes** da migração de schema: reclassificar `'periodica'` → `'entrada'` (valor mais neutro). Reverse não recupera o valor original (irreversível por natureza — documentar no `RunPython`) |
| Remoção de `Imovel.valor_aluguel` (I1) | Campo obrigatório, 2 imóveis com valor | Nenhuma migração de dados (o valor apenas deixa de ser consultado/exibido); coluna removida via schema padrão |
| Remoção de `Proprietario.endereco`, `Recibo.proveniente_sitio`, `Contrato.arquivo` | Campos opcionais, sem impacto de integridade | `RemoveField` padrão. Nota: `RemoveField` **não apaga arquivos do storage** (`media/`), só a referência no banco — arquivos de `Contrato.arquivo` ficam órfãos em disco |
| `Inquilino.renda_mensal` → `faixa_renda` (N1) | Verificar quantos inquilinos têm renda preenchida na execução | Data migration `RunPython`: mapear `renda_mensal` (em SM) para a faixa correspondente antes de dropar a coluna; se não houver registros, no-op seguro |
| Remoção do módulo Entrada/Saida (I3) | 1 registro em cada tabela | ✅ **Confirmado dropar** — `DeleteModel` de `Entrada`/`Saida` na migração de schema; os 2 registros são perdidos (aceito pelo usuário) |

---

## 4. Dependências e Setup

Nenhuma dependência **Python** nova (backend usa só o que já foi instalado na Rodada 1: Django, xhtml2pdf, reportlab, Pillow, python-dotenv).

Duas bibliotecas **JS via CDN** (sem npm/build, mesmo padrão do Bootstrap):

1. **Flatpickr** (datepicker dd/mm/yyyy) — em `templates/base.html`, no `<head>` (CSS) e antes de `</body>` (JS):
   ```html
   <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
   <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
   <script src="https://npmcdn.com/flatpickr/dist/l10n/pt.js"></script>
   ```
2. **IMask** (máscaras de telefone/moeda) — antes de `</body>`:
   ```html
   <script src="https://cdn.jsdelivr.net/npm/imask@7"></script>
   ```
3. Criar **`static/js/masks.js`** (novo, carregado em `base.html` após as libs) com inicialização automática por atributo — `data-mask="telefone|moeda"` e `data-flatpickr` — disparada em `DOMContentLoaded`, evitando repetir JS em cada template.

Nenhuma alteração em `settings.py`, `requirements.txt` ou `.env` — tudo client-side via CDN.

---

## 5. Lotes de execução (ordem, respeitando dependências)

**Lote 1 — Setup de dependências**
- `templates/base.html`: CDN Flatpickr/IMask + `<script src="{% static 'js/masks.js' %}">`
- Criar `static/js/masks.js`

**Lote 2 — Modelos, validators e migrações** (I2 antes de R2; data migration antes do schema)
1. `imoveis/validators.py`: adicionar `validate_cnpj`
2. `imoveis/models.py`:
   - `Imovel`: remover `valor_aluguel`; adicionar `numero`, `complemento`
   - `Proprietario`: remover `endereco`; aplicar `validate_cnpj` condicional em `cpf_cnpj`
   - `Inquilino`: `renda_mensal`→`faixa_renda`; adicionar `observacoes`; aplicar `validate_cpf` em `cpf` e `validate_cnpj` em `cnpj`
   - `LaudoVistoria`: remover `'periodica'` de `TIPO_CHOICES`
   - `Recibo`: `imovel`/`contrato` → obrigatórios + `PROTECT`; `periodo_referente`→`periodo_inicio`/`periodo_fim`; remover `proveniente_sitio`
   - `Contrato`: remover `arquivo`
3. `imoveis/migrations/0005_*` — data migration (`RunPython`): `periodica`→`entrada`; `renda_mensal`→`faixa_renda`
4. `imoveis/migrations/0006_*` — schema (`makemigrations`)

**Lote 3 — Forms** (`imoveis/forms.py`)
- `ImovelForm` (remove `valor_aluguel`, add `numero`/`complemento`), `ProprietarioForm` (remove `endereco`, máscara telefone), `InquilinoForm` (`faixa_renda` Select, add `observacoes`, máscara telefone), `LaudoVistoriaForm` (remove `arquivo`, prepara `contrato` para JS de L1), `ReciboForm` (remove `proveniente_sitio`, `periodo_inicio`/`fim` flatpickr, máscara moeda), `ContratoForm` (remove `arquivo`); remover `EntradaForm`/`SaidaForm` (pendente I3)

**Lote 4 — Views e URLs**
- `imoveis/views.py`: remover `_gerar_pdf_*` de `*_create`/`*_edit` (G4); `contrato_delete` com `try/except ProtectedError` (G3); **`laudo_create`: construir `ItemVistoriaFormSet` com `extra=len(catalogo)` para o checklist renderizar (L4)**; nova `contratos_por_imovel_json` (L1); anexo do laudo (L6); `imovel_detail` add `contrato_ativo`, remove contexto entradas/saídas; remover views `entrada_*`/`saida_*` (I3)
- `imoveis/urls.py`: add rota JSON; remover rotas `entrada_*`/`saida_*` (I3)
- `imoveis/admin.py`: remover `EntradaAdmin`/`SaidaAdmin` (I3); `ImovelAdmin.list_display` sem `valor_aluguel`

**Lote 5 — Templates de formulário/detalhe**
- `imovel_form.html`/`imovel_detail.html`, `proprietario_form.html`, `inquilino_form.html`, `laudo_form.html`/`laudo_detail.html`, `recibo_form.html`, `contrato_form.html`/`contrato_detail.html`, `ged/documentos.html`
- Aplicar `data-flatpickr` em todos os `DateInput` do sistema (Contrato, Notificação, Renovação, Distrato, Lançamento) e `data-mask="telefone"` nos telefones

**Lote 6 — PDFs**
- `recibo_pdf.html` (remove sítio; add número/complemento; período com duas datas), `laudo_pdf.html` + `base_pdf.html` (`.assinatura-laudo`)

**Lote 7 — UI geral**
- `base.html` + `custom.css`: colapso desktop da sidebar (ícone-only + logo compacta + `localStorage`); toasts padronizados

**Lote 8 — Testes** (`imoveis/tests.py`)
- Atualizar testes que dependem do removido (PDF automático, `valor_aluguel`, `proveniente_sitio`, tipo periódica, `Contrato.arquivo`); novos testes: G3, G4, L1 (endpoint JSON), R1 (recibo exige imóvel/contrato), `validate_cnpj`

---

## 6. Perguntas — respondidas e pendências de baixo impacto

**Respondidas pelo usuário:**
1. **I3 — perda de dados Entrada/Saída:** ✅ **pode dropar** definitivamente (1 registro em cada tabela será perdido, aceito).
2. **L2 — vistoria periódica existente:** ✅ **tanto faz** → será reclassificada para `'entrada'`.
3. **G6 — CPF/CNPJ retroativo:** ✅ **sim, aplicar** validação também aos campos existentes (`Inquilino.cpf/cnpj`, `Proprietario.cpf_cnpj`).

**Defaults de baixo impacto (sigo assim, salvo objeção):**
4. **C1 — arquivos físicos órfãos:** `RemoveField` de `Contrato.arquivo` deixa os PDFs já enviados em `media/contratos/` no disco. Nenhuma ação — limpeza manual só se desejar depois.
5. **G2 — "descentralizado":** interpretado como baixa visibilidade/posição comprimida na topbar → padronizar como toasts fixos. Ajusto se houver caso concreto diferente.
6. **G1 — persistência do colapso:** `localStorage` para lembrar o estado entre páginas (não há SPA; evita "piscar").

---

## 7. Verificação (end-to-end, ao final da implementação)

```bash
venv/Scripts/python manage.py makemigrations
venv/Scripts/python manage.py migrate
venv/Scripts/python manage.py check
venv/Scripts/python manage.py test imoveis
venv/Scripts/python manage.py runserver
```
Testes manuais no navegador:
- Colapsar/expandir a sidebar (desktop) — logo se adapta, estado persiste ao navegar.
- Deletar um contrato vinculado a um laudo — mensagem amigável, sem página de erro 500.
- Criar Contrato/Laudo/Recibo — **não** baixa PDF automaticamente; o botão "Regerar PDF" no detail gera.
- Telefone/moeda com máscara ao digitar; todos os datepickers em dd/mm/yyyy.
- CPF/CNPJ inválido — bloqueado no submit.
- Cadastrar imóvel sem "valor do aluguel" (campo não existe mais); ver valor do contrato ativo no detail.
- Criar laudo — campo contrato desabilitado até escolher imóvel, depois lista só os contratos daquele imóvel; tipo "Vistoria Periódica" ausente.
- Emitir recibo sem imóvel/contrato — bloqueado (obrigatórios agora).