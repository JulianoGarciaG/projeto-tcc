# Plano de Implementação — Geração Automática de Documentos PDF (Rodada 1)

> Arquivo histórico, movido de `docs/PLANO_GERACAO_DOCUMENTOS.md`. Ver resumo em [docs/historico_entregas.md](../historico_entregas.md) ("Rodada 1"). O comportamento de geração automática ao salvar descrito aqui foi **revertido na Rodada 2** — hoje o PDF só é gerado pelo botão "Regerar PDF" (ver [docs/historico/rodada2_plano_ajustes.md](rodada2_plano_ajustes.md)). Estado atual do sistema: `docs/02_modelagem_dados.md`, `docs/03_regras_de_negocio.md`, `docs/04_design_ui_ux.md`.

## Contexto

O sistema (Django 5.2/6.0, GED imobiliário) hoje só **armazena** documentos que o usuário faz upload (`FileField` → `media/`, listados em `templates/ged/documentos.html`). **Não existe nenhuma geração de documento pelo servidor** — nenhuma biblioteca de PDF instalada (`requirements.txt` = Django, python-dotenv, Pillow), nenhuma view de download/`HttpResponse`, nenhum `@media print`.

A feature adiciona **geração automática de PDF a partir de formulários** para três seções: **Contrato**, **Laudo de Vistoria** e **Recibo**. O usuário preenche um formulário e o sistema gera um PDF pronto para impressão, que é oferecido para download **e** arquivado no GED.

### Decisões já confirmadas com o usuário
1. **Biblioteca:** `xhtml2pdf` (puro Python, sem dependências nativas — funciona no Windows; renderiza templates HTML/CSS que a equipe já domina).
2. **Destino do PDF:** download **+** gravação no `FileField` do registro (aparece no GED).
3. **Recibo:** vira um **novo model `Recibo`** persistido (CRUD completo + geração).
4. **Laudo:** Locador derivado de `imovel.proprietario`; Locatário de `contrato.inquilino`; "Responsável pela vistoria" é o campo já existente `LaudoVistoria.responsavel`.
5. **Momento da geração:** **automático ao salvar** o formulário (fluxo em 1 passo) — o registro é criado, o PDF é gerado com base nos campos preenchidos, atrelado ao registro e baixado na hora. Editar regenera; botão "Regerar PDF" no detail reemite sem editar.

---

## 1. Estado atual relevante (arquivos reais)

| Camada | Arquivo | Padrão observado |
|---|---|---|
| Models | `imoveis/models.py` | 13 models, `FileField(upload_to=...)` para docs; `Contrato.tipo_contrato` já tem choices `PF`/`PJ`; `Contrato.observacoes` já existe; `Inquilino` tem `cpf` (obrigatório/único) e `cnpj` (opcional) |
| Forms | `imoveis/forms.py` | 100% `ModelForm`; dicts de estilo `_ctrl`/`_sel`; widgets explícitos; **nenhum `clean_*`**; formsets via `inlineformset_factory` (`FiadorFormSet`, `FotoImovelFormSet`) |
| Views | `imoveis/views.py` | 100% FBV, todas `@login_required`; padrão PRG com `messages`; `get_object_or_404`; formsets validados junto (`form.is_valid() and formset.is_valid()`) |
| URLs | `imoveis/urls.py` | `path()` plano, convenção `{modelo}_{acao}` (`_list/_create/_detail/_edit/_delete`); sem `app_name` |
| Templates | `templates/**` | todos `{% extends 'base.html' %}`; Bootstrap 5.3 via CDN; componentes `.section-card` > `.section-card-header` > `.section-card-body`; filtro `{{ v|brl }}` de `imoveis/templatetags/imoveis_tags.py`; **contrato_form.html já tem JS toggle `.campo-pf`/`.campo-pj`** (linhas 103-120) — padrão reutilizável |
| Settings | `core/settings.py` | `MEDIA_ROOT=BASE_DIR/media`, `STATICFILES_DIRS=[BASE_DIR/static]`; `LANGUAGE_CODE='pt-br'` |

**Contrato:** todos os campos pedidos já existem (`imovel`, `inquilino`, `tipo_contrato` PF/PJ, `dia_vencimento`, `valor_mensal`, `data_inicio`, `data_fim`, `observacoes`) → geração é **stateless** a partir do registro existente, sem novo model nem novo formulário.

