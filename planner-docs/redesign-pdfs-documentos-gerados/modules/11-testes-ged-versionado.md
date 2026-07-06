# Objetivo

Cobrir com testes automatizados o comportamento da nova camada de GED
versionado: criação de versão, incremento sequencial por origem, cálculo de
hash, imutabilidade do registro e comportamento do storage plugável em
ambiente de teste (sempre `filesystem`, já que `s3` não é instalado nesta
rodada).

---

# Arquivos afetados

- `imoveis/tests.py` (nova classe de testes, ex.: `DocumentoGeradoTests`)

---

## Documentação relacionada

- Nenhum documento de `/docs` é impactado por este módulo (mudança é
  exclusivamente de teste automatizado).

---

# Dependências

- `07-model-documento-gerado.md`, `08-storage-s3-ready.md`,
  `09-integracao-pdf-versionamento.md` — testa o comportamento implementado
  por esses três módulos.

---

# Casos de teste obrigatórios

## Criação e versionamento

- Gerar o PDF de um Contrato pela primeira vez cria `DocumentoGerado` com
  `numero_versao=1`.
- Gerar novamente o PDF do mesmo Contrato cria uma **segunda** linha com
  `numero_versao=2` (não sobrescreve a primeira — `DocumentoGerado.objects.filter(contrato=c).count()` deve ser 2).
- Duas origens diferentes (dois contratos distintos) têm numeração
  independente — o segundo contrato começa em `numero_versao=1`, mesmo que o
  primeiro já esteja em `numero_versao=5`.
- O mesmo teste replicado para Laudo e Recibo (numeração por tipo/origem
  isolada entre si).

## Hash

- `DocumentoGerado.hash_sha256` bate com `hashlib.sha256(conteúdo_do_arquivo).hexdigest()`
  lido de volta do storage.
- Duas gerações consecutivas do mesmo Contrato **sem alterar nenhum dado**
  produzem hashes iguais (mesmo conteúdo) mas `numero_versao` diferentes
  (confirma que o versionamento é por evento de geração, não por diff de
  conteúdo).

## Imutabilidade

- Criar um `DocumentoGerado` funciona (`save()` em instância nova).
- Buscar um `DocumentoGerado` já persistido, alterar um campo (ex.:
  `numero_versao`) e chamar `.save()` novamente deve levantar exceção
  (`ValidationError` ou exceção customizada, conforme implementado no
  módulo 07) — usar `self.assertRaises(...)`.

## Validação de origem única

- Instanciar `DocumentoGerado` sem nenhuma FK de origem preenchida e chamar
  `full_clean()` deve levantar `ValidationError`.
- Instanciar `DocumentoGerado` com duas FKs de origem preenchidas (ex.:
  `contrato` e `laudo` ao mesmo tempo) e chamar `full_clean()` deve levantar
  `ValidationError`.

## Integração com as views `*_gerar_pdf`

- `self.client.get(reverse('contrato_gerar_pdf', args=[...]))` autenticado
  cria uma versão com `gerado_por` igual ao usuário logado no teste.
- Campo legado `Contrato.documento_gerado` (recarregado do banco) aponta para
  o mesmo arquivo da versão mais recente após a geração.

## Migração de dados retroativa (se testável em `TestCase`)

- Simular um `Contrato` com `documento_gerado` preenchido **antes** de rodar
  a lógica equivalente à migration de dados do módulo 09 (chamando a função
  de migração diretamente, não via `manage.py migrate` dentro do teste) e
  confirmar que resulta em exatamente uma versão `numero_versao=1` com
  `gerado_por=None`.

---

# Critérios de aceite

- [ ] Todos os casos de teste listados acima implementados e passando.
- [ ] `venv/Scripts/python manage.py test imoveis` — suíte completa (testes
      novos + os 48 já existentes, ajustados no módulo 05) passa 100%.
- [ ] Nenhum teste depende de credenciais/rede reais de S3 (toda a suíte roda
      100% offline, com `STORAGE_BACKEND` padrão/`filesystem`).

---

# Riscos

- Testar "imutabilidade" corretamente exige cuidado para não confundir com o
  comportamento padrão do Django, que permite `save()` em qualquer instância
  por padrão — garantir que o teste realmente exercita um `UPDATE` (buscar
  do banco de novo antes de alterar e salvar), não apenas chamar `.save()`
  duas vezes na mesma instância em memória sem persistir entre as chamadas.
- Testes de hash dependem do conteúdo exato do PDF gerado pelo `xhtml2pdf`
  ser determinístico o suficiente para comparação — evitar comparar hashes
  entre execuções diferentes de teste que dependam de timestamps embutidos
  no PDF (ex.: "Emitido em" no cabeçalho, que usa `criado_em`, um valor fixo
  do objeto, não `now()` — deve ser seguro, mas vale confirmar que nenhum
  template de PDF usa `{% now %}` em lugar de um campo de data do model).
