# Objetivo

Cobrir com testes automatizados:

1. Bloqueio (`ProtectedError` tratado, sem 500) para `imovel_delete`,
   `proprietario_delete`, `inquilino_delete` — replicando o padrão dos dois
   testes já existentes para `contrato_delete`.
2. Corretude das properties `dependentes_cascata` de `Imovel` e `Contrato`
   (os dois casos com mais relacionamentos e maior risco de erro de
   `related_name`).

---

# Arquivos afetados

- `imoveis/tests.py` — adicionar testes na classe `FluxoViewTests`
  (linha ~401) ou em nova classe, conforme preferir manter coesão com os
  testes de exclusão já existentes ali.

---

# Dependências

Depende dos módulos `01-protected-error-views` e
`02-models-dependentes-cascata` já implementados (os testes exercitam o
comportamento que esses módulos implementam).

---

# Leituras adicionais

Nenhuma — `imoveis/tests.py` já contém em `FluxoViewTests.setUp()` a
fixture base (`criar_base()`) e os dois testes de referência para
`contrato_delete` (linhas ~435-450), usar como modelo direto.

---

# Detalhamento

## Testes de bloqueio (padrão: réplica dos testes de `contrato_delete`)

Para cada um dos três models, dois testes: bloqueado (com vínculo) e
funcionando (sem vínculo). Seguir exatamente a forma dos testes existentes
`test_contrato_delete_protegido_nao_da_500` e
`test_contrato_delete_sem_vinculos_funciona` (linhas ~435-450 de
`imoveis/tests.py`), adaptando o model e a mensagem esperada.

Exemplo para `Imovel` (adaptar para `Proprietario` e `Inquilino` da mesma
forma, usando os vínculos reais de cada um — `Imovel` tem `Contrato`/
`Recibo` como PROTECT; `Proprietario` tem `Imovel`; `Inquilino` tem
`Contrato`):

```python
def test_imovel_delete_protegido_nao_da_500(self):
    # self.contrato já vincula self.imovel (criado em setUp via criar_base())
    resp = self.client.post(reverse('imovel_delete', args=[self.imovel.pk]), follow=True)
    self.assertRedirects(resp, reverse('imovel_list'))
    self.assertTrue(Imovel.objects.filter(pk=self.imovel.pk).exists())
    mensagens = [str(m) for m in resp.context['messages']]
    self.assertTrue(any('não pode ser excluído' in m for m in mensagens))

def test_imovel_delete_sem_vinculos_funciona(self):
    imovel_pk = self.imovel.pk
    self.contrato.delete()  # remove o vínculo PROTECT antes de excluir o imóvel
    resp = self.client.post(reverse('imovel_delete', args=[imovel_pk]))
    self.assertRedirects(resp, reverse('imovel_list'))
    self.assertFalse(Imovel.objects.filter(pk=imovel_pk).exists())
```

Para `Proprietario` e `Inquilino`, o teste "sem vínculos" precisa criar um
objeto **novo** e isolado (sem contrato/imóvel apontando para ele), já que
`self.imovel`/`self.inquilino` de `criar_base()` já têm vínculo via
`self.contrato`. Ex.:

```python
def test_proprietario_delete_protegido_nao_da_500(self):
    resp = self.client.post(
        reverse('proprietario_delete', args=[self.imovel.proprietario.pk]), follow=True)
    self.assertRedirects(resp, reverse('proprietario_list'))
    mensagens = [str(m) for m in resp.context['messages']]
    self.assertTrue(any('não pode ser excluído' in m for m in mensagens))

def test_proprietario_delete_sem_vinculos_funciona(self):
    outro = Proprietario.objects.create(nome='Outro', cpf_cnpj='...')
    resp = self.client.post(reverse('proprietario_delete', args=[outro.pk]))
    self.assertRedirects(resp, reverse('proprietario_list'))
    self.assertFalse(Proprietario.objects.filter(pk=outro.pk).exists())
```

Aplicar raciocínio equivalente para `Inquilino` (bloqueado via
`self.contrato`; "sem vínculos" cria um `Inquilino` novo isolado). Usar
os validators corretos para CPF/CNPJ fictício válido — conferir em
`imoveis/validators.py` ou reaproveitar valores já usados em `criar_base()`
(ver início de `imoveis/tests.py`) para não ter que gerar CPF/CNPJ válido
do zero.

## Testes de `dependentes_cascata`

```python
def test_imovel_dependentes_cascata_conta_fotos_e_notificacoes(self):
    Notificacao.objects.create(imovel=self.imovel, ...)  # campos obrigatórios conforme model
    deps = dict(self.imovel.dependentes_cascata)
    self.assertEqual(deps.get('notificação(ões)'), 1)

def test_contrato_dependentes_cascata_conta_lancamentos_e_fiadores(self):
    Lancamento.objects.create(contrato=self.contrato, ...)  # campos obrigatórios conforme model
    deps = dict(self.contrato.dependentes_cascata)
    self.assertEqual(deps.get('lançamento(s) financeiro(s)'), 1)

def test_contrato_dependentes_cascata_vazio_quando_sem_vinculos(self):
    contrato_novo = Contrato.objects.create(...)  # sem fiadores/lancamentos/renovacao/distrato/docs
    self.assertEqual(contrato_novo.dependentes_cascata, [])
```

Conferir os campos obrigatórios exatos de `Notificacao` e `Lancamento` em
`imoveis/models.py` ao escrever os `.create(...)` — não foram detalhados
aqui para não duplicar a modelagem.

---

# Critérios de aceite

- [ ] 6 novos testes de bloqueio/sucesso (2 por model: Imovel, Proprietario,
      Inquilino), seguindo o padrão dos testes de `contrato_delete`.
- [ ] Ao menos 3 testes de `dependentes_cascata` (Imovel com dependentes,
      Contrato com dependentes, Contrato vazio).
- [ ] `venv/Scripts/python manage.py test imoveis` passa integralmente.

---

# Riscos

- Necessário conferir campos obrigatórios reais de `Notificacao` e
  `Lancamento` (não detalhados neste módulo) para os `.create()` de teste
  não falharem por campo faltante — ler `imoveis/models.py` ao escrever.
- Se `criar_base()` já popular vínculos que tornam o "sem vínculos" de
  Proprietario/Inquilino inválido (ex. mesmo CPF/CNPJ), gerar dados únicos
  para o objeto de teste isolado.