**LaudoVistoria:** existe (`imovel`, `contrato` opcional, `tipo`, `data`, `responsavel`, `observacoes`, `arquivo`) mas **não guarda** cômodos/itens vistoriados, testemunhas, nem local/data de assinatura → precisa de novos models.

**Recibo:** não existe nenhum model → criar do zero.

---

## 2. Arquitetura da geração de PDF

Manter o layout flat do app (não há pasta `services/`). Criar **`imoveis/pdf.py`** com helpers reutilizados pelas 3 seções:

- `html_to_pdf_bytes(html, base_url) -> bytes` — usa `xhtml2pdf.pisa.CreatePDF`.
- `link_callback(uri, rel)` — **obrigatório** no xhtml2pdf: resolve `STATIC_URL`/`MEDIA_URL` para caminhos de arquivo (`STATIC_ROOT`/`STATICFILES_DIRS`, `MEDIA_ROOT`). Sem isso, imagens/CSS não carregam no PDF.
- `render_pdf(template_name, context) -> bytes` — `render_to_string` + `html_to_pdf_bytes`.
- `pdf_download_response(pdf_bytes, filename) -> HttpResponse` — `content_type='application/pdf'`, `Content-Disposition: attachment; filename=...`.
- `save_pdf_to_field(instance, field_name, pdf_bytes, filename)` — grava via `django.core.files.base.ContentFile` no `FileField` (aparece no GED).

**Momento da geração (confirmado):** o PDF é gerado **automaticamente ao salvar** o formulário — fluxo em 1 passo. Ao salvar (create ou edit), o registro é persistido, o PDF é gerado, atrelado ao `FileField` do registro e **baixado imediatamente** (a resposta do POST é o próprio PDF, `attachment`). Editar o registro **regenera** o PDF (sobrescreve o anexo). Uma função helper única — ex. `gerar_e_anexar(instance, template_name, context, field_name, filename)` em `imoveis/pdf.py` — encapsula `render_pdf` → `save_pdf_to_field` → retorna os bytes, e é chamada dentro das views de create/edit logo após `form.save()`. Views permanecem finas; toda a lógica de PDF fica em `imoveis/pdf.py`.

Opcionalmente, manter também um botão "Regerar PDF" na tela de detalhe (rota `*_gerar_pdf`) para reemitir sem editar — reaproveita o mesmo helper.

---

## 3. Modelagem de dados

### 3.1 Contrato — 1 campo novo
Os dados do documento já existem. Adicionar **apenas** um `FileField` dedicado para o PDF gerado (não sobrescrever o `arquivo` de upload manual):
- `Contrato.documento_gerado = FileField(upload_to='contratos/gerados/', blank=True, null=True, verbose_name='Contrato gerado (PDF)')`

A qualificação PF vs PJ no documento sai de `Inquilino.cpf`/`Inquilino.cnpj`/`Inquilino.qualificacao` condicionalmente por `Contrato.tipo_contrato`.

### 3.2 Recibo — novo model (`imoveis/models.py`)
Quase todos os campos opcionais (regra: só aparecem no PDF se preenchidos).

```
class Recibo(models.Model):
    imovel        = FK Imovel  (SET_NULL, null, blank, related_name='recibos')   # opcional
    contrato      = FK Contrato (SET_NULL, null, blank, related_name='recibos')  # opcional
    parcela_atual = PositiveSmallIntegerField(null, blank)
    parcela_total = PositiveSmallIntegerField(null, blank)
    valor_aluguel     = DecimalField(10,2, null, blank)
    valor_impostos    = DecimalField(10,2, null, blank)
    valor_seguros     = DecimalField(10,2, null, blank)
    valor_condominio  = DecimalField(10,2, null, blank)
    quem_pagou        = CharField(200, blank)
    proveniente_sitio = CharField(300, blank, 'Proveniente do sítio')  # ex: "Apartamento 21C, Prédio Maranhão"
    periodo_referente = CharField(200, blank, 'Correspondente ao período de')
    vencido_em        = DateField(null, blank)
    quantia           = DecimalField(10,2, null, blank, 'Quantia de')  # TOTAL recebido
    assinante_nome    = CharField(200, blank)
    assinante_cpf     = CharField(14, blank, validators=[validate_cpf])  # ver §5 (validação de CPF)
    data_assinatura   = DateField(null, blank)
    arquivo           = FileField(upload_to='recibos/', blank, null)  # PDF gerado (model novo, sem conflito)
    criado_em         = DateTimeField(auto_now_add=True)

    def somatorio(self):  # soma dos valores que constituem a quantia
        return sum(v for v in [valor_aluguel, valor_impostos, valor_seguros, valor_condominio] if v)
```
> **Semântica confirmada:** `quantia` ("Quantia de") é o **valor total recebido**; os campos `valor_aluguel/impostos/seguros/condominio` são as **parcelas que compõem** esse total, e `somatorio()` retorna a soma delas. No PDF: exibir as parcelas preenchidas + o `somatorio()` (deve bater com `quantia`) e destacar `quantia` como o total do recibo.

