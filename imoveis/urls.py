from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Imóveis
    path('imoveis/', views.imovel_list, name='imovel_list'),
    path('imoveis/novo/', views.imovel_create, name='imovel_create'),
    path('imoveis/<int:pk>/', views.imovel_detail, name='imovel_detail'),
    path('imoveis/<int:pk>/editar/', views.imovel_edit, name='imovel_edit'),
    path('imoveis/<int:pk>/excluir/', views.imovel_delete, name='imovel_delete'),

    # Proprietários
    path('proprietarios/', views.proprietario_list, name='proprietario_list'),
    path('proprietarios/novo/', views.proprietario_create, name='proprietario_create'),
    path('proprietarios/<int:pk>/editar/', views.proprietario_edit, name='proprietario_edit'),
    path('proprietarios/<int:pk>/excluir/', views.proprietario_delete, name='proprietario_delete'),

    # Inquilinos
    path('inquilinos/', views.inquilino_list, name='inquilino_list'),
    path('inquilinos/novo/', views.inquilino_create, name='inquilino_create'),
    path('inquilinos/<int:pk>/editar/', views.inquilino_edit, name='inquilino_edit'),
    path('inquilinos/<int:pk>/excluir/', views.inquilino_delete, name='inquilino_delete'),

    # Contratos
    path('contratos/', views.contrato_list, name='contrato_list'),
    path('contratos/novo/', views.contrato_create, name='contrato_create'),
    path('contratos/<int:pk>/', views.contrato_detail, name='contrato_detail'),
    path('contratos/<int:pk>/editar/', views.contrato_edit, name='contrato_edit'),
    path('contratos/<int:pk>/excluir/', views.contrato_delete, name='contrato_delete'),

    # Laudos
    path('laudos/', views.laudo_list, name='laudo_list'),
    path('laudos/novo/', views.laudo_create, name='laudo_create'),
    path('laudos/<int:pk>/editar/', views.laudo_edit, name='laudo_edit'),
    path('laudos/<int:pk>/excluir/', views.laudo_delete, name='laudo_delete'),

    # Financeiro
    path('financeiro/', views.lancamento_list, name='lancamento_list'),
    path('financeiro/novo/', views.lancamento_create, name='lancamento_create'),
    path('financeiro/<int:pk>/editar/', views.lancamento_edit, name='lancamento_edit'),
    path('financeiro/<int:pk>/excluir/', views.lancamento_delete, name='lancamento_delete'),

    # GED
    path('documentos/', views.documentos, name='documentos'),
]
