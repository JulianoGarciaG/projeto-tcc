# Objetivo

Remover os 4 campos de "Documentos (GED)" (`comprovante_renda`, `contrato_social`, `recibo_chaves`, `comprovante_anual`) do `ContratoForm` (criacao/edicao) e criar um endpoint de upload por documento, seguindo o mesmo padrao ja usado pelo anexo do laudo (`laudo_anexar_arquivo`): POST simples a partir da tela de detalhe, sem ModelForm dedicado.

Este modulo cobre apenas backend (form, view, url, testes). A parte de template esta no modulo 08, que depende deste.

---

# Arquivos afetados

- `imoveis/forms.py`
  - `ContratoForm.Meta.fields` (linhas 121-126): remover `"comprovante_renda"`, `"contrato_social"`, `"recibo_chaves"`, `"comprovante_anual"` da lista.
  - `ContratoForm.Meta.widgets` (linhas 134-137): remover as 4 entradas correspondentes (`comprovante_renda`, `contrato_social`, `recibo_chaves`, `comprovante_anual`).
  - Nao alterar o `__init__` do form (so mexe nos widgets de data, que continuam existindo).

- `imoveis/views.py`
  - Import (linha 5): adicionar `Http404` ao import de `django.http` (hoje so importa `JsonResponse`).
  - Adicionar, na secao "Contratos" (apos `contrato_gerar_pdf`, por volta da linha 402-403), um dicionario `_CONTRATO_DOCUMENTOS = {"comprovante_renda": "Comprovante de Renda", "contrato_social": "Contrato Social", "recibo_chaves": "Recibo de Entrega de Chaves", "comprovante_anual": "Comprovante Anual de Pagamento"}` e a view `contrato_anexar_documento(request, pk, campo)`:
    - Busca o `Contrato` por `pk` (404 se nao existir).
    - Se `campo` nao estiver em `_CONTRATO_DOCUMENTOS`, levanta `Http404` (protege contra setattr em campo arbitrario do model).
    - No POST, le `request.FILES.get("arquivo")`; se presente, faz `setattr(contrato, campo, arquivo)` e `contrato.save(update_fields=[campo])`, com mensagem de sucesso citando o rotulo do documento (`_CONTRATO_DOCUMENTOS[campo]`); se ausente, mensagem de erro "Selecione um arquivo para anexar." (mesmo texto do `laudo_anexar_arquivo`).
    - Sempre redireciona para `contrato_detail` (`pk=pk`), inclusive em GET, no mesmo padrao de `laudo_anexar_arquivo` (`imoveis/views.py:566-577`).

- `imoveis/urls.py`
  - Adicionar, apos a linha `path("contratos/<int:pk>/gerar-pdf/", ...)` (linha 42), a rota `path("contratos/<int:pk>/documentos/<str:campo>/anexar/", views.contrato_anexar_documento, name="contrato_anexar_documento")`.

- `imoveis/tests.py`
  - Import (linha 11): adicionar `ContratoForm` ao import de `.forms` (hoje so importa `LaudoVistoriaForm, ReciboForm`).
  - Novos testes em `FluxoViewTests` (ver Criterios de aceite).

---

## Documentacao relacionada

- `docs/04_regras_de_negocio.md`
  Secao 5 ("Campos Condicionais por Tipo de Contrato"): o texto atual diz "O formulario exibe/oculta os campos dinamicamente via JavaScript conforme o tipo selecionado" — isso deixa de valer para os documentos GED (que saem do formulario de criacao/edicao). Atualizar para refletir que os documentos sao anexados na tela de detalhe apos a criacao do contrato, com a exibicao do campo correto (PF/PJ) feita no proprio template de detalhe (ver modulo 08).
  Secao 8 ("GED — Gestao Eletronica de Documentos"): sem mudanca de comportamento da central `/documentos/`, mas pode-se acrescentar que o upload dos documentos do contrato agora ocorre na tela de detalhe do contrato, nao mais na criacao.

- `docs/03_modelagem_dados.md`
  Secao 2.5 (Contrato): nenhum campo novo/removido do model — sem impacto na tabela de campos. Nao ha secao que descreva "onde" o campo e preenchido na UI, entao nao ha o que atualizar alem do já citado em 04_regras_de_negocio.md.

- `docs/07_design_ui_ux.md`
  Sem impacto obrigatorio.

---

# Dependencias

Nenhuma dependencia de entrada. O modulo 08 (template) depende deste modulo (usa a URL/nome `contrato_anexar_documento` e a ausencia dos campos no `ContratoForm`).

---

# Criterios de aceite

- [ ] `ContratoForm.Meta.fields` nao contem mais `comprovante_renda`, `contrato_social`, `recibo_chaves` nem `comprovante_anual`.
- [ ] `contrato_create`/`contrato_edit` continuam funcionando normalmente para os demais campos (imovel, inquilino, tipo, datas, valor, fiadores) — nenhuma mudanca de comportamento nesses fluxos alem da remocao dos 4 campos.
- [ ] Nova rota `contrato_anexar_documento` aceita POST com um arquivo no campo `arquivo`, salva no campo do model correspondente a `campo` (URL) e redireciona para `contrato_detail`.
- [ ] POST para `contrato_anexar_documento` com `campo` fora da whitelist (`_CONTRATO_DOCUMENTOS`) retorna 404.
- [ ] POST sem arquivo selecionado nao altera o contrato e exibe mensagem de erro, redirecionando normalmente para `contrato_detail` (sem erro 500).
- [ ] Novos testes em `imoveis/tests.py`:
  - `test_form_contrato_nao_expoe_documentos_ged` — espelha `test_form_nao_expoe_upload_manual` do laudo (L3): confere que os 4 campos nao estao em `ContratoForm.Meta.fields`.
  - `test_contrato_anexar_documento` — espelha `test_laudo_anexar_arquivo`: POST com `SimpleUploadedFile` para `comprovante_renda`, confere redirect para `contrato_detail`, `contrato.comprovante_renda` preenchido apos `refresh_from_db()`, e limpeza do arquivo ao final (`contrato.comprovante_renda.delete(save=False)`).
  - `test_contrato_anexar_documento_campo_invalido_404` — POST com `campo="inexistente"` retorna `404`.
  - `test_contrato_anexar_documento_sem_arquivo` — POST sem arquivo redireciona para `contrato_detail` sem alterar o contrato.
- [ ] `python manage.py test imoveis` roda sem falhas.
- [ ] `python manage.py check` sem erros.

---

# Riscos

- Baixo: `setattr(contrato, campo, arquivo)` so e seguro porque `campo` e validado contra a whitelist `_CONTRATO_DOCUMENTOS` antes — nao remover essa checagem, sob risco de permitir sobrescrever qualquer atributo do model via URL manipulada.
- Contratos existentes que ja tinham documentos anexados via formulario de criacao/edicao (antes desta mudanca) continuam com os arquivos intactos no banco — a migracao de fluxo nao apaga nem move arquivos ja salvos, so muda onde novos uploads sao feitos.