### 3.3 Laudo — catálogo configurável + dados da vistoria

**Catálogo (dado, editável no admin) — atende ao requisito "configurável/extensível como dado":**
```
class ComodoTemplate(models.Model):        # ex: Sala, Cozinha, Quarto...
    nome  = CharField(100)
    ordem = PositiveSmallIntegerField(default=0)

class ItemVistoriaTemplate(models.Model):  # ex: "paredes e pintura"
    comodo = FK ComodoTemplate (CASCADE, related_name='itens')
    nome   = CharField(150)
    ordem  = PositiveSmallIntegerField(default=0)
```

**Instância (por laudo) — snapshot desnormalizado (mudança futura no catálogo não reescreve laudos antigos):**
```
class ItemVistoria(models.Model):
    ESTADO_CHOICES = [('bom','Bom'),('regular','Regular'),('ruim','Ruim')]
    laudo      = FK LaudoVistoria (CASCADE, related_name='itens')
    comodo     = CharField(100)      # nome do cômodo (snapshot)
    item       = CharField(150)      # nome do item (snapshot)
    estado     = CharField(10, choices=ESTADO_CHOICES)
    observacao = CharField(300, blank)
    ordem      = PositiveSmallIntegerField(default=0)

class TestemunhaLaudo(models.Model):
    laudo = FK LaudoVistoria (CASCADE, related_name='testemunhas')
    nome  = CharField(200)
    cpf   = CharField(14, blank, validators=[validate_cpf])  # ver §5
```

**Mudanças em `LaudoVistoria`:**
- **`contrato` passa a ser OBRIGATÓRIO** (confirmado): `contrato = FK(Contrato, on_delete=models.PROTECT, related_name='laudos')` — remover `null=True, blank=True` e trocar `SET_NULL` por `PROTECT`. Assim todo laudo tem locatário derivável e o ponto "laudo sem contrato" deixa de existir.
- Novos campos: `local_assinatura = CharField(200, blank)`, `data_assinatura = DateField(null, blank)`.
- Campo dedicado para o PDF gerado: `documento_gerado = FileField(upload_to='laudos/gerados/', blank=True, null=True, verbose_name='Laudo gerado (PDF)')` (não sobrescreve o `arquivo` de upload manual).

**Métodos de resumo automático em `LaudoVistoria`** (calculado, nunca digitado):
```
def resumo_vistoria(self):
    itens = self.itens.all()
    return {'total': itens.count(),
            'bom':     itens.filter(estado='bom').count(),
            'regular': itens.filter(estado='regular').count(),
            'ruim':    itens.filter(estado='ruim').count()}
def locador_nome(self):   return self.imovel.proprietario.nome
def locatario_nome(self): return self.contrato.inquilino.nome   # contrato agora é obrigatório
```

### 3.4 Migrations
- `makemigrations` → 1 migração de schema (novos models + campos `local_assinatura`/`data_assinatura`/`documento_gerado` em LaudoVistoria + `documento_gerado` em Contrato + `contrato` obrigatório).
- **Atenção — `LaudoVistoria.contrato` NOT NULL:** se houver laudos existentes com `contrato` nulo no `db.sqlite3`, a migração falha. Antes de aplicar: (a) preencher/atribuir um contrato aos laudos órfãos, ou (b) excluí-los. A migração deve ser gerada com um passo de dados (`RunPython`) ou o dado corrigido manualmente antes do `migrate`.
- **Data migration** `00XX_seed_vistoria_catalog.py`: popula `ComodoTemplate`/`ItemVistoriaTemplate` com os 5 cômodos e itens do enunciado (Sala, Cozinha, Quarto, Banheiro, Área externa). Usa `RunPython` com `apps.get_model` (forward + reverse).

