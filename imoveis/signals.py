from datetime import date

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Contrato, Lancamento, Recibo


def _atualizar_status_imovel(imovel):
    if imovel.contratos.filter(status='ativo').exists():
        novo_status = 'ocupado'
    else:
        novo_status = 'vago'
    if imovel.status != novo_status:
        imovel.status = novo_status
        imovel.save(update_fields=['status'])


@receiver(post_save, sender=Contrato)
def contrato_salvo(sender, instance, **kwargs):
    _atualizar_status_imovel(instance.imovel)


@receiver(post_delete, sender=Contrato)
def contrato_deletado(sender, instance, **kwargs):
    _atualizar_status_imovel(instance.imovel)


@receiver(post_save, sender=Recibo)
def recibo_salvo(sender, instance, created, **kwargs):
    valor = instance.quantia or instance.somatorio() or 0
    vencimento = instance.vencido_em or instance.periodo_fim or date.today()
    if created:
        Lancamento.objects.create(
            natureza='ganho', tipo='aluguel', status='pendente',
            imovel=instance.imovel, contrato=instance.contrato, recibo=instance,
            valor=valor, data_vencimento=vencimento,
        )
        return
    ganho_pendente = instance.lancamentos.filter(status='pendente').first()
    if ganho_pendente:
        ganho_pendente.valor = valor
        ganho_pendente.data_vencimento = vencimento
        ganho_pendente.save(update_fields=['valor', 'data_vencimento'])
