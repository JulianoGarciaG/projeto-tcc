# Editada manualmente: Lancamento passa a indexar por Imovel (imovel
# obrigatorio, contrato opcional), ganha natureza (ganho/despesa) e recibo
# de origem. status vira exclusivo de ganho (pendente/efetivado); 'atrasado'
# deixa de ser gravado (calculado em runtime por Lancamento.vencido).
# RunPython popula imovel a partir de contrato.imovel e marca os registros
# existentes como natureza='ganho' (unico uso do model ate aqui) antes das
# constraints entrarem em vigor.

import django.db.models.deletion
from django.db import migrations, models


def preencher_imovel_e_natureza(apps, schema_editor):
    Lancamento = apps.get_model('imoveis', 'Lancamento')
    for lancamento in Lancamento.objects.select_related('contrato').all():
        lancamento.imovel_id = lancamento.contrato.imovel_id
        lancamento.natureza = 'ganho'
        if not lancamento.status or lancamento.status == 'atrasado':
            lancamento.status = 'pendente'
        elif lancamento.status == 'pago':
            lancamento.status = 'efetivado'
        lancamento.save(update_fields=['imovel', 'natureza', 'status'])


def reverter_imovel_e_natureza(apps, schema_editor):
    Lancamento = apps.get_model('imoveis', 'Lancamento')
    Lancamento.objects.filter(status='efetivado').update(status='pago')
    Lancamento.objects.filter(status='pendente').update(status='pendente')


class Migration(migrations.Migration):

    dependencies = [
        ('imoveis', '0015_cria_grupos_e_reclassifica_usuarios'),
    ]

    operations = [
        migrations.AddField(
            model_name='lancamento',
            name='imovel',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT,
                                    related_name='lancamentos', to='imoveis.imovel'),
        ),
        migrations.AddField(
            model_name='lancamento',
            name='natureza',
            field=models.CharField(
                choices=[('ganho', 'Ganho'), ('despesa', 'Despesa')],
                max_length=10, null=True,
            ),
        ),
        migrations.AddField(
            model_name='lancamento',
            name='recibo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='lancamentos', to='imoveis.recibo'),
        ),
        migrations.AlterField(
            model_name='lancamento',
            name='contrato',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name='lancamentos', to='imoveis.contrato'),
        ),
        migrations.AlterField(
            model_name='lancamento',
            name='status',
            field=models.CharField(
                blank=True, null=True,
                choices=[('pendente', 'Pendente'), ('efetivado', 'Efetivado')],
                max_length=20,
            ),
        ),
        migrations.RunPython(preencher_imovel_e_natureza, reverter_imovel_e_natureza),
        migrations.AlterField(
            model_name='lancamento',
            name='imovel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                    related_name='lancamentos', to='imoveis.imovel'),
        ),
        migrations.AlterField(
            model_name='lancamento',
            name='natureza',
            field=models.CharField(choices=[('ganho', 'Ganho'), ('despesa', 'Despesa')], max_length=10),
        ),
        migrations.AddConstraint(
            model_name='lancamento',
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(natureza='despesa', status__isnull=True)
                    | models.Q(natureza='ganho', status__isnull=False)
                ),
                name='lancamento_status_apenas_ganho',
            ),
        ),
    ]
