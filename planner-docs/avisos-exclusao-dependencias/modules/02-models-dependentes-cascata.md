# Objetivo

Adicionar, em `imoveis/models.py`, uma property por model (`Imovel`,
`Contrato`, `LaudoVistoria`, `Recibo`) que retorna a contagem de registros
que seriam apagados em cascata (`CASCADE`) junto com a exclusão daquele
registro. Cada property retorna uma **lista de tuplas `(label, count)`**
já filtrada para `count > 0`, na ordem em que os relacionamentos aparecem
no model (ver plan.md), pronta para ser iterada em template
(`{% for label, count in obj.dependentes_cascata %}`).

Não incluir relações `PROTECT` nessas properties — só `CASCADE`/`OneToOne
CASCADE`. `DocumentoGerado` permanece `CASCADE` e **deve** ser contado
(decisão do usuário: apenas avisar, nunca bloquear).

---

# Arquivos afetados

- `imoveis/models.py` — adicionar 4 properties, uma em cada classe:
  `Imovel`, `Contrato`, `LaudoVistoria`, `Recibo`.

---

# Dependências

Nenhuma.

---

# Leituras adicionais

Nenhuma.

---

# Detalhamento

Nome da property: `dependentes_cascata` (mesmo nome nas 4 classes, para
uso uniforme no template do módulo 03).

## `Imovel.dependentes_cascata`

Relacionamentos CASCADE de `Imovel` (ver `imoveis/models.py`): `fotos`
(`FotoImovel`), `notificacoes` (`Notificacao`), `laudos` (`LaudoVistoria`
— CASCADE em `Imovel`, mas o próprio `LaudoVistoria.contrato` é PROTECT;
isso não impede contar aqui, pois a contagem é sobre o que cascateia
*deste* imóvel, independente do que viria a bloquear a exclusão do
laudo). Note que `Imovel` também tem `contratos` e `recibos`, mas esses
são PROTECT — **não incluir na cascata**, pois já bloqueiam a exclusão
antes de chegar a cascatear (tratado no módulo 01).

```python
@property
def dependentes_cascata(self):
    pares = [
        ('foto(s)', self.fotos.count()),
        ('notificação(ões)', self.notificacoes.count()),
        ('laudo(s) de vistoria', self.laudos.count()),
    ]
    return [(label, n) for label, n in pares if n > 0]
```

## `Contrato.dependentes_cascata`

Relacionamentos CASCADE: `fiadores` (`Fiador`), `lancamentos`
(`Lancamento`), `renovacao` (`RenovacaoContrato`, OneToOne), `distrato`
(`Distrato`, OneToOne), `documentos_gerados` (`DocumentoGerado`).

OneToOne não tem `.count()` — usar `hasattr` para verificar existência (o
padrão já usado em `contrato_detail`, linhas ~378-385, é
`try/except DoesNotExist`; para a property, usar `hasattr` é equivalente e
mais direto):

```python
@property
def dependentes_cascata(self):
    pares = [
        ('fiador(es)', self.fiadores.count()),
        ('lançamento(s) financeiro(s)', self.lancamentos.count()),
        ('renovação', 1 if hasattr(self, 'renovacao') else 0),
        ('distrato', 1 if hasattr(self, 'distrato') else 0),
        ('documento(s) gerado(s)', self.documentos_gerados.count()),
    ]
    return [(label, n) for label, n in pares if n > 0]
```

## `LaudoVistoria.dependentes_cascata`

Relacionamentos CASCADE: `itens` (`ItemVistoria`), `testemunhas`
(`TestemunhaLaudo`), `documentos_gerados` (`DocumentoGerado`). Note que
`ItemVistoria` por sua vez cascateia `FotoItemVistoria` — não é preciso
contar esse nível (a contagem cobre apenas o primeiro nível de cascata a
partir do objeto que o usuário está excluindo, mesmo critério aplicado a
`Imovel`/`Contrato`/`Recibo` acima).

```python
@property
def dependentes_cascata(self):
    pares = [
        ('item(ns) de vistoria', self.itens.count()),
        ('testemunha(s)', self.testemunhas.count()),
        ('documento(s) gerado(s)', self.documentos_gerados.count()),
    ]
    return [(label, n) for label, n in pares if n > 0]
```

## `Recibo.dependentes_cascata`

Relacionamento CASCADE: `documentos_gerados` (`DocumentoGerado`).

```python
@property
def dependentes_cascata(self):
    pares = [
        ('documento(s) gerado(s)', self.documentos_gerados.count()),
    ]
    return [(label, n) for label, n in pares if n > 0]
```

---

# Critérios de aceite

- [ ] `Imovel`, `Contrato`, `LaudoVistoria`, `Recibo` têm a property
      `dependentes_cascata` retornando lista de tuplas `(label, count)` com
      `count > 0` apenas.
- [ ] Nenhuma relação `PROTECT` é contada nessas properties.
- [ ] `Contrato.dependentes_cascata` usa `hasattr` para `renovacao` e
      `distrato` (OneToOne), não `.count()`.
- [ ] Nenhuma migration gerada (`venv/Scripts/python manage.py makemigrations`
      não deve propor nada relacionado a essas mudanças).
- [ ] `venv/Scripts/python manage.py check` roda sem erros.

---

# Riscos

- Custo de N queries `COUNT` por objeto listado ao renderizar a listagem
  (mesmo padrão de custo já aceito hoje em `proprietario_list.html` com
  `p.imoveis.count()`); aceitável dado o volume de dados deste sistema.
- Usar `related_name` errado quebraria silenciosamente (retornaria erro de
  atributo) — conferir os nomes exatos contra `imoveis/models.py` antes de
  escrever (já listados acima, mas confirmar no arquivo real ao implementar).
