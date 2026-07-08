LIMITE_NOTIFICACOES_TOPBAR = 8


def notificacoes_usuario(request):
    """Últimas notificações do usuário logado, para o dropdown do sino na
    topbar (templates/base.html). Sem paginação, sem estado lida/não lida.
    """
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {}
    ultimas = user.notificacoes.all()[:LIMITE_NOTIFICACOES_TOPBAR]
    return {'ultimas_notificacoes_usuario': ultimas}
