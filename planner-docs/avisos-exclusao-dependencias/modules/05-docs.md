# Objetivo

Atualizar `docs/04_regras_de_negocio.md`, seção 7 ("Proteção Contra
Exclusão de Registros Vinculados"), para refletir que **todas** as views de
exclusão protegidas por `PROTECT` agora tratam `ProtectedError` com
mensagem amigável (não só `contrato_delete`), e acrescentar nota sobre o
aviso de contagem de cascata nos modais de confirmação.

---

# Arquivos afetados

- `docs/04_regras_de_negocio.md` — seção 7 (linhas ~90-98 no estado atual).

---

# Dependências

Depende dos módulos `01`, `02` e `03` já implementados (este módulo apenas
documenta o comportamento final).

---

# Leituras adicionais

Nenhuma.

---

# Detalhamento

Substituir a tabela atual da seção 7:

```
| Entidade protegida | Protege contra exclusão de |
|---|---|
| `Proprietario` | Não pode ser excluído se possui imóveis (`PROTECT`) |
| `Imovel` | Não pode ser excluído se possui contratos ou recibos (`PROTECT`) |
| `Inquilino` | Não pode ser excluído se possui contratos (`PROTECT`) |
| `Contrato` | Não pode ser excluído se possui laudos de vistoria ou recibos vinculados (`PROTECT`); a view `contrato_delete` captura `ProtectedError` e exibe mensagem orientando a excluir os vínculos primeiro |
```

Por uma versão que descreva o tratamento uniforme nas 4 views, por
exemplo (ajustar redação conforme o texto final implementado, mantendo o
delta pequeno):

```
| Entidade protegida | Protege contra exclusão de | Tratamento |
|---|---|---|
| `Proprietario` | Possui imóveis (`PROTECT`) | `proprietario_delete` captura `ProtectedError` e exibe mensagem orientando a excluir os imóveis primeiro |
| `Imovel` | Possui contratos ou recibos (`PROTECT`) | `imovel_delete` captura `ProtectedError` e exibe mensagem orientando a excluir os vínculos primeiro |
| `Inquilino` | Possui contratos (`PROTECT`) | `inquilino_delete` captura `ProtectedError` e exibe mensagem orientando a excluir os contratos primeiro |
| `Contrato` | Possui laudos de vistoria ou recibos vinculados (`PROTECT`) | `contrato_delete` captura `ProtectedError` e exibe mensagem orientando a excluir os vínculos primeiro |

Além do bloqueio por `PROTECT`, os modelos `Imovel`, `Contrato`,
`LaudoVistoria` e `Recibo` têm relacionamentos `CASCADE` (fotos,
notificações, fiadores, lançamentos, renovação/distrato, itens de
vistoria, testemunhas, documentos gerados) que são apagados junto quando o
registro pai é excluído. A property `dependentes_cascata` (em cada um
desses models, `imoveis/models.py`) calcula essa contagem, e o modal de
confirmação de exclusão das respectivas listagens exibe um aviso com a
quantidade de cada tipo de dependente que também será removido — sem
bloquear a exclusão.
```

Manter o delta pequeno: não reescrever o documento inteiro, só a seção 7.

---

# Critérios de aceite

- [ ] Seção 7 de `docs/04_regras_de_negocio.md` reflete o tratamento de
      `ProtectedError` nas 4 views (`Proprietario`, `Imovel`, `Inquilino`,
      `Contrato`).
- [ ] Seção 7 menciona a property `dependentes_cascata` e o aviso de
      cascata no modal, sem detalhar cada relação (isso já está no código).
- [ ] Nenhuma outra seção do documento foi alterada.

---

# Riscos

Nenhum risco técnico — mudança é só de documentação.
