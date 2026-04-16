from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Contrato


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
