from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse

from .forms import LaudoVistoriaForm, ReciboForm
from .models import (
    Contrato, Imovel, Inquilino, ItemVistoria, LaudoVistoria,
    Proprietario, Recibo, TestemunhaLaudo,
)
from .validators import validate_cpf

CPF_VALIDO = '529.982.247-25'
CPF_INVALIDO = '111.111.111-11'


def criar_base():
    """Fixtures mínimas: proprietário, imóvel, inquilino e contrato ativo."""
    proprietario = Proprietario.objects.create(nome='Maria Dona', cpf_cnpj='123.456.789-00')
    imovel = Imovel.objects.create(
        proprietario=proprietario, tipo='casa', endereco='Rua A, 100',
        cidade='Maringá', valor_aluguel=Decimal('1500.00'),
    )
    inquilino = Inquilino.objects.create(
        nome='João Locatário', cpf='987.654.321-00', cnpj='12.345.678/0001-90',
        qualificacao='solteiro, brasileiro, empresário',
    )
    contrato = Contrato.objects.create(
        imovel=imovel, inquilino=inquilino, tipo_contrato='PF',
        data_inicio=date(2026, 1, 1), data_fim=date(2027, 1, 1),
        valor_mensal=Decimal('1500.00'), dia_vencimento=10,
    )
    return proprietario, imovel, inquilino, contrato


class ValidateCpfTests(TestCase):
    def test_cpf_valido_com_mascara(self):
        validate_cpf(CPF_VALIDO)  # não deve levantar

    def test_cpf_valido_sem_mascara(self):
        validate_cpf('52998224725')

    def test_cpf_com_digitos_repetidos_invalido(self):
        with self.assertRaises(ValidationError):
            validate_cpf(CPF_INVALIDO)

    def test_cpf_com_digito_verificador_errado(self):
        with self.assertRaises(ValidationError):
            validate_cpf('529.982.247-26')

    def test_cpf_curto_invalido(self):
        with self.assertRaises(ValidationError):
            validate_cpf('123')


