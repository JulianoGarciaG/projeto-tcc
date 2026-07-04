# Plano de Implementação — Geração Automática de Documentos PDF

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

### 3.1 Contrato — sem novo model
Nenhuma mudança de schema necessária. A qualificação PF vs PJ no documento sai de `Inquilino.cpf`/`Inquilino.cnpj`/`Inquilino.qualificacao` condicionalmente por `Contrato.tipo_contrato`.

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
    quantia           = DecimalField(10,2, null, blank, 'Quantia de')
    assinante_nome    = CharField(200, blank)
    assinante_cpf     = CharField(14, blank)
    data_assinatura   = DateField(null, blank)
    arquivo           = FileField(upload_to='recibos/', blank, null)  # PDF gerado
    criado_em         = DateTimeField(auto_now_add=True)

    def total(self):  # "somatório dos valores inseridos"
        return sum(v for v in [valor_aluguel, valor_impostos, valor_seguros, valor_condominio] if v)
```
> Ponto aberto: `quantia` ("Quantia de") — tratado como campo opcional separado; o somatório exibido = soma dos 4 componentes. Confirmar (ver §9).

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
    cpf   = CharField(14, blank)
```

**Novos campos em `LaudoVistoria`:**
- `local_assinatura = CharField(200, blank)`
- `data_assinatura  = DateField(null, blank)`

**Métodos de resumo automático em `LaudoVistoria`** (calculado, nunca digitado):
```
def resumo_vistoria(self):
    itens = self.itens.all()
    return {'total': itens.count(),
            'bom':     itens.filter(estado='bom').count(),
            'regular': itens.filter(estado='regular').count(),
            'ruim':    itens.filter(estado='ruim').count()}
def locador_nome(self):   return self.imovel.proprietario.nome
def locatario_nome(self): return self.contrato.inquilino.nome if self.contrato else ''
```

### 3.4 Migrations
- `makemigrations` → 1 migração de schema (novos models + 2 campos em LaudoVistoria).
- **Data migration** `00XX_seed_vistoria_catalog.py`: popula `ComodoTemplate`/`ItemVistoriaTemplate` com os 5 cômodos e itens do enunciado (Sala, Cozinha, Quarto, Banheiro, Área externa). Usa `RunPython` com `apps.get_model` (forward + reverse).

---

## 4. Templates de documento (PDF)

xhtml2pdf renderiza um **subconjunto** de HTML/CSS — **não** herda `base.html` (que tem sidebar/JS/Bootstrap CDN e é incompatível). Criar templates standalone com CSS inline simples (tabelas, `@page` para margens).

- `templates/documentos/base_pdf.html` — HTML mínimo autossuficiente: `@page { size:A4; margin:2cm }`, cabeçalho, tipografia; blocks `titulo_doc`/`conteudo`.
- `templates/documentos/contrato_pdf.html` — dados do imóvel, do inquilino (qualificação **condicional PF/PJ**: CPF+comprovante de renda vs CNPJ+contrato social), dia de pagamento, valor, datas início/término; bloco **Observações só se `contrato.observacoes`**.
- `templates/documentos/laudo_pdf.html` — tipo (entrada/saída), imóvel (endereço), locador, locatário, data, responsável; **tabela por cômodo** com itens (estado + observação, observação só se preenchida); **resumo automático** de `resumo_vistoria`; local/data assinatura; assinaturas locador/locatário; lista de testemunhas (nome + CPF).
- `templates/documentos/recibo_pdf.html` — **renderiza só os campos preenchidos** (`{% if %}` por campo) + **somatório** (`recibo.total|brl`).

Reutilizar o filtro `{{ valor|brl }}` (`{% load imoveis_tags %}`) e `|date:"d/m/Y"`.

> Logo: `static/assets/Shelter_LOGO_white.svg` é **SVG — não suportado pelo xhtml2pdf**. Usar um PNG do logo (ou cabeçalho em texto) nos PDFs (ver §9).

---

## 5. Forms (`imoveis/forms.py`)

Seguir convenção `_ctrl`/`_sel`, widgets explícitos.

- **`ReciboForm(ModelForm)`** — todos os campos; datas `DateInput(type=date)`; valores `NumberInput(step=0.01)`. `clean()`: exigir ao menos um valor/campo preenchido.
- **`LaudoVistoriaForm`** — adicionar `local_assinatura`, `data_assinatura`. Manter `arquivo` (upload manual) opcional, já que agora o PDF é gerado.
- **`ItemVistoriaForm` + `ItemVistoriaFormSet`** = `inlineformset_factory(LaudoVistoria, ItemVistoria, extra=0, can_delete=True)` — no `laudo_create`, pré-popular `initial` a partir de `ItemVistoriaTemplate` (agrupado por cômodo), padrão idêntico ao `FiadorFormSet`.
- **`TestemunhaLaudoForm` + `TestemunhaFormSet`** = `inlineformset_factory(LaudoVistoria, TestemunhaLaudo, extra=2, can_delete=True)`.
- Contrato: **sem alteração** (dados já capturados).

---

## 6. Views e URLs

> **Padrão comum:** as views de `create`/`edit` de cada seção, após `form.save()` (e `formset.save()` quando houver), chamam o helper de geração, gravam no `FileField` e **retornam o PDF como resposta** (download automático). A rota `*_gerar_pdf` continua existindo para "Regerar" a partir do detail.

