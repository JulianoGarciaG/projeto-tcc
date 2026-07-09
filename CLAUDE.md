# CLAUDE.md

Guia do Claude Code (claude.ai/code) para este repositório.

> Sistema Integrado de Gestão Imobiliária (GED e BI) — "Shelter"

Este arquivo é lido no início de **toda** janela de trabalho. Mantenha-o enxuto: apenas o que é necessário na maioria das tarefas e as travas que evitam erro. Detalhe pertence a `/docs` (referenciado, nunca replicado). Critérios de manutenção no fim.

---

## Comandos essenciais

Tudo roda pelo Python do virtualenv em `venv/Scripts/` (Windows).

```bash
venv/Scripts/python manage.py runserver          # dev server
venv/Scripts/python manage.py makemigrations
venv/Scripts/python manage.py migrate
venv/Scripts/python manage.py check              # integridade
venv/Scripts/python manage.py test imoveis       # suíte completa
venv/Scripts/python manage.py test imoveis.tests.NomeDaClasse   # teste único
venv/Scripts/python manage.py createsuperuser
```

---

## Fluxo de trabalho

Tarefa nova de implementação → rode a skill roteador antes de codar (decide entre prompt direto, Plan Mode + /model opusplan, ou o subagente Planner conforme o escopo real).
Ao concluir → rode a skill validate-implementation (roda check/migrations/test reais e confere o diff contra os invariantes deste arquivo).

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
- `static/css/` — `shelter.css` (estilo global; **é o único** — não usar `custom.css`).
- `static/js/` — `masks.js`, `theme.js` (dark mode), `imovel-view-toggle.js`.
- `media/` — uploads (fotos, PDFs gerados/anexados).

### Modelos (`imoveis/models.py`)
Entidades: `Proprietario`, `Inquilino`, `Fiador`, `Imovel`, `FotoImovel`, `Contrato`, `LaudoVistoria`, `ComodoTemplate`, `ItemVistoriaTemplate`, `ItemVistoria`, `TestemunhaLaudo`, `Recibo`, `Lancamento`, `Notificacao`, `RenovacaoContrato`, `Distrato`, `DocumentoGerado`.

Campos, relacionamentos e caminhos de upload completos em **[docs/02_modelagem_dados.md](docs/02_modelagem_dados.md)**. Abaixo, apenas os modelos com armadilhas que você precisa conhecer **antes** de mexer:

| Modelo | Gotcha |
|---|---|
| `Proprietario` / `Inquilino` / `Fiador` | CPF/CNPJ/RG/telefone validados (ver convenções). `Inquilino.faixa_renda` em faixas de R$. `Fiador` tem `rg_cpf` legado **e** `rg`/`cpf`/`endereco`/`conjuge_*` discretos (qualificação jurídica completa), todos opcionais. |
| `Imovel` | Status `vago`/`ocupado` via **signal**. **Não tem** `valor_aluguel` (vem do contrato ativo). |
| `Contrato` | 4 docs GED (`comprovante_renda`/`contrato_social`/`recibo_chaves`/`comprovante_anual`) anexados no **detail** via `contrato_anexar_documento`, não no form. **O locador exibido no PDF gerado não é `imovel.proprietario`** — é sempre `settings.SHELTER_LOCADOR` (dados fixos da administradora); o `Proprietario` cadastrado continua normal no resto do sistema. `finalidade`/`local_assinatura`/`data_assinatura` alimentam o PDF jurídico. |
| `LaudoVistoria` | `contrato` **obrigatório** (`PROTECT`), select dependente do imóvel (`contratos_por_imovel_json`). `arquivo` = anexo assinado (upload só no detail). |
| `ItemVistoriaTemplate` | Catálogo do checklist semeado na migração 0004 (5 cômodos, 32 itens). |
| `Recibo` | `imovel`/`contrato` obrigatórios (`PROTECT`); período `periodo_inicio`/`periodo_fim`. |
| `Lancamento` | **Único** módulo financeiro (`Entrada`/`Saida` removidos — **não recriar**). |
| `DocumentoGerado` | **Versão imutável** de PDF (GED versionado). FKs opcionais `contrato`/`laudo`/`recibo` (uma via `CheckConstraint`), `numero_versao` sequencial por origem, `sha256`, `gerado_por`. Campos legados `*.documento_gerado`/`Recibo.arquivo` são **espelho** da última versão. Detalhes em **[docs/05_ged_documentos_versionados.md](docs/05_ged_documentos_versionados.md)**. |

