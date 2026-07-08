from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .identidade import IdentificavelMixin, mes_ano_abreviado
from .validators import (
    validate_cpf, validate_cnpj, validate_cpf_cnpj, validate_rg,
    validate_rg_cpf, validate_telefone,
)


class Proprietario(models.Model):
    nome = models.CharField(max_length=200)
    cpf_cnpj = models.CharField(max_length=20, unique=True, validators=[validate_cpf_cnpj],
                                verbose_name='CPF/CNPJ')
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True, validators=[validate_telefone])
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Proprietário'
        verbose_name_plural = 'Proprietários'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Imovel(IdentificavelMixin, models.Model):
    PREFIXO_CODIGO = 'IMV'

    TIPO_CHOICES = [
        ('apartamento', 'Apartamento'),
        ('casa', 'Casa'),
        ('comercial', 'Comercial'),
        ('terreno', 'Terreno'),
        ('galpao', 'Galpão'),
    ]
    STATUS_CHOICES = [
        ('ocupado', 'Ocupado'),
        ('vago', 'Vago'),
        ('manutencao', 'Em Manutenção'),
    ]
    CATEGORIA_CHOICES = [
        ('urbano', 'Urbano'),
        ('rural', 'Rural'),
    ]

    proprietario = models.ForeignKey(Proprietario, on_delete=models.PROTECT, related_name='imoveis')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='vago')
    categoria = models.CharField(max_length=10, choices=CATEGORIA_CHOICES, default='urbano', verbose_name='Categoria')
    endereco = models.CharField(max_length=300)
    numero = models.CharField(max_length=20, blank=True, verbose_name='Número')
    complemento = models.CharField(max_length=100, blank=True, verbose_name='Complemento')
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, default='')
    area_m2 = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='Área (m²)')
    descricao = models.TextField(blank=True)
    # Campos comuns urbano/rural
    matricula = models.CharField(max_length=100, blank=True, verbose_name='Matrícula')
    data_aquisicao = models.DateField(null=True, blank=True, verbose_name='Data de Aquisição')
    valor_aquisicao = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, verbose_name='Valor de Aquisição')
    # Campos exclusivos Urbano
    cadastro_prefeitura = models.CharField(max_length=100, blank=True, verbose_name='Cadastro Prefeitura')
    planta_projeto = models.FileField(upload_to='plantas/', blank=True, null=True, verbose_name='Planta/Projeto')
    # Campos exclusivos Rural
    nirf = models.CharField(max_length=50, blank=True, verbose_name='NIRF')
    incra = models.CharField(max_length=50, blank=True, verbose_name='INCRA')
    car = models.CharField(max_length=100, blank=True, verbose_name='CAR')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Imóvel'
        verbose_name_plural = 'Imóveis'
        ordering = ['endereco']

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.endereco}'

    @property
    def rotulo_curto(self):
        end = self.endereco
        if self.numero:
            end = f'{end}, {self.numero}'
        local = self.bairro or self.cidade or ''
        if local:
            end = f'{end} – {local}'
        return f'{self.codigo} · {self.get_tipo_display()} · {end}'

    @property
    def rotulo_longo(self):
        base = self.rotulo_curto
        if self.cidade and self.cidade not in base:
            return f'{base}, {self.cidade}'
        return base

    @property
    def dependentes_cascata(self):
        pares = [
            ('foto(s)', self.fotos.count()),
            ('notificação(ões)', self.notificacoes.count()),
            ('laudo(s) de vistoria', self.laudos.count()),
        ]
        return [(label, n) for label, n in pares if n > 0]


