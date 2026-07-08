from django import forms
from django.forms import inlineformset_factory
from .models import (
    Imovel, Proprietario, Inquilino, Contrato, LaudoVistoria, Lancamento,
    FotoImovel, Fiador, Notificacao, RenovacaoContrato, Distrato,
    Recibo, ItemVistoria, TestemunhaLaudo,
)

_ctrl = {'class': 'form-control'}
_sel = {'class': 'form-select'}


def _date_widget():
    """Input de data com Flatpickr (dd/mm/aaaa) — init centralizada em static/js/masks.js."""
    return forms.DateInput(
        format='%d/%m/%Y',
        attrs={**_ctrl, 'data-flatpickr': 'true', 'placeholder': 'dd/mm/aaaa', 'autocomplete': 'off'},
    )


def _moeda_widget():
    """Input monetário com máscara IMask (data-mask="moeda"); requer campo localized."""
    return forms.TextInput(attrs={**_ctrl, 'data-mask': 'moeda', 'inputmode': 'decimal',
                                  'placeholder': '0,00'})


_telefone_attrs = {**_ctrl, 'data-mask': 'telefone', 'placeholder': '(00) 00000-0000'}


# Selects de Imóvel/Contrato/Laudo exibem o `rotulo_curto` legível (código +
# contexto) no lugar do `str(obj)` padrão. Três classes quase idênticas (não
# uma genérica) para tipar cada campo ao model correto e deixar explícito, em
# cada ModelForm, qual entidade está sendo escolhida.
class ImovelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.rotulo_curto


class ContratoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.rotulo_curto


class LaudoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.rotulo_curto


class DashboardFiltroForm(forms.Form):
    """Filtro de período do Dashboard — datas em dd/mm/aaaa (Flatpickr)."""
    data_inicio = forms.DateField(required=False, widget=_date_widget())
    data_fim = forms.DateField(required=False, widget=_date_widget())


class ProprietarioForm(forms.ModelForm):
    class Meta:
        model = Proprietario
        fields = ['nome', 'cpf_cnpj', 'email', 'telefone']
        widgets = {
            'nome': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Nome completo'}),
            'cpf_cnpj': forms.TextInput(attrs={**_ctrl, 'placeholder': '000.000.000-00 ou 00.000.000/0000-00'}),
            'email': forms.EmailInput(attrs={**_ctrl, 'placeholder': 'email@exemplo.com'}),
            'telefone': forms.TextInput(attrs=_telefone_attrs),
        }


