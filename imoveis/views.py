from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, ProtectedError
from django.http import JsonResponse
from datetime import date, timedelta

from .models import (
    Imovel, Proprietario, Inquilino, Contrato, LaudoVistoria, Lancamento,
    FotoImovel, Notificacao, RenovacaoContrato, Distrato,
    Recibo, ItemVistoriaTemplate,
)
from .forms import (
    ImovelForm, FotoImovelFormSet, ProprietarioForm, InquilinoForm,
    ContratoForm, FiadorFormSet, LaudoVistoriaForm, LancamentoForm,
    NotificacaoForm, RenovacaoContratoForm, DistratoForm,
    ReciboForm, ItemVistoriaFormSet, TestemunhaFormSet, item_vistoria_formset_factory,
)
from .pdf import gerar_e_anexar, pdf_download_response


# ============================================================
# Helpers de geração de PDF (documentos GED)
# ============================================================

def _gerar_pdf_contrato(contrato):
    filename = f'contrato_{contrato.pk}.pdf'
    pdf_bytes = gerar_e_anexar(contrato, 'documentos/contrato_pdf.html',
                               {'contrato': contrato}, 'documento_gerado', filename)
    return pdf_download_response(pdf_bytes, filename)


def _itens_agrupados(laudo):
    """Agrupa os itens do laudo por cômodo, preservando a ordem."""
    grupos = []
    for item in laudo.itens.all():
        if not grupos or grupos[-1]['comodo'] != item.comodo:
            grupos.append({'comodo': item.comodo, 'itens': []})
        grupos[-1]['itens'].append(item)
    return grupos


def _gerar_pdf_laudo(laudo):
    filename = f'laudo_{laudo.pk}.pdf'
    contexto = {
        'laudo': laudo,
        'grupos': _itens_agrupados(laudo),
        'resumo': laudo.resumo_vistoria(),
        'testemunhas': laudo.testemunhas.all(),
    }
    pdf_bytes = gerar_e_anexar(laudo, 'documentos/laudo_pdf.html',
                               contexto, 'documento_gerado', filename)
    return pdf_download_response(pdf_bytes, filename)


def _gerar_pdf_recibo(recibo):
    filename = f'recibo_{recibo.pk}.pdf'
    pdf_bytes = gerar_e_anexar(recibo, 'documentos/recibo_pdf.html',
                               {'recibo': recibo}, 'arquivo', filename)
    return pdf_download_response(pdf_bytes, filename)


# ============================================================
# Dashboard
# ============================================================