class FotoImovel(models.Model):
    imovel = models.ForeignKey(Imovel, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(upload_to='fotos_imoveis/')
    legenda = models.CharField(max_length=200, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Foto do Imóvel'
        verbose_name_plural = 'Fotos do Imóvel'
        ordering = ['criado_em']

    def __str__(self):
        return f'Foto de {self.imovel} — {self.legenda or self.pk}'


class Inquilino(models.Model):
    FAIXA_RENDA_CHOICES = [
        ('ate_2k', '< R$ 2k'),
        ('2_4k', 'R$ 2k - R$ 3.9k'),
        ('4_7k', 'R$ 4k - R$ 6.9k'),
        ('7_10k', 'R$ 7k - R$ 9.9k'),
        ('10_16k', 'R$ 10k - R$ 15.9k'),
        ('acima_16k', 'R$ 16k +'),
    ]

    nome = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14, unique=True, validators=[validate_cpf], verbose_name='CPF')
    cnpj = models.CharField(max_length=18, blank=True, validators=[validate_cnpj], verbose_name='CNPJ')
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True, validators=[validate_telefone])
    rg = models.CharField(max_length=20, blank=True, validators=[validate_rg], verbose_name='RG')
    qualificacao = models.CharField(max_length=300, blank=True, verbose_name='Qualificação',
                                    help_text='Estado civil, profissão, nacionalidade')
    profissao = models.CharField(max_length=100, blank=True, verbose_name='Profissão')
    faixa_renda = models.CharField(max_length=20, choices=FAIXA_RENDA_CHOICES, blank=True,
                                   verbose_name='Faixa de Renda')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Inquilino'
        verbose_name_plural = 'Inquilinos'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Contrato(IdentificavelMixin, models.Model):
    PREFIXO_CODIGO = 'CTR'

    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('encerrado', 'Encerrado'),
        ('rescindido', 'Rescindido'),
    ]
    TIPO_CONTRATO_CHOICES = [
        ('PF', 'Pessoa Física'),
        ('PJ', 'Pessoa Jurídica'),
    ]
    FINALIDADE_CHOICES = [
        ('residencial', 'Residencial'),
        ('comercial', 'Comercial'),
    ]

    imovel = models.ForeignKey(Imovel, on_delete=models.PROTECT, related_name='contratos')
    inquilino = models.ForeignKey(Inquilino, on_delete=models.PROTECT, related_name='contratos')
    tipo_contrato = models.CharField(max_length=2, choices=TIPO_CONTRATO_CHOICES, default='PF',
                                     verbose_name='Tipo de Contrato')
    finalidade = models.CharField(max_length=12, choices=FINALIDADE_CHOICES,
                                  default='residencial', verbose_name='Finalidade')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')
    data_inicio = models.DateField(verbose_name='Data de Início')
    data_fim = models.DateField(verbose_name='Data de Término')
    valor_mensal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor Mensal')
    dia_vencimento = models.PositiveSmallIntegerField(
        default=10, verbose_name='Dia de Vencimento',
        validators=[MinValueValidator(1), MaxValueValidator(31)])
    # Documentos GED vinculados ao contrato
    comprovante_renda = models.FileField(upload_to='comprovantes_renda/', blank=True, null=True,
                                         verbose_name='Comprovante de Renda (PF)')
    contrato_social = models.FileField(upload_to='contratos_sociais/', blank=True, null=True,
                                       verbose_name='Contrato Social (PJ)')
    recibo_chaves = models.FileField(upload_to='contratos/recibo_chaves/', blank=True, null=True,
                                     verbose_name='Recibo de Entrega de Chaves')
    comprovante_anual = models.FileField(upload_to='contratos/comprovante_anual/', blank=True, null=True,
                                         verbose_name='Comprovante Anual de Pagamento')
    documento_gerado = models.FileField(upload_to='contratos/gerados/', blank=True, null=True,
                                        verbose_name='Contrato gerado (PDF)')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    local_assinatura = models.CharField(max_length=200, blank=True,
                                        verbose_name='Local da Assinatura')
    data_assinatura = models.DateField(null=True, blank=True,
                                       verbose_name='Data da Assinatura')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'
        ordering = ['-data_inicio']

    def __str__(self):
        return f'Contrato #{self.pk} — {self.inquilino} / {self.imovel}'

    @property
    def rotulo_curto(self):
        periodo = f'{self.data_inicio:%m/%y}–{self.data_fim:%m/%y}'
        end = self.imovel.endereco
        if self.imovel.numero:
            end = f'{end} {self.imovel.numero}'
        return (f'{self.codigo} · {self.inquilino.nome} · {end} · '
                f'{periodo} · {self.get_status_display()}')

    @property
    def rotulo_longo(self):
        end = self.imovel.endereco
        if self.imovel.numero:
            end = f'{end}, {self.imovel.numero}'
        if self.imovel.bairro:
            end = f'{end} – {self.imovel.bairro}'
        periodo = f'{self.data_inicio:%d/%m/%Y} a {self.data_fim:%d/%m/%Y}'
        return (f'Contrato {self.codigo} — {self.inquilino.nome} — {end} — '
                f'{periodo} — {self.get_status_display()}')

    @property
    def dependentes_cascata(self):
        pares = [
            ('fiador(es)', self.fiadores.count()),
            ('lançamento(s) financeiro(s)', self.lancamentos.count()),
            ('renovação', 1 if hasattr(self, 'renovacao') else 0),
            ('distrato', 1 if hasattr(self, 'distrato') else 0),
            ('documento(s) gerado(s)', self.documentos_gerados.count()),
        ]
        return [(label, n) for label, n in pares if n > 0]