### Contrato (geração stateless, dispara no save)
- Contrato já é criado por `contrato_create`. Ao **salvar** (`contrato_create`/`contrato_edit`), gerar `documentos/contrato_pdf.html`, salvar em `contrato.arquivo` e baixar. Botão "Regerar PDF" no detail → `contrato_gerar_pdf`.
- URL: `contratos/<int:pk>/gerar-pdf/` name `contrato_gerar_pdf`.

### Laudo (formsets + detail + geração no save)
- Atualizar `laudo_create`/`laudo_edit` para validar/salvar `LaudoVistoriaForm` + `ItemVistoriaFormSet` + `TestemunhaFormSet` juntos (padrão `contrato_create`); **após salvar, gerar e anexar o PDF** em `laudo.arquivo` e baixar. No create, pré-popular itens do catálogo.
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
- **Recibo:** valores `Decimal ≥ 0`; datas `type=date`; `clean()` exige ≥ 1 campo preenchido. CPF: manter placeholder-mask como o resto do projeto (sem validação estrita — ver §9).
- **Laudo:** `estado` obrigatório em cada linha usada de `ItemVistoria`; `data` obrigatória; testemunhas opcionais. Convenção do projeto = sem `clean_*` estrito de CPF.

---

## 8. Integração com a interface

- **`templates/contratos/contrato_detail.html`** (linhas 8-13): adicionar botão `Regerar Contrato (PDF)` → `contrato_gerar_pdf`.
- **`templates/laudos/laudo_detail.html`** (novo): botão `Regerar Laudo (PDF)`, tabela de itens por cômodo, card de resumo, testemunhas. Atualizar `laudo_list.html` para linkar ao detail. Atualizar `laudo_form.html` para renderizar os dois formsets (grade estado/observação por cômodo; reutilizar padrão de loop de `contrato_form.html`).
- **`templates/recibos/`** (novos): `recibo_list.html`, `recibo_form.html`, `recibo_detail.html` (com botão regerar).
- **`templates/base.html`**: adicionar item de menu **"Recibos"** na seção *Operações* + block `nav_recibos` (seguindo `nav_contratos`/`nav_laudos`).
- **Pós-geração:** ao salvar o formulário o PDF já é baixado automaticamente (`attachment`) e o link passa a aparecer na página de detalhe e no GED (`documentos.html`).

---

## 9. Riscos, pontos em aberto e confirmações necessárias

1. **`arquivo` sobrescrito:** gravar o PDF gerado em `Contrato.arquivo`/`LaudoVistoria.arquivo` **sobrescreve** um upload manual anterior no mesmo campo. Alternativa: campo dedicado `documento_gerado`. → *Confirmar se pode sobrescrever ou se prefere campo separado.*
2. **Recibo `quantia` vs somatório:** "Quantia de" tratado como campo opcional separado; somatório = soma de aluguel+impostos+seguros+condomínio. → *Confirmar semântica.*
3. **UI de itens do Laudo (MVP):** o formulário mostra todos os itens do catálogo agrupados por cômodo, cada um com `estado` (select, em branco = não vistoriado) + observação; só salva os com estado preenchido. Um "adicionar cômodo dinamicamente" via JS fica como evolução. → *Confirmar se o MVP atende.*
4. **Logo em SVG:** `Shelter_LOGO_white.svg` não renderiza no xhtml2pdf → usar PNG ou cabeçalho textual nos PDFs. → *Fornecer um PNG do logo, ou aceitar cabeçalho em texto.*
5. **Laudo sem contrato vinculado:** `contrato` é opcional → sem locatário derivável. Deixar em branco no PDF ou adicionar campos-override de texto livre? → *Confirmar comportamento.*
6. **CPF/valores:** projeto não tem validação estrita de CPF (só placeholder). Manter assim ou adicionar validação? → *Confirmar.*
7. **Compatibilidade:** venv está com Django 6.0.6 (requirements diz `<7.0`); `xhtml2pdf` puxa `reportlab` como dependência transitiva. Validar `manage.py check` após instalar.

---

## 10. Arquivos a criar/modificar (ordem de execução)

1. `requirements.txt` — adicionar `xhtml2pdf`; instalar no venv (`venv/Scripts/pip install xhtml2pdf`).
2. `imoveis/models.py` — `Recibo`, `ComodoTemplate`, `ItemVistoriaTemplate`, `ItemVistoria`, `TestemunhaLaudo`; +campos e métodos em `LaudoVistoria`.
3. `imoveis/migrations/` — `makemigrations` (schema) + data migration `seed_vistoria_catalog`.
4. `imoveis/pdf.py` — helpers pisa + `link_callback`.
5. `imoveis/forms.py` — `ReciboForm`, extensão de `LaudoVistoriaForm`, `ItemVistoria`/`Testemunha` forms + formsets.
6. `imoveis/views.py` — recibo CRUD + `*_gerar_pdf` (3), `laudo_detail`, laudo create/edit com formsets, `documentos` atualizado.
7. `imoveis/urls.py` — novas rotas.
8. `imoveis/admin.py` — registrar novos models + inline do catálogo.
9. Templates: `documentos/base_pdf.html`, `documentos/contrato_pdf.html`, `documentos/laudo_pdf.html`, `documentos/recibo_pdf.html`; `recibos/recibo_list|form|detail.html`; `laudos/laudo_detail.html` + update `laudo_form.html`/`laudo_list.html`; update `contratos/contrato_detail.html`, `ged/documentos.html`, `base.html`.
10. Verificação (§11).

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