---

## 4. Templates de documento (PDF)

xhtml2pdf renderiza um **subconjunto** de HTML/CSS — **não** herda `base.html` (que tem sidebar/JS/Bootstrap CDN e é incompatível). Criar templates standalone com CSS inline simples (tabelas, `@page` para margens).

- `templates/documentos/base_pdf.html` — HTML mínimo autossuficiente: `@page { size:A4; margin:2cm }`, cabeçalho, tipografia; blocks `titulo_doc`/`conteudo`.
- `templates/documentos/contrato_pdf.html` — dados do imóvel, do inquilino (qualificação **condicional PF/PJ**: CPF+comprovante de renda vs CNPJ+contrato social), dia de pagamento, valor, datas início/término; bloco **Observações só se `contrato.observacoes`**.
- `templates/documentos/laudo_pdf.html` — tipo (entrada/saída), imóvel (endereço), locador, locatário, data, responsável; **tabela por cômodo** com itens (estado + observação, observação só se preenchida); **resumo automático** de `resumo_vistoria`; local/data assinatura; assinaturas locador/locatário; lista de testemunhas (nome + CPF).
- `templates/documentos/recibo_pdf.html` — **renderiza só os campos preenchidos** (`{% if %}` por campo) + **somatório** (`recibo.total|brl`).

Reutilizar o filtro `{{ valor|brl }}` (`{% load imoveis_tags %}`) e `|date:"d/m/Y"`.

> **Logo (resolvido):** o usuário adicionou `Shelter_LOGO.jpg` (escuro) e `Shelter_LOGO_white.jpg` (branco) em **`./assets/`** (raiz). O xhtml2pdf renderiza JPG. Passos na execução: (1) **copiar** os JPG para **`static/assets/`** (só o que está em `STATICFILES_DIRS` é resolvido pelo `link_callback`); (2) no cabeçalho dos PDFs (fundo branco) usar a versão **escura** via `<img src="{% static 'assets/Shelter_LOGO.jpg' %}">`.

---

## 5. Forms (`imoveis/forms.py`) + validação de CPF

**Validação de CPF (confirmado):** criar **`imoveis/validators.py`** com `validate_cpf(value)` — implementa o algoritmo dos dígitos verificadores do CPF (aceita com/sem máscara), levanta `ValidationError` se inválido. Aplicar como `validators=[validate_cpf]` nos novos campos de CPF: `Recibo.assinante_cpf` e `TestemunhaLaudo.cpf`. (Opcional: aplicar também a `Inquilino.cpf`; **não** retroativo a dados já existentes para não quebrar registros legados — decidir na execução.)

Seguir convenção `_ctrl`/`_sel`, widgets explícitos.

- **`ReciboForm(ModelForm)`** — todos os campos; datas `DateInput(type=date)`; valores `NumberInput(step=0.01)`. `clean()`: exigir ao menos um valor/campo preenchido; validação de CPF vem do validator do model.
- **`LaudoVistoriaForm`** — adicionar `local_assinatura`, `data_assinatura`; **`contrato` agora obrigatório** (campo required, sem `empty_label` vazio selecionável). Manter `arquivo` (upload manual) opcional, já que o PDF vai para `documento_gerado`.
- **`ItemVistoriaForm` + `ItemVistoriaFormSet`** = `inlineformset_factory(LaudoVistoria, ItemVistoria, extra=0, can_delete=True)` — no `laudo_create`, pré-popular `initial` a partir de `ItemVistoriaTemplate` (agrupado por cômodo), padrão idêntico ao `FiadorFormSet`.
- **`TestemunhaLaudoForm` + `TestemunhaFormSet`** = `inlineformset_factory(LaudoVistoria, TestemunhaLaudo, extra=2, can_delete=True)`.
- Contrato: **sem alteração no form** (dados já capturados; o novo `documento_gerado` é preenchido pela view, não pelo usuário).

---

## 6. Views e URLs

> **Padrão comum:** as views de `create`/`edit` de cada seção, após `form.save()` (e `formset.save()` quando houver), chamam o helper de geração, gravam no `FileField` e **retornam o PDF como resposta** (download automático). A rota `*_gerar_pdf` continua existindo para "Regerar" a partir do detail.