class Fiador(models.Model):
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='fiadores')
    nome = models.CharField(max_length=200)
    qualificacao = models.CharField(max_length=300, blank=True, verbose_name='Qualificação',
                                    help_text='Estado civil, profissão, nacionalidade')
    rg_cpf = models.CharField(max_length=20, validators=[validate_rg_cpf], verbose_name='RG/CPF')
    rg = models.CharField(max_length=20, blank=True, validators=[validate_rg],
                          verbose_name='RG')
    cpf = models.CharField(max_length=14, blank=True, validators=[validate_cpf],
                           verbose_name='CPF')
    endereco = models.CharField(max_length=300, blank=True,
                                verbose_name='Endereço Completo')
    conjuge_nome = models.CharField(max_length=200, blank=True,
                                    verbose_name='Nome do Cônjuge')
    conjuge_rg = models.CharField(max_length=20, blank=True, validators=[validate_rg],
                                  verbose_name='RG do Cônjuge')
    conjuge_cpf = models.CharField(max_length=14, blank=True, validators=[validate_cpf],
                                   verbose_name='CPF do Cônjuge')
    certidao_onus = models.FileField(upload_to='certidoes/', blank=True, null=True,
                                     verbose_name='Certidão de Ônus')
    garantia = models.CharField(max_length=200, blank=True, verbose_name='Garantia')

    class Meta:
        verbose_name = 'Fiador'
        verbose_name_plural = 'Fiadores'

    def __str__(self):
        return f'{self.nome} (Fiador do Contrato #{self.contrato_id})'


class LaudoVistoria(IdentificavelMixin, models.Model):
    PREFIXO_CODIGO = 'LAU'

    TIPO_CHOICES = [
        ('entrada', 'Vistoria de Entrada'),
        ('saida', 'Vistoria de Saída'),
    ]

    imovel = models.ForeignKey(Imovel, on_delete=models.CASCADE, related_name='laudos')
    contrato = models.ForeignKey(Contrato, on_delete=models.PROTECT, related_name='laudos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    data = models.DateField()
    responsavel = models.CharField(max_length=200, verbose_name='Responsável pela Vistoria')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    local_assinatura = models.CharField(max_length=200, blank=True, verbose_name='Local da Assinatura')
    data_assinatura = models.DateField(null=True, blank=True, verbose_name='Data da Assinatura')
    arquivo = models.FileField(upload_to='laudos/', blank=True, null=True, verbose_name='Laudo em PDF')
    documento_gerado = models.FileField(upload_to='laudos/gerados/', blank=True, null=True,
                                        verbose_name='Laudo gerado (PDF)')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Laudo de Vistoria'
        verbose_name_plural = 'Laudos de Vistoria'
        ordering = ['-data']

    def resumo_vistoria(self):
        """Resumo automático calculado a partir dos itens (nunca digitado)."""
        itens = self.itens.all()
        return {
            'total': itens.count(),
            'bom': itens.filter(estado='bom').count(),
            'regular': itens.filter(estado='regular').count(),
            'ruim': itens.filter(estado='ruim').count(),
        }

    def locador_nome(self):
        return self.imovel.proprietario.nome

    def locatario_nome(self):
        return self.contrato.inquilino.nome

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.imovel} ({self.data})'

    @property
    def rotulo_curto(self):
        end = self.imovel.endereco
        if self.imovel.numero:
            end = f'{end} {self.imovel.numero}'
        return (f'{self.codigo} · {self.get_tipo_display()} · {end} · '
                f'{self.locatario_nome()}')

    @property
    def rotulo_longo(self):
        return f'{self.rotulo_curto} · {self.data:%d/%m/%Y}'

    @property
    def dependentes_cascata(self):
        pares = [
            ('item(ns) de vistoria', self.itens.count()),
            ('testemunha(s)', self.testemunhas.count()),
            ('documento(s) gerado(s)', self.documentos_gerados.count()),
        ]
        return [(label, n) for label, n in pares if n > 0]


