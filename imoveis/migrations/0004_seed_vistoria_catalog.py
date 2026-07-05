from django.db import migrations

CATALOGO = [
    ('Sala', [
        'Paredes e pintura',
        'Piso',
        'Teto e forro',
        'Portas e janelas',
        'Instalações elétricas',
    ]),
    ('Cozinha', [
        'Paredes e pintura',
        'Piso',
        'Teto e forro',
        'Portas e janelas',
        'Instalações elétricas',
        'Louças e metais',
        'Bancada e armários',
        'Instalações hidráulicas',
    ]),
    ('Quarto', [
        'Paredes e pintura',
        'Piso',
        'Teto e forro',
        'Portas e janelas',
        'Instalações elétricas',
        'Armários embutidos',
    ]),
    ('Banheiro', [
        'Paredes e pintura',
        'Piso',
        'Teto e forro',
        'Portas e janelas',
        'Instalações elétricas',
        'Louças e metais',
        'Box e azulejos',
        'Instalações hidráulicas',
    ]),
    ('Área externa', [
        'Paredes e pintura',
        'Piso e revestimentos',
        'Portões e gradis',
        'Instalações elétricas',
        'Instalações hidráulicas',
    ]),
]


def seed_catalogo(apps, schema_editor):
    ComodoTemplate = apps.get_model('imoveis', 'ComodoTemplate')
    ItemVistoriaTemplate = apps.get_model('imoveis', 'ItemVistoriaTemplate')
    for ordem_comodo, (nome_comodo, itens) in enumerate(CATALOGO):
        comodo = ComodoTemplate.objects.create(nome=nome_comodo, ordem=ordem_comodo)
        ItemVistoriaTemplate.objects.bulk_create([
            ItemVistoriaTemplate(comodo=comodo, nome=nome_item, ordem=ordem_item)
            for ordem_item, nome_item in enumerate(itens)
        ])


def unseed_catalogo(apps, schema_editor):
    ComodoTemplate = apps.get_model('imoveis', 'ComodoTemplate')
    ComodoTemplate.objects.filter(nome__in=[nome for nome, _ in CATALOGO]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('imoveis', '0003_comodotemplate_contrato_documento_gerado_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_catalogo, unseed_catalogo),
    ]
