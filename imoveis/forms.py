from django import forms
from django.forms import inlineformset_factory
from .models import (
    Imovel, Proprietario, Inquilino, Contrato, LaudoVistoria, Lancamento,
    FotoImovel, Fiador, Notificacao, RenovacaoContrato, Distrato, Saida, Entrada,
)

_ctrl = {'class': 'form-control'}
_sel = {'class': 'form-select'}


class ProprietarioForm(forms.ModelForm):
    class Meta:
        model = Proprietario
        fields = ['nome', 'cpf_cnpj', 'email', 'telefone', 'endereco']
        widgets = {
            'nome': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Nome completo'}),
            'cpf_cnpj': forms.TextInput(attrs={**_ctrl, 'placeholder': '000.000.000-00 ou 00.000.000/0000-00'}),
            'email': forms.EmailInput(attrs={**_ctrl, 'placeholder': 'email@exemplo.com'}),
            'telefone': forms.TextInput(attrs={**_ctrl, 'placeholder': '(00) 00000-0000'}),
            'endereco': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Rua, número, bairro, cidade'}),
        }


class ImovelForm(forms.ModelForm):
    class Meta:
        model = Imovel
        fields = [
            'proprietario', 'tipo', 'categoria', 'status',
            'endereco', 'bairro', 'cidade',
            'valor_aluguel', 'area_m2', 'descricao',
            'matricula', 'data_aquisicao', 'valor_aquisicao',
            # Urbano
            'cadastro_prefeitura', 'planta_projeto',
            # Rural
            'nirf', 'incra', 'car',
        ]
        widgets = {
            'proprietario': forms.Select(attrs=_sel),
            'tipo': forms.Select(attrs=_sel),
            'categoria': forms.Select(attrs=_sel),
            'status': forms.Select(attrs=_sel),
            'endereco': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Rua e número'}),
            'bairro': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Bairro'}),
            'cidade': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Cidade'}),
            'valor_aluguel': forms.NumberInput(attrs={**_ctrl, 'placeholder': '0,00', 'step': '0.01'}),
            'area_m2': forms.NumberInput(attrs={**_ctrl, 'placeholder': 'm²', 'step': '0.01'}),
            'descricao': forms.Textarea(attrs={**_ctrl, 'rows': 3}),
            'matricula': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Número da matrícula'}),
            'data_aquisicao': forms.DateInput(attrs={**_ctrl, 'type': 'date'}),
            'valor_aquisicao': forms.NumberInput(attrs={**_ctrl, 'step': '0.01'}),
            'cadastro_prefeitura': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Nº cadastro prefeitura'}),
            'planta_projeto': forms.ClearableFileInput(attrs=_ctrl),
            'nirf': forms.TextInput(attrs={**_ctrl, 'placeholder': 'NIRF'}),
            'incra': forms.TextInput(attrs={**_ctrl, 'placeholder': 'INCRA'}),
            'car': forms.TextInput(attrs={**_ctrl, 'placeholder': 'CAR'}),
        }


class FotoImovelForm(forms.ModelForm):
    class Meta:
        model = FotoImovel
        fields = ['imagem', 'legenda']
        widgets = {
            'imagem': forms.ClearableFileInput(attrs=_ctrl),
            'legenda': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Legenda (opcional)'}),
        }


FotoImovelFormSet = inlineformset_factory(
    Imovel, FotoImovel,
    form=FotoImovelForm,
    extra=3,
    can_delete=True,
)