class ComodoTemplate(models.Model):
    """Catálogo configurável de cômodos padrão da vistoria (editável no admin)."""
    nome = models.CharField(max_length=100)
    ordem = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'Cômodo (Modelo de Vistoria)'
        verbose_name_plural = 'Cômodos (Modelo de Vistoria)'
        ordering = ['ordem', 'nome']

    def __str__(self):
        return self.nome


class ItemVistoriaTemplate(models.Model):
    """Item avaliável de um cômodo do catálogo (ex: paredes e pintura)."""
    comodo = models.ForeignKey(ComodoTemplate, on_delete=models.CASCADE, related_name='itens')
    nome = models.CharField(max_length=150)
    ordem = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'Item (Modelo de Vistoria)'
        verbose_name_plural = 'Itens (Modelo de Vistoria)'
        ordering = ['comodo__ordem', 'ordem', 'nome']

    def __str__(self):
        return f'{self.comodo.nome} — {self.nome}'


class ItemVistoria(models.Model):
    """Item avaliado em um laudo (snapshot do catálogo na data da vistoria)."""
    ESTADO_CHOICES = [
        ('bom', 'Bom'),
        ('regular', 'Regular'),
        ('ruim', 'Ruim'),
    ]

    laudo = models.ForeignKey(LaudoVistoria, on_delete=models.CASCADE, related_name='itens')
    comodo = models.CharField(max_length=100, verbose_name='Cômodo')
    item = models.CharField(max_length=150, verbose_name='Item')
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES)
    observacao = models.CharField(max_length=300, blank=True, verbose_name='Observação')
    ordem = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'Item de Vistoria'
        verbose_name_plural = 'Itens de Vistoria'
        ordering = ['ordem', 'pk']

    def __str__(self):
        return f'{self.comodo} — {self.item} ({self.get_estado_display()})'


def foto_item_vistoria_upload_to(instance, filename):
    """itens_vistoria/{item_id}/{filename} — usa instance.item_id (FK id),
    sem precisar carregar o ItemVistoria nem o LaudoVistoria relacionado."""
    return f'itens_vistoria/{instance.item_id}/{filename}'


class FotoItemVistoria(models.Model):
    """Foto anexada a um item do checklist de vistoria. Visível apenas no
    detalhe do laudo — nunca no PDF nem na central GED."""
    item = models.ForeignKey(ItemVistoria, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(upload_to=foto_item_vistoria_upload_to)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Foto do Item de Vistoria'
        verbose_name_plural = 'Fotos do Item de Vistoria'
        ordering = ['criado_em']

    def __str__(self):
        return f'Foto de {self.item} ({self.criado_em:%d/%m/%Y})'


class TestemunhaLaudo(models.Model):
    laudo = models.ForeignKey(LaudoVistoria, on_delete=models.CASCADE, related_name='testemunhas')
    nome = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14, blank=True, validators=[validate_cpf], verbose_name='CPF')

    class Meta:
        verbose_name = 'Testemunha do Laudo'
        verbose_name_plural = 'Testemunhas do Laudo'

    def __str__(self):
        return f'{self.nome} (Testemunha do Laudo #{self.laudo_id})'


class Lancamento(models.Model):
    TIPO_CHOICES = [
        ('aluguel', 'Aluguel'),
        ('condominio', 'Condomínio'),
        ('iptu', 'IPTU'),
        ('manutencao', 'Manutenção'),
        ('multa', 'Multa'),
        ('outros', 'Outros'),
    ]
    STATUS_CHOICES = [
        ('pago', 'Pago'),
        ('pendente', 'Pendente'),
        ('atrasado', 'Atrasado'),
    ]

    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='lancamentos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_vencimento = models.DateField(verbose_name='Data de Vencimento')
    data_pagamento = models.DateField(null=True, blank=True, verbose_name='Data de Pagamento')
    comprovante = models.FileField(upload_to='comprovantes/', blank=True, null=True)
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Lançamento'
        verbose_name_plural = 'Lançamentos'
        ordering = ['-data_vencimento']

    def __str__(self):
        return f'{self.get_tipo_display()} — R$ {self.valor} ({self.get_status_display()})'


