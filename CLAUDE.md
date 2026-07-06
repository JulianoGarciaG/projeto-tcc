# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Sistema Integrado de Gestão Imobiliária (GED e BI) — "Shelter"

---

## Comandos essenciais

Todos os comandos usam o Python do virtualenv em `venv/Scripts/` (Windows).

```bash
# Servidor de desenvolvimento
venv/Scripts/python manage.py runserver

# Migrações
venv/Scripts/python manage.py makemigrations
venv/Scripts/python manage.py migrate

# Verificação de integridade
venv/Scripts/python manage.py check

# Testes
venv/Scripts/python manage.py test imoveis
venv/Scripts/python manage.py test imoveis.tests.NomeDaClasse  # teste único

# Criar superusuário
venv/Scripts/python manage.py createsuperuser
```

---

## Arquitetura

### Stack
- **Backend:** Django 6.0 com SQLite (dev)
- **Frontend:** Templates Django + CSS estático — sem build system. Libs via CDN em `base.html`: Bootstrap 5.3, Bootstrap Icons, **Flatpickr** (datepicker dd/mm/yyyy) e **IMask** (máscaras) — init automática em `static/js/masks.js` por atributos `data-flatpickr` / `data-mask="telefone|moeda"`
- **PDF:** `xhtml2pdf` renderiza os templates de `templates/documentos/` (contrato, laudo, recibo)
- **Uploads:** `Pillow` para imagens, PDFs salvos em `media/`

### Estrutura de diretórios relevante
- `core/` — configuração Django (`settings.py`, `urls.py`, `wsgi.py`)
- `imoveis/` — único app do projeto (models, views, urls, forms, validators, signals, admin)
- `templates/` — templates globais por módulo (`imoveis/`, `contratos/`, `financeiro/`, `ged/`, `laudos/`, `proprietarios/`, `inquilinos/`, `recibos/`, `documentos/` = PDFs)
- `static/css/` — estilos globais (`custom.css`)
- `static/js/` — `masks.js` (init de máscaras e datepickers)
- `media/` — uploads de usuário (fotos, PDFs gerados/anexados)

### Modelos principais (`imoveis/models.py`)
| Modelo | Papel |
|---|---|
| `Proprietario` | Dono do imóvel (`cpf_cnpj` validado) |
| `Imovel` | Imóvel com `numero`/`complemento` e status `vago`/`ocupado` (gerenciado por signal); **não tem** `valor_aluguel` — o valor vem do contrato ativo |
| `FotoImovel` | Fotos vinculadas ao imóvel |
| `Inquilino` | Locatário (`faixa_renda` em faixas de R$, não mais em salários mínimos; CPF/CNPJ/RG/telefone validados) |
| `Contrato` | Contrato de locação (Imovel ↔ Inquilino); PDF gerado em `documento_gerado`; documentos GED (`comprovante_renda`/`contrato_social`/`recibo_chaves`/`comprovante_anual`) anexados individualmente pela tela de detalhe via `contrato_anexar_documento` (não fazem parte do form de criação/edição) |
| `Fiador` | Fiadores do contrato (`rg_cpf` validado) |
| `LaudoVistoria` | Laudo de vistoria (tipos `entrada`/`saida`); `contrato` é **obrigatório** (`PROTECT`) e o select é dependente do imóvel escolhido (endpoint `contratos_por_imovel_json`); `documento_gerado` = PDF do sistema, `arquivo` = anexo do laudo assinado (upload só no detail) |
| `ComodoTemplate` / `ItemVistoriaTemplate` | Catálogo do checklist de vistoria (seed na migração 0004: 5 cômodos, 32 itens) |
| `ItemVistoria` | Itens vistoriados de um laudo (estado bom/regular/ruim) |
| `TestemunhaLaudo` | Testemunhas do laudo |
| `Recibo` | Recibo de pagamento; `imovel`/`contrato` obrigatórios (`PROTECT`), período com `periodo_inicio`/`periodo_fim` |
| `Lancamento` | Lançamento financeiro (único módulo financeiro — `Entrada`/`Saida` foram removidos na Rodada 2; não recriar) |
| `Notificacao` | Notificações de compliance |
| `RenovacaoContrato` | Renovações de contrato |
| `Distrato` | Distratos (rescisões) |
| `DocumentoGerado` | **Versão imutável** de PDF gerado (GED versionado, Rodada 4); 3 FKs opcionais (`contrato`/`laudo`/`recibo`, uma preenchida via `CheckConstraint`), `numero_versao` sequencial por origem, `sha256`, `gerado_por`; `upload_to` = `ged/{tipo}/{origem_pk}/v{numero_versao}/`; campos legados `*.documento_gerado`/`Recibo.arquivo` são espelho da última versão |

