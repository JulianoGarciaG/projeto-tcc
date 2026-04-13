from django.contrib import admin
from .models import Imovel, Proprietario, Inquilino, Contrato, LaudoVistoria, Lancamento


@admin.register(Proprietario)
class ProprietarioAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cpf_cnpj', 'telefone', 'email']
    search_fields = ['nome', 'cpf_cnpj']


@admin.register(Imovel)
class ImovelAdmin(admin.ModelAdmin):
    list_display = ['endereco', 'tipo', 'status', 'proprietario', 'valor_aluguel']
    list_filter = ['status', 'tipo']
    search_fields = ['endereco', 'bairro', 'cidade']


@admin.register(Inquilino)
class InquilinoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cpf', 'telefone', 'email']
    search_fields = ['nome', 'cpf']


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ['pk', 'inquilino', 'imovel', 'status', 'data_inicio', 'data_fim', 'valor_mensal']
    list_filter = ['status']
    search_fields = ['inquilino__nome', 'imovel__endereco']


@admin.register(LaudoVistoria)
class LaudoVistoriaAdmin(admin.ModelAdmin):
    list_display = ['imovel', 'tipo', 'data', 'responsavel']
    list_filter = ['tipo']


@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    list_display = ['contrato', 'tipo', 'status', 'valor', 'data_vencimento', 'data_pagamento']
    list_filter = ['status', 'tipo']