class Notificacao(models.Model):
    TIPO_CHOICES = [
        ('prefeitura', 'Prefeitura'),
        ('receita_federal', 'Receita Federal'),
        ('bombeiros', 'Corpo de Bombeiros'),
        ('outro', 'Outro'),
    ]
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('respondida', 'Respondida'),
        ('arquivada', 'Arquivada'),
    ]

    imovel = models.ForeignKey(Imovel, on_delete=models.CASCADE, related_name='notificacoes')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=200, verbose_name='Título')
    data_recebimento = models.DateField(verbose_name='Data de Recebimento')
    data_resposta = models.DateField(null=True, blank=True, verbose_name='Data de Resposta')
    arquivo = models.FileField(upload_to='notificacoes/', blank=True, null=True, verbose_name='Documento')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-data_recebimento']

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.titulo} ({self.imovel})'


class RenovacaoContrato(models.Model):
    TIPO_CHOICES = [
        ('12_12', '12/12 meses'),
        ('12_30', '12/30 meses'),
        ('12_indeterminado', '12/Indeterminado'),
    ]

    contrato = models.OneToOneField(Contrato, on_delete=models.CASCADE, related_name='renovacao')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo de Renovação')
    data_renovacao = models.DateField(verbose_name='Data da Renovação')
    novo_valor_mensal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                            verbose_name='Novo Valor Mensal')
    observacoes = models.TextField(blank=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Renovação de Contrato'
        verbose_name_plural = 'Renovações de Contrato'

    def __str__(self):
        return f'Renovação {self.get_tipo_display()} — Contrato #{self.contrato_id}'


class Distrato(models.Model):
    TIPO_CHOICES = [
        ('amigavel', 'Distrato Amigável'),
        ('judicial', 'Ação Judicial de Cobrança'),
    ]

    contrato = models.OneToOneField(Contrato, on_delete=models.CASCADE, related_name='distrato')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name='Tipo de Distrato')
    data_distrato = models.DateField(verbose_name='Data do Distrato')
    recibo_chaves = models.FileField(upload_to='distratos/recibos/', blank=True, null=True,
                                     verbose_name='Recibo de Devolução de Chaves')
    laudo_saida = models.ForeignKey(LaudoVistoria, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name='Laudo de Vistoria de Saída')
    observacoes = models.TextField(blank=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Distrato'
        verbose_name_plural = 'Distratos'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.contrato.status = 'encerrado'
        self.contrato.save(update_fields=['status'])

    def __str__(self):
        return f'{self.get_tipo_display()} — Contrato #{self.contrato_id}'


class Recibo(IdentificavelMixin, models.Model):
    """Recibo de pagamento — imóvel/contrato obrigatórios, demais campos opcionais.

    No PDF aparecem apenas os campos preenchidos. `quantia` é o valor total
    recebido; os valores de aluguel/impostos/seguros/condomínio são as
    parcelas que compõem esse total (ver somatorio()).
    """
    PREFIXO_CODIGO = 'REC'

    imovel = models.ForeignKey(Imovel, on_delete=models.PROTECT, related_name='recibos')
    contrato = models.ForeignKey(Contrato, on_delete=models.PROTECT, related_name='recibos')
    parcela_atual = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Parcela Atual')
    parcela_total = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Total de Parcelas')
    valor_aluguel = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                        verbose_name='Aluguel')
    valor_impostos = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                         verbose_name='Impostos')
    valor_seguros = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                        verbose_name='Seguros')
    valor_condominio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                           verbose_name='Condomínio')
    quem_pagou = models.CharField(max_length=200, blank=True, verbose_name='Quem Pagou')
    periodo_inicio = models.DateField(null=True, blank=True, verbose_name='Período — Início')
    periodo_fim = models.DateField(null=True, blank=True, verbose_name='Período — Fim')
    vencido_em = models.DateField(null=True, blank=True, verbose_name='Vencido em')
    quantia = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                  verbose_name='Quantia de')
    assinante_nome = models.CharField(max_length=200, blank=True, verbose_name='Nome de Quem Assinou')
    assinante_cpf = models.CharField(max_length=14, blank=True, validators=[validate_cpf],
                                     verbose_name='CPF de Quem Assinou')
    data_assinatura = models.DateField(null=True, blank=True, verbose_name='Data da Assinatura')
    arquivo = models.FileField(upload_to='recibos/', blank=True, null=True, verbose_name='Recibo gerado (PDF)')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Recibo'
        verbose_name_plural = 'Recibos'
        ordering = ['-criado_em']

    def somatorio(self):
        """Soma das parcelas preenchidas que constituem a quantia."""
        valores = [self.valor_aluguel, self.valor_impostos, self.valor_seguros, self.valor_condominio]
        return sum(v for v in valores if v)

    def __str__(self):
        return f'Recibo #{self.pk} — {self.imovel}'

    @property
    def dependentes_cascata(self):
        pares = [
            ('documento(s) gerado(s)', self.documentos_gerados.count()),
        ]
        return [(label, n) for label, n in pares if n > 0]

    @property
    def rotulo_curto(self):
        quem = self.quem_pagou or self.contrato.inquilino.nome
        partes = [self.codigo, quem]
        periodo = mes_ano_abreviado(self.periodo_inicio)
        if periodo:
            partes.append(periodo)
        if self.parcela_atual and self.parcela_total:
            partes.append(f'parcela {self.parcela_atual}/{self.parcela_total}')
        return ' · '.join(partes)

    @property
    def rotulo_longo(self):
        return f'Recibo {self.rotulo_curto}'


