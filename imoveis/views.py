from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Sum, Avg, Count, Q, ProtectedError, F
from django.db.models.functions import Coalesce
from django.http import Http404, JsonResponse
from datetime import date, datetime, timedelta

from django.utils import timezone

from .models import (
    Imovel, Proprietario, Inquilino, Contrato, LaudoVistoria, Lancamento,
    FotoImovel, Notificacao, Distrato,
    Recibo, ItemVistoriaTemplate, ItemVistoria, FotoItemVistoria,
    HistoricoStatusImovel, DocumentoContrato,
)
from .forms import (
    ImovelForm, FotoImovelFormSet, ProprietarioForm, InquilinoForm,
    ContratoForm, FiadorFormSet, LaudoVistoriaForm, LancamentoForm,
    NotificacaoForm, RenovacaoContratoForm, DistratoForm, ReajusteContratoForm,
    ReciboForm, ItemVistoriaFormSet, TestemunhaFormSet, item_vistoria_formset_factory,
    DashboardFiltroForm,
)
from .extenso import meses_entre
from .pdf import gerar_e_anexar, pdf_download_response


# ============================================================
# Helpers de geração de PDF (documentos GED)
# ============================================================

def _gerar_pdf_contrato(contrato):
    contexto = {
        'contrato': contrato,
        'locador': settings.SHELTER_LOCADOR,
        'prazo_meses': meses_entre(contrato.data_inicio, contrato.data_fim),
    }
    pdf_bytes, filename = gerar_e_anexar(contrato, 'documentos/contrato_pdf.html',
                                         contexto, 'documento_gerado')
    return pdf_download_response(pdf_bytes, filename)


def _itens_agrupados(laudo):
    """Agrupa os itens do laudo por cômodo, preservando a ordem."""
    grupos = []
    for item in laudo.itens.all():
        if not grupos or grupos[-1]['comodo'] != item.comodo:
            grupos.append({'comodo': item.comodo, 'itens': []})
        grupos[-1]['itens'].append(item)
    return grupos


def _reindexar_ordem_itens(laudo):
    """Renumera `ordem` sequencialmente agrupando por cômodo (na ordem em que
    cada cômodo aparece pela primeira vez em `laudo.itens.all()`), garantindo
    que itens do mesmo cômodo fiquem contíguos quando reordenados por
    `ordem`. Necessário porque itens/cômodos adicionados dinamicamente no
    formset não têm como calcular a `ordem` exata que os mantém contíguos —
    sem isso, `_itens_agrupados` pode quebrar um cômodo em dois blocos."""
    grupos = {}
    for item in laudo.itens.all():
        grupos.setdefault(item.comodo, []).append(item)

    atualizar = []
    ordem = 0
    for itens in grupos.values():
        for item in itens:
            if item.ordem != ordem:
                item.ordem = ordem
                atualizar.append(item)
            ordem += 1
    if atualizar:
        ItemVistoria.objects.bulk_update(atualizar, ['ordem'])


def _salvar_fotos_itens(item_formset):
    """Roda depois de item_formset.save(): mapeia os arquivos enviados em
    cada linha do formset para o ItemVistoria já persistido (precisa de PK).
    Linhas puladas (extra sem mudança) não têm cleaned_data — ignorar."""
    for f in item_formset.forms:
        cleaned = getattr(f, 'cleaned_data', None)
        if not cleaned or cleaned.get('DELETE'):
            continue
        instance = f.instance
        if not instance.pk:
            continue
        arquivos = cleaned.get('fotos') or []
        if arquivos:
            FotoItemVistoria.objects.bulk_create(
                FotoItemVistoria(item=instance, imagem=arquivo) for arquivo in arquivos
            )


def _gerar_pdf_laudo(laudo):
    contexto = {
        'laudo': laudo,
        'grupos': _itens_agrupados(laudo),
        'resumo': laudo.resumo_vistoria(),
        'testemunhas': laudo.testemunhas.all(),
    }
    pdf_bytes, filename = gerar_e_anexar(laudo, 'documentos/laudo_pdf.html',
                                         contexto, 'documento_gerado')
    return pdf_download_response(pdf_bytes, filename)


def _gerar_pdf_recibo(recibo):
    pdf_bytes, filename = gerar_e_anexar(recibo, 'documentos/recibo_pdf.html',
                                         {'recibo': recibo}, 'arquivo')
    return pdf_download_response(pdf_bytes, filename)


def erro_403(request, exception=None):
    return render(request, '403.html', status=403)


# ============================================================
# Landing
# ============================================================

@login_required
def landing(request):
    hora = datetime.now().hour
    if hora < 12:
        saudacao = 'Bom dia'
    elif hora < 18:
        saudacao = 'Boa tarde'
    else:
        saudacao = 'Boa noite'
    return render(request, 'imoveis/landing.html', {'saudacao': saudacao})


# ============================================================
# Dashboard
# ============================================================

