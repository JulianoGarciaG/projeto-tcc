# Plano: Avisos de dependência ao excluir registros

## Objetivo

Cobrir dois problemas de exclusão de registros no app `imoveis`:

1. **Bloqueios reais (`PROTECT`) sem tratamento amigável**: `imovel_delete`,
   `proprietario_delete` e `inquilino_delete` não capturam `ProtectedError`,
   resultando em erro 500 quando o registro tem vínculos. Aplicar o mesmo
   padrão já usado em `contrato_delete` (`imoveis/views.py`).
2. **Cascatas silenciosas (`CASCADE`) sem aviso**: ao excluir `Imovel`,
   `Contrato`, `LaudoVistoria` ou `Recibo`, registros dependentes são
   apagados junto sem qualquer aviso. Adicionar contagem desses dependentes
   no modal de confirmação já existente nas páginas de listagem (sem criar
   página dedicada).

## Estado atual (confirmado por leitura direta do código)

- `imoveis/views.py`: views de exclusão são funções simples
  `get_object_or_404` + `if request.method == 'POST': obj.delete()`.
  `ProtectedError` já importado (linha 5, `from django.db.models import Sum, Q, ProtectedError`).
  Apenas `contrato_delete` (linha ~461) trata `ProtectedError`.
- Não existem views `proprietario_detail` nem `inquilino_detail` — o redirect
  de bloqueio para esses dois só pode ser para a própria `_list`.
- Confirmação de exclusão é sempre um **modal Bootstrap inline** dentro do
  template de listagem (não há `*_confirm_delete.html` dedicado). Padrão
  documentado em `docs/07_design_ui_ux.md` §14 (modal-sm, título vermelho,
  dois botões, `border-0`) — não alterar esse padrão visual, só adicionar
  texto de aviso condicional dentro do `modal-body`.
- `imovel_list.html` tem **duas** cópias do modal (vista Cards e vista
  Tabela, `modalExcluir{{ pk }}` / `modalExcluirTb{{ pk }}`) iterando o
  mesmo queryset — qualquer texto de aviso deve ser adicionado nas duas.
- Relações CASCADE confirmadas em `imoveis/models.py`:
  - `Imovel` → `FotoImovel` (`related_name='fotos'`), `Notificacao`
    (`related_name='notificacoes'`), `LaudoVistoria` (`related_name='laudos'`,
    CASCADE em Imovel mas PROTECT em Contrato — só é alcançável se o imóvel
    não tiver contrato/recibo vinculado, caso raro mas possível).
  - `Contrato` → `Fiador` (`related_name='fiadores'`), `Lancamento`
    (`related_name='lancamentos'`), `RenovacaoContrato` (OneToOne,
    `related_name='renovacao'`), `Distrato` (OneToOne, `related_name='distrato'`),
    `DocumentoGerado` (`related_name='documentos_gerados'`).
  - `LaudoVistoria` → `ItemVistoria` (`related_name='itens'`), `TestemunhaLaudo`
    (`related_name='testemunhas'`), `DocumentoGerado` (`related_name='documentos_gerados'`).
  - `Recibo` → `DocumentoGerado` (`related_name='documentos_gerados'`).
  - `DocumentoGerado` permanece CASCADE (decisão do usuário) — só contar,
    nunca bloquear.

## Abordagem técnica (decisão)

**Contagem de cascata via property no model**, não via `annotate` na
queryset da view nem via template tag customizada.

Justificativa:
- `annotate(Count(...))` exigiria múltiplos `Count` com `distinct=True` por
  view de listagem (risco de multiplicação de linhas ao fazer JOIN de
  múltiplas relações *-to-many ao mesmo tempo) e duplicaria a mesma lógica
  em 4 views (`imovel_list`, `contrato_list`, `laudo_list`, `recibo_list`).
- Uma property no model (ex. `Imovel.dependentes_cascata`) centraliza a
  lógica uma única vez, é reutilizável em qualquer template/view futura, e
  seu custo (algumas queries `COUNT` simples por objeto listado) é aceitável
  dado o volume de dados deste sistema — mesmo padrão de custo que já existe
  hoje em `proprietario_list.html` chamando `p.imoveis.count` direto no
  template.
- Uma template tag customizada seria mais indireta para o mesmo resultado,
  sem ganho real sobre a property.

Cada property retorna uma **lista de tuplas `(label, count)`** já filtrada
para `count > 0`, pronta para iterar no template (`{% for label, count in
im.dependentes_cascata %}`). Sem essas tuplas, nenhuma seção de aviso é
renderizada.

## Resumo dos módulos

| Módulo | Responsabilidade |
|---|---|
| `01-protected-error-views` | Tratar `ProtectedError` em `imovel_delete`, `proprietario_delete`, `inquilino_delete` (mesmo padrão de `contrato_delete`) |
| `02-models-dependentes-cascata` | Adicionar properties de contagem de cascata em `Imovel`, `Contrato`, `LaudoVistoria`, `Recibo` |
| `03-templates-aviso-cascata` | Exibir a contagem nos modais de confirmação das 4 listagens afetadas |
| `04-testes` | Testes de bloqueio `ProtectedError` (proprietario/imovel/inquilino) + testes das properties de cascata |
| `05-docs` | Atualizar `docs/04_regras_de_negocio.md` §7 |

## Ordem de implementação

1. `01-protected-error-views` (independente)
2. `02-models-dependentes-cascata` (independente)
3. `03-templates-aviso-cascata` (depende de `02`, precisa das properties já existirem)
4. `04-testes` (depende de `01` e `02` estarem implementados)
5. `05-docs` (depende de `01`, `02`, `03` — descreve o resultado final)

Módulos `01` e `02` podem ser feitos em qualquer ordem entre si (nenhuma
dependência mútua).

## Afinidade de cache entre módulos

- `01` e `04` tocam **apenas** `imoveis/views.py` (01) e `imoveis/tests.py`
  (04) — arquivos diferentes, sem afinidade direta, mas ambos leem o mesmo
  trecho de `views.py` como contexto. Baixa afinidade.
- `02` e `03` têm afinidade forte: `02` define as properties em
  `imoveis/models.py`; `03` consome essas properties nos templates. Se
  implementados na mesma janela, a janela já sabe o nome exato das
  properties sem precisar reabrir `models.py` — recomendado implementar
  `02` e `03` na mesma janela quando possível.
- `04` depende de ler `imoveis/models.py` (para as properties) e
  `imoveis/views.py` (para as views corrigidas) — sem afinidade de arquivo
  direta com os demais (só lê, não edita esses arquivos).
- `05` só edita `docs/04_regras_de_negocio.md`, arquivo não tocado por
  nenhum outro módulo.

## Observações gerais

- Nenhuma migration é necessária — todas as mudanças são properties Python
  (`@property`) e tratamento de exceção em views, sem alteração de schema.
- Não criar rotas novas nem `*_detail` novos para Proprietario/Inquilino.
- Não alterar o comportamento de `DocumentoGerado` (permanece CASCADE).
- Padrão visual do modal (`docs/07_design_ui_ux.md` §14) deve ser preservado;
  o aviso de cascata é um bloco de texto adicional dentro do `modal-body`,
  não uma mudança estrutural do modal.
