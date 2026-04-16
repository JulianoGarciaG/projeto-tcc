from django.contrib import admin
from .models import (
    Imovel, Proprietario, Inquilino, Contrato, LaudoVistoria, Lancamento,
    FotoImovel, Fiador, Notificacao, RenovacaoContrato, Distrato, Saida, Entrada,
)


@admin.register(Proprietario)
class ProprietarioAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cpf_cnpj', 'telefone', 'email']
    search_fields = ['nome', 'cpf_cnpj']


class FotoImovelInline(admin.TabularInline):
    model = FotoImovel
    extra = 1


@admin.register(Imovel)
class ImovelAdmin(admin.ModelAdmin):
    list_display = ['endereco', 'tipo', 'categoria', 'status', 'proprietario', 'valor_aluguel']
    list_filter = ['status', 'tipo', 'categoria']
    search_fields = ['endereco', 'bairro', 'cidade']
    inlines = [FotoImovelInline]


@admin.register(Inquilino)
class InquilinoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cpf', 'telefone', 'email']
    search_fields = ['nome', 'cpf']


class FiadorInline(admin.TabularInline):
    model = Fiador
    extra = 0


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ['pk', 'inquilino', 'imovel', 'tipo_contrato', 'status', 'data_inicio', 'data_fim', 'valor_mensal']
    list_filter = ['status', 'tipo_contrato']
    search_fields = ['inquilino__nome', 'imovel__endereco']
    inlines = [FiadorInline]


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ['imovel', 'tipo', 'titulo', 'data_recebimento', 'status']
    list_filter = ['tipo', 'status']
    search_fields = ['titulo', 'imovel__endereco']


@admin.register(RenovacaoContrato)
class RenovacaoContratoAdmin(admin.ModelAdmin):
    list_display = ['contrato', 'tipo', 'data_renovacao', 'novo_valor_mensal']
    list_filter = ['tipo']


@admin.register(Distrato)
class DistratoAdmin(admin.ModelAdmin):
    list_display = ['contrato', 'tipo', 'data_distrato']
    list_filter = ['tipo']


@admin.register(Saida)
class SaidaAdmin(admin.ModelAdmin):
    list_display = ['imovel', 'tipo', 'valor', 'data', 'pago_por']
    list_filter = ['tipo', 'pago_por']
    search_fields = ['imovel__endereco']


@admin.register(Entrada)
class EntradaAdmin(admin.ModelAdmin):
    list_display = ['imovel', 'tipo', 'valor', 'data']
    list_filter = ['tipo']
    search_fields = ['imovel__endereco']


@admin.register(LaudoVistoria)
class LaudoVistoriaAdmin(admin.ModelAdmin):
    list_display = ['imovel', 'tipo', 'data', 'responsavel']
    list_filter = ['tipo']


@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    list_display = ['contrato', 'tipo', 'status', 'valor', 'data_vencimento', 'data_pagamento']
    list_filter = ['status', 'tipo']