class InquilinoForm(forms.ModelForm):
    class Meta:
        model = Inquilino
        fields = ['nome', 'cpf', 'cnpj', 'rg', 'qualificacao', 'email', 'telefone', 'profissao', 'renda_mensal']
        widgets = {
            'nome': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Nome completo'}),
            'cpf': forms.TextInput(attrs={**_ctrl, 'placeholder': '000.000.000-00'}),
            'cnpj': forms.TextInput(attrs={**_ctrl, 'placeholder': '00.000.000/0000-00 (PJ)'}),
            'rg': forms.TextInput(attrs={**_ctrl, 'placeholder': 'RG'}),
            'qualificacao': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Ex: solteiro, brasileiro, empresário'}),
            'email': forms.EmailInput(attrs={**_ctrl, 'placeholder': 'email@exemplo.com'}),
            'telefone': forms.TextInput(attrs={**_ctrl, 'placeholder': '(00) 00000-0000'}),
            'profissao': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Profissão'}),
            'renda_mensal': forms.NumberInput(attrs={**_ctrl, 'placeholder': '0,00', 'step': '0.01'}),
        }


class ContratoForm(forms.ModelForm):
    class Meta:
        model = Contrato
        fields = [
            'imovel', 'inquilino', 'tipo_contrato', 'status',
            'data_inicio', 'data_fim', 'valor_mensal', 'dia_vencimento',
            'arquivo', 'comprovante_renda', 'contrato_social',
            'recibo_chaves', 'comprovante_anual', 'observacoes',
        ]
        widgets = {
            'imovel': forms.Select(attrs=_sel),
            'inquilino': forms.Select(attrs=_sel),
            'tipo_contrato': forms.Select(attrs=_sel),
            'status': forms.Select(attrs=_sel),
            'data_inicio': forms.DateInput(attrs={**_ctrl, 'type': 'date'}),
            'data_fim': forms.DateInput(attrs={**_ctrl, 'type': 'date'}),
            'valor_mensal': forms.NumberInput(attrs={**_ctrl, 'step': '0.01'}),
            'dia_vencimento': forms.NumberInput(attrs={**_ctrl, 'min': 1, 'max': 31}),
            'arquivo': forms.ClearableFileInput(attrs=_ctrl),
            'comprovante_renda': forms.ClearableFileInput(attrs=_ctrl),
            'contrato_social': forms.ClearableFileInput(attrs=_ctrl),
            'recibo_chaves': forms.ClearableFileInput(attrs=_ctrl),
            'comprovante_anual': forms.ClearableFileInput(attrs=_ctrl),
            'observacoes': forms.Textarea(attrs={**_ctrl, 'rows': 3}),
        }


class FiadorForm(forms.ModelForm):
    class Meta:
        model = Fiador
        fields = ['nome', 'qualificacao', 'rg_cpf', 'certidao_onus', 'garantia']
        widgets = {
            'nome': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Nome completo'}),
            'qualificacao': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Ex: casado, brasileiro, comerciante'}),
            'rg_cpf': forms.TextInput(attrs={**_ctrl, 'placeholder': 'RG ou CPF'}),
            'certidao_onus': forms.ClearableFileInput(attrs=_ctrl),
            'garantia': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Ex: imóvel próprio, caução'}),
        }


FiadorFormSet = inlineformset_factory(
    Contrato, Fiador,
    form=FiadorForm,
    extra=1,
    can_delete=True,
)


class LaudoVistoriaForm(forms.ModelForm):
    class Meta:
        model = LaudoVistoria
        fields = ['imovel', 'contrato', 'tipo', 'data', 'responsavel', 'observacoes', 'arquivo']
        widgets = {
            'imovel': forms.Select(attrs=_sel),
            'contrato': forms.Select(attrs=_sel),
            'tipo': forms.Select(attrs=_sel),
            'data': forms.DateInput(attrs={**_ctrl, 'type': 'date'}),
            'responsavel': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Nome do vistoriador'}),
            'observacoes': forms.Textarea(attrs={**_ctrl, 'rows': 4}),
            'arquivo': forms.ClearableFileInput(attrs=_ctrl),
        }