@login_required
def dashboard_imobiliario(request):
    tipo_filtro = request.GET.get('tipo', '')
    status_filtro = request.GET.get('status', '')
    # Seletor de imóvel da linha do tempo — independente dos filtros de
    # Tipo/Status acima, não afeta KPIs/donuts (brief do redesign visual).
    timeline_imovel_id = request.GET.get('timeline_imovel_id', '')

    # Janela fixa dos últimos 90 dias para o KPI de tempo médio de vacância
    # e para a linha do tempo (não há mais filtro de período na UI).
    hoje = date.today()
    janela_inicio = hoje - timedelta(days=90)
    janela_fim = hoje
    # Converte para datetime aware cobrindo o dia inteiro do fim.
    janela_inicio_dt = timezone.make_aware(datetime.combine(janela_inicio, datetime.min.time()))
    janela_fim_dt = timezone.make_aware(datetime.combine(janela_fim, datetime.max.time()))

    imoveis_qs = Imovel.objects.all()
    if tipo_filtro:
        imoveis_qs = imoveis_qs.filter(tipo=tipo_filtro)
    if status_filtro:
        imoveis_qs = imoveis_qs.filter(status=status_filtro)

    total_imoveis = imoveis_qs.count()
    vagos = imoveis_qs.filter(status='vago').count()
    ocupados = imoveis_qs.filter(status='ocupado').count()
    manutencao = imoveis_qs.filter(status='manutencao').count()
    contratos_ativos = Contrato.objects.filter(status='ativo').count()
    taxa_vacancia = round((vagos / total_imoveis * 100), 1) if total_imoveis else 0

    # Donut — distribuição por situação do imóvel
    pizza_labels = ['Ocupados', 'Vagos', 'Em Manutenção']
    pizza_data = [ocupados, vagos, manutencao]

    # Donut — distribuição por tipo de imóvel
    tipo_labels = [label for _, label in Imovel.TIPO_CHOICES]
    contagem_por_tipo = dict(
        imoveis_qs.values_list('tipo').annotate(total=Count('pk')).values_list('tipo', 'total')
    )
    tipo_data = [contagem_por_tipo.get(valor, 0) for valor, _ in Imovel.TIPO_CHOICES]

    contratos_atencao = []
    for c in Contrato.objects.filter(status='ativo').select_related('imovel', 'inquilino'):
        if not c.precisa_atencao:
            continue
        # Mesmo critério de janela de Contrato.precisa_atencao (30 dias antes a 7
        # dias depois): rotula pela âncora que efetivamente disparou o aviso.
        dias_para_fim = (c.data_fim - hoje).days
        if -7 <= dias_para_fim <= 30:
            motivo = 'Fim de vigência'
            prazo = f'{dias_para_fim} dia(s)'
        else:
            motivo = 'Aniversário de reajuste'
            prazo = c.data_inicio.strftime('%d/%m')
        contratos_atencao.append({
            'imovel': c.imovel, 'inquilino': c.inquilino,
            'motivo': motivo, 'prazo': prazo,
        })

    # --- Tempo Médio de Vacância (agregado) ---
    # Períodos de vacância concluídos (data_fim preenchida) que se iniciaram
    # dentro da janela, respeitando os filtros de tipo/status.
    periodos_vagos = HistoricoStatusImovel.objects.filter(
        imovel__in=imoveis_qs, status='vago', data_fim__isnull=False,
        data_inicio__gte=janela_inicio_dt, data_inicio__lte=janela_fim_dt,
    )
    amostra_vacancia = 0
    soma_dias = 0
    for periodo in periodos_vagos:
        amostra_vacancia += 1
        soma_dias += (periodo.data_fim - periodo.data_inicio).days
    if amostra_vacancia:
        tempo_medio_vacancia = round(soma_dias / amostra_vacancia, 1)
        vacancia_sem_dados = False
    else:
        tempo_medio_vacancia = None
        vacancia_sem_dados = True

    # --- Linha do tempo de status: seletor de imóvel independente dos
    # filtros de Tipo/Status, sempre visível. Sem seleção, usa o primeiro
    # imóvel cadastrado (ordenado por endereço) como padrão.
    imoveis_lista = Imovel.objects.all().order_by('endereco')
    if timeline_imovel_id:
        imovel_selecionado = imoveis_lista.filter(pk=timeline_imovel_id).first()
    else:
        imovel_selecionado = imoveis_lista.first()

    imovel_timeline = None
    if imovel_selecionado:
        periodos = (imovel_selecionado.historico_status
                    .filter(data_inicio__lte=janela_fim_dt)
                    .filter(Q(data_fim__isnull=True) | Q(data_fim__gte=janela_inicio_dt))
                    .order_by('data_inicio'))
        imovel_timeline = [
            {
                'status': p.status,
                'label': p.get_status_display(),
                'data_inicio': p.data_inicio,
                'data_fim': p.data_fim,
                'dias': p.duracao_dias,
                'em_aberto': p.data_fim is None,
            }
            for p in periodos
        ]

    context = {
        'total_imoveis': total_imoveis,
        'vagos': vagos,
        'ocupados': ocupados,
        'manutencao': manutencao,
        'contratos_ativos': contratos_ativos,
        'taxa_vacancia': taxa_vacancia,
        'pizza_labels': pizza_labels,
        'pizza_data': pizza_data,
        'tipo_labels': tipo_labels,
        'tipo_data': tipo_data,
        'contratos_atencao': contratos_atencao,
        # Tempo médio de vacância (dado real a partir do lançamento da feature)
        'tempo_medio_vacancia': tempo_medio_vacancia,
        'vacancia_sem_dados': vacancia_sem_dados,
        'amostra_vacancia': amostra_vacancia,
        # Linha do tempo de status (seletor de imóvel independente)
        'imovel_timeline': imovel_timeline,
        'imovel_selecionado': imovel_selecionado,
        'timeline_imovel_id': str(imovel_selecionado.pk) if imovel_selecionado else '',
        # Filtros
        'imoveis_lista': imoveis_lista,
        'filtro_tipo': tipo_filtro,
        'filtro_status': status_filtro,
        'tipo_choices': Imovel.TIPO_CHOICES,
        'status_choices': Imovel.STATUS_CHOICES,
    }
    return render(request, 'imoveis/dashboard_imobiliario.html', context)


