# Objetivo

Configurar o storage de arquivos do Django de forma plugável via `.env`,
seguindo o mesmo padrão já usado no projeto para o banco de dados
(`DB_ENGINE`), de modo que `DocumentoGerado.arquivo` (e, no futuro, os demais
`FileField`s do projeto) possam migrar de `FileSystemStorage` (dev) para um
backend S3 (produção) **sem alterar código de aplicação** — apenas variáveis
de ambiente e, quando for a hora, a instalação de uma dependência nova.

**Não instalar `boto3`/`django-storages` nesta rodada** — só preparar a
arquitetura.

---

# Arquivos afetados

- `core/settings.py` (nova configuração `STORAGES`)
- `.env.example` (se existir no projeto) ou documentação inline de novas
  variáveis de ambiente — verificar se o projeto já tem um arquivo de exemplo
  de `.env` antes de criar um novo.

---

## Documentação relacionada

- CLAUDE.md
  Adicionar à seção "Banco de dados" (ou nova seção "Armazenamento de
  arquivos") a variável `STORAGE_BACKEND` e o padrão de troca para S3,
  espelhando a documentação já existente de `DB_ENGINE`.
- docs/01_visao_geral.md
  Avaliar se a stack tecnológica documentada deve mencionar "armazenamento
  plugável (FileSystemStorage / S3-ready)" como característica arquitetural.

---

# Dependências

- `07-model-documento-gerado.md` — o `FileField` de `DocumentoGerado` é o
  primeiro (e nesta rodada, único) campo que declaradamente depende deste
  storage configurável; conceitualmente este módulo poderia vir antes, mas
  faz mais sentido validá-lo já apontando para um campo real.

---

# Detalhamento técnico

## Padrão a seguir (análogo ao `DB_ENGINE`)

`core/settings.py` já resolve o backend de banco assim (linhas 54-75):
```python
DB_ENGINE = os.getenv('DB_ENGINE', 'django.db.backends.sqlite3')
if DB_ENGINE == 'django.db.backends.mysql':
    DATABASES = {...}
else:
    DATABASES = {...}
```

Replicar o mesmo espírito para storage, usando a chave `STORAGES` (padrão
Django >= 4.2, substitui `DEFAULT_FILE_STORAGE`):

```python
STORAGE_BACKEND = os.getenv('STORAGE_BACKEND', 'filesystem')

if STORAGE_BACKEND == 's3':
    # Backend real só deve ser configurado quando django-storages for
    # instalado (fora do escopo desta rodada). Deixar o mapeamento pronto:
    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3.S3Storage',  # requer django-storages
            'OPTIONS': {
                'bucket_name': os.getenv('AWS_STORAGE_BUCKET_NAME', ''),
                'region_name': os.getenv('AWS_S3_REGION_NAME', ''),
                # demais credenciais via variáveis de ambiente padrão da lib
                # (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY), nunca hardcoded.
            },
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }
else:
    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }
```

Pontos importantes:
- Se `STORAGE_BACKEND=s3` for setado **sem** `django-storages` instalado, o
  Django deve falhar de forma clara no boot (`ImportError` ao resolver o
  `BACKEND`) — **isso é aceitável e esperado** nesta rodada: o objetivo é a
  arquitetura estar pronta, não o backend S3 funcionar de fato sem a
  dependência. Documentar isso no `CLAUDE.md` para não gerar confusão futura
  ("se for ativar S3, primeiro rode `pip install django-storages[s3] boto3`").
- Em dev (`STORAGE_BACKEND` não setado ou `filesystem`), o comportamento deve
  ser **idêntico ao atual** — nenhuma regressão nos `FileField`s existentes
  (`FotoImovel.imagem`, `Contrato.documento_gerado`, etc.), já que o backend
  default do Django já é `FileSystemStorage`; a config explícita só formaliza
  o que já acontece implicitamente.
- `MEDIA_URL`/`MEDIA_ROOT` continuam existindo e sendo usados pelo
  `FileSystemStorage`; ao migrar para S3 no futuro, `MEDIA_URL` deixa de ser
  necessário para os arquivos que forem para o bucket (o backend S3 gera suas
  próprias URLs), mas isso é uma decisão da migração futura, não desta rodada.
- `imoveis/pdf.py::link_callback` (usado para resolver imagens dentro do PDF
  gerado, ex.: logo) **não depende deste módulo** — continua resolvendo via
  `STATIC_URL`/`MEDIA_URL` como hoje; não alterar essa função aqui.

## Passo futuro (documentar, não implementar)

Registrar em `CLAUDE.md` ou em um comentário extenso no `settings.py`:
1. `pip install django-storages[s3] boto3`.
2. Adicionar `'storages'` a `INSTALLED_APPS`.
3. Configurar `.env`: `STORAGE_BACKEND=s3`, `AWS_STORAGE_BUCKET_NAME`,
   `AWS_S3_REGION_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`.
4. Nenhuma mudança de código de aplicação é esperada — todos os `FileField`s
   já usam a API padrão do Django (`.save()`, `.url`, `.path` com cautela,
   já que `.path` não existe em storages remotos — ver risco abaixo).

---

# Critérios de aceite

- [ ] `STORAGES` configurado em `core/settings.py`, plugável via
      `STORAGE_BACKEND` (`.env`), com `filesystem` como default.
- [ ] Comportamento em dev (`STORAGE_BACKEND` ausente) idêntico ao atual —
      suíte de testes completa (`manage.py test imoveis`) passa sem alteração
      de comportamento de upload/leitura de arquivos.
- [ ] Nenhuma dependência nova (`boto3`, `django-storages`) adicionada ao
      ambiente/`requirements.txt` nesta rodada.
- [ ] Documentação do passo futuro de migração para S3 registrada em
      `CLAUDE.md`.

---

# Riscos

- Código que hoje possa depender de `.path` de um `FileField` (específico de
  `FileSystemStorage`, não existe em storages remotos como S3) quebraria
  silenciosamente numa futura migração para S3 — auditar rapidamente
  `imoveis/pdf.py` e `imoveis/views.py` em busca de usos de `.path` em
  qualquer `FileField` (não apenas os de PDF) e registrar como aviso, mesmo
  que a correção fique fora do escopo desta rodada.
- Alterar `STORAGES` incorretamente pode quebrar o `collectstatic`
  (`staticfiles`) — por isso a config acima mantém `staticfiles` sempre em
  `StaticFilesStorage`, independentemente do backend de `default`.