class LancamentoForm(forms.ModelForm):
    class Meta:
        model = Lancamento
        fields = ['contrato', 'tipo', 'status', 'valor', 'data_vencimento', 'data_pagamento', 'comprovante', 'observacoes']
        widgets = {
            'contrato': forms.Select(attrs=_sel),
            'tipo': forms.Select(attrs=_sel),
            'status': forms.Select(attrs=_sel),
            'valor': forms.NumberInput(attrs={**_ctrl, 'step': '0.01'}),
            'data_vencimento': forms.DateInput(attrs={**_ctrl, 'type': 'date'}),
            'data_pagamento': forms.DateInput(attrs={**_ctrl, 'type': 'date'}),
            'comprovante': forms.ClearableFileInput(attrs=_ctrl),
            'observacoes': forms.Textarea(attrs={**_ctrl, 'rows': 2}),
        }


class NotificacaoForm(forms.ModelForm):
    class Meta:
        model = Notificacao
        fields = ['imovel', 'tipo', 'titulo', 'data_recebimento', 'data_resposta', 'arquivo', 'observacoes', 'status']
        widgets = {
            'imovel': forms.Select(attrs=_sel),
            'tipo': forms.Select(attrs=_sel),
            'titulo': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Título da notificação'}),
            'data_recebimento': forms.DateInput(attrs={**_ctrl, 'type': 'date'}),
            'data_resposta': forms.DateInput(attrs={**_ctrl, 'type': 'date'}),
            'arquivo': forms.ClearableFileInput(attrs=_ctrl),
            'observacoes': forms.Textarea(attrs={**_ctrl, 'rows': 3}),
            'status': forms.Select(attrs=_sel),
        }


class RenovacaoContratoForm(forms.ModelForm):
    class Meta:
        model = RenovacaoContrato
        fields = ['tipo', 'data_renovacao', 'novo_valor_mensal', 'observacoes']
        widgets = {
            'tipo': forms.Select(attrs=_sel),
            'data_renovacao': forms.DateInput(attrs={**_ctrl, 'type': 'date'}),
            'novo_valor_mensal': forms.NumberInput(attrs={**_ctrl, 'step': '0.01'}),
            'observacoes': forms.Textarea(attrs={**_ctrl, 'rows': 3}),
        }


class DistratoForm(forms.ModelForm):
    class Meta:
        model = Distrato
        fields = ['tipo', 'data_distrato', 'recibo_chaves', 'laudo_saida', 'observacoes']
        widgets = {
            'tipo': forms.Select(attrs=_sel),
            'data_distrato': forms.DateInput(attrs={**_ctrl, 'type': 'date'}),
            'recibo_chaves': forms.ClearableFileInput(attrs=_ctrl),
            'laudo_saida': forms.Select(attrs=_sel),
            'observacoes': forms.Textarea(attrs={**_ctrl, 'rows': 3}),
        }


class SaidaForm(forms.ModelForm):
    class Meta:
        model = Saida
        fields = ['imovel', 'tipo', 'descricao', 'valor', 'data', 'pago_por', 'comprovante', 'observacoes']
        widgets = {
            'imovel': forms.Select(attrs=_sel),
            'tipo': forms.Select(attrs=_sel),
            'descricao': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Descrição'}),
            'valor': forms.NumberInput(attrs={**_ctrl, 'step': '0.01'}),
            'data': forms.DateInput(attrs={**_ctrl, 'type': 'date'}),
            'pago_por': forms.Select(attrs=_sel),
            'comprovante': forms.ClearableFileInput(attrs=_ctrl),
            'observacoes': forms.Textarea(attrs={**_ctrl, 'rows': 2}),
        }


class EntradaForm(forms.ModelForm):
    class Meta:
        model = Entrada
        fields = ['imovel', 'tipo', 'descricao', 'valor', 'data', 'comprovante', 'observacoes']
        widgets = {
            'imovel': forms.Select(attrs=_sel),
            'tipo': forms.Select(attrs=_sel),
            'descricao': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Descrição'}),
            'valor': forms.NumberInput(attrs={**_ctrl, 'step': '0.01'}),
            'data': forms.DateInput(attrs={**_ctrl, 'type': 'date'}),
            'comprovante': forms.ClearableFileInput(attrs=_ctrl),
            'observacoes': forms.Textarea(attrs={**_ctrl, 'rows': 2}),
        }
