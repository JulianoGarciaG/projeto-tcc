# CLAUDE.md

Guia do Claude Code (claude.ai/code) para este repositório.

> Sistema Integrado de Gestão Imobiliária (GED e BI) — "Shelter"

---

## Comandos essenciais

Tudo roda pelo Python do virtualenv em `venv/Scripts/` (Windows).

```bash
venv/Scripts/python manage.py runserver          # dev server
venv/Scripts/python manage.py makemigrations
venv/Scripts/python manage.py migrate
venv/Scripts/python manage.py check              # integridade
venv/Scripts/python manage.py test imoveis       # suíte (98 testes)
venv/Scripts/python manage.py test imoveis.tests.NomeDaClasse   # teste único
venv/Scripts/python manage.py createsuperuser
```

---

## Arquitetura

### Stack
- **Backend:** Django 6.0, SQLite (dev) / MySQL (prod) — ver [Configuração](#configuração).
- **Frontend:** Templates Django + CSS estático, **sem build system**. Libs via CDN em `base.html`: Bootstrap 5.3, Bootstrap Icons, **Flatpickr** (datepicker dd/mm/yyyy), **IMask** (máscaras), **Chart.js** (dashboard). Init de máscaras/datepickers em `static/js/masks.js` por atributos `data-flatpickr` / `data-mask="telefone|moeda"`.
- **PDF:** `xhtml2pdf` renderiza os templates de `templates/documentos/`.
- **Uploads:** `Pillow` (imagens) + PDFs; storage plugável via `STORAGES` (ver convenções).

### Estrutura de diretórios
- `core/` — configuração Django (`settings.py`, `urls.py`, `wsgi.py`).
- `imoveis/` — **único app** (models, views, urls, forms, validators, signals, admin, `pdf.py`).
- `templates/` — por módulo: `imoveis/`, `contratos/`, `financeiro/`, `ged/`, `laudos/`, `proprietarios/`, `inquilinos/`, `recibos/` + `documentos/` (PDFs).
- `static/css/` — `shelter.css` (estilo global atual). `custom.css` está **órfão** (não referenciado).
- `static/js/` — `masks.js`, `theme.js` (dark mode), `imovel-view-toggle.js`.
- `media/` — uploads (fotos, PDFs gerados/anexados).

### Modelos (`imoveis/models.py`) — referência rápida
Detalhamento completo de campos/relacionamentos em **[docs/03_modelagem_dados.md](docs/03_modelagem_dados.md)**.

| Modelo | Papel / gotcha |
|---|---|
| `Proprietario` / `Inquilino` / `Fiador` | Partes; CPF/CNPJ/RG/telefone validados (ver convenções). `Inquilino.faixa_renda` em faixas de R$. |
| `Imovel` | `numero`/`complemento`; status `vago`/`ocupado` via **signal**. **Não tem** `valor_aluguel` (vem do contrato ativo). |
| `FotoImovel` | Fotos do imóvel. |
| `Contrato` | Imóvel ↔ Inquilino. 4 docs GED (`comprovante_renda`/`contrato_social`/`recibo_chaves`/`comprovante_anual`) são anexados no **detail** via `contrato_anexar_documento`, não no form. |
| `LaudoVistoria` | Tipos `entrada`/`saida`; `contrato` **obrigatório** (`PROTECT`), select dependente do imóvel (`contratos_por_imovel_json`). `arquivo` = anexo assinado (upload só no detail). |
| `ComodoTemplate` / `ItemVistoriaTemplate` | Catálogo do checklist (seed migração 0004: 5 cômodos, 32 itens). |
| `ItemVistoria` / `TestemunhaLaudo` | Itens vistoriados (bom/regular/ruim) e testemunhas de um laudo. |
| `Recibo` | `imovel`/`contrato` obrigatórios (`PROTECT`); período `periodo_inicio`/`periodo_fim`. |
| `Lancamento` | **Único** módulo financeiro (`Entrada`/`Saida` removidos — não recriar). |
| `Notificacao` / `RenovacaoContrato` / `Distrato` | Compliance, renovações e distratos. |
| `DocumentoGerado` | **Versão imutável** de PDF (GED versionado). FKs opcionais `contrato`/`laudo`/`recibo` (uma via `CheckConstraint`), `numero_versao` sequencial por origem, `sha256`, `gerado_por`. Campos legados `*.documento_gerado`/`Recibo.arquivo` são **espelho** da última versão. |

### Signal crítico (`imoveis/signals.py`)
`Imovel.status` é recalculado por `post_save`/`post_delete` de `Contrato` (há contrato `ativo` → `ocupado`, senão `vago`). Registrado em `imoveis/apps.py`. Regras de negócio completas em **[docs/04_regras_de_negocio.md](docs/04_regras_de_negocio.md)**.

---

## Convenções obrigatórias

- **PDF nunca é gerado ao salvar** — create/edit fazem redirect + toast (PRG); só as views `*_gerar_pdf` geram/baixam PDF.
- **GED é a fonte de verdade dos PDFs** — cada geração cria uma versão **imutável** em `DocumentoGerado` (`save()` bloqueia updates). Gerar sempre via `imoveis/pdf.py:gerar_e_anexar(instance, ..., usuario=request.user)`; nunca gravar direto no FileField legado. Para "corrigir", gerar outra versão — não editar/deletar.
- **Uploads via storage `default` do `STORAGES`** — plugável por `STORAGE_BACKEND` no `.env`. Não instalar `boto3`/`django-storages` nem ativar o backend `s3` sem seguir o passo a passo comentado em `core/settings.py`.
- **Campos de data** usam `_date_widget()` (`imoveis/forms.py`, Flatpickr dd/mm/yyyy); **moeda** usa `_moeda_widget()` + `localized_fields` (aceita "1500,00"; **sem** separador de milhar — `USE_THOUSAND_SEPARATOR` fica desligado).
- **Validadores** (`imoveis/validators.py`): `validate_cpf`, `validate_cnpj`, `validate_cpf_cnpj`, `validate_rg`, `validate_rg_cpf` (`Fiador.rg_cpf`), `validate_telefone` (`Proprietario`/`Inquilino.telefone`). **Reutilizar, não duplicar.**
- **Checklist do laudo**: laudo novo exige `item_vistoria_formset_factory(extra=len(catalogo))` — `extra=0` renderiza 0 linhas e o checklist some.
- **Templates de PDF (xhtml2pdf 0.2.17)**: o motor **ignora `text-transform`** e **não suporta `margin: ... auto ...`** — textos estáticos em CAIXA ALTA literal (ou `|upper`), centralizar com `<table align="center">`; `border`/`padding` de cartão vão na `<td>` (não em `<div>` com múltiplos filhos block-level). Detalhes em [docs/07_design_ui_ux.md](docs/07_design_ui_ux.md) §17.
- **Camada visual**: estilo global em `static/css/shelter.css` (não `custom.css`). Usar tokens (`var(--brand)`/`var(--ink)`/`var(--surface)`/pares `--x`/`--x-bg`), nunca hex da paleta antiga. Overrides de Bootstrap redefinem as vars `--bs-*` e o `<link>` do `shelter.css` vem **depois** do bundle. Todo estilo novo funciona nos dois temas (`data-theme` no `<html>`) — testar claro **e** escuro.
- **Encoding (Windows)**: nunca editar templates com `Get-Content`/`Set-Content` do PowerShell 5.1 (corrompe UTF-8) — usar o Edit tool.

---

## Configuração

- **Banco** (`.env`): `DB_ENGINE=django.db.backends.sqlite3` (dev) ou `django.db.backends.mysql` + `DB_NAME`/`DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT` (prod).
- **Storage** (`.env`): `STORAGE_BACKEND=filesystem` (default) / `s3` (preparado, não ativado).
- **Auth**: padrão Django; todas as views com `@login_required`. Rotas `/login/`, `/logout/`; login redireciona para `/` (dashboard).
- **Dashboard (BI)**: agrega `Lancamento` em gráficos de barras/pizza (Chart.js lê CSS vars e redesenha no toggle de tema).

---

## Documentação

Referência viva do sistema em `/docs/`:

| Arquivo | Conteúdo |
|---|---|
| [01_visao_geral.md](docs/01_visao_geral.md) | Sistema, público-alvo, stack, módulos, requisitos funcionais |
| [03_modelagem_dados.md](docs/03_modelagem_dados.md) | Entidades, campos, relacionamentos, caminhos de upload |
| [04_regras_de_negocio.md](docs/04_regras_de_negocio.md) | Signals, automações, restrições, GED, dashboard, acesso |
| [07_design_ui_ux.md](docs/07_design_ui_ux.md) | Paleta/tokens, tipografia, layout, componentes, responsividade, dark mode, PDFs |

### Histórico de rodadas (o "porquê" de cada mudança)
O detalhamento de cada entrega vive nos planos, não aqui:

| Rodada / entrega | Onde |
|---|---|
| Geração de PDFs (Rodada 1) | [docs/PLANO_GERACAO_DOCUMENTOS.md](docs/PLANO_GERACAO_DOCUMENTOS.md) |
| Ajustes (Rodada 2) | [docs/PLANO_AJUSTES_RODADA2.md](docs/PLANO_AJUSTES_RODADA2.md) |
| Validação/visualização + sidebar/logo (Rodada 3) | `planner-docs/melhorias-validacao-visualizacao-documentos/`, `planner-docs/remover-colapso-sidebar-e-ajustar-logo/` |
| Redesign dos PDFs + GED versionado (Rodada 4) | `planner-docs/redesign-pdfs-documentos-gerados/` |
| Correção visual dos PDFs | `planner-docs/fix-visual-pdfs-gerados/` |
| Redesign Visual UI (paleta/tokens, dark mode, `shelter.css`) | `planner-docs/redesign-ui-shelter/` |
| Contrato jurídico | `planner-docs/contrato-juridico-completo/` |