### Contrato (geração stateless, dispara no save)
- Contrato já é criado por `contrato_create`. Ao **salvar** (`contrato_create`/`contrato_edit`), gerar `documentos/contrato_pdf.html`, salvar em **`contrato.documento_gerado`** e baixar. Botão "Regerar PDF" no detail → `contrato_gerar_pdf`.
- URL: `contratos/<int:pk>/gerar-pdf/` name `contrato_gerar_pdf`.

### Laudo (formsets + detail + geração no save)
- Atualizar `laudo_create`/`laudo_edit` para validar/salvar `LaudoVistoriaForm` + `ItemVistoriaFormSet` + `TestemunhaFormSet` juntos (padrão `contrato_create`); **após salvar, gerar e anexar o PDF** em **`laudo.documento_gerado`** e baixar. No create, pré-popular itens do catálogo.
- Nova view `laudo_detail(request, pk)` (hoje não existe) — mostra itens por cômodo, resumo, testemunhas, link do PDF e botão "Regerar".
- URLs: `laudos/<int:pk>/` `laudo_detail`; `laudos/<int:pk>/gerar-pdf/` `laudo_gerar_pdf`.

### Recibo (CRUD completo + geração no save)
- `recibo_create`/`recibo_edit`: **ao salvar**, gerar e anexar o PDF em `recibo.arquivo` e baixar. Demais views `recibo_list/detail/delete` no padrão dos outros módulos + `recibo_gerar_pdf` (regerar).
- URLs: `recibos/`, `recibos/novo/`, `recibos/<int:pk>/`, `recibos/<int:pk>/editar/`, `recibos/<int:pk>/excluir/`, `recibos/<int:pk>/gerar-pdf/`.

### GED
- Atualizar view `documentos` e `templates/ged/documentos.html` para listar `Recibo.arquivo` e laudos gerados.

### Admin (`imoveis/admin.py`)
- Registrar `Recibo`, `ComodoTemplate` (com `TabularInline` de `ItemVistoriaTemplate`), `ItemVistoria`, `TestemunhaLaudo` — permite editar o catálogo de cômodos/itens sem código.

---

## 7. Validação por formulário

- **Contrato:** já garantido pelas constraints do model (todos obrigatórios exceto `observacoes`). Nenhuma validação nova obrigatória; PF/PJ é visual/condicional no template.
- **Recibo:** valores `Decimal ≥ 0`; datas `type=date`; `clean()` exige ≥ 1 campo preenchido; **CPF validado** por `validate_cpf` (`assinante_cpf`).
- **Laudo:** **`contrato` obrigatório**; `estado` obrigatório em cada linha usada de `ItemVistoria`; `data` obrigatória; testemunhas opcionais, mas **CPF (se preenchido) validado** por `validate_cpf`.

---

## 8. Integração com a interface

- **`templates/contratos/contrato_detail.html`** (linhas 8-13): adicionar botão `Regerar Contrato (PDF)` → `contrato_gerar_pdf`.
- **`templates/laudos/laudo_detail.html`** (novo): botão `Regerar Laudo (PDF)`, tabela de itens por cômodo, card de resumo, testemunhas. Atualizar `laudo_list.html` para linkar ao detail. Atualizar `laudo_form.html` para renderizar os dois formsets (grade estado/observação por cômodo; reutilizar padrão de loop de `contrato_form.html`).
- **`templates/recibos/`** (novos): `recibo_list.html`, `recibo_form.html`, `recibo_detail.html` (com botão regerar).
- **`templates/base.html`**: adicionar item de menu **"Recibos"** na seção *Operações* + block `nav_recibos` (seguindo `nav_contratos`/`nav_laudos`).
- **Pós-geração:** ao salvar o formulário o PDF já é baixado automaticamente (`attachment`) e o link passa a aparecer na página de detalhe e no GED (`documentos.html`).

---

## 9. Decisões dos pontos em aberto (resolvidas) + riscos

