"""Popula o banco com dados fictícios para demonstração.

Uso: venv/Scripts/python manage.py seed_demo
Cria um lote novo a cada execução (não limpa o banco antes).
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from imoveis.models import (
    Proprietario, Inquilino, Imovel, Contrato, Fiador,
    LaudoVistoria, ItemVistoria, TestemunhaLaudo, ComodoTemplate,
    Lancamento, Notificacao, RenovacaoContrato, Distrato, Recibo,
)


def _dv_cpf(base):
    for pos in (9, 10):
        soma = sum(int(base[i]) * ((pos + 1) - i) for i in range(pos))
        d = (soma * 10) % 11
        d = 0 if d == 10 else d
        base += str(d)
    return base


def gera_cpf():
    base = ''.join(str(random.randint(0, 9)) for _ in range(9))
    while base == base[0] * 9:
        base = ''.join(str(random.randint(0, 9)) for _ in range(9))
    d = _dv_cpf(base)
    return f'{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}'


def gera_cnpj():
    base = ''.join(str(random.randint(0, 9)) for _ in range(8)) + '0001'
    pesos = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for pos in (12, 13):
        soma = sum(int(base[i]) * pesos[len(pesos) - pos + i] for i in range(pos))
        d = soma % 11
        d = 0 if d < 2 else 11 - d
        base += str(d)
    return f'{base[:2]}.{base[2:5]}.{base[5:8]}/{base[8:12]}-{base[12:]}'


def gera_tel():
    return f'(44) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}'


def gera_rg():
    return f'{random.randint(10, 99)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(0, 9)}'


NOMES = [
    'Ana Beatriz Souza', 'Carlos Eduardo Lima', 'Fernanda Oliveira Costa',
    'Rafael Almeida Nunes', 'Juliana Ribeiro Martins', 'Bruno Henrique Alves',
    'Patrícia Gomes Ferreira', 'Marcelo Tavares Rocha', 'Camila Duarte Pinto',
    'Gustavo Barbosa Mendes',
]
EMPRESAS = [
    'Comércio Sul Ltda', 'Padaria Estrela ME', 'AutoPeças Maringá Ltda',
    'Tech Solutions EIRELI', 'Restaurante Sabor & Cia Ltda',
]
RUAS = [
    'Rua das Palmeiras', 'Avenida Brasil', 'Rua Santos Dumont',
    'Rua Getúlio Vargas', 'Avenida Colombo', 'Rua Paraná',
    'Rua Joubert de Carvalho', 'Avenida São Paulo', 'Rua Néo Alves Martins',
    'Rua Pioneiro João Fernandes',
]
BAIRROS = ['Centro', 'Zona 7', 'Jardim Alvorada', 'Vila Esperança', 'Zona 2',
           'Novo Centro', 'Jardim Universo', 'Parque das Grevíleas']
PROFISSOES = ['Professor', 'Engenheira', 'Advogado', 'Médica', 'Comerciante',
              'Contadora', 'Designer', 'Enfermeiro', 'Analista', 'Arquiteta']
FAIXAS = ['ate_2k', '2_4k', '4_7k', '7_10k', '10_16k', 'acima_16k']
TIPOS = ['apartamento', 'casa', 'comercial', 'terreno', 'galpao']


class Command(BaseCommand):
    help = 'Popula o banco com dados fictícios para demonstração.'

    def handle(self, *args, **options):
        random.seed(42)
        w = self.stdout.write
        w('== Seed iniciado ==')

        # --- Proprietários (mix PF/PJ)
        proprietarios = []
        for nome in NOMES[:7]:
            proprietarios.append(Proprietario.objects.create(
                nome=nome, cpf_cnpj=gera_cpf(),
                email=f'{nome.split()[0].lower()}@email.com', telefone=gera_tel(),
            ))
        for emp in EMPRESAS[:2]:
            proprietarios.append(Proprietario.objects.create(
                nome=emp, cpf_cnpj=gera_cnpj(),
                email=f'contato@{emp.split()[0].lower()}.com.br', telefone=gera_tel(),
            ))
        w(f'Proprietários: {len(proprietarios)}')

        # --- Inquilinos
        inquilinos = []
        for nome in NOMES:
            inquilinos.append(Inquilino.objects.create(
                nome=nome, cpf=gera_cpf(),
                email=f'{nome.split()[0].lower()}.inq@email.com', telefone=gera_tel(),
                rg=gera_rg(), profissao=random.choice(PROFISSOES),
                qualificacao=f'{random.choice(["Solteiro(a)", "Casado(a)", "Divorciado(a)"])}, '
                             f'{random.choice(PROFISSOES).lower()}, brasileiro(a)',
                faixa_renda=random.choice(FAIXAS),
                observacoes='Cliente cadastrado para demonstração.',
            ))
        w(f'Inquilinos: {len(inquilinos)}')

        # --- Imóveis (8 urbanos, 2 rurais)
        imoveis = []
        for i in range(10):
            rural = i >= 8
            tipo = 'terreno' if rural else random.choice(TIPOS)
            imoveis.append(Imovel.objects.create(
                proprietario=random.choice(proprietarios),
                tipo=tipo, categoria='rural' if rural else 'urbano',
                endereco=random.choice(RUAS), numero=str(random.randint(50, 2000)),
                complemento=random.choice(['', 'Apto 12', 'Casa 2', 'Bloco B', 'Sala 3']),
                bairro='' if rural else random.choice(BAIRROS), cidade='Maringá',
                area_m2=Decimal(random.randint(45, 350)) if not rural else Decimal(random.randint(5000, 40000)),
                descricao='Imóvel bem localizado, cadastrado para demonstração do sistema.',
                matricula=f'{random.randint(10000, 99999)}',
                data_aquisicao=date(random.randint(2010, 2022), random.randint(1, 12), random.randint(1, 28)),
                valor_aquisicao=Decimal(random.randint(150, 900)) * 1000,
                cadastro_prefeitura='' if rural else f'PMM-{random.randint(1000, 9999)}',
                nirf=f'{random.randint(1000000, 9999999)}' if rural else '',
                incra=f'{random.randint(100000, 999999)}' if rural else '',
                car=f'PR-{random.randint(100000, 999999)}' if rural else '',
            ))
        w(f'Imóveis: {len(imoveis)}')

        # --- Contratos ativos (imóveis 0..7)
        hoje = date.today()
        contratos = []
        for i, imv in enumerate(imoveis[:8]):
            inicio = hoje - timedelta(days=random.randint(30, 600))
            fim = inicio + timedelta(days=365 * random.choice([1, 2, 3]))
            valor = Decimal(random.randint(120, 550)) * 10
            pj = imv.tipo in ('comercial', 'galpao')
            ctr = Contrato.objects.create(
                imovel=imv, inquilino=random.choice(inquilinos),
                tipo_contrato='PJ' if pj else 'PF',
                finalidade='comercial' if pj else 'residencial', status='ativo',
                data_inicio=inicio, data_fim=fim, valor_mensal=valor,
                dia_vencimento=random.choice([5, 10, 15, 20]),
                local_assinatura='Maringá/PR', data_assinatura=inicio,
                observacoes='Contrato de demonstração.',
            )
            contratos.append(ctr)
            if i % 2 == 0:
                Fiador.objects.create(
                    contrato=ctr, nome=random.choice(NOMES),
                    qualificacao='Casado(a), comerciante, brasileiro(a)',
                    rg_cpf=gera_cpf(), rg=gera_rg(), cpf=gera_cpf(),
                    endereco=f'{random.choice(RUAS)}, {random.randint(1, 999)} - Maringá/PR',
                    conjuge_nome=random.choice(NOMES),
                    conjuge_rg=gera_rg(), conjuge_cpf=gera_cpf(), garantia='Fiança',
                )
        w(f'Contratos ativos: {len(contratos)}')

        # --- Contrato encerrado via distrato (imóvel 8 volta a vago)
        imv_enc = imoveis[8]
        ctr_enc = Contrato.objects.create(
            imovel=imv_enc, inquilino=random.choice(inquilinos),
            tipo_contrato='PF', finalidade='residencial', status='ativo',
            data_inicio=hoje - timedelta(days=800), data_fim=hoje - timedelta(days=60),
            valor_mensal=Decimal('1800.00'), dia_vencimento=10,
            local_assinatura='Maringá/PR', data_assinatura=hoje - timedelta(days=800),
        )

        # --- Laudos de entrada (5 contratos) com checklist e testemunhas
        comodos = list(ComodoTemplate.objects.prefetch_related('itens').all())
        laudos = []
        for ctr in contratos[:5]:
            laudo = LaudoVistoria.objects.create(
                imovel=ctr.imovel, contrato=ctr, tipo='entrada', data=ctr.data_inicio,
                responsavel='Vistoriador Shelter',
                observacoes='Vistoria de entrada realizada para demonstração.',
                local_assinatura='Maringá/PR', data_assinatura=ctr.data_inicio,
            )
            ordem = 0
            for comodo in comodos:
                for item_t in comodo.itens.all():
                    ItemVistoria.objects.create(
                        laudo=laudo, comodo=comodo.nome, item=item_t.nome,
                        estado=random.choice(['bom', 'bom', 'regular', 'ruim']),
                        observacao=random.choice(['', 'Sem avarias', 'Pequeno desgaste', 'Requer reparo']),
                        ordem=ordem,
                    )
                    ordem += 1
            TestemunhaLaudo.objects.create(laudo=laudo, nome=random.choice(NOMES), cpf=gera_cpf())
            TestemunhaLaudo.objects.create(laudo=laudo, nome=random.choice(NOMES), cpf=gera_cpf())
            laudos.append(laudo)
        w(f'Laudos: {len(laudos)} (com checklist e testemunhas)')

        # --- Laudo de saída + distrato do contrato encerrado
        laudo_saida = LaudoVistoria.objects.create(
            imovel=imv_enc, contrato=ctr_enc, tipo='saida',
            data=hoje - timedelta(days=60), responsavel='Vistoriador Shelter',
            observacoes='Vistoria de saída.', local_assinatura='Maringá/PR',
            data_assinatura=hoje - timedelta(days=60),
        )
        Distrato.objects.create(
            contrato=ctr_enc, tipo='amigavel', data_distrato=hoje - timedelta(days=58),
            laudo_saida=laudo_saida, observacoes='Distrato amigável de demonstração.',
        )
        w('Distrato criado (contrato encerrado)')

        # --- Renovação em um contrato ativo
        RenovacaoContrato.objects.create(
            contrato=contratos[0], tipo='12_12', data_renovacao=hoje - timedelta(days=10),
            novo_valor_mensal=contratos[0].valor_mensal + Decimal('200.00'),
            observacoes='Renovação de demonstração.',
        )
        w('Renovação criada')

        # --- Recibos (cada um gera Lancamento de ganho via signal)
        recibos = 0
        for ctr in contratos[:6]:
            for parcela in range(1, random.randint(2, 4)):
                ini = date(2026, parcela, 1)
                cond = Decimal(random.choice([0, 150, 200, 350]))
                Recibo.objects.create(
                    imovel=ctr.imovel, contrato=ctr,
                    parcela_atual=parcela, parcela_total=12,
                    valor_aluguel=ctr.valor_mensal, valor_condominio=cond,
                    quem_pagou=ctr.inquilino.nome, periodo_inicio=ini,
                    periodo_fim=ini + timedelta(days=29),
                    vencido_em=ini + timedelta(days=ctr.dia_vencimento),
                    quantia=ctr.valor_mensal + cond,
                    assinante_nome='Administradora Shelter', assinante_cpf=gera_cpf(),
                    data_assinatura=ini,
                )
                recibos += 1
        w(f'Recibos: {recibos} (cada um gerou lançamento de ganho)')

        # --- Lançamentos avulsos (despesa + ganho efetivado por contrato)
        lanc = 0
        for ctr in contratos:
            Lancamento.objects.create(
                imovel=ctr.imovel, contrato=ctr, natureza='despesa',
                tipo=random.choice(['iptu', 'condominio', 'manutencao', 'outros']),
                valor=Decimal(random.randint(80, 600)),
                data_vencimento=hoje - timedelta(days=random.randint(1, 90)),
                data_pagamento=hoje - timedelta(days=random.randint(1, 30)),
                observacoes='Despesa de demonstração.',
            )
            Lancamento.objects.create(
                imovel=ctr.imovel, contrato=ctr, natureza='ganho', tipo='aluguel',
                status='efetivado', valor=ctr.valor_mensal,
                data_vencimento=hoje - timedelta(days=random.randint(1, 60)),
                data_pagamento=hoje - timedelta(days=random.randint(1, 30)),
            )
            lanc += 2
        w(f'Lançamentos avulsos: {lanc}')

        # --- Notificações
        notif = 0
        for imv in imoveis[:6]:
            Notificacao.objects.create(
                imovel=imv, tipo=random.choice(['prefeitura', 'receita_federal', 'bombeiros', 'outro']),
                titulo=random.choice([
                    'Notificação de IPTU', 'Vistoria do Corpo de Bombeiros',
                    'Regularização cadastral', 'Malha fina Receita Federal',
                ]),
                data_recebimento=hoje - timedelta(days=random.randint(5, 120)),
                data_resposta=None if random.random() < 0.5 else hoje - timedelta(days=random.randint(1, 20)),
                status=random.choice(['pendente', 'respondida', 'arquivada']),
                observacoes='Notificação de demonstração.',
            )
            notif += 1
        w(f'Notificações: {notif}')

        w(self.style.SUCCESS('== Seed concluído =='))