### Signal crítico (`imoveis/signals.py`)
`Imovel.status` é atualizado automaticamente via `post_save`/`post_delete` em `Contrato`. Sempre que um contrato é criado, alterado ou excluído, o sistema verifica se há contratos `ativo` vinculados ao imóvel e define o status como `ocupado` ou `vago`. O signal é registrado em `imoveis/apps.py`.

---

## ESTADO ATUAL

### Consolidado
- **Rodada 1** (`PLANO_GERACAO_DOCUMENTOS.md`): geração de PDF para Contrato/Laudo/Recibo (xhtml2pdf), models `Recibo`/`ComodoTemplate`/`ItemVistoriaTemplate`/`ItemVistoria`/`TestemunhaLaudo`, CRUD de Recibos, seed do catálogo de vistoria.
- **Rodada 2** (`PLANO_AJUSTES_RODADA2.md`, 25 itens, migrações 0005–0006): PDF deixou de ser automático (padrão PRG; botão "Regerar PDF" é o único gatilho); toasts Bootstrap para mensagens; colapso da sidebar no desktop (persistido em `localStorage`) — **removido na Rodada 3, ver abaixo**; máscaras IMask + Flatpickr; validação de CPF/CNPJ/RG; `Imovel.numero`/`complemento`; remoção de `Imovel.valor_aluguel`, `Proprietario.endereco`, `Contrato.arquivo`, `Recibo.proveniente_sitio`, tipo `periodica` de laudo e do módulo Entrada/Saída; `Inquilino.faixa_renda` + `observacoes`; select de contrato dependente do imóvel no laudo (endpoint `contratos_por_imovel_json`); Recibo com vínculos obrigatórios e período em duas datas; anexo do laudo assinado via `laudo_anexar_arquivo`.
- **Rodada 3** (`planner-docs/melhorias-validacao-visualizacao-documentos/` + `planner-docs/remover-colapso-sidebar-e-ajustar-logo/`, migração 0007–0008): novos validators `validate_rg_cpf` (`Fiador.rg_cpf`) e `validate_telefone` (`Proprietario.telefone`/`Inquilino.telefone`); `MinValueValidator(1)`/`MaxValueValidator(31)` em `Contrato.dia_vencimento`; filtro de período do Dashboard migrado para `DashboardFiltroForm` (Flatpickr dd/mm/aaaa, antes era `input type="date"` nativo); preview da Planta/Projeto na tela de detalhe do imóvel; aumento do espaço de assinatura no PDF do laudo; os 4 campos de documento GED do Contrato (`comprovante_renda`/`contrato_social`/`recibo_chaves`/`comprovante_anual`) saíram do `ContratoForm` e passaram a ser anexados na tela de detalhe via `contrato_anexar_documento` (mesmo padrão do `laudo_anexar_arquivo`); remoção completa do colapso da sidebar no desktop (sempre expandida — sem toggle, sem `localStorage`, sem `.sidebar-collapsed`/`.brand-compact`) e ajuste do CSS da logo (`#sidebar .sidebar-brand img`) para preencher a largura do container.
- **Rodada 4** (`planner-docs/redesign-pdfs-documentos-gerados/`, migrações 0009–0010): **redesign visual dos 3 PDFs** (Contrato/Laudo/Recibo) para replicar 1:1 os mockups de `docs/pdf-models/*.html`, mantendo xhtml2pdf — `base_pdf.html` concentra o CSS comum, cada template filho tem o CSS exclusivo (laudo: `.data-table`/`.badge-*`; recibo: caixa de destaque da quantia); logo sempre `Shelter_LOGO.jpg`; cabeçalho usa `{{ objeto.pk }}` + data de criação (sem campo de número formatado). **GED versionado**: novo model imutável `DocumentoGerado` (migração 0009; 0010 registra retroativamente os PDFs existentes como versão 1); `imoveis/pdf.py` ganhou `registrar_documento_gerado()` e `gerar_e_anexar(..., usuario=None)` (cria versão sequencial por origem + espelha no FileField legado); views `*_gerar_pdf` passam `request.user`; view `documentos` (GED) lista **todas** as versões via `DocumentoGerado.objects.filter(tipo=...)`; `DocumentoGeradoAdmin` somente leitura. **Storage plugável**: `STORAGES` (Django 4.2+) via `STORAGE_BACKEND` no `.env` (`filesystem` default / `s3` preparado mas não ativado — `ImproperlyConfigured` se setado sem libs; `boto3`/`django-storages` não instalados).
- Suíte de testes: **72 testes** em `imoveis/tests.py` (nova classe `DocumentoGeradoTests` + asserts de PDF ajustados ao redesign; helper `limpar_arquivos_gerados()` no `tearDown`), todos passando.

