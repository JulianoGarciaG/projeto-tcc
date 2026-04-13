from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import date

from .models import Imovel, Proprietario, Inquilino, Contrato, LaudoVistoria, Lancamento
from .forms import (
    ImovelForm, ProprietarioForm, InquilinoForm,
    ContratoForm, LaudoVistoriaForm, LancamentoForm,
)


# ============================================================
# Dashboard
# ============================================================

@login_required
def dashboard(request):
    hoje = date.today()

    total_imoveis = Imovel.objects.count()
    vagos = Imovel.objects.filter(status='vago').count()
    ocupados = Imovel.objects.filter(status='ocupado').count()
    contratos_ativos = Contrato.objects.filter(status='ativo').count()
    inadimplentes = Lancamento.objects.filter(status='atrasado').count()

    taxa_vacancia = round((vagos / total_imoveis * 100), 1) if total_imoveis else 0

    # Últimos lançamentos
    ultimos_lancamentos = Lancamento.objects.select_related('contrato__inquilino', 'contrato__imovel').order_by('-criado_em')[:8]

    # Dados para gráfico de pizza (ocupado/vago)
    pizza_labels = ['Ocupados', 'Vagos', 'Em Manutenção']
    pizza_data = [
        Imovel.objects.filter(status='ocupado').count(),
        Imovel.objects.filter(status='vago').count(),
        Imovel.objects.filter(status='manutencao').count(),
    ]

    # Dados para gráfico de barras (pagamentos últimos 6 meses)
    from datetime import timedelta
    import calendar
    meses_labels = []
    meses_pagos = []
    meses_pendentes = []
    for i in range(5, -1, -1):
        mes_ref = hoje.replace(day=1) - timedelta(days=i * 30)
        label = mes_ref.strftime('%b/%Y')
        meses_labels.append(label)
        pagos = Lancamento.objects.filter(
            data_vencimento__year=mes_ref.year,
            data_vencimento__month=mes_ref.month,
            status='pago'
        ).aggregate(total=Sum('valor'))['total'] or 0
        pendentes = Lancamento.objects.filter(
            data_vencimento__year=mes_ref.year,
            data_vencimento__month=mes_ref.month,
            status__in=['pendente', 'atrasado']
        ).aggregate(total=Sum('valor'))['total'] or 0
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

    imoveis = Imovel.objects.select_related('proprietario')
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
    contratos = imovel.contratos.select_related('inquilino').order_by('-data_inicio')[:5]
    laudos = imovel.laudos.order_by('-data')[:5]
    return render(request, 'imoveis/imovel_detail.html', {
        'imovel': imovel, 'contratos': contratos, 'laudos': laudos
    })


@login_required
def imovel_create(request):
    form = ImovelForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Imóvel cadastrado com sucesso.')
        return redirect('imovel_list')
    return render(request, 'imoveis/imovel_form.html', {'form': form, 'titulo': 'Novo Imóvel'})


@login_required
def imovel_edit(request, pk):
    imovel = get_object_or_404(Imovel, pk=pk)
    form = ImovelForm(request.POST or None, instance=imovel)
    if form.is_valid():
        form.save()
        messages.success(request, 'Imóvel atualizado.')
        return redirect('imovel_detail', pk=pk)
    return render(request, 'imoveis/imovel_form.html', {'form': form, 'titulo': 'Editar Imóvel', 'obj': imovel})


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
    return render(request, 'contratos/contrato_detail.html', {
        'contrato': contrato, 'lancamentos': lancamentos, 'laudos': laudos
    })


@login_required
def contrato_create(request):
    form = ContratoForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Contrato cadastrado com sucesso.')
        return redirect('contrato_list')
    return render(request, 'contratos/contrato_form.html', {'form': form, 'titulo': 'Novo Contrato'})


@login_required
def contrato_edit(request, pk):
    obj = get_object_or_404(Contrato, pk=pk)
    form = ContratoForm(request.POST or None, request.FILES or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Contrato atualizado.')
        return redirect('contrato_detail', pk=pk)
    return render(request, 'contratos/contrato_form.html', {'form': form, 'titulo': 'Editar Contrato', 'obj': obj})


@login_required
def contrato_delete(request, pk):
    obj = get_object_or_404(Contrato, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Contrato removido.')
    return redirect('contrato_list')


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


@login_required
def laudo_create(request):
    form = LaudoVistoriaForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Laudo registrado com sucesso.')
        return redirect('laudo_list')
    return render(request, 'laudos/laudo_form.html', {'form': form, 'titulo': 'Novo Laudo de Vistoria'})


@login_required
def laudo_edit(request, pk):
    obj = get_object_or_404(LaudoVistoria, pk=pk)
    form = LaudoVistoriaForm(request.POST or None, request.FILES or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Laudo atualizado.')
        return redirect('laudo_list')
    return render(request, 'laudos/laudo_form.html', {'form': form, 'titulo': 'Editar Laudo', 'obj': obj})


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
    form = LancamentoForm(request.POST or None, request.FILES or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'Lançamento atualizado.')
        return redirect('lancamento_list')
    return render(request, 'financeiro/lancamento_form.html', {'form': form, 'titulo': 'Editar Lançamento', 'obj': obj})


@login_required
def lancamento_delete(request, pk):
    obj = get_object_or_404(Lancamento, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Lançamento removido.')
    return redirect('lancamento_list')


# ============================================================
# GED — Documentos centralizados
# ============================================================

@login_required
def documentos(request):
    contratos = Contrato.objects.exclude(arquivo='').select_related('imovel', 'inquilino')
    laudos = LaudoVistoria.objects.exclude(arquivo='').select_related('imovel')
    comprovantes = Lancamento.objects.exclude(comprovante='').select_related('contrato__imovel')
    return render(request, 'ged/documentos.html', {
        'contratos': contratos,
        'laudos': laudos,
        'comprovantes': comprovantes,
    })