### Signal crítico (`imoveis/signals.py`)
`Imovel.status` é recalculado por `post_save`/`post_delete` de `Contrato` (há contrato `ativo` → `ocupado`, senão `vago`). Registrado em `imoveis/apps.py`. Regras de negócio completas em **[docs/03_regras_de_negocio.md](docs/03_regras_de_negocio.md)**.

---

## Convenções obrigatórias

- **PDF nunca é gerado ao salvar** — create/edit fazem redirect + toast (PRG); só as views `*_gerar_pdf` geram/baixam PDF.
- **GED é a fonte de verdade dos PDFs** — cada geração cria uma versão **imutável** em `DocumentoGerado` (`save()` bloqueia updates). Gerar sempre via `imoveis/pdf.py:gerar_e_anexar(instance, ..., usuario=request.user)`; nunca gravar direto no FileField legado. Para "corrigir", gerar outra versão — não editar/deletar.
- **Uploads via storage `default` do `STORAGES`** — plugável por `STORAGE_BACKEND` no `.env`. Não instalar `boto3`/`django-storages` nem ativar o backend `s3` sem seguir o passo a passo comentado em `core/settings.py`.
- **Campos de data** usam `_date_widget()` (`imoveis/forms.py`, Flatpickr dd/mm/yyyy); **moeda** usa `_moeda_widget()` + `localized_fields` (aceita "1500,00"; **sem** separador de milhar — `USE_THOUSAND_SEPARATOR` fica desligado).
- **Validadores** (`imoveis/validators.py`): `validate_cpf`, `validate_cnpj`, `validate_cpf_cnpj`, `validate_rg`, `validate_rg_cpf` (`Fiador.rg_cpf`), `validate_telefone` (`Proprietario`/`Inquilino.telefone`). **Reutilizar, não duplicar.**
- **Checklist do laudo**: laudo novo exige `item_vistoria_formset_factory(extra=len(catalogo))` — `extra=0` renderiza 0 linhas e o checklist some.
- **Templates de PDF (xhtml2pdf 0.2.17)**: o motor **ignora `text-transform`** e **não suporta `margin: ... auto ...`** — textos estáticos em CAIXA ALTA literal (ou `|upper`), centralizar com `<table align="center">`; `border`/`padding` de cartão vão na `<td>` (não em `<div>` com múltiplos filhos block-level). Detalhes em [docs/04_design_ui_ux.md](docs/04_design_ui_ux.md) §17.
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
| [02_modelagem_dados.md](docs/02_modelagem_dados.md) | Entidades, campos, relacionamentos, caminhos de upload |
| [03_regras_de_negocio.md](docs/03_regras_de_negocio.md) | Signals, automações, restrições, dashboard, acesso |
| [04_design_ui_ux.md](docs/04_design_ui_ux.md) | Paleta/tokens, tipografia, layout, componentes, responsividade, dark mode, PDFs |
| [05_ged_documentos_versionados.md](docs/05_ged_documentos_versionados.md) | `DocumentoGerado`, versionamento de PDFs, storage plugável (S3-ready) |

Histórico de entregas e o "porquê" de cada rodada (planos por rodada, mapeados aos diretórios `planner-docs/`): **[docs/historico_entregas.md](docs/historico_entregas.md)**.

---

## Manutenção deste arquivo

CLAUDE.md é o prefixo imutável lido em toda janela; cada linha é paga muitas vezes. Antes de adicionar algo, verifique se passa nos quatro testes:

1. **Frequência** — é necessário na *maioria* das tarefas? Se for específico de um subsistema, vai para `/docs` e é referenciado aqui.
2. **Estabilidade** — é estável? Fatos voláteis (contagens, "rodada atual", changelog) desatualizam e poluem o cache; movê-los para `/docs`.
3. **Prevenção de erro** — sua violação causa bug ou retrabalho? Invariantes e armadilhas ficam aqui mesmo se forem de nicho, porque o custo do erro supera o custo dos tokens.
4. **Não-duplicação** — já existe em `/docs`? Então referencie, não copie.

Atualize CLAUDE.md quando um **invariante** mudar (nova convenção, novo footgun, comando alterado, nova estrutura de topo) — **não** a cada feature entregue (isso vive nos planos/histórico). Durante a implementação de uma feature, trate-o como imutável.