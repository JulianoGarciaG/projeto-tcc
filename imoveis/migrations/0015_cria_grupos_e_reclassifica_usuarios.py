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
        defaults={'name': 'Pode acessar o módulo Financeiro'},
    )

    owner_group, _ = Group.objects.get_or_create(name='Owner')
    owner_group.permissions.set([perm_dashboard, perm_financeiro])

    comum_group, _ = Group.objects.get_or_create(name='Comum')

    # Reclassifica usuários já existentes no banco neste momento.
    User.objects.filter(is_staff=True, is_superuser=False).update(is_superuser=True)
    for user in User.objects.filter(is_staff=False):
        user.groups.add(comum_group)


def reverte_grupos(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    # Remove apenas os registros criados por esta migration. NAO desfaz
    # is_superuser=True nem memberships de Comum atribuídas a usuários reais
    # (irreversível por design - ver módulo 02 do plano perfis-usuario).
    Group.objects.filter(name__in=['Owner', 'Comum']).delete()
    Permission.objects.filter(
        codename__in=['pode_acessar_dashboard', 'pode_acessar_financeiro'],
        content_type__app_label='imoveis', content_type__model='permissaotela',
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('imoveis', '0014_permissaotela'),
        ('auth', '__latest__'),
        ('contenttypes', '__latest__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(cria_grupos_e_permissoes, reverte_grupos),
    ]
