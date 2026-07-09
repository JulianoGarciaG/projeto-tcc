# Objetivo

Migration de dados (RunPython) que: cria os Permission
pode_acessar_dashboard/pode_acessar_financeiro (nao confiar no signal
post_migrate para isso, ver "Contexto tecnico"), cria os Group Owner (com
essas 2 permissoes) e Comum (sem permissoes), e reclassifica os usuarios ja
existentes no banco: is_staff=True vira tambem is_superuser=True; todos os
demais (is_staff=False) sao adicionados ao Group Comum.

---

# Arquivos afetados

- imoveis/migrations/ - nova migration de dados (arquivo novo, escrito a
  mao ou via `makemigrations imoveis --empty --name
  cria_grupos_e_reclassifica_usuarios`).

---

# Dependencias

Depende do modulo 01-modelo-permissao-host (a migration deste modulo
declara dependencies apontando para a migration de schema que cria
PermissaoTela).

---

# Leituras adicionais

Nenhuma.

---

# Contexto tecnico (por que criar a Permission manualmente)

O Django cria as Permission declaradas em Meta.permissions atraves do
receiver create_permissions, conectado ao signal post_migrate. Esse signal
so dispara **depois que todas as migrations do comando `migrate` terminam**
- nunca no meio de uma migration especifica. Se esta migration de dados
tentar `Permission.objects.get(codename='pode_acessar_dashboard', ...)` sem
criar o registro primeiro, ela falha com DoesNotExist, porque o signal ainda
nao rodou.

A solucao padrao (usada nesta migration) e criar a Permission diretamente
via ORM dentro do proprio RunPython, usando get_or_create - o mesmo
resultado que o signal criaria depois, so que adiantado e de forma
idempotente (get_or_create nao duplica quando o signal rodar em seguida).

---

# Implementacao

```python
from django.conf import settings
from django.db import migrations


def cria_grupos_e_permissoes(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')
    Group = apps.get_model('auth', 'Group')
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))

    content_type, _ = ContentType.objects.get_or_create(
        app_label='imoveis', model='permissaotela',
    )
    perm_dashboard, _ = Permission.objects.get_or_create(
        codename='pode_acessar_dashboard', content_type=content_type,
        defaults={'name': 'Pode acessar o Dashboard'},
    )
    perm_financeiro, _ = Permission.objects.get_or_create(
        codename='pode_acessar_financeiro', content_type=content_type,
        defaults={'name': 'Pode acessar o modulo Financeiro'},
    )

    owner_group, _ = Group.objects.get_or_create(name='Owner')
    owner_group.permissions.set([perm_dashboard, perm_financeiro])

    comum_group, _ = Group.objects.get_or_create(name='Comum')

    # Reclassifica usuarios ja existentes no banco neste momento.
    User.objects.filter(is_staff=True, is_superuser=False).update(is_superuser=True)
    for user in User.objects.filter(is_staff=False):
        user.groups.add(comum_group)


def reverte_grupos(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    # Remove apenas os registros criados por esta migration. NAO desfaz
    # is_superuser=True nem memberships de Comum atribuidas a usuarios reais
    # (irreversivel por design - ver Riscos).
    Group.objects.filter(name__in=['Owner', 'Comum']).delete()
    Permission.objects.filter(
        codename__in=['pode_acessar_dashboard', 'pode_acessar_financeiro'],
        content_type__app_label='imoveis', content_type__model='permissaotela',
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('imoveis', '00XX_permissaotela'),  # substituir pelo nome real da migration do modulo 1
        ('auth', '__latest__'),
        ('contenttypes', '__latest__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(cria_grupos_e_permissoes, reverte_grupos),
    ]
```

Ajustar a dependencia `('imoveis', '00XX_permissaotela')` para o nome real
do arquivo de migration gerado no modulo 1.

**Testabilidade**: manter `cria_grupos_e_permissoes` como funcao de modulo
top-level (nao aninhada), com a assinatura `(apps, schema_editor)` exatamente
como acima - o modulo 5 (testes) importa esta funcao diretamente do arquivo
de migration e a chama passando `django.apps.apps` (o registry real) no
lugar de `apps`, para testar a logica de reclassificacao sem depender do
timing de criacao do banco de teste (que roda as migrations antes de
qualquer usuario de teste existir).

---

# Criterios de aceite

- [ ] Migration criada com as dependencies corretas (apontando para a
      migration real do modulo 1).
- [ ] `venv/Scripts/python manage.py migrate` roda sem erro em um banco
      zerado.
- [ ] Apos migrate, existem os Group 'Owner' (com as 2 permissoes) e
      'Comum' (sem permissoes) - validar via shell ou admin.
- [ ] Rodando a migration em um banco com usuarios pre-existentes: usuarios
      com is_staff=True passam a ter is_superuser=True; usuarios com
      is_staff=False sao adicionados ao Group Comum. Validar manualmente
      criando 2-3 usuarios de teste antes de migrar (ou usando um fixture),
      rodando a migration e conferindo o resultado.
- [ ] `venv/Scripts/python manage.py check` sem erros.

---

# Riscos

- **Irreversibilidade parcial**: o reverse desta migration remove os Groups
  e Permissions, mas nao reverte `is_superuser=True` nem as memberships de
  Comum ja atribuidas - nao ha como saber, ao reverter, quais contas ja
  eram superuser antes. Documentar isso no proprio arquivo de migration
  (comentario) para quem for ler o historico depois.
- `apps.get_model(*settings.AUTH_USER_MODEL.split('.'))` assume o formato
  padrao "app_label.ModelName" de AUTH_USER_MODEL (o projeto nao customiza
  esse setting - confirmado em core/settings.py - entao o valor efetivo e
  'auth.User').
- Se esta migration rodar mais de uma vez por engano (ex.: fake-reapply),
  get_or_create em todos os pontos garante idempotencia - nao ha risco de
  duplicar Group/Permission.
