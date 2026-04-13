from django import forms
from .models import Imovel, Proprietario, Inquilino, Contrato, LaudoVistoria, Lancamento


class ProprietarioForm(forms.ModelForm):
    class Meta:
        model = Proprietario
        fields = ['nome', 'cpf_cnpj', 'email', 'telefone', 'endereco']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'cpf_cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00 ou 00.000.000/0000-00'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rua, número, bairro, cidade'}),
        }


class ImovelForm(forms.ModelForm):
    class Meta:
        model = Imovel
        fields = ['proprietario', 'tipo', 'status', 'endereco', 'bairro', 'cidade', 'valor_aluguel', 'area_m2', 'descricao']
        widgets = {
            'proprietario': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rua e número'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bairro'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cidade'}),
            'valor_aluguel': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0,00', 'step': '0.01'}),
            'area_m2': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'm²', 'step': '0.01'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class InquilinoForm(forms.ModelForm):
    class Meta:
        model = Inquilino
        fields = ['nome', 'cpf', 'rg', 'email', 'telefone', 'profissao', 'renda_mensal']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'rg': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RG'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
            'profissao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Profissão'}),
            'renda_mensal': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0,00', 'step': '0.01'}),
        }


class ContratoForm(forms.ModelForm):
    class Meta:
        model = Contrato
        fields = ['imovel', 'inquilino', 'status', 'data_inicio', 'data_fim', 'valor_mensal', 'dia_vencimento', 'arquivo', 'observacoes']
        widgets = {
            'imovel': forms.Select(attrs={'class': 'form-select'}),
            'inquilino': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'data_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valor_mensal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'dia_vencimento': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 31}),
            'arquivo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class LaudoVistoriaForm(forms.ModelForm):
    class Meta:
        model = LaudoVistoria
        fields = ['imovel', 'contrato', 'tipo', 'data', 'responsavel', 'observacoes', 'arquivo']
        widgets = {
            'imovel': forms.Select(attrs={'class': 'form-select'}),
            'contrato': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'responsavel': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do vistoriador'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'arquivo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class LancamentoForm(forms.ModelForm):
    class Meta:
        model = Lancamento
        fields = ['contrato', 'tipo', 'status', 'valor', 'data_vencimento', 'data_pagamento', 'comprovante', 'observacoes']
        widgets = {
            'contrato': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'data_vencimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_pagamento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'comprovante': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
