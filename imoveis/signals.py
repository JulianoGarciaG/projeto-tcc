from datetime import date

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Contrato, HistoricoStatusImovel, Imovel, Lancamento, Recibo


def _registrar_transicao_status(imovel):
    """Fecha o período de status anterior e abre um novo, se o status mudou.

    Idempotente: salvar o imóvel sem trocar o status não cria linha nova.
    Captura toda origem de mudança (signal de contrato e edição manual, única
    forma de chegar a 'manutencao'), pois escuta o post_save do próprio Imovel.
    """
    ultimo = (imovel.historico_status
              .filter(data_fim__isnull=True)
              .order_by('-data_inicio')
              .first())
    if ultimo and ultimo.status == imovel.status:
        return
    agora = timezone.now()
    if ultimo:
        ultimo.data_fim = agora
        ultimo.save(update_fields=['data_fim'])
    HistoricoStatusImovel.objects.create(
        imovel=imovel, status=imovel.status, data_inicio=agora,
    )


@receiver(post_save, sender=Imovel)
def imovel_salvo(sender, instance, **kwargs):
    _registrar_transicao_status(instance)


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