def documento_gerado_upload_to(instance, filename):
    """Caminho determinístico por origem/versão.

    Vira a key do objeto quando o storage for trocado para S3 (ver STORAGES em
    core/settings.py) — por isso não depende de nada além de tipo, pk da
    origem e número da versão.
    """
    return f'ged/{instance.tipo}/{instance.origem_pk}/v{instance.numero_versao}/{filename}'


class DocumentoGerado(models.Model):
    """Versão imutável de um PDF gerado pelo sistema (GED versionado).

    Um registro por geração — nunca atualizado após criado (save() bloqueia
    updates). O "documento atual" de uma origem é a versão de numero_versao
    mais alto. Os campos legados Contrato.documento_gerado /
    LaudoVistoria.documento_gerado / Recibo.arquivo são mantidos apenas como
    espelhos da última versão, sincronizados por imoveis.pdf.gerar_e_anexar().

    A origem é modelada com 3 FKs explícitas (uma por tipo) + campo `tipo`,
    em vez de GenericForeignKey: o conjunto de origens é fixo (Contrato,
    Laudo, Recibo), permite select_related e constraints reais no banco, e
    segue o estilo de modelagem explícita do restante do projeto.
    """
    TIPO_CHOICES = [
        ('contrato', 'Contrato'),
        ('laudo', 'Laudo de Vistoria'),
        ('recibo', 'Recibo'),
    ]

    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, null=True, blank=True,
                                 related_name='documentos_gerados')
    laudo = models.ForeignKey(LaudoVistoria, on_delete=models.CASCADE, null=True, blank=True,
                              related_name='documentos_gerados')
    recibo = models.ForeignKey(Recibo, on_delete=models.CASCADE, null=True, blank=True,
                               related_name='documentos_gerados')
    numero_versao = models.PositiveIntegerField(verbose_name='Versão')
    arquivo = models.FileField(upload_to=documento_gerado_upload_to, verbose_name='Arquivo (PDF)')
    sha256 = models.CharField(max_length=64, verbose_name='SHA-256')
    gerado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='documentos_gerados',
                                   verbose_name='Gerado por')
    gerado_em = models.DateTimeField(auto_now_add=True, verbose_name='Gerado em')

    class Meta:
        verbose_name = 'Documento Gerado (GED)'
        verbose_name_plural = 'Documentos Gerados (GED)'
        ordering = ['-gerado_em', '-pk']
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(contrato__isnull=False, laudo__isnull=True, recibo__isnull=True)
                    | models.Q(contrato__isnull=True, laudo__isnull=False, recibo__isnull=True)
                    | models.Q(contrato__isnull=True, laudo__isnull=True, recibo__isnull=False)
                ),
                name='documentogerado_origem_unica',
            ),
            models.UniqueConstraint(fields=['contrato', 'numero_versao'],
                                    condition=models.Q(contrato__isnull=False),
                                    name='documentogerado_versao_unica_contrato'),
            models.UniqueConstraint(fields=['laudo', 'numero_versao'],
                                    condition=models.Q(laudo__isnull=False),
                                    name='documentogerado_versao_unica_laudo'),
            models.UniqueConstraint(fields=['recibo', 'numero_versao'],
                                    condition=models.Q(recibo__isnull=False),
                                    name='documentogerado_versao_unica_recibo'),
        ]

    @property
    def origem(self):
        """Registro de negócio que originou o documento."""
        return self.contrato or self.laudo or self.recibo

    @property
    def origem_pk(self):
        return self.contrato_id or self.laudo_id or self.recibo_id

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError('DocumentoGerado é imutável — gere uma nova versão em vez de editar.')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.get_tipo_display()} #{self.origem_pk} — v{self.numero_versao}'
