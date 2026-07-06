# Rodada 2 — L2: a opção "Vistoria Periódica" deixa de existir.
# Reclassifica os laudos existentes com tipo='periodica' para 'entrada'
# (valor mais neutro, decisão confirmada pelo usuário) ANTES da migração
# de schema que remove a choice.
from django.db import migrations


def reclassificar_periodica(apps, schema_editor):
    LaudoVistoria = apps.get_model('imoveis', 'LaudoVistoria')
    LaudoVistoria.objects.filter(tipo='periodica').update(tipo='entrada')


def reverter(apps, schema_editor):
    # Irreversível por natureza: não há como saber quais laudos 'entrada'
    # eram originalmente 'periodica'. O reverse é um no-op documentado.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('imoveis', '0004_seed_vistoria_catalog'),
    ]

    operations = [
        migrations.RunPython(reclassificar_periodica, reverter),
    ]
