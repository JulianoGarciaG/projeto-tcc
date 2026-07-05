from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse

from .forms import LaudoVistoriaForm, ReciboForm
from .models import (
    Contrato, Imovel, Inquilino, ItemVistoria, LaudoVistoria,
    Proprietario, Recibo, TestemunhaLaudo,
)
from .validators import validate_cpf, validate_cnpj, validate_cpf_cnpj

CPF_VALIDO = '529.982.247-25'
CPF_VALIDO_2 = '111.444.777-35'
CPF_INVALIDO = '111.111.111-11'
CNPJ_VALIDO = '11.222.333/0001-81'
CNPJ_INVALIDO = '11.222.333/0001-99'


def criar_base():
    """Fixtures mínimas: proprietário, imóvel, inquilino e contrato ativo."""
    proprietario = Proprietario.objects.create(nome='Maria Dona', cpf_cnpj=CPF_VALIDO_2)
    imovel = Imovel.objects.create(
        proprietario=proprietario, tipo='casa', endereco='Rua A',
        numero='100', complemento='Fundos', cidade='Maringá',
    )
    inquilino = Inquilino.objects.create(
        nome='João Locatário', cpf=CPF_VALIDO, cnpj=CNPJ_VALIDO,
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


class ValidateCnpjTests(TestCase):
    def test_cnpj_valido_com_mascara(self):
        validate_cnpj(CNPJ_VALIDO)  # não deve levantar

    def test_cnpj_valido_sem_mascara(self):
        validate_cnpj('11222333000181')

    def test_cnpj_digito_verificador_errado(self):
        with self.assertRaises(ValidationError):
            validate_cnpj(CNPJ_INVALIDO)

    def test_cnpj_digitos_repetidos_invalido(self):
        with self.assertRaises(ValidationError):
            validate_cnpj('11.111.111/1111-11')

    def test_cnpj_curto_invalido(self):
        with self.assertRaises(ValidationError):
            validate_cnpj('123')

    def test_cpf_cnpj_condicional(self):
        validate_cpf_cnpj(CPF_VALIDO)     # 11 dígitos → CPF
        validate_cpf_cnpj(CNPJ_VALIDO)    # 14 dígitos → CNPJ
        with self.assertRaises(ValidationError):
            validate_cpf_cnpj('123456789012')  # 12 dígitos → nem CPF nem CNPJ

    def test_inquilino_cpf_invalido_bloqueado(self):
        inquilino = Inquilino(nome='Zé', cpf=CPF_INVALIDO)
        with self.assertRaises(ValidationError):
            inquilino.full_clean()

    def test_proprietario_cnpj_valido_aceito(self):
        proprietario = Proprietario(nome='Empresa Dona', cpf_cnpj=CNPJ_VALIDO)
        proprietario.full_clean()  # não deve levantar


class ReciboTests(TestCase):
    def setUp(self):
        _, self.imovel, self.inquilino, self.contrato = criar_base()
        self.vinculos = {'imovel': str(self.imovel.pk), 'contrato': str(self.contrato.pk)}

    def test_somatorio_considera_apenas_valores_preenchidos(self):
        recibo = Recibo(valor_aluguel=Decimal('1200.00'), valor_condominio=Decimal('300.00'))
        self.assertEqual(recibo.somatorio(), Decimal('1500.00'))

    def test_somatorio_vazio_e_zero(self):
        self.assertEqual(Recibo().somatorio(), 0)

    def test_form_exige_imovel_e_contrato(self):
        # R1 — imóvel e contrato passam a ser obrigatórios
        form = ReciboForm(data={'quem_pagou': 'Fulano'})
        self.assertFalse(form.is_valid())
        self.assertIn('imovel', form.errors)
        self.assertIn('contrato', form.errors)

    def test_form_exige_ao_menos_um_campo_alem_dos_vinculos(self):
        form = ReciboForm(data=self.vinculos)
        self.assertFalse(form.is_valid())
        self.assertIn('Preencha ao menos um campo', str(form.errors))

    def test_form_valido_com_um_campo(self):
        form = ReciboForm(data={**self.vinculos, 'quem_pagou': 'Fulano'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_aceita_moeda_com_virgula(self):
        # G5 — campos monetários localizados aceitam "1500,00"
        form = ReciboForm(data={**self.vinculos, 'quantia': '1500,00'})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['quantia'], Decimal('1500.00'))

    def test_form_aceita_data_ddmmyyyy(self):
        # G7 — datepickers em dd/mm/yyyy
        form = ReciboForm(data={**self.vinculos, 'periodo_inicio': '01/06/2026',
                                'periodo_fim': '30/06/2026'})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['periodo_inicio'], date(2026, 6, 1))
        self.assertEqual(form.cleaned_data['periodo_fim'], date(2026, 6, 30))

    def test_form_rejeita_cpf_invalido(self):
        form = ReciboForm(data={**self.vinculos, 'assinante_cpf': CPF_INVALIDO})
        self.assertFalse(form.is_valid())
        self.assertIn('assinante_cpf', form.errors)

    def test_form_aceita_cpf_valido(self):
        form = ReciboForm(data={**self.vinculos, 'assinante_cpf': CPF_VALIDO})
        self.assertTrue(form.is_valid(), form.errors)

    def test_pdf_exibe_apenas_campos_preenchidos(self):
        recibo = Recibo(
            imovel=self.imovel, contrato=self.contrato,
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

    def test_pdf_endereco_completo_e_periodo(self):
        # R2/R3 — endereço com número/complemento; período só com as duas datas
        recibo = Recibo(imovel=self.imovel, contrato=self.contrato,
                        quantia=Decimal('100.00'),
                        periodo_inicio=date(2026, 6, 1), periodo_fim=date(2026, 6, 30))
        html = render_to_string('documentos/recibo_pdf.html', {'recibo': recibo})
        self.assertIn('Rua A, 100 — Fundos', html)
        self.assertIn('de 01/06/2026 a 30/06/2026', html)

        recibo.periodo_fim = None
        html = render_to_string('documentos/recibo_pdf.html', {'recibo': recibo})
        self.assertNotIn('Correspondente ao Período', html)


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

    def test_form_restringe_contratos_ao_imovel(self):
        # L1 — contrato de outro imóvel é rejeitado
        outro_imovel = Imovel.objects.create(
            proprietario=self.imovel.proprietario, tipo='casa',
            endereco='Rua B', cidade='Maringá',
        )
        form = LaudoVistoriaForm(data={
            'imovel': outro_imovel.pk, 'contrato': self.contrato.pk,
            'tipo': 'entrada', 'data': '2026-07-01', 'responsavel': 'Carlos',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('contrato', form.errors)

    def test_tipo_periodica_removido(self):
        # L2 — a opção "Vistoria Periódica" não existe mais
        tipos = [t[0] for t in LaudoVistoria.TIPO_CHOICES]
        self.assertNotIn('periodica', tipos)

    def test_form_nao_expoe_upload_manual(self):
        # L3 — o upload manual saiu da criação (fica só no detail, L6)
        self.assertNotIn('arquivo', LaudoVistoriaForm.Meta.fields)

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
        # L5 — espaço extra acima das linhas de assinatura do laudo
        self.assertIn('assinatura-laudo', html)
        # Sem observações gerais preenchidas, a seção não aparece
        self.assertNotIn('Observações Gerais', html)


class FluxoViewTests(TestCase):
    """G3/G4/L1/L4/L6 — comportamento das views após a Rodada 2."""

    def setUp(self):
        self.user = User.objects.create_user('tester', password='x')
        self.client.force_login(self.user)
        _, self.imovel, self.inquilino, self.contrato = criar_base()

    def test_recibo_create_redireciona_sem_pdf(self):
        # G4 — salvar não gera/baixa PDF; segue o padrão PRG
        resp = self.client.post(reverse('recibo_create'), {
            'imovel': str(self.imovel.pk), 'contrato': str(self.contrato.pk),
            'quem_pagou': 'Fulano', 'quantia': '1500,00', 'valor_aluguel': '1500,00',
        })
        recibo = Recibo.objects.latest('criado_em')
        self.assertRedirects(resp, reverse('recibo_detail', args=[recibo.pk]))
        self.assertFalse(recibo.arquivo)  # nenhum PDF anexado automaticamente
        self.assertEqual(recibo.quantia, Decimal('1500.00'))

    def test_contrato_create_redireciona_sem_pdf(self):
        # G4 + G7 — datas em dd/mm/yyyy aceitas
        resp = self.client.post(reverse('contrato_create'), {
            'imovel': str(self.imovel.pk), 'inquilino': str(self.inquilino.pk),
            'tipo_contrato': 'PF', 'status': 'ativo',
            'data_inicio': '01/08/2026', 'data_fim': '01/08/2027',
            'valor_mensal': '2000.00', 'dia_vencimento': '10',
            'fiadores-TOTAL_FORMS': '1', 'fiadores-INITIAL_FORMS': '0',
            'fiadores-MIN_NUM_FORMS': '0', 'fiadores-MAX_NUM_FORMS': '1000',
        })
        contrato = Contrato.objects.latest('criado_em')
        self.assertRedirects(resp, reverse('contrato_detail', args=[contrato.pk]))
        self.assertFalse(contrato.documento_gerado)
        self.assertEqual(contrato.data_inicio, date(2026, 8, 1))

    def test_contrato_delete_protegido_nao_da_500(self):
        # G3 — contrato com laudo vinculado: mensagem amigável + redirect
        LaudoVistoria.objects.create(
            imovel=self.imovel, contrato=self.contrato, tipo='entrada',
            data=date(2026, 7, 1), responsavel='Carlos',
        )
        resp = self.client.post(reverse('contrato_delete', args=[self.contrato.pk]), follow=True)
        self.assertRedirects(resp, reverse('contrato_detail', args=[self.contrato.pk]))
        self.assertTrue(Contrato.objects.filter(pk=self.contrato.pk).exists())
        mensagens = [str(m) for m in resp.context['messages']]
        self.assertTrue(any('não pode ser excluído' in m for m in mensagens))

    def test_contrato_delete_sem_vinculos_funciona(self):
        contrato_pk = self.contrato.pk
        resp = self.client.post(reverse('contrato_delete', args=[contrato_pk]))
        self.assertRedirects(resp, reverse('contrato_list'))
        self.assertFalse(Contrato.objects.filter(pk=contrato_pk).exists())

    def test_contratos_por_imovel_json(self):
        # L1 — endpoint retorna apenas os contratos do imóvel
        resp = self.client.get(reverse('contratos_por_imovel_json', args=[self.imovel.pk]))
        self.assertEqual(resp.status_code, 200)
        dados = resp.json()['contratos']
        self.assertEqual(len(dados), 1)
        self.assertEqual(dados[0]['id'], self.contrato.pk)
        self.assertIn('João Locatário', dados[0]['label'])

        outro = Imovel.objects.create(proprietario=self.imovel.proprietario, tipo='casa',
                                      endereco='Rua B', cidade='Maringá')
        resp = self.client.get(reverse('contratos_por_imovel_json', args=[outro.pk]))
        self.assertEqual(resp.json()['contratos'], [])

    def test_laudo_create_renderiza_checklist_do_catalogo(self):
        # L4 — o GET de "Novo Laudo" exibe as 32 linhas do catálogo seedado
        resp = self.client.get(reverse('laudo_create'))
        self.assertEqual(resp.status_code, 200)
        item_formset = resp.context['item_formset']
        self.assertEqual(item_formset.total_form_count(), 32)
        self.assertContains(resp, 'Sala')
        self.assertContains(resp, 'Cozinha')

    def test_laudo_anexar_arquivo(self):
        # L6 — anexo do laudo assinado enviado a partir do detail
        laudo = LaudoVistoria.objects.create(
            imovel=self.imovel, contrato=self.contrato, tipo='entrada',
            data=date(2026, 7, 1), responsavel='Carlos',
        )
        arquivo = SimpleUploadedFile('laudo_assinado.pdf', b'%PDF-1.4 fake', 'application/pdf')
        resp = self.client.post(reverse('laudo_anexar_arquivo', args=[laudo.pk]), {'arquivo': arquivo})
        self.assertRedirects(resp, reverse('laudo_detail', args=[laudo.pk]))
        laudo.refresh_from_db()
        self.assertTrue(laudo.arquivo)
        laudo.arquivo.delete(save=False)


class GeracaoPdfViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', password='x')
        self.client.force_login(self.user)
        _, self.imovel, self.inquilino, self.contrato = criar_base()

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

    def test_recibo_gerar_pdf_view(self):
        recibo = Recibo.objects.create(imovel=self.imovel, contrato=self.contrato,
                                       quantia=Decimal('1500.00'))
        resp = self.client.get(reverse('recibo_gerar_pdf', args=[recibo.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
        self.assertTrue(resp.content.startswith(b'%PDF-'))
        recibo.refresh_from_db()
        self.assertTrue(recibo.arquivo)
        recibo.arquivo.delete(save=False)

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
        laudo = LaudoVistoria.objects.latest('criado_em')
        # G4 — sem download automático de PDF: redireciona para o detail
        self.assertRedirects(resp, reverse('laudo_detail', args=[laudo.pk]))
        self.assertEqual(laudo.itens.count(), 3)
        self.assertEqual(laudo.resumo_vistoria(), {'total': 3, 'bom': 3, 'regular': 0, 'ruim': 0})
        self.assertEqual(laudo.testemunhas.count(), 1)
        self.assertFalse(laudo.documento_gerado)

    def test_ged_nao_quebra_com_documento_gerado_nulo(self):
        # Regressão: registros antigos têm documento_gerado NULL (não '') e o
        # exclude('') do Django mantém NULLs — o GED não pode listá-los.
        self.assertIsNone(self.contrato.documento_gerado.name)
        resp = self.client.get(reverse('documentos'))
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(self.contrato, resp.context['contratos_gerados'])