def _dashboard_financeiro_context(request):
    """Monta o contexto de KPIs/gráficos do dashboard financeiro,
    reutilizando os filtros de data/imóvel da tela de Financeiro."""
    hoje = date.today()

    imovel_ids = [v for v in request.GET.getlist('imovel_id') if v]
    filtro_form = DashboardFiltroForm(request.GET)
    data_inicio = data_fim = None
    if filtro_form.is_valid():
        data_inicio = filtro_form.cleaned_data.get('data_inicio')
        data_fim = filtro_form.cleaned_data.get('data_fim')

    lancamentos_qs = Lancamento.objects.select_related('imovel', 'contrato__inquilino').annotate(
        data_caixa=Coalesce(F('data_pagamento'), F('data_vencimento')),
    )
    imoveis_qs = Imovel.objects.all()

    if imovel_ids:
        lancamentos_qs = lancamentos_qs.filter(imovel_id__in=imovel_ids)
        imoveis_qs = imoveis_qs.filter(pk__in=imovel_ids)
    if data_inicio:
        lancamentos_qs = lancamentos_qs.filter(data_caixa__gte=data_inicio)
    if data_fim:
        lancamentos_qs = lancamentos_qs.filter(data_caixa__lte=data_fim)

    # KPIs do período
    ganhos_periodo = lancamentos_qs.filter(
        natureza='ganho', status='efetivado',
    ).aggregate(total=Sum('valor'))['total'] or 0
    despesas_periodo = lancamentos_qs.filter(
        natureza='despesa',
    ).aggregate(total=Sum('valor'))['total'] or 0
    saldo_periodo = ganhos_periodo - despesas_periodo
    total_pendente = lancamentos_qs.filter(
        natureza='ganho', status='pendente',
    ).aggregate(total=Sum('valor'))['total'] or 0

    alugueis_ativos = lancamentos_qs.filter(natureza='ganho', tipo='aluguel')
    ticket_medio_aluguel = alugueis_ativos.aggregate(media=Avg('valor'))['media'] or 0

    total_ganhos_count = lancamentos_qs.filter(natureza='ganho').count()
    inadimplentes_count = lancamentos_qs.filter(
        natureza='ganho', status='pendente', data_vencimento__lt=hoje,
    ).count()
    pct_inadimplencia = round((inadimplentes_count / total_ganhos_count * 100), 1) if total_ganhos_count else 0

    # Gráfico de barras — ganhos x despesas por mês.
    # Sem filtro de data: últimos 6 meses fixos. Com filtro (início e/ou
    # fim): todos os meses do período informado (mínimo 1 mês).
    if data_inicio or data_fim:
        evolucao_titulo = 'ganhos vs despesas · período filtrado'
        mes_inicial = (data_inicio or data_fim).replace(day=1)
        mes_final = (data_fim or data_inicio).replace(day=1)
        meses_periodo = []
        cursor = mes_inicial
        while cursor <= mes_final:
            meses_periodo.append(cursor)
            cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
    else:
        evolucao_titulo = 'ganhos vs despesas · últimos 6 meses'
        mes_atual = hoje.replace(day=1)
        meses_periodo = []
        cursor = mes_atual
        for _ in range(6):
            meses_periodo.append(cursor)
            cursor = (cursor.replace(day=1) - timedelta(days=1)).replace(day=1)
        meses_periodo.reverse()

    meses_labels = []
    meses_ganhos = []
    meses_despesas = []
    ganhos_qs = lancamentos_qs.filter(natureza='ganho')
    despesas_qs = lancamentos_qs.filter(natureza='despesa')
    for mes_ref in meses_periodo:
        meses_labels.append(mes_ref.strftime('%b/%Y'))
        ganhos_mes = ganhos_qs.filter(
            data_caixa__year=mes_ref.year,
            data_caixa__month=mes_ref.month,
        ).aggregate(total=Sum('valor'))['total'] or 0
        despesas_mes = despesas_qs.filter(
            data_caixa__year=mes_ref.year,
            data_caixa__month=mes_ref.month,
        ).aggregate(total=Sum('valor'))['total'] or 0
        meses_ganhos.append(float(ganhos_mes))
        meses_despesas.append(float(despesas_mes))

    # Rentabilidade por imóvel: ganhos efetivados - despesas
    ganhos_por_imovel = dict(
        lancamentos_qs.filter(natureza='ganho', status='efetivado')
        .values_list('imovel_id').annotate(total=Sum('valor')).values_list('imovel_id', 'total')
    )
    despesas_por_imovel = dict(
        lancamentos_qs.filter(natureza='despesa')
        .values_list('imovel_id').annotate(total=Sum('valor')).values_list('imovel_id', 'total')
    )
    rentabilidade_por_imovel = sorted(
        (
            {
                'imovel': imovel,
                'ganhos': ganhos_por_imovel.get(imovel.pk, 0) or 0,
                'despesas': despesas_por_imovel.get(imovel.pk, 0) or 0,
                'saldo': (ganhos_por_imovel.get(imovel.pk, 0) or 0) - (despesas_por_imovel.get(imovel.pk, 0) or 0),
            }
            for imovel in imoveis_qs
            if imovel.pk in ganhos_por_imovel or imovel.pk in despesas_por_imovel
        ),
        key=lambda r: r['saldo'],
        reverse=True,
    )

    # Donut — composição de despesas por categoria
    despesas_por_tipo = dict(
        lancamentos_qs.filter(natureza='despesa')
        .values_list('tipo').annotate(total=Sum('valor')).values_list('tipo', 'total')
    )
    categoria_labels = [label for valor, label in Lancamento.TIPO_CHOICES if despesas_por_tipo.get(valor)]
    categoria_data = [float(despesas_por_tipo[valor]) for valor, _ in Lancamento.TIPO_CHOICES if despesas_por_tipo.get(valor)]

    # Lançamentos pendentes mais antigos
    pendentes_antigos = lancamentos_qs.filter(
        natureza='ganho', status='pendente',
    ).order_by('data_vencimento')[:5]
    pendentes_antigos = [
        {'lancamento': l, 'atraso_dias': (hoje - l.data_vencimento).days if l.data_vencimento < hoje else 0}
        for l in pendentes_antigos
    ]

    return {
        'ganhos_periodo': ganhos_periodo,
        'despesas_periodo': despesas_periodo,
        'saldo_periodo': saldo_periodo,
        'dash_total_pendente': total_pendente,
        'ticket_medio_aluguel': ticket_medio_aluguel,
        'pct_inadimplencia': pct_inadimplencia,
        'meses_labels': meses_labels,
        'meses_ganhos': meses_ganhos,
        'meses_despesas': meses_despesas,
        'evolucao_titulo': evolucao_titulo,
        'rentabilidade_por_imovel': rentabilidade_por_imovel,
        'categoria_labels': categoria_labels,
        'categoria_data': categoria_data,
        'pendentes_antigos': pendentes_antigos,
        # Filtros do dashboard
        'dash_imoveis_lista': Imovel.objects.all(),
        'dash_filtro_imovel_ids': imovel_ids,
        'dash_filtro_form': filtro_form,
    }


# ============================================================
# Imóveis
# ============================================================

