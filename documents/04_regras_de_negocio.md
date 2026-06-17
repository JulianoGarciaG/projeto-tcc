# 04 — Regras de Negócio
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
- O formulário exibe/oculta os campos dinamicamente via JavaScript conforme o tipo selecionado.

---

## 6. Laudo de Vistoria Vinculado ao Distrato

- O `Distrato` pode referenciar um `LaudoVistoria` do tipo `saida` como laudo de saída.
- O vínculo é **opcional** (`null=True`, `blank=True`).
- Na view de distrato, o queryset de laudos é filtrado para exibir **somente os laudos do imóvel vinculado ao contrato**.

---

## 7. Proteção Contra Exclusão de Registros Vinculados

| Entidade protegida | Protege contra exclusão de |
|---|---|
| `Proprietario` | Não pode ser excluído se possui imóveis (`PROTECT`) |
| `Imovel` | Não pode ser excluído se possui contratos (`PROTECT`) |
| `Inquilino` | Não pode ser excluído se possui contratos (`PROTECT`) |

---

## 8. GED — Gestão Eletrônica de Documentos

- Todos os documentos do sistema são armazenados digitalmente, eliminando a dependência de pastas físicas.
- A central GED (`/documentos/`) agrega automaticamente todos os arquivos anexados, agrupados por tipo:
  - Contratos com arquivo PDF
  - Laudos de vistoria com arquivo
  - Comprovantes de pagamento
  - Recibos de entrega de chaves
  - Comprovantes anuais de pagamento
- Um documento só aparece na central GED se o campo de arquivo **não estiver vazio**.

---

## 9. Dashboard — Filtros e Métricas

O dashboard suporta filtros combinados aplicados simultaneamente:

| Filtro | Campo filtrado |
|---|---|
| Imóvel | `contrato__imovel_id` |
| Data início | `data_vencimento__gte` |
| Data fim | `data_vencimento__lte` |
| Status do lançamento | `status` |

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

---

## 11. Alimentação em Tempo Real

- Todas as operações CRUD (criação, edição, exclusão) refletem imediatamente no banco de dados.
- O status do imóvel é recalculado a cada alteração de contrato (via signal), sem necessidade de ação manual.

---

## 12. Acesso Mobile (Vistoriadores em Campo)

- A interface é responsiva e permite que vistoriadores realizem consultas e atualizações diretamente do local do imóvel via dispositivos móveis.
- A sidebar é ocultada no mobile e acessada via toggle hamburger.