### Pendente
- Validação manual no navegador dos itens visuais/UX da Rodada 3 (datepicker do dashboard, preview da planta, espaço de assinatura do laudo, uploads de documento do contrato pelo detail).
- Validação visual dos 3 PDFs redesenhados (Rodada 4) frente aos mockups de `docs/pdf-models/`.
- Nenhuma rodada futura planejada ainda.

### Convenções obrigatórias (estabelecidas nas Rodadas 1–4)
- **PDF nunca é gerado ao salvar** — create/edit fazem redirect + toast; só as views `*_gerar_pdf` geram/baixam PDF.
- **GED versionado é a fonte de verdade dos PDFs gerados** (Rodada 4) — cada geração de PDF cria uma nova versão **imutável** em `DocumentoGerado` (`numero_versao` sequencial **por origem**; `save()` bloqueia updates). Sempre gerar via `imoveis/pdf.py:gerar_e_anexar(instance, ..., usuario=request.user)`, nunca gravar direto no FileField legado — os campos `Contrato.documento_gerado`/`LaudoVistoria.documento_gerado`/`Recibo.arquivo` são **espelho automático** da última versão, não fonte de verdade. Não editar/deletar uma versão para "corrigir"; gerar outra.
- **Uploads via storage `default` do `STORAGES`** (Rodada 4) — plugável por `STORAGE_BACKEND` no `.env` (mesmo padrão de `DB_ENGINE`); não instalar `boto3`/`django-storages` nem trocar o backend `s3` sem seguir o passo a passo comentado em `core/settings.py`.
- **Campos de data novos** usam `_date_widget()` de `imoveis/forms.py` (Flatpickr dd/mm/yyyy); **moeda** usa `_moeda_widget()` + campo em `localized_fields` (aceita "1500,00"; máscara **sem** separador de milhar — `USE_THOUSAND_SEPARATOR` está desligado, não ligar).
- **Documentos**: `imoveis/validators.py` tem `validate_cpf`, `validate_cnpj`, `validate_cpf_cnpj` (condicional 11/14 dígitos), `validate_rg`, `validate_rg_cpf` (condicional: 11 dígitos → CPF, senão RG — usado em `Fiador.rg_cpf`) e `validate_telefone` (exige 10 ou 11 dígitos incluindo DDD, com ou sem máscara — usado em `Proprietario.telefone`/`Inquilino.telefone`) — reutilizar, não duplicar.
- **Checklist do laudo**: laudo novo exige `item_vistoria_formset_factory(extra=len(catalogo))`; `extra=0` renderiza 0 linhas e o checklist some.
- **Encoding (Windows)**: nunca editar templates com `Get-Content`/`Set-Content` do PowerShell 5.1 — corrompe UTF-8. Usar o Edit tool.

---

## Banco de dados
Controlado por variáveis de ambiente no `.env`:
- `DB_ENGINE=django.db.backends.sqlite3` (padrão dev)
- `DB_ENGINE=django.db.backends.mysql` + `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` (prod)

## Autenticação
Sistema de autenticação padrão do Django. Todas as views exigem login (`@login_required`). Rotas: `/login/`, `/logout/`. Após login redireciona para `/` (dashboard).

## Dashboard (BI)
A view do dashboard agrega dados de `Lancamento` para gerar gráficos de barras e pizza, passados como contexto ao template `dashboard.html`.

---

## Documentação do projeto em `/docs/`

| Arquivo | Conteúdo |
|---|---|
| [01_visao_geral.md](docs/01_visao_geral.md) | Descrição do sistema, público-alvo, stack tecnológica, módulos e requisitos funcionais |
| [03_modelagem_dados.md](docs/03_modelagem_dados.md) | Entidades, campos, tipos, relacionamentos e caminhos de upload |
| [04_regras_de_negocio.md](docs/04_regras_de_negocio.md) | Signals, automações, restrições, campos condicionais, GED, dashboard e acesso |
| [07_design_ui_ux.md](docs/07_design_ui_ux.md) | Paleta, tipografia, layout, componentes, responsividade e bibliotecas frontend |
