from django.contrib import admin
from .models import (
    Imovel, Proprietario, Inquilino, Contrato, LaudoVistoria, Lancamento,
    FotoImovel, Fiador, Notificacao, RenovacaoContrato, Distrato,
    Recibo, ComodoTemplate, ItemVistoriaTemplate, ItemVistoria, TestemunhaLaudo,
    DocumentoGerado, NotificacaoUsuario,
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
    list_display = ['endereco', 'tipo', 'categoria', 'status', 'proprietario']
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


class ItemVistoriaInline(admin.TabularInline):
    model = ItemVistoria
    extra = 0


class TestemunhaLaudoInline(admin.TabularInline):
    model = TestemunhaLaudo
    extra = 0


@admin.register(LaudoVistoria)
class LaudoVistoriaAdmin(admin.ModelAdmin):
    list_display = ['imovel', 'tipo', 'data', 'responsavel']
    list_filter = ['tipo']
    inlines = [ItemVistoriaInline, TestemunhaLaudoInline]


class ItemVistoriaTemplateInline(admin.TabularInline):
    model = ItemVistoriaTemplate
    extra = 1


@admin.register(ComodoTemplate)
class ComodoTemplateAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ordem']
    inlines = [ItemVistoriaTemplateInline]


@admin.register(Recibo)
class ReciboAdmin(admin.ModelAdmin):
    list_display = ['pk', 'imovel', 'quem_pagou', 'quantia', 'data_assinatura', 'criado_em']
    search_fields = ['quem_pagou', 'assinante_nome', 'imovel__endereco']


@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    list_display = ['contrato', 'tipo', 'status', 'valor', 'data_vencimento', 'data_pagamento']
    list_filter = ['status', 'tipo']


@admin.register(DocumentoGerado)
class DocumentoGeradoAdmin(admin.ModelAdmin):
    """Registro imutável: consulta apenas — criação só pela geração de PDF."""
    list_display = ['pk', 'tipo', 'origem', 'numero_versao', 'gerado_por', 'gerado_em']
    list_filter = ['tipo']
    date_hierarchy = 'gerado_em'
    readonly_fields = ['tipo', 'contrato', 'laudo', 'recibo', 'numero_versao',
                       'arquivo', 'sha256', 'gerado_por', 'gerado_em']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(NotificacaoUsuario)
class NotificacaoUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'nivel', 'mensagem', 'criado_em')
    list_filter = ('nivel', 'criado_em')
    date_hierarchy = 'criado_em'
    readonly_fields = ('usuario', 'mensagem', 'nivel', 'criado_em')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
