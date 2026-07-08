from django.contrib.messages import constants
from django.contrib.messages.storage.fallback import FallbackStorage

from imoveis.models import NotificacaoUsuario

_NIVEL_POR_LEVEL = {
    constants.SUCCESS: 'success',
    constants.ERROR: 'error',
    constants.WARNING: 'warning',
    constants.INFO: 'info',
    constants.DEBUG: 'info',
}


class PersistentFallbackStorage(FallbackStorage):
    """FallbackStorage padrão do Django + persistência em NotificacaoUsuario.

    Não altera o comportamento de exibição dos toasts (base.html continua
    consumindo request._messages normalmente) — apenas grava uma cópia
    permanente por usuário autenticado.
    """

    def add(self, level, message, extra_tags=''):
        super().add(level, message, extra_tags=extra_tags)
        user = getattr(self.request, 'user', None)
        if user is not None and user.is_authenticated and message:
            NotificacaoUsuario.objects.create(
                usuario=user,
                mensagem=message,
                nivel=_NIVEL_POR_LEVEL.get(level, 'info'),
            )