@login_required
def imovel_list(request):
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    tipo = request.GET.get('tipo', '')

    imoveis = Imovel.objects.select_related('proprietario').prefetch_related('fotos')
    if q:
        imoveis = imoveis.filter(Q(endereco__icontains=q) | Q(bairro__icontains=q) | Q(cidade__icontains=q))
    if status:
        imoveis = imoveis.filter(status=status)
    if tipo:
        imoveis = imoveis.filter(tipo=tipo)

    return render(request, 'imoveis/imovel_list.html', {
        'imoveis': imoveis,
        'q': q, 'status': status, 'tipo': tipo,
        'status_choices': Imovel.STATUS_CHOICES,
        'tipo_choices': Imovel.TIPO_CHOICES,
    })


@login_required
def imovel_detail(request, pk):
    imovel = get_object_or_404(Imovel, pk=pk)
    contratos = imovel.contratos.select_related('inquilino').order_by('-data_inicio')
    laudos = imovel.laudos.order_by('-data')
    fotos = imovel.fotos.all()
    notificacoes = imovel.notificacoes.order_by('-data_recebimento')
    contrato_ativo = imovel.contratos.filter(status='ativo').order_by('-data_inicio').first()
    planta_e_imagem = bool(
        imovel.planta_projeto
        and imovel.planta_projeto.name.lower().endswith(
            ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'))
    )

    # Histórico de status completo do imóvel (sem recorte de período, sem
    # seletor — diferente da timeline de 90 dias do dashboard).
    historico = imovel.historico_status.order_by('data_inicio')
    imovel_timeline = [
        {
            'status': h.status,
            'label': h.get_status_display(),
            'data_inicio': h.data_inicio,
            'data_fim': h.data_fim,
            'dias': h.duracao_dias,
            'em_aberto': h.data_fim is None,
        }
        for h in historico
    ]
    dias_por_status = {'vago': 0, 'ocupado': 0, 'manutencao': 0}
    for h in historico:
        dias_por_status[h.status] = dias_por_status.get(h.status, 0) + h.duracao_dias

    return render(request, 'imoveis/imovel_detail.html', {
        'imovel': imovel,
        'contratos': contratos,
        'laudos': laudos,
        'fotos': fotos,
        'notificacoes': notificacoes,
        'contrato_ativo': contrato_ativo,
        'planta_e_imagem': planta_e_imagem,
        'imovel_timeline': imovel_timeline,
        'dias_vago': dias_por_status['vago'],
        'dias_ocupado': dias_por_status['ocupado'],
        'dias_manutencao': dias_por_status['manutencao'],
    })


@login_required
def imovel_create(request):
    form = ImovelForm(request.POST or None, request.FILES or None)
    foto_formset = FotoImovelFormSet(request.POST or None, request.FILES or None)
    if form.is_valid() and foto_formset.is_valid():
        imovel = form.save()
        foto_formset.instance = imovel
        foto_formset.save()
        messages.success(request, 'Imóvel cadastrado com sucesso.')
        return redirect('imovel_list')
    return render(request, 'imoveis/imovel_form.html', {
        'form': form, 'foto_formset': foto_formset, 'titulo': 'Novo Imóvel'
    })


@login_required
def imovel_edit(request, pk):
    imovel = get_object_or_404(Imovel, pk=pk)
    if request.method == 'POST':
        form = ImovelForm(request.POST, request.FILES, instance=imovel)
        foto_formset = FotoImovelFormSet(request.POST, request.FILES, instance=imovel)
        if form.is_valid() and foto_formset.is_valid():
            form.save()
            foto_formset.save()
            messages.success(request, 'Imóvel atualizado.')
            return redirect('imovel_detail', pk=pk)
    else:
        form = ImovelForm(instance=imovel)
        foto_formset = FotoImovelFormSet(instance=imovel)
    return render(request, 'imoveis/imovel_form.html', {
        'form': form, 'foto_formset': foto_formset, 'titulo': 'Editar Imóvel', 'obj': imovel
    })


@login_required
def imovel_delete(request, pk):
    imovel = get_object_or_404(Imovel, pk=pk)
    if request.method == 'POST':
        try:
            imovel.delete()
        except ProtectedError:
            messages.error(request, 'Este imóvel não pode ser excluído: há contratos '
                                    'ou recibos vinculados a ele. Exclua-os primeiro.')
            return redirect('imovel_list')
        messages.success(request, 'Imóvel removido.')
    return redirect('imovel_list')


# ============================================================
# Proprietários
# ============================================================

@login_required
def proprietario_list(request):
    q = request.GET.get('q', '')
    qs = Proprietario.objects.all()
    if q:
        qs = qs.filter(Q(nome__icontains=q) | Q(cpf_cnpj__icontains=q))
    return render(request, 'proprietarios/proprietario_list.html', {'proprietarios': qs, 'q': q})


@login_required
def proprietario_create(request):
    form = ProprietarioForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Proprietário cadastrado com sucesso.')
        return redirect('proprietario_list')
    return render(request, 'proprietarios/proprietario_form.html', {'form': form, 'titulo': 'Novo Proprietário'})


@login_required
def proprietario_edit(request, pk):
    obj = get_object_or_404(Proprietario, pk=pk)
    form = ProprietarioForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Proprietário atualizado.')
        return redirect('proprietario_list')
    return render(request, 'proprietarios/proprietario_form.html', {'form': form, 'titulo': 'Editar Proprietário', 'obj': obj})


@login_required
def proprietario_delete(request, pk):
    obj = get_object_or_404(Proprietario, pk=pk)
    if request.method == 'POST':
        try:
            obj.delete()
        except ProtectedError:
            messages.error(request, 'Este proprietário não pode ser excluído: possui '
                                    'imóveis vinculados. Exclua-os primeiro.')
            return redirect('proprietario_list')
        messages.success(request, 'Proprietário removido.')
    return redirect('proprietario_list')


# ============================================================
# Inquilinos
# ============================================================

@login_required
def inquilino_list(request):
    q = request.GET.get('q', '')
    qs = Inquilino.objects.all()
    if q:
        qs = qs.filter(Q(nome__icontains=q) | Q(cpf__icontains=q))
    return render(request, 'inquilinos/inquilino_list.html', {'inquilinos': qs, 'q': q})


@login_required
def inquilino_create(request):
    form = InquilinoForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Inquilino cadastrado com sucesso.')
        return redirect('inquilino_list')
    return render(request, 'inquilinos/inquilino_form.html', {'form': form, 'titulo': 'Novo Inquilino'})


@login_required
def inquilino_edit(request, pk):
    obj = get_object_or_404(Inquilino, pk=pk)
    form = InquilinoForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Inquilino atualizado.')
        return redirect('inquilino_list')
    return render(request, 'inquilinos/inquilino_form.html', {'form': form, 'titulo': 'Editar Inquilino', 'obj': obj})


@login_required
def inquilino_delete(request, pk):
    obj = get_object_or_404(Inquilino, pk=pk)
    if request.method == 'POST':
        try:
            obj.delete()
        except ProtectedError:
            messages.error(request, 'Este inquilino não pode ser excluído: possui '
                                    'contratos vinculados. Exclua-os primeiro.')
            return redirect('inquilino_list')
        messages.success(request, 'Inquilino removido.')
    return redirect('inquilino_list')


# ============================================================
# Contratos
# ============================================================

@login_required
def contrato_list(request):
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    atencao = request.GET.get('atencao', '')
    qs = Contrato.objects.select_related('imovel', 'inquilino')
    if q:
        qs = qs.filter(Q(inquilino__nome__icontains=q) | Q(imovel__endereco__icontains=q))
    if status:
        qs = qs.filter(status=status)
    contratos = list(qs)
    if atencao == 'sim':
        contratos = [c for c in contratos if c.precisa_atencao]
    elif atencao == 'nao':
        contratos = [c for c in contratos if not c.precisa_atencao]
    return render(request, 'contratos/contrato_list.html', {
        'contratos': contratos, 'q': q, 'status': status, 'atencao': atencao,
        'status_choices': Contrato.STATUS_CHOICES,
    })


@login_required
def contrato_detail(request, pk):
    contrato = get_object_or_404(
        Contrato.objects.select_related('imovel', 'inquilino')
        .prefetch_related('documentos_pessoais'), pk=pk)
    lancamentos = contrato.lancamentos.order_by('-data_vencimento')
    laudos = contrato.laudos.order_by('-data')
    fiadores = contrato.fiadores.all()
    recibos = contrato.recibos.all()
    renovacoes = contrato.renovacoes.all()
    try:
        distrato = contrato.distrato
    except Distrato.DoesNotExist:
        distrato = None
    return render(request, 'contratos/contrato_detail.html', {
        'contrato': contrato,
        'lancamentos': lancamentos,
        'laudos': laudos,
        'fiadores': fiadores,
        'recibos': recibos,
        'renovacoes': renovacoes,
        'distrato': distrato,
    })


@login_required
def contrato_create(request):
    form = ContratoForm(request.POST or None, request.FILES or None)
    fiador_formset = FiadorFormSet(request.POST or None, request.FILES or None)
    if form.is_valid() and fiador_formset.is_valid():
        contrato = form.save()
        fiador_formset.instance = contrato
        fiador_formset.save()
        messages.success(request, 'Contrato cadastrado com sucesso. Use "Regerar Contrato (PDF)" para gerar o documento.')
        return redirect('contrato_detail', pk=contrato.pk)
    return render(request, 'contratos/contrato_form.html', {
        'form': form, 'fiador_formset': fiador_formset, 'titulo': 'Novo Contrato'
    })


@login_required
def contrato_edit(request, pk):
    obj = get_object_or_404(Contrato, pk=pk)
    if request.method == 'POST':
        form = ContratoForm(request.POST, request.FILES, instance=obj)
        fiador_formset = FiadorFormSet(request.POST, request.FILES, instance=obj)
        if form.is_valid() and fiador_formset.is_valid():
            contrato = form.save()
            fiador_formset.save()
            messages.success(request, 'Contrato atualizado.')
            return redirect('contrato_detail', pk=contrato.pk)
    else:
        form = ContratoForm(instance=obj)
        fiador_formset = FiadorFormSet(instance=obj)
    return render(request, 'contratos/contrato_form.html', {
        'form': form, 'fiador_formset': fiador_formset, 'titulo': 'Editar Contrato', 'obj': obj
    })


@login_required
def contrato_gerar_pdf(request, pk):
    contrato = get_object_or_404(Contrato.objects.select_related('imovel', 'inquilino'), pk=pk)
    return _gerar_pdf_contrato(contrato)


# Campos de documento (GED) do contrato anexáveis pela tela de detalhe.
CAMPOS_DOCUMENTO_CONTRATO = (
    'comprovante_renda', 'contrato_social', 'recibo_chaves', 'comprovante_anual',
)


@login_required
def contrato_anexar_documento(request, pk, campo):
    """Anexo dos documentos GED do contrato, enviado a partir do detail
    (mesmo padrão do laudo_anexar_arquivo)."""
    contrato = get_object_or_404(Contrato, pk=pk)
    if campo not in CAMPOS_DOCUMENTO_CONTRATO:
        raise Http404('Documento inválido.')
    if request.method == 'POST':
        arquivo = request.FILES.get('arquivo')
        if arquivo:
            setattr(contrato, campo, arquivo)
            contrato.save(update_fields=[campo])
            messages.success(request, 'Documento anexado ao contrato com sucesso.')
        else:
            messages.error(request, 'Selecione um arquivo para anexar.')
    return redirect('contrato_detail', pk=pk)


@login_required
def contrato_documento_pessoal_upload(request, pk):
    """Anexo de múltiplos documentos pessoais avulsos ao contrato, enviados a
    partir do detail. Uma linha DocumentoContrato por arquivo; aceita vários de
    uma vez (input multiple) e formatos variados, como os demais anexos."""
    contrato = get_object_or_404(Contrato, pk=pk)
    if request.method == 'POST':
        arquivos = request.FILES.getlist('arquivos')
        if arquivos:
            for arquivo in arquivos:
                DocumentoContrato.objects.create(
                    contrato=contrato, arquivo=arquivo, nome_original=arquivo.name)
            plural = 's' if len(arquivos) > 1 else ''
            messages.success(request,
                             f'{len(arquivos)} documento{plural} anexado{plural} ao contrato.')
        else:
            messages.error(request, 'Selecione ao menos um arquivo para anexar.')
    return redirect('contrato_detail', pk=pk)


@login_required
def contrato_documento_pessoal_delete(request, pk, doc_pk):
    """Remove um documento pessoal individual do contrato, sem afetar os demais."""
    contrato = get_object_or_404(Contrato, pk=pk)
    documento = get_object_or_404(DocumentoContrato, pk=doc_pk, contrato=contrato)
    if request.method == 'POST':
        documento.arquivo.delete(save=False)
        documento.delete()
        messages.success(request, 'Documento pessoal removido do contrato.')
    return redirect('contrato_detail', pk=pk)


@login_required
def contrato_delete(request, pk):
    obj = get_object_or_404(Contrato, pk=pk)
    if request.method == 'POST':
        try:
            obj.delete()
        except ProtectedError:
            messages.error(request, 'Este contrato não pode ser excluído: há laudos de vistoria '
                                    'ou recibos vinculados a ele. Exclua-os primeiro.')
            return redirect('contrato_detail', pk=pk)
        messages.success(request, 'Contrato removido.')
    return redirect('contrato_list')


# ============================================================
# Reajuste de Contrato
# ============================================================

@login_required
def contrato_reajuste(request, pk):
    contrato = get_object_or_404(Contrato, pk=pk)
    if not contrato.pode_reajustar:
        messages.warning(request, 'Este contrato não está elegível para reajuste no momento.')
        return redirect('contrato_detail', pk=pk)
    form = ReajusteContratoForm(request.POST or None, instance=contrato)
    if form.is_valid():
        contrato = form.save(commit=False)
        contrato.data_ultimo_reajuste = date.today()
        contrato.save()
        messages.success(request, 'Valor de cobrança reajustado com sucesso.')
        return redirect('contrato_detail', pk=pk)
    return render(request, 'contratos/reajuste_form.html', {
        'form': form, 'contrato': contrato, 'titulo': 'Reajuste de Aluguel'
    })


# ============================================================
# Renovação de Contrato
# ============================================================

@login_required
def renovacao_create(request, contrato_pk):
    contrato = get_object_or_404(Contrato, pk=contrato_pk)
    if contrato.status != 'ativo':
        messages.warning(request, 'Só é possível registrar renovação para contrato ativo.')
        return redirect('contrato_detail', pk=contrato_pk)
    form = RenovacaoContratoForm(request.POST or None)
    if form.is_valid():
        renovacao = form.save(commit=False)
        renovacao.contrato = contrato
        renovacao.save()
        messages.success(request, 'Renovação registrada com sucesso.')
        return redirect('contrato_detail', pk=contrato_pk)
    return render(request, 'contratos/renovacao_form.html', {
        'form': form, 'contrato': contrato, 'titulo': 'Registrar Renovação'
    })


# ============================================================
# Distrato de Contrato
# ============================================================

@login_required
def distrato_create(request, contrato_pk):
    contrato = get_object_or_404(Contrato, pk=contrato_pk)
    if hasattr(contrato, 'distrato'):
        messages.warning(request, 'Este contrato já possui um distrato registrado.')
        return redirect('contrato_detail', pk=contrato_pk)
    form = DistratoForm(request.POST or None, request.FILES or None)
    # Limitar laudo_saida aos laudos do imóvel
    form.fields['laudo_saida'].queryset = LaudoVistoria.objects.filter(imovel=contrato.imovel)
    if form.is_valid():
        distrato = form.save(commit=False)
        distrato.contrato = contrato
        distrato.save()
        messages.success(request, 'Distrato registrado. Contrato marcado como encerrado.')
        return redirect('contrato_detail', pk=contrato_pk)
    return render(request, 'contratos/distrato_form.html', {
        'form': form, 'contrato': contrato, 'titulo': 'Registrar Distrato'
    })


# ============================================================
# Laudos de Vistoria
# ============================================================

@login_required
def laudo_list(request):
    q = request.GET.get('q', '')
    tipo = request.GET.get('tipo', '')
    qs = LaudoVistoria.objects.select_related('imovel', 'contrato')
    if q:
        qs = qs.filter(Q(imovel__endereco__icontains=q) | Q(responsavel__icontains=q))
    if tipo:
        qs = qs.filter(tipo=tipo)
    return render(request, 'laudos/laudo_list.html', {
        'laudos': qs, 'q': q, 'tipo': tipo,
        'tipo_choices': LaudoVistoria.TIPO_CHOICES,
    })


def _initial_itens_catalogo():
    """Pré-popula o formset de itens a partir do catálogo configurável."""
    itens = ItemVistoriaTemplate.objects.select_related('comodo').order_by('comodo__ordem', 'ordem', 'nome')
    return [
        {'comodo': t.comodo.nome, 'item': t.nome, 'ordem': ordem}
        for ordem, t in enumerate(itens)
    ]


@login_required
def laudo_detail(request, pk):
    laudo = get_object_or_404(
        LaudoVistoria.objects.select_related('imovel__proprietario', 'contrato__inquilino')
        .prefetch_related('itens__fotos'), pk=pk)
    return render(request, 'laudos/laudo_detail.html', {
        'laudo': laudo,
        'grupos': _itens_agrupados(laudo),
        'resumo': laudo.resumo_vistoria(),
        'testemunhas': laudo.testemunhas.all(),
    })


@login_required
def laudo_create(request):
    # L4: o formset precisa de extra=len(catalogo) para as linhas de `initial`
    # renderizarem no GET (com extra=0 o formset novo gera 0 linhas).
    catalogo = _initial_itens_catalogo()
    CatalogoFormSet = item_vistoria_formset_factory(extra=len(catalogo))
    if request.method == 'POST':
        form = LaudoVistoriaForm(request.POST)
        # initial também no POST: linhas com estado em branco continuam
        # "inalteradas" (não vistoriadas) e são ignoradas pelo formset.
        item_formset = CatalogoFormSet(request.POST, request.FILES, prefix='itens', initial=catalogo)
        testemunha_formset = TestemunhaFormSet(request.POST, prefix='testemunhas')
        if form.is_valid() and item_formset.is_valid() and testemunha_formset.is_valid():
            laudo = form.save()
            item_formset.instance = laudo
            item_formset.save()
            _salvar_fotos_itens(item_formset)
            _reindexar_ordem_itens(laudo)
            testemunha_formset.instance = laudo
            testemunha_formset.save()
            messages.success(request, 'Laudo registrado com sucesso. Use "Regerar PDF" para gerar o documento.')
            return redirect('laudo_detail', pk=laudo.pk)
    else:
        form = LaudoVistoriaForm()
        item_formset = CatalogoFormSet(prefix='itens', initial=catalogo)
        testemunha_formset = TestemunhaFormSet(prefix='testemunhas')
    return render(request, 'laudos/laudo_form.html', {
        'form': form, 'item_formset': item_formset, 'testemunha_formset': testemunha_formset,
        'titulo': 'Novo Laudo de Vistoria',
    })


@login_required
def laudo_edit(request, pk):
    obj = get_object_or_404(LaudoVistoria, pk=pk)
    if request.method == 'POST':
        form = LaudoVistoriaForm(request.POST, instance=obj)
        item_formset = ItemVistoriaFormSet(request.POST, request.FILES, instance=obj, prefix='itens')
        testemunha_formset = TestemunhaFormSet(request.POST, instance=obj, prefix='testemunhas')
        if form.is_valid() and item_formset.is_valid() and testemunha_formset.is_valid():
            laudo = form.save()
            item_formset.save()
            _salvar_fotos_itens(item_formset)
            _reindexar_ordem_itens(laudo)
            testemunha_formset.save()
            messages.success(request, 'Laudo atualizado.')
            return redirect('laudo_detail', pk=laudo.pk)
    else:
        form = LaudoVistoriaForm(instance=obj)
        item_formset = ItemVistoriaFormSet(instance=obj, prefix='itens')
        testemunha_formset = TestemunhaFormSet(instance=obj, prefix='testemunhas')
    return render(request, 'laudos/laudo_form.html', {
        'form': form, 'item_formset': item_formset, 'testemunha_formset': testemunha_formset,
        'titulo': 'Editar Laudo', 'obj': obj,
    })


@login_required
def laudo_gerar_pdf(request, pk):
    laudo = get_object_or_404(
        LaudoVistoria.objects.select_related('imovel__proprietario', 'contrato__inquilino'), pk=pk)
    return _gerar_pdf_laudo(laudo)


@login_required
def laudo_anexar_arquivo(request, pk):
    """L6 — anexo do laudo assinado (pós-vistoria), enviado a partir do detail."""
    laudo = get_object_or_404(LaudoVistoria, pk=pk)
    if request.method == 'POST':
        arquivo = request.FILES.get('arquivo')
        if arquivo:
            laudo.arquivo = arquivo
            laudo.save(update_fields=['arquivo'])
            messages.success(request, 'Anexo do laudo salvo com sucesso.')
        else:
            messages.error(request, 'Selecione um arquivo para anexar.')
    return redirect('laudo_detail', pk=pk)


@login_required
def contratos_por_imovel_json(request, imovel_pk):
    """L1 — contratos de um imóvel, para popular o select dependente do laudo."""
    contratos = Contrato.objects.filter(imovel_id=imovel_pk).select_related('inquilino', 'imovel').order_by('-data_inicio')
    # rotulo_curto acessa self.inquilino.nome e self.imovel.endereco/numero — o select_related acima cobre ambos.
    dados = [{'id': c.pk, 'label': c.rotulo_curto, 'valor_cobranca': str(c.valor_cobranca)}
             for c in contratos]
    return JsonResponse({'contratos': dados})


@login_required
def laudo_delete(request, pk):
    obj = get_object_or_404(LaudoVistoria, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Laudo removido.')
    return redirect('laudo_list')


# ============================================================
# Lançamentos Financeiros
# ============================================================

@login_required
@permission_required('imoveis.pode_acessar_financeiro', raise_exception=True)
def lancamento_list(request):
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    tipo = request.GET.get('tipo', '')
    natureza = request.GET.get('natureza', '')
    imovel_ids = [v for v in request.GET.getlist('imovel_id') if v]
    qs = Lancamento.objects.select_related('imovel', 'contrato__inquilino')
    if q:
        qs = qs.filter(Q(contrato__inquilino__nome__icontains=q) | Q(imovel__endereco__icontains=q))
    if status:
        qs = qs.filter(status=status)
    if tipo:
        qs = qs.filter(tipo=tipo)
    if natureza:
        qs = qs.filter(natureza=natureza)
    if imovel_ids:
        qs = qs.filter(imovel_id__in=imovel_ids)

    context = {
        'lancamentos': qs,
        'q': q, 'status': status, 'tipo': tipo, 'natureza': natureza, 'imovel_ids': imovel_ids,
        'status_choices': Lancamento.STATUS_CHOICES,
        'tipo_choices': Lancamento.TIPO_CHOICES,
        'natureza_choices': Lancamento.NATUREZA_CHOICES,
        'imoveis_lista': Imovel.objects.all(),
    }
    context.update(_dashboard_financeiro_context(request))
    return render(request, 'financeiro/lancamento_list.html', context)


@login_required
@permission_required('imoveis.pode_acessar_financeiro', raise_exception=True)
def lancamento_create(request):
    form = LancamentoForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Lançamento registrado.')
        return redirect('lancamento_list')
    return render(request, 'financeiro/lancamento_form.html', {'form': form, 'titulo': 'Novo Lançamento'})


@login_required
@permission_required('imoveis.pode_acessar_financeiro', raise_exception=True)
def lancamento_edit(request, pk):
    obj = get_object_or_404(Lancamento, pk=pk)
    if request.method == 'POST':
        form = LancamentoForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lançamento atualizado.')
            return redirect('lancamento_list')
    else:
        form = LancamentoForm(instance=obj)
    return render(request, 'financeiro/lancamento_form.html', {'form': form, 'titulo': 'Editar Lançamento', 'obj': obj})



@login_required
@permission_required('imoveis.pode_acessar_financeiro', raise_exception=True)
def lancamento_delete(request, pk):
    obj = get_object_or_404(Lancamento, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Lançamento removido.')
    return redirect('lancamento_list')


@login_required
@permission_required('imoveis.pode_acessar_financeiro', raise_exception=True)
def lancamento_efetivar(request, pk):
    obj = get_object_or_404(Lancamento, pk=pk, natureza='ganho')
    if request.method == 'POST':
        obj.status = 'efetivado'
        obj.data_pagamento = obj.data_pagamento or date.today()
        obj.save(update_fields=['status', 'data_pagamento'])
        messages.success(request, 'Lançamento efetivado.')
    return redirect('lancamento_list')


# ============================================================
# Notificações
# ============================================================

@login_required
def notificacao_create(request, imovel_pk):
    imovel = get_object_or_404(Imovel, pk=imovel_pk)
    form = NotificacaoForm(request.POST or None, request.FILES or None,
                           initial={'imovel': imovel})
    form.fields['imovel'].initial = imovel
    if form.is_valid():
        form.save()
        messages.success(request, 'Notificação registrada.')
        return redirect('imovel_detail', pk=imovel_pk)
    return render(request, 'imoveis/notificacao_form.html', {
        'form': form, 'imovel': imovel, 'titulo': 'Nova Notificação'
    })


@login_required
def notificacao_edit(request, pk):
    obj = get_object_or_404(Notificacao, pk=pk)
    if request.method == 'POST':
        form = NotificacaoForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notificação atualizada.')
            return redirect('imovel_detail', pk=obj.imovel_id)
    else:
        form = NotificacaoForm(instance=obj)
    return render(request, 'imoveis/notificacao_form.html', {
        'form': form, 'imovel': obj.imovel, 'titulo': 'Editar Notificação'
    })


@login_required
def notificacao_delete(request, pk):
    obj = get_object_or_404(Notificacao, pk=pk)
    imovel_pk = obj.imovel_id
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Notificação removida.')
    return redirect('imovel_detail', pk=imovel_pk)


# ============================================================
# Recibos
# ============================================================

@login_required
def recibo_list(request):
    q = request.GET.get('q', '')
    qs = Recibo.objects.select_related('imovel', 'contrato__inquilino')
    if q:
        qs = qs.filter(Q(quem_pagou__icontains=q) | Q(assinante_nome__icontains=q) |
                       Q(imovel__endereco__icontains=q))
    return render(request, 'recibos/recibo_list.html', {'recibos': qs, 'q': q})


@login_required
def recibo_detail(request, pk):
    recibo = get_object_or_404(Recibo.objects.select_related('imovel', 'contrato__inquilino'), pk=pk)
    return render(request, 'recibos/recibo_detail.html', {'recibo': recibo})


@login_required
def recibo_create(request):
    form = ReciboForm(request.POST or None)
    if form.is_valid():
        recibo = form.save()
        messages.success(request, 'Recibo registrado com sucesso. Use "Regerar PDF" para gerar o documento.')
        return redirect('recibo_detail', pk=recibo.pk)
    return render(request, 'recibos/recibo_form.html', {'form': form, 'titulo': 'Novo Recibo'})


@login_required
def recibo_create_from_contrato(request, contrato_pk):
    contrato = get_object_or_404(Contrato, pk=contrato_pk)
    form = ReciboForm(request.POST or None,
                      initial={'imovel': contrato.imovel, 'contrato': contrato},
                      bloquear_imovel=True)
    if form.is_valid():
        recibo = form.save()
        messages.success(request, 'Recibo registrado com sucesso. Use "Regerar PDF" para gerar o documento.')
        return redirect('recibo_detail', pk=recibo.pk)
    return render(request, 'recibos/recibo_form.html', {'form': form, 'titulo': 'Novo Recibo'})


@login_required
def recibo_edit(request, pk):
    obj = get_object_or_404(Recibo, pk=pk)
    form = ReciboForm(request.POST or None, instance=obj)
    if form.is_valid():
        recibo = form.save()
        messages.success(request, 'Recibo atualizado.')
        return redirect('recibo_detail', pk=recibo.pk)
    return render(request, 'recibos/recibo_form.html', {'form': form, 'titulo': 'Editar Recibo', 'obj': obj})


@login_required
def recibo_gerar_pdf(request, pk):
    recibo = get_object_or_404(Recibo.objects.select_related('imovel', 'contrato__inquilino'), pk=pk)
    return _gerar_pdf_recibo(recibo)


@login_required
def recibo_delete(request, pk):
    obj = get_object_or_404(Recibo, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Recibo removido.')
    return redirect('recibo_list')


# ============================================================
# GED — Documentos centralizados
# ============================================================

@login_required
def documentos(request):
    # Documentos gerados pelo sistema: apenas o documento vigente de cada
    # origem (campos legados são a única fonte de verdade, sem histórico).
    contratos_gerados = (Contrato.objects.exclude(documento_gerado='')
                         .exclude(documento_gerado__isnull=True)
                         .select_related('imovel', 'inquilino'))
    laudos_gerados = (LaudoVistoria.objects.exclude(documento_gerado='')
                      .exclude(documento_gerado__isnull=True)
                      .select_related('imovel'))
    recibos = (Recibo.objects.exclude(arquivo='').exclude(arquivo__isnull=True)
               .select_related('imovel', 'contrato__inquilino'))
    # Anexos manuais (não versionados)
    laudos = LaudoVistoria.objects.exclude(arquivo='').exclude(arquivo__isnull=True).select_related('imovel')
    comprovantes = Lancamento.objects.exclude(comprovante='').select_related('contrato__imovel')
    contratos_recibo = Contrato.objects.exclude(recibo_chaves='').select_related('imovel', 'inquilino')
    contratos_anual = Contrato.objects.exclude(comprovante_anual='').select_related('imovel', 'inquilino')
    return render(request, 'ged/documentos.html', {
        'contratos_gerados': contratos_gerados,
        'laudos': laudos,
        'laudos_gerados': laudos_gerados,
        'comprovantes': comprovantes,
        'contratos_recibo': contratos_recibo,
        'contratos_anual': contratos_anual,
        'recibos': recibos,
    })
