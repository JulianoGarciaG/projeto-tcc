---
name: validate-implementation
description: >-
  Use ao FINAL de qualquer implementação (prompt direto, Plan Mode ou módulo do
  Planner) para validar o diff antes de considerá-lo pronto. Roda os comandos
  reais do projeto e confere o diff contra os invariantes do Shelter. Dispare
  quando o usuário disser "validar", "revisar antes de fechar", "terminei isto",
  ou ao concluir um módulo. Não é específica do Planner.
---

# validate-implementation

Valida uma implementação do Shelter antes de dá-la por concluída. Duas partes:
**(A) evidência real** (rodar comandos, nunca presumir) e **(B) invariantes do
projeto** (footguns que uma revisão genérica não conhece).

Regra mestra: **evidência antes de afirmação.** Nunca escreva "os testes passam"
ou "está pronto" sem ter rodado o comando nesta sessão e visto a saída.

---

## A. Evidência real (rode, não presuma)

Rode pelo Python do venv (Windows: `venv/Scripts/python`). Reporte a saída real
de cada um; se algum falhar, corrija antes de prosseguir.

```bash
venv/Scripts/python manage.py check
venv/Scripts/python manage.py makemigrations --check --dry-run   # migração faltando?
venv/Scripts/python manage.py test imoveis                        # suíte do app
```

- Se o diff mexeu em models → confirme que a migração foi criada e aplicada.
- Se mexeu só em template/CSS/JS → `test` pode não cobrir; valide manualmente
  (ver invariantes de UI/PDF abaixo) e diga isso explicitamente.

---

## B. Invariantes do Shelter (confira o diff contra cada um aplicável)

Ignore os que a mudança não toca. Para os que toca, confirme conformidade.

### Dados e persistência
- [ ] **PRG / PDF nunca ao salvar.** create/edit fazem redirect + toast; só views
      `*_gerar_pdf` geram PDF. O diff não gera PDF dentro de create/edit?
- [ ] **GED imutável.** PDF gerado sempre via `imoveis/pdf.py:gerar_e_anexar(instance,
      ..., usuario=request.user)`. Nunca gravar direto no FileField legado
      (`*.documento_gerado` / `Recibo.arquivo` são espelho, não destino de escrita).
      Correção de PDF = nova versão, nunca editar/deletar.
- [ ] **Financeiro só `Lancamento`.** `Entrada`/`Saida` não foram recriados.
- [ ] **Validadores reutilizados**, não duplicados (`imoveis/validators.py`:
      `validate_cpf`, `validate_cnpj`, `validate_cpf_cnpj`, `validate_rg`,
      `validate_rg_cpf`, `validate_telefone`). Nenhuma regex de CPF/telefone nova?
- [ ] **`Imovel` não ganhou `valor_aluguel`** (vem do contrato ativo); status
      `vago`/`ocupado` continua via signal, não setado à mão.

### Forms e widgets
- [ ] **Datas** via `_date_widget()`; **moeda** via `_moeda_widget()` +
      `localized_fields` (aceita "1500,00", sem separador de milhar).
- [ ] **Checklist do laudo**: laudo novo usa
      `item_vistoria_formset_factory(extra=len(catalogo))` — `extra=0` some com o
      checklist.

### PDF (xhtml2pdf 0.2.17)
- [ ] Sem depender de `text-transform` (motor ignora) — CAIXA ALTA literal ou
      `|upper`.
- [ ] Sem `margin: ... auto ...` — centralizar com `<table align="center">`.
- [ ] `border`/`padding` de cartão na `<td>`, não em `<div>` com múltiplos filhos
      block-level.

### Camada visual
- [ ] Estilo novo em `static/css/shelter.css` (não `custom.css`), via tokens
      (`var(--brand)`/`--ink`/`--surface`/pares `--x`/`--x-bg`), sem hex antigo.
- [ ] Testado em tema **claro e escuro** (`data-theme` no `<html>`).

### Encoding (Windows)
- [ ] Templates não foram editados com `Get-Content`/`Set-Content` do PowerShell
      5.1 (corrompe UTF-8). Se houver dúvida, verifique se acentos estão íntegros.

---

## C. Escopo

- [ ] O diff mexeu **apenas** no que a tarefa pedia? Nada fora de escopo entrou?
- [ ] A documentação impactada foi atualizada (só deltas pequenos, sem reescrever
      documentos inteiros)?

---

## Saída da validação

Reporte de forma condensada:

1. **Comandos** — resultado real de check / migrations / test (passou/falhou + o quê).
2. **Invariantes** — só os aplicáveis: conformes / violados (com arquivo e linha).
3. **Veredito** — pronto, ou lista de pendências a corrigir antes de fechar.

Se esta for a validação de um módulo do Planner, marque-o como validado em
`planner-docs/<feature>/progress.md` (nunca em plan.md). Se for tarefa avulsa,
ignore esta linha.