class ImovelForm(forms.ModelForm):
    class Meta:
        model = Imovel
        fields = [
            'proprietario', 'tipo', 'categoria', 'status',
            'endereco', 'numero', 'complemento', 'bairro', 'cidade',
            'area_m2', 'descricao',
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
            'endereco': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Rua/Logradouro'}),
            'numero': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Nº'}),
            'complemento': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Apto, bloco, sala...'}),
            'bairro': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Bairro'}),
            'cidade': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Cidade'}),
            'area_m2': forms.NumberInput(attrs={**_ctrl, 'placeholder': 'm²', 'step': '0.01'}),
            'descricao': forms.Textarea(attrs={**_ctrl, 'rows': 3}),
            'matricula': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Número da matrícula'}),
            'valor_aquisicao': forms.NumberInput(attrs={**_ctrl, 'step': '0.01'}),
            'cadastro_prefeitura': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Nº cadastro prefeitura'}),
            'planta_projeto': forms.ClearableFileInput(attrs=_ctrl),
            'nirf': forms.TextInput(attrs={**_ctrl, 'placeholder': 'NIRF'}),
            'incra': forms.TextInput(attrs={**_ctrl, 'placeholder': 'INCRA'}),
            'car': forms.TextInput(attrs={**_ctrl, 'placeholder': 'CAR'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_aquisicao'].widget = _date_widget()


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
        fields = ['nome', 'cpf', 'cnpj', 'rg', 'qualificacao', 'email', 'telefone',
                  'profissao', 'faixa_renda', 'observacoes']
        widgets = {
            'nome': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Nome completo'}),
            'cpf': forms.TextInput(attrs={**_ctrl, 'placeholder': '000.000.000-00'}),
            'cnpj': forms.TextInput(attrs={**_ctrl, 'placeholder': '00.000.000/0000-00 (PJ)'}),
            'rg': forms.TextInput(attrs={**_ctrl, 'placeholder': 'RG'}),
            'qualificacao': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Ex: solteiro, brasileiro, empresário'}),
            'email': forms.EmailInput(attrs={**_ctrl, 'placeholder': 'email@exemplo.com'}),
            'telefone': forms.TextInput(attrs=_telefone_attrs),
            'profissao': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Profissão'}),
            'faixa_renda': forms.Select(attrs=_sel),
            'observacoes': forms.Textarea(attrs={**_ctrl, 'rows': 3}),
        }


class ContratoForm(forms.ModelForm):
    imovel = ImovelChoiceField(queryset=Imovel.objects.all(), widget=forms.Select(attrs=_sel))

    class Meta:
        model = Contrato
        fields = [
            'imovel', 'inquilino', 'tipo_contrato', 'finalidade', 'status',
            'data_inicio', 'data_fim', 'valor_mensal', 'dia_vencimento',
            'local_assinatura', 'data_assinatura', 'observacoes',
        ]
        widgets = {
            'inquilino': forms.Select(attrs=_sel),
            'tipo_contrato': forms.Select(attrs=_sel),
            'finalidade': forms.Select(attrs=_sel),
            'status': forms.Select(attrs=_sel),
            'valor_mensal': forms.NumberInput(attrs={**_ctrl, 'step': '0.01'}),
            'dia_vencimento': forms.NumberInput(attrs={**_ctrl, 'min': 1, 'max': 31}),
            'local_assinatura': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Cidade da assinatura'}),
            'observacoes': forms.Textarea(attrs={**_ctrl, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_inicio'].widget = _date_widget()
        self.fields['data_fim'].widget = _date_widget()
        self.fields['data_assinatura'].widget = _date_widget()


class FiadorForm(forms.ModelForm):
    class Meta:
        model = Fiador
        fields = ['nome', 'qualificacao', 'rg_cpf', 'rg', 'cpf', 'endereco',
                  'conjuge_nome', 'conjuge_rg', 'conjuge_cpf',
                  'certidao_onus', 'garantia']
        widgets = {
            'nome': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Nome completo'}),
            'qualificacao': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Ex: casado, brasileiro, comerciante'}),
            'rg_cpf': forms.TextInput(attrs={**_ctrl, 'placeholder': 'RG ou CPF'}),
            'rg': forms.TextInput(attrs={**_ctrl, 'placeholder': 'RG'}),
            'cpf': forms.TextInput(attrs={**_ctrl, 'placeholder': 'CPF'}),
            'endereco': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Endereço completo'}),
            'conjuge_nome': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Nome do cônjuge'}),
            'conjuge_rg': forms.TextInput(attrs={**_ctrl, 'placeholder': 'RG do cônjuge'}),
            'conjuge_cpf': forms.TextInput(attrs={**_ctrl, 'placeholder': 'CPF do cônjuge'}),
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
    imovel = ImovelChoiceField(queryset=Imovel.objects.all(), widget=forms.Select(attrs=_sel))
    # queryset inicial vazio: o __init__ sempre reatribui conforme o imóvel.
    contrato = ContratoChoiceField(queryset=Contrato.objects.none(), widget=forms.Select(attrs=_sel))

    class Meta:
        model = LaudoVistoria
        fields = ['imovel', 'contrato', 'tipo', 'data', 'responsavel',
                  'local_assinatura', 'data_assinatura', 'observacoes']
        widgets = {
            'tipo': forms.Select(attrs=_sel),
            'responsavel': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Nome do vistoriador'}),
            'local_assinatura': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Cidade da assinatura'}),
            'observacoes': forms.Textarea(attrs={**_ctrl, 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data'].widget = _date_widget()
        self.fields['data_assinatura'].widget = _date_widget()
        # Contrato depende do imóvel (L1): o servidor restringe as opções ao
        # imóvel escolhido; o JS do template popula o select dinamicamente.
        imovel_id = None
        if self.data:
            imovel_id = self.data.get(self.add_prefix('imovel')) or None
        elif self.instance.pk:
            imovel_id = self.instance.imovel_id
        if imovel_id:
            self.fields['contrato'].queryset = Contrato.objects.filter(imovel_id=imovel_id)
        else:
            self.fields['contrato'].queryset = Contrato.objects.none()


class ItemVistoriaForm(forms.ModelForm):
    class Meta:
        model = ItemVistoria
        fields = ['comodo', 'item', 'estado', 'observacao', 'ordem']
        widgets = {
            'comodo': forms.HiddenInput(),
            'item': forms.HiddenInput(),
            'ordem': forms.HiddenInput(),
            'estado': forms.Select(attrs=_sel),
            'observacao': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Observação (opcional)'}),
        }


def item_vistoria_formset_factory(extra=0):
    """Formset de itens do laudo. Em laudos novos, `extra` deve ser o tamanho do
    catálogo para as linhas de `initial` renderizarem (L4)."""
    return inlineformset_factory(
        LaudoVistoria, ItemVistoria,
        form=ItemVistoriaForm,
        extra=extra,
        can_delete=True,
    )


ItemVistoriaFormSet = item_vistoria_formset_factory()


class TestemunhaLaudoForm(forms.ModelForm):
    class Meta:
        model = TestemunhaLaudo
        fields = ['nome', 'cpf']
        widgets = {
            'nome': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Nome completo'}),
            'cpf': forms.TextInput(attrs={**_ctrl, 'placeholder': '000.000.000-00'}),
        }


TestemunhaFormSet = inlineformset_factory(
    LaudoVistoria, TestemunhaLaudo,
    form=TestemunhaLaudoForm,
    extra=2,
    can_delete=True,
)


class LancamentoForm(forms.ModelForm):
    contrato = ContratoChoiceField(queryset=Contrato.objects.all(), widget=forms.Select(attrs=_sel))

    class Meta:
        model = Lancamento
        fields = ['contrato', 'tipo', 'status', 'valor', 'data_vencimento', 'data_pagamento', 'comprovante', 'observacoes']
        widgets = {
            'tipo': forms.Select(attrs=_sel),
            'status': forms.Select(attrs=_sel),
            'valor': forms.NumberInput(attrs={**_ctrl, 'step': '0.01'}),
            'comprovante': forms.ClearableFileInput(attrs=_ctrl),
            'observacoes': forms.Textarea(attrs={**_ctrl, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_vencimento'].widget = _date_widget()
        self.fields['data_pagamento'].widget = _date_widget()


class NotificacaoForm(forms.ModelForm):
    imovel = ImovelChoiceField(queryset=Imovel.objects.all(), widget=forms.Select(attrs=_sel))

    class Meta:
        model = Notificacao
        fields = ['imovel', 'tipo', 'titulo', 'data_recebimento', 'data_resposta', 'arquivo', 'observacoes', 'status']
        widgets = {
            'tipo': forms.Select(attrs=_sel),
            'titulo': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Título da notificação'}),
            'arquivo': forms.ClearableFileInput(attrs=_ctrl),
            'observacoes': forms.Textarea(attrs={**_ctrl, 'rows': 3}),
            'status': forms.Select(attrs=_sel),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_recebimento'].widget = _date_widget()
        self.fields['data_resposta'].widget = _date_widget()


class RenovacaoContratoForm(forms.ModelForm):
    class Meta:
        model = RenovacaoContrato
        fields = ['tipo', 'data_renovacao', 'novo_valor_mensal', 'observacoes']
        widgets = {
            'tipo': forms.Select(attrs=_sel),
            'novo_valor_mensal': forms.NumberInput(attrs={**_ctrl, 'step': '0.01'}),
            'observacoes': forms.Textarea(attrs={**_ctrl, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_renovacao'].widget = _date_widget()


class DistratoForm(forms.ModelForm):
    laudo_saida = LaudoChoiceField(queryset=LaudoVistoria.objects.all(), required=False,
                                   widget=forms.Select(attrs=_sel))

    class Meta:
        model = Distrato
        fields = ['tipo', 'data_distrato', 'recibo_chaves', 'laudo_saida', 'observacoes']
        widgets = {
            'tipo': forms.Select(attrs=_sel),
            'recibo_chaves': forms.ClearableFileInput(attrs=_ctrl),
            'observacoes': forms.Textarea(attrs={**_ctrl, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_distrato'].widget = _date_widget()


class ReciboForm(forms.ModelForm):
    imovel = ImovelChoiceField(queryset=Imovel.objects.all(), widget=forms.Select(attrs=_sel))
    contrato = ContratoChoiceField(queryset=Contrato.objects.all(), widget=forms.Select(attrs=_sel))

    class Meta:
        model = Recibo
        fields = [
            'imovel', 'contrato', 'parcela_atual', 'parcela_total',
            'valor_aluguel', 'valor_impostos', 'valor_seguros', 'valor_condominio',
            'quem_pagou', 'periodo_inicio', 'periodo_fim', 'vencido_em',
            'quantia', 'assinante_nome', 'assinante_cpf', 'data_assinatura',
        ]
        # Campos monetários aceitam vírgula como separador decimal ("1500,00"),
        # em par com a máscara data-mask="moeda".
        localized_fields = ['quantia', 'valor_aluguel', 'valor_impostos',
                            'valor_seguros', 'valor_condominio']
        widgets = {
            'parcela_atual': forms.NumberInput(attrs={**_ctrl, 'min': 1, 'placeholder': 'Nº'}),
            'parcela_total': forms.NumberInput(attrs={**_ctrl, 'min': 1, 'placeholder': 'Total'}),
            'quem_pagou': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Nome de quem pagou'}),
            'assinante_nome': forms.TextInput(attrs={**_ctrl, 'placeholder': 'Nome completo'}),
            'assinante_cpf': forms.TextInput(attrs={**_ctrl, 'placeholder': '000.000.000-00'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.Meta.localized_fields:
            widget = _moeda_widget()
            widget.is_localized = True  # renderiza valores iniciais com vírgula
            self.fields[campo].widget = widget
        for campo in ('periodo_inicio', 'periodo_fim', 'vencido_em', 'data_assinatura'):
            self.fields[campo].widget = _date_widget()

    def clean(self):
        cleaned = super().clean()
        conteudo = [v for campo, v in cleaned.items()
                    if campo not in ('imovel', 'contrato') and v not in (None, '')]
        if not conteudo:
            raise forms.ValidationError('Preencha ao menos um campo para emitir o recibo.')
        return cleaned