class ReciboTests(TestCase):
    def test_somatorio_considera_apenas_valores_preenchidos(self):
        recibo = Recibo(valor_aluguel=Decimal('1200.00'), valor_condominio=Decimal('300.00'))
        self.assertEqual(recibo.somatorio(), Decimal('1500.00'))

    def test_somatorio_vazio_e_zero(self):
        self.assertEqual(Recibo().somatorio(), 0)

    def test_form_exige_ao_menos_um_campo(self):
        form = ReciboForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('Preencha ao menos um campo', str(form.errors))

    def test_form_valido_com_um_campo(self):
        form = ReciboForm(data={'quem_pagou': 'Fulano'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_rejeita_cpf_invalido(self):
        form = ReciboForm(data={'assinante_cpf': CPF_INVALIDO})
        self.assertFalse(form.is_valid())
        self.assertIn('assinante_cpf', form.errors)

    def test_form_aceita_cpf_valido(self):
        form = ReciboForm(data={'assinante_cpf': CPF_VALIDO})
        self.assertTrue(form.is_valid(), form.errors)

    def test_pdf_exibe_apenas_campos_preenchidos(self):
        recibo = Recibo(
            quantia=Decimal('1500.00'), valor_aluguel=Decimal('1200.00'),
            valor_condominio=Decimal('300.00'), quem_pagou='Fulano de Tal',
        )
        html = render_to_string('documentos/recibo_pdf.html', {'recibo': recibo})
        self.assertIn('Aluguel', html)
        self.assertIn('Condomínio', html)
        self.assertIn('Fulano de Tal', html)
        self.assertIn('Somatório', html)
        self.assertIn('1.500,00', html)  # somatório = 1200 + 300
        # Campos vazios não aparecem
        self.assertNotIn('Impostos', html)
        self.assertNotIn('Seguros', html)
        self.assertNotIn('Vencido em', html)
        self.assertNotIn('Proveniente do Sítio', html)


class ContratoPdfTests(TestCase):
    def setUp(self):
        _, self.imovel, self.inquilino, self.contrato = criar_base()

    def test_observacoes_aparecem_apenas_se_preenchidas(self):
        html = render_to_string('documentos/contrato_pdf.html', {'contrato': self.contrato})
        self.assertNotIn('Observações', html)

        self.contrato.observacoes = 'Permitido animal de pequeno porte.'
        html = render_to_string('documentos/contrato_pdf.html', {'contrato': self.contrato})
        self.assertIn('Observações', html)
        self.assertIn('Permitido animal de pequeno porte.', html)

    def test_pf_exibe_cpf_e_nao_cnpj(self):
        html = render_to_string('documentos/contrato_pdf.html', {'contrato': self.contrato})
        self.assertIn('Pessoa Física', html)
        self.assertIn(self.inquilino.cpf, html)
        self.assertNotIn('Razão Social', html)
        self.assertNotIn(self.inquilino.cnpj, html)

    def test_pj_exibe_cnpj(self):
        self.contrato.tipo_contrato = 'PJ'
        html = render_to_string('documentos/contrato_pdf.html', {'contrato': self.contrato})
        self.assertIn('Pessoa Jurídica', html)
        self.assertIn('Razão Social', html)
        self.assertIn(self.inquilino.cnpj, html)


class LaudoTests(TestCase):
    def setUp(self):
        _, self.imovel, self.inquilino, self.contrato = criar_base()
        self.laudo = LaudoVistoria.objects.create(
            imovel=self.imovel, contrato=self.contrato, tipo='entrada',
            data=date(2026, 7, 1), responsavel='Carlos Vistoriador',
        )

    def test_contrato_obrigatorio_no_form(self):
        form = LaudoVistoriaForm(data={
            'imovel': self.imovel.pk, 'tipo': 'entrada',
            'data': '2026-07-01', 'responsavel': 'Carlos',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('contrato', form.errors)

    def test_resumo_vistoria_calculado(self):
        ItemVistoria.objects.create(laudo=self.laudo, comodo='Sala', item='Piso', estado='bom', ordem=0)
        ItemVistoria.objects.create(laudo=self.laudo, comodo='Sala', item='Teto e forro', estado='regular', ordem=1)
        ItemVistoria.objects.create(laudo=self.laudo, comodo='Cozinha', item='Louças e metais', estado='ruim', ordem=2)
        resumo = self.laudo.resumo_vistoria()
        self.assertEqual(resumo, {'total': 3, 'bom': 1, 'regular': 1, 'ruim': 1})

    def test_nomes_derivados_dos_cadastros(self):
        self.assertEqual(self.laudo.locador_nome(), 'Maria Dona')
        self.assertEqual(self.laudo.locatario_nome(), 'João Locatário')

    def test_testemunha_cpf_invalido_rejeitado(self):
        testemunha = TestemunhaLaudo(laudo=self.laudo, nome='Zé', cpf=CPF_INVALIDO)
        with self.assertRaises(ValidationError):
            testemunha.full_clean()

    def test_pdf_laudo_condicionais(self):
        ItemVistoria.objects.create(laudo=self.laudo, comodo='Sala', item='Piso', estado='bom',
                                    observacao='Piso novo', ordem=0)
        TestemunhaLaudo.objects.create(laudo=self.laudo, nome='Testemunha Um', cpf=CPF_VALIDO)
        from .views import _itens_agrupados
        html = render_to_string('documentos/laudo_pdf.html', {
            'laudo': self.laudo,
            'grupos': _itens_agrupados(self.laudo),
            'resumo': self.laudo.resumo_vistoria(),
            'testemunhas': self.laudo.testemunhas.all(),
        })
        self.assertIn('Vistoria de Entrada', html)
        self.assertIn('Maria Dona', html)
        self.assertIn('João Locatário', html)
        self.assertIn('Sala', html)
        self.assertIn('Piso novo', html)
        self.assertIn('1 item vistoriado', html)
        self.assertIn('Testemunha Um', html)
        # Sem observações gerais preenchidas, a seção não aparece
        self.assertNotIn('Observações Gerais', html)


class GeracaoPdfViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', password='x')
        self.client.force_login(self.user)
        _, self.imovel, self.inquilino, self.contrato = criar_base()

    def test_recibo_create_gera_pdf_e_anexa(self):
        resp = self.client.post(reverse('recibo_create'), {
            'quem_pagou': 'Fulano', 'quantia': '1500.00', 'valor_aluguel': '1500.00',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
        self.assertTrue(resp.content.startswith(b'%PDF-'))
        recibo = Recibo.objects.latest('criado_em')
        self.assertTrue(recibo.arquivo)
        recibo.arquivo.delete(save=False)

    def test_contrato_gerar_pdf_view(self):
        resp = self.client.get(reverse('contrato_gerar_pdf', args=[self.contrato.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
        self.assertTrue(resp.content.startswith(b'%PDF-'))
        self.contrato.refresh_from_db()
        self.assertTrue(self.contrato.documento_gerado)
        self.contrato.documento_gerado.delete(save=False)

    def test_laudo_gerar_pdf_view(self):
        laudo = LaudoVistoria.objects.create(
            imovel=self.imovel, contrato=self.contrato, tipo='saida',
            data=date(2026, 7, 1), responsavel='Carlos',
        )
        resp = self.client.get(reverse('laudo_gerar_pdf', args=[laudo.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.content.startswith(b'%PDF-'))
        laudo.refresh_from_db()
        self.assertTrue(laudo.documento_gerado)
        laudo.documento_gerado.delete(save=False)

    def test_gerar_pdf_exige_login(self):
        self.client.logout()
        resp = self.client.get(reverse('contrato_gerar_pdf', args=[self.contrato.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)

    def test_laudo_create_salva_apenas_itens_com_estado(self):
        from .views import _initial_itens_catalogo
        itens = _initial_itens_catalogo()
        n = len(itens)
        self.assertEqual(n, 32)  # catálogo seedado: 5 cômodos, 32 itens
        data = {
            'imovel': str(self.imovel.pk), 'contrato': str(self.contrato.pk),
            'tipo': 'entrada', 'data': '2026-07-05', 'responsavel': 'Vistoriador Teste',
            'local_assinatura': 'Maringá', 'data_assinatura': '2026-07-05',
            'itens-TOTAL_FORMS': str(n), 'itens-INITIAL_FORMS': '0',
            'itens-MIN_NUM_FORMS': '0', 'itens-MAX_NUM_FORMS': '1000',
            'testemunhas-TOTAL_FORMS': '2', 'testemunhas-INITIAL_FORMS': '0',
            'testemunhas-MIN_NUM_FORMS': '0', 'testemunhas-MAX_NUM_FORMS': '1000',
            'testemunhas-0-nome': 'Testemunha A', 'testemunhas-0-cpf': CPF_VALIDO,
            'testemunhas-1-nome': '', 'testemunhas-1-cpf': '',
        }
        for i, item in enumerate(itens):
            data[f'itens-{i}-comodo'] = item['comodo']
            data[f'itens-{i}-item'] = item['item']
            data[f'itens-{i}-ordem'] = str(item['ordem'])
            # estado preenchido só nos 3 primeiros; o resto fica "não vistoriado"
            data[f'itens-{i}-estado'] = 'bom' if i < 3 else ''
            data[f'itens-{i}-observacao'] = 'obs teste' if i == 0 else ''

        resp = self.client.post(reverse('laudo_create'), data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
        self.assertTrue(resp.content.startswith(b'%PDF-'))
        laudo = LaudoVistoria.objects.latest('criado_em')
        self.assertEqual(laudo.itens.count(), 3)
        self.assertEqual(laudo.resumo_vistoria(), {'total': 3, 'bom': 3, 'regular': 0, 'ruim': 0})
        self.assertEqual(laudo.testemunhas.count(), 1)
        self.assertTrue(laudo.documento_gerado)
        laudo.documento_gerado.delete(save=False)

    def test_ged_nao_quebra_com_documento_gerado_nulo(self):
        # Regressão: registros antigos têm documento_gerado NULL (não '') e o
        # exclude('') do Django mantém NULLs — o GED não pode listá-los.
        self.assertIsNone(self.contrato.documento_gerado.name)
        resp = self.client.get(reverse('documentos'))
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(self.contrato, resp.context['contratos_gerados'])
