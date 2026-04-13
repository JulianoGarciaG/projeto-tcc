from django.db import models


class Proprietario(models.Model):
    nome = models.CharField(max_length=200)
    cpf_cnpj = models.CharField(max_length=20, unique=True, verbose_name='CPF/CNPJ')
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    endereco = models.CharField(max_length=300, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Proprietário'
        verbose_name_plural = 'Proprietários'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Imovel(models.Model):
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

    proprietario = models.ForeignKey(Proprietario, on_delete=models.PROTECT, related_name='imoveis')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='vago')
    endereco = models.CharField(max_length=300)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, default='')
    valor_aluguel = models.DecimalField(max_digits=10, decimal_places=2)
    area_m2 = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='Área (m²)')
    descricao = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Imóvel'
        verbose_name_plural = 'Imóveis'
        ordering = ['endereco']

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.endereco}'


class Inquilino(models.Model):
    nome = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14, unique=True, verbose_name='CPF')
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    rg = models.CharField(max_length=20, blank=True, verbose_name='RG')
    profissao = models.CharField(max_length=100, blank=True, verbose_name='Profissão')
    renda_mensal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Inquilino'
        verbose_name_plural = 'Inquilinos'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Contrato(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('encerrado', 'Encerrado'),
        ('rescindido', 'Rescindido'),
    ]

    imovel = models.ForeignKey(Imovel, on_delete=models.PROTECT, related_name='contratos')
    inquilino = models.ForeignKey(Inquilino, on_delete=models.PROTECT, related_name='contratos')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')
    data_inicio = models.DateField(verbose_name='Data de Início')
    data_fim = models.DateField(verbose_name='Data de Término')
    valor_mensal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor Mensal')
    dia_vencimento = models.PositiveSmallIntegerField(default=10, verbose_name='Dia de Vencimento')
    arquivo = models.FileField(upload_to='contratos/', blank=True, null=True, verbose_name='Arquivo do Contrato')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'
        ordering = ['-data_inicio']

    def __str__(self):
        return f'Contrato #{self.pk} — {self.inquilino} / {self.imovel}'


class LaudoVistoria(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Vistoria de Entrada'),
        ('saida', 'Vistoria de Saída'),
        ('periodica', 'Vistoria Periódica'),
    ]

    imovel = models.ForeignKey(Imovel, on_delete=models.CASCADE, related_name='laudos')
    contrato = models.ForeignKey(Contrato, on_delete=models.SET_NULL, null=True, blank=True, related_name='laudos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    data = models.DateField()
    responsavel = models.CharField(max_length=200, verbose_name='Responsável pela Vistoria')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    arquivo = models.FileField(upload_to='laudos/', blank=True, null=True, verbose_name='Laudo em PDF')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Laudo de Vistoria'
        verbose_name_plural = 'Laudos de Vistoria'
        ordering = ['-data']

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.imovel} ({self.data})'


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