@login_required
def dashboard(request):
    hoje = date.today()

    # Filtros
    imovel_id = request.GET.get('imovel_id', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    status_filtro = request.GET.get('status', '')

    lancamentos_qs = Lancamento.objects.select_related('contrato__inquilino', 'contrato__imovel')
    imoveis_qs = Imovel.objects.all()

    if imovel_id:
        lancamentos_qs = lancamentos_qs.filter(contrato__imovel_id=imovel_id)
        imoveis_qs = imoveis_qs.filter(pk=imovel_id)
    if data_inicio:
        lancamentos_qs = lancamentos_qs.filter(data_vencimento__gte=data_inicio)
    if data_fim:
        lancamentos_qs = lancamentos_qs.filter(data_vencimento__lte=data_fim)
    if status_filtro:
        lancamentos_qs = lancamentos_qs.filter(status=status_filtro)

    total_imoveis = imoveis_qs.count()
    vagos = imoveis_qs.filter(status='vago').count()
    ocupados = imoveis_qs.filter(status='ocupado').count()
    contratos_ativos = Contrato.objects.filter(status='ativo').count()
    inadimplentes = lancamentos_qs.filter(status='atrasado').count()

    taxa_vacancia = round((vagos / total_imoveis * 100), 1) if total_imoveis else 0

    ultimos_lancamentos = lancamentos_qs.order_by('-criado_em')[:8]

    # Gráfico de pizza
    pizza_labels = ['Ocupados', 'Vagos', 'Em Manutenção']
    pizza_data = [
        imoveis_qs.filter(status='ocupado').count(),
        imoveis_qs.filter(status='vago').count(),
        imoveis_qs.filter(status='manutencao').count(),
    ]

    # Gráfico de barras — últimos 6 meses
    meses_labels = []
    meses_pagos = []
    meses_pendentes = []
    for i in range(5, -1, -1):
        mes_ref = hoje.replace(day=1) - timedelta(days=i * 30)
        meses_labels.append(mes_ref.strftime('%b/%Y'))
        base = lancamentos_qs.filter(
            data_vencimento__year=mes_ref.year,
            data_vencimento__month=mes_ref.month,
        )
        pagos = base.filter(status='pago').aggregate(total=Sum('valor'))['total'] or 0
        pendentes = base.filter(status__in=['pendente', 'atrasado']).aggregate(total=Sum('valor'))['total'] or 0
        meses_pagos.append(float(pagos))
        meses_pendentes.append(float(pendentes))

    context = {
        'total_imoveis': total_imoveis,
        'vagos': vagos,
        'ocupados': ocupados,
        'contratos_ativos': contratos_ativos,
        'inadimplentes': inadimplentes,
        'taxa_vacancia': taxa_vacancia,
        'ultimos_lancamentos': ultimos_lancamentos,
        'pizza_labels': pizza_labels,
        'pizza_data': pizza_data,
        'meses_labels': meses_labels,
        'meses_pagos': meses_pagos,
        'meses_pendentes': meses_pendentes,
        # Filtros
        'imoveis_lista': Imovel.objects.all(),
        'filtro_imovel_id': imovel_id,
        'filtro_data_inicio': data_inicio,
        'filtro_data_fim': data_fim,
        'filtro_status': status_filtro,
        'status_choices': Lancamento.STATUS_CHOICES,
    }
    return render(request, 'dashboard.html', context)


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
    return render(request, 'imoveis/imovel_detail.html', {
        'imovel': imovel,
        'contratos': contratos,
        'laudos': laudos,
        'fotos': fotos,
        'notificacoes': notificacoes,
        'contrato_ativo': contrato_ativo,
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
        imovel.delete()
        messages.success(request, 'Imóvel removido.')
        return redirect('imovel_list')
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
        obj.delete()
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
        obj.delete()
        messages.success(request, 'Inquilino removido.')
    return redirect('inquilino_list')


# ============================================================
# Contratos
# ============================================================

@login_required
def contrato_list(request):
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    qs = Contrato.objects.select_related('imovel', 'inquilino')
    if q:
        qs = qs.filter(Q(inquilino__nome__icontains=q) | Q(imovel__endereco__icontains=q))
    if status:
        qs = qs.filter(status=status)
    return render(request, 'contratos/contrato_list.html', {
        'contratos': qs, 'q': q, 'status': status,
        'status_choices': Contrato.STATUS_CHOICES,
    })


@login_required
def contrato_detail(request, pk):
    contrato = get_object_or_404(Contrato.objects.select_related('imovel', 'inquilino'), pk=pk)
    lancamentos = contrato.lancamentos.order_by('-data_vencimento')
    laudos = contrato.laudos.order_by('-data')
    fiadores = contrato.fiadores.all()
    try:
        renovacao = contrato.renovacao
    except RenovacaoContrato.DoesNotExist:
        renovacao = None
    try:
        distrato = contrato.distrato
    except Distrato.DoesNotExist:
        distrato = None
    return render(request, 'contratos/contrato_detail.html', {
        'contrato': contrato,
        'lancamentos': lancamentos,
        'laudos': laudos,
        'fiadores': fiadores,
        'renovacao': renovacao,
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
# Renovação de Contrato
# ============================================================

@login_required
def renovacao_create(request, contrato_pk):
    contrato = get_object_or_404(Contrato, pk=contrato_pk)
    if hasattr(contrato, 'renovacao'):
        messages.warning(request, 'Este contrato já possui uma renovação registrada.')
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
        LaudoVistoria.objects.select_related('imovel__proprietario', 'contrato__inquilino'), pk=pk)
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
        item_formset = CatalogoFormSet(request.POST, prefix='itens', initial=catalogo)
        testemunha_formset = TestemunhaFormSet(request.POST, prefix='testemunhas')
        if form.is_valid() and item_formset.is_valid() and testemunha_formset.is_valid():
            laudo = form.save()
            item_formset.instance = laudo
            item_formset.save()
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
        item_formset = ItemVistoriaFormSet(request.POST, instance=obj, prefix='itens')
        testemunha_formset = TestemunhaFormSet(request.POST, instance=obj, prefix='testemunhas')
        if form.is_valid() and item_formset.is_valid() and testemunha_formset.is_valid():
            laudo = form.save()
            item_formset.save()
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
    contratos = Contrato.objects.filter(imovel_id=imovel_pk).select_related('inquilino').order_by('-data_inicio')
    dados = [{'id': c.pk, 'label': f'Contrato #{c.pk} — {c.inquilino.nome} ({c.get_status_display()})'}
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
def lancamento_list(request):
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    tipo = request.GET.get('tipo', '')
    qs = Lancamento.objects.select_related('contrato__inquilino', 'contrato__imovel')
    if q:
        qs = qs.filter(Q(contrato__inquilino__nome__icontains=q) | Q(contrato__imovel__endereco__icontains=q))
    if status:
        qs = qs.filter(status=status)
    if tipo:
        qs = qs.filter(tipo=tipo)

    total_pago = qs.filter(status='pago').aggregate(t=Sum('valor'))['t'] or 0
    total_pendente = qs.filter(status__in=['pendente', 'atrasado']).aggregate(t=Sum('valor'))['t'] or 0

    return render(request, 'financeiro/lancamento_list.html', {
        'lancamentos': qs,
        'q': q, 'status': status, 'tipo': tipo,
        'status_choices': Lancamento.STATUS_CHOICES,
        'tipo_choices': Lancamento.TIPO_CHOICES,
        'total_pago': total_pago,
        'total_pendente': total_pendente,
    })


@login_required
def lancamento_create(request):
    form = LancamentoForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Lançamento registrado.')
        return redirect('lancamento_list')
    return render(request, 'financeiro/lancamento_form.html', {'form': form, 'titulo': 'Novo Lançamento'})


@login_required
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
def lancamento_delete(request, pk):
    obj = get_object_or_404(Lancamento, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Lançamento removido.')
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
    contratos_gerados = (Contrato.objects.exclude(documento_gerado='')
                         .exclude(documento_gerado__isnull=True).select_related('imovel', 'inquilino'))
    laudos = LaudoVistoria.objects.exclude(arquivo='').exclude(arquivo__isnull=True).select_related('imovel')
    laudos_gerados = (LaudoVistoria.objects.exclude(documento_gerado='')
                      .exclude(documento_gerado__isnull=True).select_related('imovel'))
    comprovantes = Lancamento.objects.exclude(comprovante='').select_related('contrato__imovel')
    contratos_recibo = Contrato.objects.exclude(recibo_chaves='').select_related('imovel', 'inquilino')
    contratos_anual = Contrato.objects.exclude(comprovante_anual='').select_related('imovel', 'inquilino')
    recibos = (Recibo.objects.exclude(arquivo='').exclude(arquivo__isnull=True)
               .select_related('imovel', 'contrato__inquilino'))
    return render(request, 'ged/documentos.html', {
        'contratos_gerados': contratos_gerados,
        'laudos': laudos,
        'laudos_gerados': laudos_gerados,
        'comprovantes': comprovantes,
        'contratos_recibo': contratos_recibo,
        'contratos_anual': contratos_anual,
        'recibos': recibos,
    })