1. **PDF gerado ✅ campo separado:** grava em `Contrato.documento_gerado` e `LaudoVistoria.documento_gerado` (não sobrescreve o `arquivo` de upload manual). Recibo usa seu próprio `arquivo` (model novo, sem conflito).
2. **Recibo `quantia` ✅:** `quantia` = **valor total recebido**; as parcelas (aluguel/impostos/seguros/condomínio) **compõem** esse total; `somatorio()` soma as parcelas. PDF mostra parcelas + somatório + destaca `quantia` como total.
3. **UI de itens do Laudo (MVP) ✅:** itens do catálogo agrupados por cômodo, `estado` em branco = não vistoriado, só salva os com estado preenchido. "Adicionar cômodo dinâmico" fica como evolução futura.
4. **Logo ✅:** usar `Shelter_LOGO.jpg` (escuro) — copiar de `./assets/` para `static/assets/` e referenciar via `{% static %}` no cabeçalho dos PDFs (ver §4).
5. **Laudo `contrato` ✅ obrigatório:** deixa de existir laudo sem contrato; locatário sempre derivável. Requer cuidado na migração (ver §3.4).
6. **CPF ✅ validado:** `imoveis/validators.py::validate_cpf` aplicado a `Recibo.assinante_cpf` e `TestemunhaLaudo.cpf` (ver §5).

**Riscos remanescentes:**
- **Migração `LaudoVistoria.contrato` NOT NULL:** laudos órfãos existentes quebram o `migrate` — corrigir dados antes (ver §3.4).
- **Compatibilidade:** venv está com Django 6.0.6 (requirements diz `<7.0`); `xhtml2pdf` puxa `reportlab` como dependência transitiva. Validar `manage.py check` após instalar.
- **CPF legado:** se aplicar `validate_cpf` também a `Inquilino.cpf`, registros já cadastrados com CPF inválido passam a falhar na edição — por isso a aplicação retroativa fica **opcional** e não é o padrão.

---

## 10. Arquivos a criar/modificar (ordem de execução)

1. `requirements.txt` — adicionar `xhtml2pdf`; instalar no venv (`venv/Scripts/pip install xhtml2pdf`).
2. **Copiar** `assets/Shelter_LOGO.jpg` e `assets/Shelter_LOGO_white.jpg` para `static/assets/` (para o `{% static %}`/`link_callback` resolver).
3. `imoveis/validators.py` — `validate_cpf` (algoritmo dos dígitos verificadores).
4. `imoveis/models.py` — `Recibo`, `ComodoTemplate`, `ItemVistoriaTemplate`, `ItemVistoria`, `TestemunhaLaudo`; em `LaudoVistoria`: `contrato` obrigatório + `local_assinatura`/`data_assinatura`/`documento_gerado` + métodos; em `Contrato`: `documento_gerado`.
5. `imoveis/migrations/` — **corrigir laudos órfãos** (sem contrato) → `makemigrations` (schema) + data migration `seed_vistoria_catalog`.
6. `imoveis/pdf.py` — helpers pisa + `link_callback` + `gerar_e_anexar`.
7. `imoveis/forms.py` — `ReciboForm`, extensão de `LaudoVistoriaForm` (contrato required), `ItemVistoria`/`Testemunha` forms + formsets.
8. `imoveis/views.py` — recibo CRUD + `*_gerar_pdf` (3), `laudo_detail`, laudo create/edit com formsets, `documentos` atualizado.
9. `imoveis/urls.py` — novas rotas.
10. `imoveis/admin.py` — registrar novos models + inline do catálogo.
11. Templates: `documentos/base_pdf.html`, `documentos/contrato_pdf.html`, `documentos/laudo_pdf.html`, `documentos/recibo_pdf.html`; `recibos/recibo_list|form|detail.html`; `laudos/laudo_detail.html` + update `laudo_form.html`/`laudo_list.html`; update `contratos/contrato_detail.html`, `ged/documentos.html`, `base.html`.
12. Verificação (§11).

---

## 11. Verificação (end-to-end)

```bash
venv/Scripts/python manage.py makemigrations
venv/Scripts/python manage.py migrate
venv/Scripts/python manage.py check
venv/Scripts/python manage.py runserver
```
Testes manuais no navegador (logado):
- **Contrato:** salvar um contrato → PDF baixa na hora, campos PF vs PJ corretos, Observações aparece só se preenchida, e o link surge no GED.
- **Laudo:** criar laudo, preencher estados de vários itens em cômodos distintos + testemunhas → ao salvar o PDF baixa; o detail mostra **resumo automático** correto (ex: "32 itens — 32 bom, 0 regular, 0 ruim") e a tabela por cômodo/assinaturas confere.
- **Recibo:** criar recibo preenchendo **só alguns** valores → PDF mostra **apenas os campos preenchidos** + **somatório** correto.
- `venv/Scripts/python manage.py test imoveis` (garantir que signals/migrations não quebraram).