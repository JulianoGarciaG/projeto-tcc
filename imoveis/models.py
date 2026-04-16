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
    CATEGORIA_CHOICES = [
        ('urbano', 'Urbano'),
        ('rural', 'Rural'),
    ]

    proprietario = models.ForeignKey(Proprietario, on_delete=models.PROTECT, related_name='imoveis')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='vago')
    categoria = models.CharField(max_length=10, choices=CATEGORIA_CHOICES, default='urbano', verbose_name='Categoria')
    endereco = models.CharField(max_length=300)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, default='')
    valor_aluguel = models.DecimalField(max_digits=10, decimal_places=2)
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
    nome = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14, unique=True, verbose_name='CPF')
    cnpj = models.CharField(max_length=18, blank=True, verbose_name='CNPJ')
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    rg = models.CharField(max_length=20, blank=True, verbose_name='RG')
    qualificacao = models.CharField(max_length=300, blank=True, verbose_name='Qualificação',
                                    help_text='Estado civil, profissão, nacionalidade')
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
    TIPO_CONTRATO_CHOICES = [
        ('PF', 'Pessoa Física'),
        ('PJ', 'Pessoa Jurídica'),
    ]

    imovel = models.ForeignKey(Imovel, on_delete=models.PROTECT, related_name='contratos')
    inquilino = models.ForeignKey(Inquilino, on_delete=models.PROTECT, related_name='contratos')
    tipo_contrato = models.CharField(max_length=2, choices=TIPO_CONTRATO_CHOICES, default='PF',
                                     verbose_name='Tipo de Contrato')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')
    data_inicio = models.DateField(verbose_name='Data de Início')
    data_fim = models.DateField(verbose_name='Data de Término')
    valor_mensal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor Mensal')
    dia_vencimento = models.PositiveSmallIntegerField(default=10, verbose_name='Dia de Vencimento')
    arquivo = models.FileField(upload_to='contratos/', blank=True, null=True, verbose_name='Arquivo do Contrato')
    # Documentos GED vinculados ao contrato
    comprovante_renda = models.FileField(upload_to='comprovantes_renda/', blank=True, null=True,
                                         verbose_name='Comprovante de Renda (PF)')
    contrato_social = models.FileField(upload_to='contratos_sociais/', blank=True, null=True,
                                       verbose_name='Contrato Social (PJ)')
    recibo_chaves = models.FileField(upload_to='contratos/recibo_chaves/', blank=True, null=True,
                                     verbose_name='Recibo de Entrega de Chaves')
    comprovante_anual = models.FileField(upload_to='contratos/comprovante_anual/', blank=True, null=True,
                                         verbose_name='Comprovante Anual de Pagamento')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Contrato'
        verbose_name_plural = 'Contratos'
        ordering = ['-data_inicio']

    def __str__(self):
        return f'Contrato #{self.pk} — {self.inquilino} / {self.imovel}'


class Fiador(models.Model):
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='fiadores')
    nome = models.CharField(max_length=200)
    qualificacao = models.CharField(max_length=300, blank=True, verbose_name='Qualificação')
    rg_cpf = models.CharField(max_length=20, verbose_name='RG/CPF')
    certidao_onus = models.FileField(upload_to='certidoes/', blank=True, null=True,
                                     verbose_name='Certidão de Ônus')
    garantia = models.CharField(max_length=200, blank=True, verbose_name='Garantia')

    class Meta:
        verbose_name = 'Fiador'
        verbose_name_plural = 'Fiadores'

    def __str__(self):
        return f'{self.nome} (Fiador do Contrato #{self.contrato_id})'


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


class Saida(models.Model):
    TIPO_CHOICES = [
        ('tributos', 'Pagamento de Tributos (IPTU/ITR)'),
        ('reforma', 'Reforma/Adequação'),
        ('construcao_inicial', 'Construção Inicial'),
        ('consumos', 'Consumos (água/energia/condom.)'),
        ('despesas_juridicas', 'Despesas Jurídicas'),
        ('previsao_despesas', 'Previsão de Despesas'),
    ]
    PAGO_POR_CHOICES = [
        ('inquilino', 'Inquilino'),
        ('administradora', 'Administradora'),
    ]

    imovel = models.ForeignKey(Imovel, on_delete=models.CASCADE, related_name='saidas')
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    descricao = models.CharField(max_length=300, blank=True, verbose_name='Descrição')
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField()
    pago_por = models.CharField(max_length=15, choices=PAGO_POR_CHOICES, verbose_name='Pago Por')
    comprovante = models.FileField(upload_to='saidas/', blank=True, null=True)
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Saída'
        verbose_name_plural = 'Saídas'
        ordering = ['-data']

    def __str__(self):
        return f'{self.get_tipo_display()} — R$ {self.valor} ({self.imovel})'


class Entrada(models.Model):
    TIPO_CHOICES = [
        ('recibo_imovel', 'Recibo por Imóvel'),
        ('recibo_periodo', 'Recibo por Período'),
        ('previsao_mes', 'Previsão de Recebíveis (Mês)'),
        ('previsao_ano', 'Previsão de Recebíveis (Ano)'),
    ]

    imovel = models.ForeignKey(Imovel, on_delete=models.CASCADE, related_name='entradas')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descricao = models.CharField(max_length=300, blank=True, verbose_name='Descrição')
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField()
    comprovante = models.FileField(upload_to='entradas/', blank=True, null=True)
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Entrada'
        verbose_name_plural = 'Entradas'
        ordering = ['-data']

    def __str__(self):
        return f'{self.get_tipo_display()} — R$ {self.valor} ({self.imovel})'
