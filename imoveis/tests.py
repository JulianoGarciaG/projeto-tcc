from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Group, Permission, User
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from .context_processors import LIMITE_NOTIFICACOES_TOPBAR, notificacoes_usuario
from .extenso import (
    dia_ordinal_extenso, meses_entre, meses_por_extenso, valor_por_extenso,
)
from .forms import (
    ContratoForm, DistratoForm, FiadorForm, LancamentoForm, LaudoVistoriaForm,
    NotificacaoForm, ReciboForm,
)
from .identidade import nome_arquivo
from .models import (
    Contrato, DocumentoContrato, Fiador, FotoItemVistoria, HistoricoStatusImovel,
    Imovel, Inquilino, ItemVistoria, Lancamento, LaudoVistoria, Notificacao,
    NotificacaoUsuario, Proprietario, Recibo, RenovacaoContrato, TestemunhaLaudo,
)


def limpar_arquivos_gerados():
    """Remove do storage os PDFs criados durante os testes (campos legados)."""
    for c in Contrato.objects.exclude(documento_gerado='').exclude(documento_gerado__isnull=True):
        c.documento_gerado.delete(save=False)
    for l in LaudoVistoria.objects.exclude(documento_gerado='').exclude(documento_gerado__isnull=True):
        l.documento_gerado.delete(save=False)
    for r in Recibo.objects.exclude(arquivo='').exclude(arquivo__isnull=True):
        r.arquivo.delete(save=False)
from .validators import (
    validate_cpf, validate_cnpj, validate_cpf_cnpj,
    validate_rg_cpf, validate_telefone,
)

CPF_VALIDO = '529.982.247-25'
CPF_VALIDO_2 = '111.444.777-35'
CPF_VALIDO_3 = '390.533.447-05'
CPF_VALIDO_4 = '148.745.392-20'
CPF_INVALIDO = '111.111.111-11'
CNPJ_VALIDO = '11.222.333/0001-81'
CNPJ_INVALIDO = '11.222.333/0001-99'

# PNG 1x1 válido (Pillow precisa de bytes de imagem reais, não conteúdo arbitrário)
PNG_1X1 = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0'
    b'\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82'
)


def _imagem_teste(nome='foto.png'):
    return SimpleUploadedFile(nome, PNG_1X1, content_type='image/png')


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
        self.assertIn('Rua A, 100, Fundos — Maringá', html)
        self.assertIn('01/06/2026 a 30/06/2026', html)

        recibo.periodo_fim = None
        html = render_to_string('documentos/recibo_pdf.html', {'recibo': recibo})
        self.assertNotIn('Período correspondente', html)


class ContratoPdfTests(TestCase):
    """Layout jurídico do PDF de contrato (preâmbulo + 21 cláusulas)."""

    def setUp(self):
        _, self.imovel, self.inquilino, self.contrato = criar_base()

    def render(self):
        """Renderiza com o mesmo contexto de views._gerar_pdf_contrato."""
        return render_to_string('documentos/contrato_pdf.html', {
            'contrato': self.contrato,
            'locador': settings.SHELTER_LOCADOR,
            'prazo_meses': meses_entre(self.contrato.data_inicio, self.contrato.data_fim),
        })

    def test_clausulas_presentes(self):
        html = self.render()
        for clausula in ('CLÁUSULA I', 'CLÁUSULA V', 'CLÁUSULA X', 'CLÁUSULA XI',
                         'CLÁUSULA XV', 'CLÁUSULA XIX', 'CLÁUSULA XXI'):
            self.assertIn(clausula, html)

    def test_locador_e_sempre_shelter(self):
        # O Proprietario cadastrado ("Maria Dona") NÃO aparece como locador.
        html = self.render()
        self.assertIn(settings.SHELTER_LOCADOR['razao_social'], html)
        self.assertIn(settings.SHELTER_LOCADOR['cnpj'], html)
        self.assertIn(settings.SHELTER_LOCADOR['representante_nome'], html)
        self.assertNotIn('Maria Dona', html)

    def test_titulo_por_finalidade(self):
        html = self.render()
        self.assertIn('CONTRATO DE LOCAÇÃO RESIDENCIAL', html)
        self.assertIn('RESIDENCIAIS', html)  # cláusula VI

        self.contrato.finalidade = 'comercial'
        html = self.render()
        self.assertIn('CONTRATO DE LOCAÇÃO COMERCIAL', html)
        self.assertIn('COMERCIAIS', html)

    def test_valores_por_extenso(self):
        html = self.render()
        # Valor: R$ 1.500,00 (mil e quinhentos reais)
        self.assertIn('1.500,00', html)
        self.assertIn('mil e quinhentos reais', html)
        # Prazo: 12 meses (01/01/2026 a 01/01/2027)
        self.assertIn('12 (DOZE MESES)', html)
        # Vencimento dia 10: "10º (décimo)"
        self.assertIn('10º (décimo)', html)
        # Datas por extenso (filtro date nativo pt-br)
        self.assertIn('1 de Janeiro de 2026', html)
        self.assertIn('1 de Janeiro de 2027', html)

    def test_pf_exibe_cpf_e_nao_cnpj(self):
        html = self.render()
        self.assertIn(self.inquilino.cpf, html)
        self.assertNotIn(self.inquilino.cnpj, html)

    def test_pj_exibe_cnpj(self):
        self.contrato.tipo_contrato = 'PJ'
        html = self.render()
        self.assertIn(self.inquilino.cnpj, html)
        self.assertIn('pessoa jurídica', html)

    def test_sem_fiador_omite_clausula_xx(self):
        html = self.render()
        self.assertNotIn('CLÁUSULA XX – FIADORES', html)
        self.assertNotIn('FIADOR(A)', html)

    def test_fiador_legado_fallback_rg_cpf(self):
        # Fiador criado antes da migration 0011: só rg_cpf preenchido.
        Fiador.objects.create(contrato=self.contrato, nome='Fiador Antigo',
                              rg_cpf=CPF_VALIDO_2)
        html = self.render()
        self.assertIn('CLÁUSULA XX – FIADORES', html)
        self.assertIn('FIADOR ANTIGO', html)
        self.assertIn(f'RG/CPF n.º {CPF_VALIDO_2}', html)

    def test_fiador_completo_exibe_qualificacao_e_conjuge(self):
        Fiador.objects.create(
            contrato=self.contrato, nome='Vanda Rolnik',
            qualificacao='brasileira, casada', rg_cpf=CPF_VALIDO_2,
            rg='5.932.125', cpf=CPF_VALIDO_2,
            endereco='Avenida Liberdade, 3566, São Paulo - SP',
            conjuge_nome='Francisco Marques', conjuge_rg='42.440.749',
            conjuge_cpf=CPF_VALIDO,
        )
        html = self.render()
        self.assertIn('VANDA ROLNIK', html)
        self.assertIn('RG n.º 5.932.125', html)
        self.assertIn(f'CPF/MF sob n.º {CPF_VALIDO_2}', html)
        self.assertIn('FRANCISCO MARQUES', html)
        self.assertIn('42.440.749', html)
        self.assertIn('Avenida Liberdade, 3566, São Paulo - SP', html)
        # Fallback legado não é usado quando rg/cpf discretos existem
        self.assertNotIn('RG/CPF n.º', html)

    def test_local_e_data_de_assinatura(self):
        self.contrato.local_assinatura = 'Poços de Caldas'
        self.contrato.data_assinatura = date(2026, 5, 28)
        html = self.render()
        self.assertIn('Poços de Caldas, 28 de Maio de 2026.', html)


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
        # Resumo em cards (redesign) — total e badge do estado do item
        self.assertIn('RESUMO DA VISTORIA', html)
        self.assertIn('TOTAL DE ITENS', html)
        self.assertIn('badge-bom', html)
        self.assertIn('Testemunha Um', html)
        # Assinaturas do redesign (sign-table com espaço de 80px do mockup)
        self.assertIn('sign-line', html)
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
            'tipo_contrato': 'PF', 'finalidade': 'residencial', 'status': 'ativo',
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

    def test_imovel_delete_protegido_nao_da_500(self):
        # self.contrato já vincula self.imovel (criado em setUp via criar_base())
        resp = self.client.post(reverse('imovel_delete', args=[self.imovel.pk]), follow=True)
        self.assertRedirects(resp, reverse('imovel_list'))
        self.assertTrue(Imovel.objects.filter(pk=self.imovel.pk).exists())
        mensagens = [str(m) for m in resp.context['messages']]
        self.assertTrue(any('não pode ser excluído' in m for m in mensagens))

    def test_imovel_delete_sem_vinculos_funciona(self):
        imovel_pk = self.imovel.pk
        self.contrato.delete()  # remove o vínculo PROTECT antes de excluir o imóvel
        resp = self.client.post(reverse('imovel_delete', args=[imovel_pk]))
        self.assertRedirects(resp, reverse('imovel_list'))
        self.assertFalse(Imovel.objects.filter(pk=imovel_pk).exists())

    def test_proprietario_delete_protegido_nao_da_500(self):
        resp = self.client.post(
            reverse('proprietario_delete', args=[self.imovel.proprietario.pk]), follow=True)
        self.assertRedirects(resp, reverse('proprietario_list'))
        self.assertTrue(Proprietario.objects.filter(pk=self.imovel.proprietario.pk).exists())
        mensagens = [str(m) for m in resp.context['messages']]
        self.assertTrue(any('não pode ser excluído' in m for m in mensagens))

    def test_proprietario_delete_sem_vinculos_funciona(self):
        outro = Proprietario.objects.create(nome='Outro Dono', cpf_cnpj=CPF_VALIDO_3)
        resp = self.client.post(reverse('proprietario_delete', args=[outro.pk]))
        self.assertRedirects(resp, reverse('proprietario_list'))
        self.assertFalse(Proprietario.objects.filter(pk=outro.pk).exists())

    def test_inquilino_delete_protegido_nao_da_500(self):
        resp = self.client.post(reverse('inquilino_delete', args=[self.inquilino.pk]), follow=True)
        self.assertRedirects(resp, reverse('inquilino_list'))
        self.assertTrue(Inquilino.objects.filter(pk=self.inquilino.pk).exists())
        mensagens = [str(m) for m in resp.context['messages']]
        self.assertTrue(any('não pode ser excluído' in m for m in mensagens))

    def test_inquilino_delete_sem_vinculos_funciona(self):
        outro = Inquilino.objects.create(nome='Outro Locatário', cpf=CPF_VALIDO_3)
        resp = self.client.post(reverse('inquilino_delete', args=[outro.pk]))
        self.assertRedirects(resp, reverse('inquilino_list'))
        self.assertFalse(Inquilino.objects.filter(pk=outro.pk).exists())

    def test_imovel_dependentes_cascata_conta_fotos_e_notificacoes(self):
        Notificacao.objects.create(
            imovel=self.imovel, tipo='prefeitura', titulo='Aviso',
            data_recebimento=date(2026, 7, 1),
        )
        deps = dict(self.imovel.dependentes_cascata)
        self.assertEqual(deps.get('notificação(ões)'), 1)

    def test_contrato_dependentes_cascata_conta_lancamentos_e_fiadores(self):
        Lancamento.objects.create(
            imovel=self.imovel, contrato=self.contrato, natureza='ganho', tipo='aluguel',
            valor=Decimal('1500.00'), data_vencimento=date(2026, 8, 10),
        )
        deps = dict(self.contrato.dependentes_cascata)
        self.assertEqual(deps.get('lançamento(s) financeiro(s)'), 1)

    def test_contrato_dependentes_cascata_vazio_quando_sem_vinculos(self):
        outro_inquilino = Inquilino.objects.create(nome='Outro Locatário 2', cpf=CPF_VALIDO_4)
        contrato_novo = Contrato.objects.create(
            imovel=self.imovel, inquilino=outro_inquilino, tipo_contrato='PF',
            data_inicio=date(2027, 1, 1), data_fim=date(2028, 1, 1),
            valor_mensal=Decimal('1500.00'), dia_vencimento=10,
        )
        self.assertEqual(contrato_novo.dependentes_cascata, [])

    def test_contratos_por_imovel_json(self):
        # L1 — endpoint retorna apenas os contratos do imóvel
        resp = self.client.get(reverse('contratos_por_imovel_json', args=[self.imovel.pk]))
        self.assertEqual(resp.status_code, 200)
        dados = resp.json()['contratos']
        self.assertEqual(len(dados), 1)
        self.assertEqual(dados[0]['id'], self.contrato.pk)
        self.assertIn('João Locatário', dados[0]['label'])
        # label agora é o rotulo_curto legível (código + contexto), não '#pk'
        self.assertEqual(dados[0]['label'], self.contrato.rotulo_curto)
        self.assertIn(self.contrato.codigo, dados[0]['label'])

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

    def tearDown(self):
        limpar_arquivos_gerados()

    def test_contrato_gerar_pdf_view(self):
        resp = self.client.get(reverse('contrato_gerar_pdf', args=[self.contrato.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
        self.assertTrue(resp.content.startswith(b'%PDF-'))
        disp = resp['Content-Disposition']
        self.assertIn(self.contrato.codigo, disp)
        self.contrato.refresh_from_db()
        self.assertTrue(self.contrato.documento_gerado)
        # segunda geração sobrescreve o arquivo, sem manter histórico
        nome_v1 = self.contrato.documento_gerado.name
        resp2 = self.client.get(reverse('contrato_gerar_pdf', args=[self.contrato.pk]))
        self.assertEqual(resp2.status_code, 200)
        self.contrato.refresh_from_db()
        self.assertTrue(default_storage.exists(self.contrato.documento_gerado.name))
        with self.contrato.documento_gerado.open('rb') as f:
            self.assertEqual(f.read(), resp2.content)

    def test_laudo_gerar_pdf_view(self):
        laudo = LaudoVistoria.objects.create(
            imovel=self.imovel, contrato=self.contrato, tipo='saida',
            data=date(2026, 7, 1), responsavel='Carlos',
        )
        resp = self.client.get(reverse('laudo_gerar_pdf', args=[laudo.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.content.startswith(b'%PDF-'))
        disp = resp['Content-Disposition']
        self.assertIn(laudo.codigo, disp)
        laudo.refresh_from_db()
        self.assertTrue(laudo.documento_gerado)
        resp2 = self.client.get(reverse('laudo_gerar_pdf', args=[laudo.pk]))
        self.assertEqual(resp2.status_code, 200)
        laudo.refresh_from_db()
        self.assertTrue(default_storage.exists(laudo.documento_gerado.name))
        with laudo.documento_gerado.open('rb') as f:
            self.assertEqual(f.read(), resp2.content)

    def test_recibo_gerar_pdf_view(self):
        recibo = Recibo.objects.create(imovel=self.imovel, contrato=self.contrato,
                                       quantia=Decimal('1500.00'))
        resp = self.client.get(reverse('recibo_gerar_pdf', args=[recibo.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
        self.assertTrue(resp.content.startswith(b'%PDF-'))
        disp = resp['Content-Disposition']
        self.assertIn(recibo.codigo, disp)
        recibo.refresh_from_db()
        self.assertTrue(recibo.arquivo)
        resp2 = self.client.get(reverse('recibo_gerar_pdf', args=[recibo.pk]))
        self.assertEqual(resp2.status_code, 200)
        recibo.refresh_from_db()
        self.assertTrue(default_storage.exists(recibo.arquivo.name))
        with recibo.arquivo.open('rb') as f:
            self.assertEqual(f.read(), resp2.content)

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
        # Regressão: contrato sem PDF gerado (documento_gerado NULL) não pode
        # aparecer no GED.
        self.assertIsNone(self.contrato.documento_gerado.name)
        resp = self.client.get(reverse('documentos'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['contratos_gerados'].count(), 0)


class FotoItemVistoriaTests(TestCase):
    """Fotos por item do checklist de vistoria (0..N por ItemVistoria)."""

    def setUp(self):
        self.user = User.objects.create_user('tester', password='x')
        self.client.force_login(self.user)
        _, self.imovel, self.inquilino, self.contrato = criar_base()

    def tearDown(self):
        for foto in FotoItemVistoria.objects.all():
            foto.imagem.delete(save=False)
        limpar_arquivos_gerados()

    def _payload_item_unico(self, estado='bom'):
        from .views import _initial_itens_catalogo
        itens = _initial_itens_catalogo()
        n = len(itens)
        data = {
            'imovel': str(self.imovel.pk), 'contrato': str(self.contrato.pk),
            'tipo': 'entrada', 'data': '2026-07-05', 'responsavel': 'Vistoriador Teste',
            'local_assinatura': 'Maringá', 'data_assinatura': '2026-07-05',
            'itens-TOTAL_FORMS': str(n), 'itens-INITIAL_FORMS': '0',
            'itens-MIN_NUM_FORMS': '0', 'itens-MAX_NUM_FORMS': '1000',
            'testemunhas-TOTAL_FORMS': '2', 'testemunhas-INITIAL_FORMS': '0',
            'testemunhas-MIN_NUM_FORMS': '0', 'testemunhas-MAX_NUM_FORMS': '1000',
            'testemunhas-0-nome': '', 'testemunhas-0-cpf': '',
            'testemunhas-1-nome': '', 'testemunhas-1-cpf': '',
        }
        for i, item in enumerate(itens):
            data[f'itens-{i}-comodo'] = item['comodo']
            data[f'itens-{i}-item'] = item['item']
            data[f'itens-{i}-ordem'] = str(item['ordem'])
            data[f'itens-{i}-estado'] = estado if i == 0 else ''
            data[f'itens-{i}-observacao'] = ''
        return data

    def test_criacao_com_foto_e_estado_preenchido(self):
        data = self._payload_item_unico(estado='bom')
        data['itens-0-fotos'] = _imagem_teste()
        resp = self.client.post(reverse('laudo_create'), data)
        laudo = LaudoVistoria.objects.latest('criado_em')
        self.assertRedirects(resp, reverse('laudo_detail', args=[laudo.pk]))
        item = laudo.itens.get()
        self.assertEqual(FotoItemVistoria.objects.filter(item=item).count(), 1)
        self.assertTrue(item.fotos.first().imagem)

    def test_multiplas_fotos_na_mesma_linha(self):
        data = self._payload_item_unico(estado='bom')
        data['itens-0-fotos'] = [_imagem_teste('a.png'), _imagem_teste('b.png')]
        resp = self.client.post(reverse('laudo_create'), data)
        laudo = LaudoVistoria.objects.latest('criado_em')
        self.assertRedirects(resp, reverse('laudo_detail', args=[laudo.pk]))
        item = laudo.itens.get()
        self.assertEqual(FotoItemVistoria.objects.filter(item=item).count(), 2)

    def test_foto_sem_estado_nao_salva_silenciosamente(self):
        data = self._payload_item_unico(estado='')
        data['itens-0-fotos'] = _imagem_teste()
        antes = LaudoVistoria.objects.count()
        resp = self.client.post(reverse('laudo_create'), data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(LaudoVistoria.objects.count(), antes)
        self.assertEqual(ItemVistoria.objects.count(), 0)
        self.assertEqual(FotoItemVistoria.objects.count(), 0)

    def test_edicao_adiciona_foto_a_item_existente(self):
        data = self._payload_item_unico(estado='bom')
        resp = self.client.post(reverse('laudo_create'), data)
        laudo = LaudoVistoria.objects.latest('criado_em')
        self.assertRedirects(resp, reverse('laudo_detail', args=[laudo.pk]))
        item = laudo.itens.get()

        edit_data = {
            'imovel': str(self.imovel.pk), 'contrato': str(self.contrato.pk),
            'tipo': 'entrada', 'data': '2026-07-05', 'responsavel': 'Vistoriador Teste',
            'local_assinatura': 'Maringá', 'data_assinatura': '2026-07-05',
            'itens-TOTAL_FORMS': '1', 'itens-INITIAL_FORMS': '1',
            'itens-MIN_NUM_FORMS': '0', 'itens-MAX_NUM_FORMS': '1000',
            'itens-0-id': str(item.pk),
            'itens-0-comodo': item.comodo, 'itens-0-item': item.item,
            'itens-0-ordem': str(item.ordem), 'itens-0-estado': 'bom',
            'itens-0-observacao': '', 'itens-0-fotos': _imagem_teste('nova.png'),
            'testemunhas-TOTAL_FORMS': '2', 'testemunhas-INITIAL_FORMS': '0',
            'testemunhas-MIN_NUM_FORMS': '0', 'testemunhas-MAX_NUM_FORMS': '1000',
            'testemunhas-0-nome': '', 'testemunhas-0-cpf': '',
            'testemunhas-1-nome': '', 'testemunhas-1-cpf': '',
        }
        resp = self.client.post(reverse('laudo_edit', args=[laudo.pk]), edit_data)
        self.assertRedirects(resp, reverse('laudo_detail', args=[laudo.pk]))
        self.assertEqual(FotoItemVistoria.objects.filter(item=item).count(), 1)
        self.assertEqual(FotoItemVistoria.objects.first().item_id, item.pk)

    def test_detalhe_exibe_fotos_agrupadas_por_item(self):
        laudo = LaudoVistoria.objects.create(
            imovel=self.imovel, contrato=self.contrato, tipo='entrada',
            data=date(2026, 7, 1), responsavel='Carlos',
        )
        item = ItemVistoria.objects.create(laudo=laudo, comodo='Sala', item='Piso', estado='bom', ordem=0)
        FotoItemVistoria.objects.create(item=item, imagem=_imagem_teste('a.png'))
        FotoItemVistoria.objects.create(item=item, imagem=_imagem_teste('b.png'))

        resp = self.client.get(reverse('laudo_detail', args=[laudo.pk]))
        self.assertEqual(resp.status_code, 200)
        grupos = resp.context['grupos']
        item_no_contexto = grupos[0]['itens'][0]
        self.assertEqual(item_no_contexto.fotos.count(), 2)
        self.assertContains(resp, 'Foto de Piso', count=2)

    def test_regressao_pdf_nao_contem_fotos(self):
        # Confirma que _gerar_pdf_laudo não foi alterado para incluir fotos
        # no contexto do PDF (RF4) — se este teste falhar, sinaliza que o
        # módulo 03-views-laudo passou a expor fotos no PDF.
        import inspect
        from . import views
        fonte = inspect.getsource(views._gerar_pdf_laudo)
        self.assertNotIn('foto', fonte.lower())

        laudo = LaudoVistoria.objects.create(
            imovel=self.imovel, contrato=self.contrato, tipo='entrada',
            data=date(2026, 7, 1), responsavel='Carlos',
        )
        item = ItemVistoria.objects.create(laudo=laudo, comodo='Sala', item='Piso', estado='bom', ordem=0)
        FotoItemVistoria.objects.create(item=item, imagem=_imagem_teste())

        resp = self.client.get(reverse('laudo_gerar_pdf', args=[laudo.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.content.startswith(b'%PDF-'))

    def test_regressao_ged_nao_lista_fotos_de_item(self):
        laudo = LaudoVistoria.objects.create(
            imovel=self.imovel, contrato=self.contrato, tipo='entrada',
            data=date(2026, 7, 1), responsavel='Carlos',
        )
        item = ItemVistoria.objects.create(laudo=laudo, comodo='Sala', item='Piso', estado='bom', ordem=0)
        FotoItemVistoria.objects.create(item=item, imagem=_imagem_teste())

        resp = self.client.get(reverse('documentos'))
        self.assertEqual(resp.status_code, 200)
        chaves_esperadas = {
            'contratos_gerados', 'laudos', 'laudos_gerados', 'comprovantes',
            'contratos_recibo', 'contratos_anual', 'recibos',
        }
        chaves_contexto = set(resp.context.keys()) & (chaves_esperadas | {
            k for k in resp.context.keys() if 'foto' in k.lower()
        })
        self.assertEqual(chaves_contexto, chaves_esperadas)
        for chave in chaves_esperadas:
            self.assertIn(chave, resp.context)


class GeracaoPdfSobrescreveTests(TestCase):
    """Geração de PDF sobrescreve o campo legado, sem manter histórico."""

    def setUp(self):
        self.user = User.objects.create_user('tester', password='x')
        self.client.force_login(self.user)
        _, self.imovel, self.inquilino, self.contrato = criar_base()

    def tearDown(self):
        limpar_arquivos_gerados()

    def test_gerar_pdf_sobrescreve_campo_legado_sem_historico(self):
        resp = self.client.get(reverse('contrato_gerar_pdf', args=[self.contrato.pk]))
        self.contrato.refresh_from_db()
        self.assertTrue(default_storage.exists(self.contrato.documento_gerado.name))
        with self.contrato.documento_gerado.open('rb') as f:
            self.assertEqual(f.read(), resp.content)

        _, arquivos_v1 = default_storage.listdir('contratos/gerados')
        resp2 = self.client.get(reverse('contrato_gerar_pdf', args=[self.contrato.pk]))
        self.contrato.refresh_from_db()
        _, arquivos_v2 = default_storage.listdir('contratos/gerados')
        # mesma quantidade de arquivos: a 2a geração substituiu, não acumulou
        self.assertEqual(len(arquivos_v2), len(arquivos_v1))
        with self.contrato.documento_gerado.open('rb') as f:
            self.assertEqual(f.read(), resp2.content)

    def test_laudo_e_recibo_tambem_sobrescrevem(self):
        laudo = LaudoVistoria.objects.create(
            imovel=self.imovel, contrato=self.contrato, tipo='entrada',
            data=date(2026, 7, 1), responsavel='Carlos',
        )
        self.client.get(reverse('laudo_gerar_pdf', args=[laudo.pk]))
        _, arquivos_v1 = default_storage.listdir('laudos/gerados')
        self.client.get(reverse('laudo_gerar_pdf', args=[laudo.pk]))
        _, arquivos_v2 = default_storage.listdir('laudos/gerados')
        self.assertEqual(len(arquivos_v2), len(arquivos_v1))

        recibo = Recibo.objects.create(imovel=self.imovel, contrato=self.contrato,
                                       quantia=Decimal('100.00'))
        self.client.get(reverse('recibo_gerar_pdf', args=[recibo.pk]))
        _, arquivos_v1_recibo = default_storage.listdir('recibos')
        self.client.get(reverse('recibo_gerar_pdf', args=[recibo.pk]))
        _, arquivos_v2_recibo = default_storage.listdir('recibos')
        self.assertEqual(len(arquivos_v2_recibo), len(arquivos_v1_recibo))

    def test_ged_lista_documento_vigente_unico(self):
        self.client.get(reverse('contrato_gerar_pdf', args=[self.contrato.pk]))
        self.client.get(reverse('contrato_gerar_pdf', args=[self.contrato.pk]))
        resp = self.client.get(reverse('documentos'))
        self.assertEqual(resp.status_code, 200)
        docs = list(resp.context['contratos_gerados'])
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].pk, self.contrato.pk)


class ValidateRgCpfTests(TestCase):
    """Módulo 01 — validate_rg_cpf (Fiador.rg_cpf)."""

    def test_cpf_valido_aceito(self):
        validate_rg_cpf(CPF_VALIDO)  # 11 dígitos → validado como CPF

    def test_cpf_11_digitos_invalido_rejeitado(self):
        with self.assertRaises(ValidationError):
            validate_rg_cpf('529.982.247-26')  # DV errado

    def test_rg_valido_aceito(self):
        validate_rg_cpf('MG-12.345.678')  # não tem 11 dígitos → validado como RG

    def test_rg_com_caractere_invalido_rejeitado(self):
        with self.assertRaises(ValidationError):
            validate_rg_cpf('12.345.678/9')  # "/" não é aceito no RG


class ValidateTelefoneTests(TestCase):
    """Módulo 02 — validate_telefone (Proprietario/Inquilino.telefone)."""

    def test_fixo_10_digitos_com_mascara(self):
        validate_telefone('(44) 3222-1111')

    def test_celular_11_digitos_sem_mascara(self):
        validate_telefone('44999998888')

    def test_telefone_curto_rejeitado(self):
        with self.assertRaises(ValidationError):
            validate_telefone('123')

    def test_proprietario_telefone_invalido_bloqueado(self):
        proprietario = Proprietario(nome='Dona', cpf_cnpj=CPF_VALIDO_2, telefone='99')
        with self.assertRaises(ValidationError):
            proprietario.full_clean()


class DiaVencimentoTests(TestCase):
    """Módulo 03 — faixa 1..31 em Contrato.dia_vencimento."""

    def setUp(self):
        _, _, _, self.contrato = criar_base()

    def test_dia_zero_rejeitado(self):
        self.contrato.dia_vencimento = 0
        with self.assertRaises(ValidationError):
            self.contrato.full_clean()

    def test_dia_32_rejeitado(self):
        self.contrato.dia_vencimento = 32
        with self.assertRaises(ValidationError):
            self.contrato.full_clean()

    def test_dias_validos_aceitos(self):
        for dia in (1, 15, 31):
            self.contrato.dia_vencimento = dia
            self.contrato.full_clean()  # não deve levantar


class DashboardFiltroTests(TestCase):
    """Módulo 04 — filtro de período do Dashboard em dd/mm/aaaa."""

    def setUp(self):
        self.user = User.objects.create_user('tester', password='x')
        self.user.user_permissions.add(
            Permission.objects.get(codename='pode_acessar_financeiro'))
        self.client.force_login(self.user)
        _, self.imovel, self.inquilino, self.contrato = criar_base()
        self.lanc_junho = Lancamento.objects.create(
            imovel=self.imovel, contrato=self.contrato, natureza='ganho', tipo='aluguel',
            status='efetivado', valor=Decimal('1500.00'), data_vencimento=date(2026, 6, 15),
        )
        self.lanc_agosto = Lancamento.objects.create(
            imovel=self.imovel, contrato=self.contrato, natureza='ganho', tipo='aluguel',
            status='pendente', valor=Decimal('1500.00'), data_vencimento=date(2026, 8, 15),
        )

    def test_filtro_datas_ddmmyyyy(self):
        resp = self.client.get(reverse('lancamento_list'),
                               {'data_inicio': '01/06/2026', 'data_fim': '30/06/2026'})
        self.assertEqual(resp.status_code, 200)
        meses = resp.context['meses_labels']
        self.assertIn('Jun/2026', meses)

    def test_sem_filtro_lista_todos(self):
        resp = self.client.get(reverse('lancamento_list'))
        self.assertEqual(resp.status_code, 200)
        lancamentos = list(resp.context['lancamentos'])
        self.assertIn(self.lanc_junho, lancamentos)
        self.assertIn(self.lanc_agosto, lancamentos)

    def test_campos_usam_flatpickr(self):
        resp = self.client.get(reverse('lancamento_list'))
        form = resp.context['dash_filtro_form']
        self.assertEqual(form.fields['data_inicio'].widget.attrs.get('data-flatpickr'), 'true')
        self.assertEqual(form.fields['data_fim'].widget.attrs.get('data-flatpickr'), 'true')


class ContratoDocumentoTests(TestCase):
    """Módulos 07/08 — documentos GED do contrato anexados pelo detail."""

    def setUp(self):
        self.user = User.objects.create_user('tester', password='x')
        self.client.force_login(self.user)
        _, self.imovel, self.inquilino, self.contrato = criar_base()

    def test_form_nao_expoe_campos_de_documento(self):
        form = ContratoForm()
        for campo in ('comprovante_renda', 'contrato_social',
                      'recibo_chaves', 'comprovante_anual'):
            self.assertNotIn(campo, ContratoForm.Meta.fields)
            self.assertNotIn(campo, form.fields)

    def test_anexar_documento_campo_valido(self):
        arquivo = SimpleUploadedFile('recibo_chaves.pdf', b'%PDF-1.4 fake', 'application/pdf')
        resp = self.client.post(
            reverse('contrato_anexar_documento', args=[self.contrato.pk, 'recibo_chaves']),
            {'arquivo': arquivo})
        self.assertRedirects(resp, reverse('contrato_detail', args=[self.contrato.pk]))
        self.contrato.refresh_from_db()
        self.assertTrue(self.contrato.recibo_chaves)
        self.contrato.recibo_chaves.delete(save=False)

    def test_anexar_documento_campo_fora_da_whitelist(self):
        arquivo = SimpleUploadedFile('x.pdf', b'%PDF-1.4 fake', 'application/pdf')
        resp = self.client.post(
            reverse('contrato_anexar_documento', args=[self.contrato.pk, 'documento_gerado']),
            {'arquivo': arquivo})
        self.assertEqual(resp.status_code, 404)
        self.contrato.refresh_from_db()
        self.assertFalse(self.contrato.documento_gerado)

    def test_anexar_sem_arquivo_nao_salva(self):
        resp = self.client.post(
            reverse('contrato_anexar_documento', args=[self.contrato.pk, 'recibo_chaves']), {})
        self.assertRedirects(resp, reverse('contrato_detail', args=[self.contrato.pk]))
        self.contrato.refresh_from_db()
        self.assertFalse(self.contrato.recibo_chaves)

    def test_documentos_pessoais_upload_multiplo(self):
        a = SimpleUploadedFile('rg.pdf', b'%PDF-1.4 a', 'application/pdf')
        b = SimpleUploadedFile('cpf.jpg', PNG_1X1, 'image/jpeg')
        resp = self.client.post(
            reverse('contrato_documento_pessoal_upload', args=[self.contrato.pk]),
            {'arquivos': [a, b]})
        self.assertRedirects(resp, reverse('contrato_detail', args=[self.contrato.pk]))
        docs = self.contrato.documentos_pessoais.all()
        self.assertEqual(docs.count(), 2)
        self.assertEqual({d.nome_original for d in docs}, {'rg.pdf', 'cpf.jpg'})
        for d in docs:
            d.arquivo.delete(save=False)

    def test_documentos_pessoais_upload_sem_arquivo(self):
        resp = self.client.post(
            reverse('contrato_documento_pessoal_upload', args=[self.contrato.pk]), {})
        self.assertRedirects(resp, reverse('contrato_detail', args=[self.contrato.pk]))
        self.assertEqual(self.contrato.documentos_pessoais.count(), 0)

    def test_documento_pessoal_delete_individual(self):
        a = SimpleUploadedFile('a.pdf', b'%PDF-1.4 a', 'application/pdf')
        b = SimpleUploadedFile('b.pdf', b'%PDF-1.4 b', 'application/pdf')
        self.client.post(
            reverse('contrato_documento_pessoal_upload', args=[self.contrato.pk]),
            {'arquivos': [a, b]})
        alvo, restante = self.contrato.documentos_pessoais.all()
        resp = self.client.post(
            reverse('contrato_documento_pessoal_delete', args=[self.contrato.pk, alvo.pk]))
        self.assertRedirects(resp, reverse('contrato_detail', args=[self.contrato.pk]))
        docs = self.contrato.documentos_pessoais.all()
        self.assertEqual([d.pk for d in docs], [restante.pk])
        restante.arquivo.delete(save=False)

    def test_documento_pessoal_delete_de_outro_contrato_404(self):
        outro = Contrato.objects.create(
            imovel=self.imovel, inquilino=self.inquilino, tipo_contrato='PF',
            data_inicio=date(2025, 1, 1), data_fim=date(2026, 1, 1),
            valor_mensal=Decimal('900.00'), dia_vencimento=5,
        )
        doc = DocumentoContrato.objects.create(
            contrato=outro, arquivo=SimpleUploadedFile('x.pdf', b'%PDF-1.4', 'application/pdf'),
            nome_original='x.pdf')
        resp = self.client.post(
            reverse('contrato_documento_pessoal_delete', args=[self.contrato.pk, doc.pk]))
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(DocumentoContrato.objects.filter(pk=doc.pk).exists())
        doc.arquivo.delete(save=False)


class ExtensoTests(TestCase):
    """Módulo 01 (contrato jurídico) — utilitários puros de imoveis/extenso.py."""

    def test_valor_por_extenso_redondo(self):
        self.assertEqual(valor_por_extenso(Decimal('1500.00')), 'mil e quinhentos reais')

    def test_valor_por_extenso_com_centavos(self):
        self.assertEqual(
            valor_por_extenso(Decimal('1234.56')),
            'mil, duzentos e trinta e quatro reais e cinquenta e seis centavos')

    def test_valor_por_extenso_none_e_vazio(self):
        self.assertEqual(valor_por_extenso(None), '')
        self.assertEqual(valor_por_extenso(''), '')

    def test_meses_entre_ano_cheio(self):
        self.assertEqual(meses_entre(date(2026, 1, 1), date(2027, 1, 1)), 12)

    def test_meses_entre_ajuste_de_dia(self):
        self.assertEqual(meses_entre(date(2026, 1, 15), date(2027, 1, 10)), 11)

    def test_meses_entre_30_meses(self):
        self.assertEqual(meses_entre(date(2026, 6, 1), date(2028, 12, 1)), 30)

    def test_meses_por_extenso_singular_e_plural(self):
        self.assertEqual(meses_por_extenso(1), 'um mês')
        self.assertEqual(meses_por_extenso(12), 'doze meses')
        self.assertEqual(meses_por_extenso(30), 'trinta meses')

    def test_dia_ordinal_extenso(self):
        self.assertEqual(dia_ordinal_extenso(1), 'primeiro')
        self.assertEqual(dia_ordinal_extenso(10), 'décimo')
        self.assertEqual(dia_ordinal_extenso(31), 'trigésimo primeiro')

    def test_dia_ordinal_extenso_none_nao_levanta(self):
        self.assertEqual(dia_ordinal_extenso(None), '')


class ContratoCamposNovosTests(TestCase):
    """Módulo 03 (contrato jurídico) — finalidade/local_assinatura/data_assinatura."""

    def setUp(self):
        _, self.imovel, self.inquilino, self.contrato = criar_base()

    def test_finalidade_default_residencial(self):
        # criar_base() não define finalidade — assume o default
        self.assertEqual(self.contrato.finalidade, 'residencial')
        self.contrato.full_clean()  # não deve levantar

    def test_finalidade_comercial_aceita(self):
        self.contrato.finalidade = 'comercial'
        self.contrato.full_clean()
        self.contrato.save()
        self.contrato.refresh_from_db()
        self.assertEqual(self.contrato.get_finalidade_display(), 'Comercial')

    def test_form_aceita_assinatura_ddmmyyyy(self):
        form = ContratoForm(data={
            'imovel': str(self.imovel.pk), 'inquilino': str(self.inquilino.pk),
            'tipo_contrato': 'PF', 'finalidade': 'comercial', 'status': 'ativo',
            'data_inicio': '01/06/2026', 'data_fim': '01/12/2028',
            'valor_mensal': '890.00', 'dia_vencimento': '1',
            'local_assinatura': 'Poços de Caldas', 'data_assinatura': '28/05/2026',
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['data_assinatura'], date(2026, 5, 28))
        self.assertEqual(form.cleaned_data['local_assinatura'], 'Poços de Caldas')

    def test_data_assinatura_usa_flatpickr(self):
        form = ContratoForm()
        self.assertEqual(
            form.fields['data_assinatura'].widget.attrs.get('data-flatpickr'), 'true')


class FiadorCamposNovosTests(TestCase):
    """Módulo 04 (contrato jurídico) — RG/CPF discretos, endereço e cônjuge."""

    def setUp(self):
        _, _, _, self.contrato = criar_base()

    def test_fiador_completo_valido(self):
        fiador = Fiador(
            contrato=self.contrato, nome='Vanda Rolnik',
            qualificacao='brasileira, casada', rg_cpf=CPF_VALIDO_2,
            rg='5.932.125', cpf=CPF_VALIDO_2,
            endereco='Avenida Liberdade, 3566, São Paulo - SP',
            conjuge_nome='Francisco Marques', conjuge_rg='42.440.749',
            conjuge_cpf=CPF_VALIDO,
        )
        fiador.full_clean()  # não deve levantar

    def test_fiador_legado_somente_rg_cpf_valido(self):
        fiador = Fiador(contrato=self.contrato, nome='Fiador Antigo', rg_cpf=CPF_VALIDO_2)
        fiador.full_clean()  # campos novos vazios continuam válidos

    def test_cpf_invalido_rejeitado(self):
        fiador = Fiador(contrato=self.contrato, nome='Zé', rg_cpf=CPF_VALIDO_2,
                        cpf=CPF_INVALIDO)
        with self.assertRaises(ValidationError):
            fiador.full_clean()

    def test_conjuge_cpf_invalido_rejeitado(self):
        fiador = Fiador(contrato=self.contrato, nome='Zé', rg_cpf=CPF_VALIDO_2,
                        conjuge_cpf=CPF_INVALIDO)
        with self.assertRaises(ValidationError):
            fiador.full_clean()

    def test_form_aceita_campos_novos(self):
        form = FiadorForm(data={
            'nome': 'Vanda Rolnik', 'qualificacao': 'brasileira, casada',
            'rg_cpf': CPF_VALIDO_2, 'rg': '5.932.125', 'cpf': CPF_VALIDO_2,
            'endereco': 'Avenida Liberdade, 3566, São Paulo - SP',
            'conjuge_nome': 'Francisco Marques', 'conjuge_rg': '42.440.749',
            'conjuge_cpf': CPF_VALIDO, 'garantia': 'imóvel próprio',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_formset_no_create_aceita_campos_novos(self):
        # FiadorFormSet (extra=1) continua funcionando via contrato_create
        user = User.objects.create_user('tester', password='x')
        self.client.force_login(user)
        resp = self.client.post(reverse('contrato_create'), {
            'imovel': str(self.contrato.imovel.pk),
            'inquilino': str(self.contrato.inquilino.pk),
            'tipo_contrato': 'PF', 'finalidade': 'residencial', 'status': 'ativo',
            'data_inicio': '01/08/2026', 'data_fim': '01/08/2027',
            'valor_mensal': '2000.00', 'dia_vencimento': '10',
            'fiadores-TOTAL_FORMS': '1', 'fiadores-INITIAL_FORMS': '0',
            'fiadores-MIN_NUM_FORMS': '0', 'fiadores-MAX_NUM_FORMS': '1000',
            'fiadores-0-nome': 'Vanda Rolnik', 'fiadores-0-rg_cpf': CPF_VALIDO_2,
            'fiadores-0-rg': '5.932.125', 'fiadores-0-cpf': CPF_VALIDO_2,
            'fiadores-0-endereco': 'Avenida Liberdade, 3566',
            'fiadores-0-conjuge_nome': 'Francisco Marques',
            'fiadores-0-conjuge_rg': '42.440.749',
            'fiadores-0-conjuge_cpf': CPF_VALIDO,
        })
        contrato = Contrato.objects.latest('criado_em')
        self.assertRedirects(resp, reverse('contrato_detail', args=[contrato.pk]))
        fiador = contrato.fiadores.get()
        self.assertEqual(fiador.cpf, CPF_VALIDO_2)
        self.assertEqual(fiador.conjuge_nome, 'Francisco Marques')


class ContratoReajusteTests(TestCase):
    """Indicador de atenção (fim de vigência / aniversário) e reajuste do valor de cobrança."""

    def setUp(self):
        self.user = User.objects.create_user('tester', password='x')
        self.client.force_login(self.user)
        _, self.imovel, self.inquilino, self.contrato = criar_base()

    def test_precisa_atencao_false_fora_da_janela(self):
        # criar_base(): data_inicio=2026-01-01, data_fim=2027-01-01 — nem
        # aniversário nem fim de vigência na data corrente dos testes.
        self.assertFalse(self.contrato.precisa_atencao)

    def test_precisa_atencao_true_perto_do_fim_de_vigencia(self):
        hoje = date.today()
        self.contrato.data_inicio = hoje - timedelta(days=365)
        self.contrato.data_fim = hoje + timedelta(days=10)
        self.contrato.save()
        self.assertTrue(self.contrato.precisa_atencao)

    def test_precisa_atencao_false_fim_de_vigencia_distante(self):
        hoje = date.today()
        # 60 dias antes do fim de vigência está fora da janela (que abre em -30).
        self.contrato.data_inicio = hoje - timedelta(days=305)
        self.contrato.data_fim = hoje + timedelta(days=60)
        self.contrato.save()
        self.assertFalse(self.contrato.precisa_atencao)

    def test_precisa_atencao_true_no_limite_30_dias_antes(self):
        # Extremo inclusivo: exatamente 30 dias antes do fim de vigência já dispara.
        hoje = date.today()
        self.contrato.data_inicio = hoje - timedelta(days=335)
        self.contrato.data_fim = hoje + timedelta(days=30)
        self.contrato.save()
        self.assertTrue(self.contrato.precisa_atencao)

    def test_precisa_atencao_true_ate_7_dias_depois_do_vencimento(self):
        # Contrato ativo com data_fim já vencida há 7 dias ainda exibe aviso.
        hoje = date.today()
        self.contrato.data_inicio = hoje - timedelta(days=372)
        self.contrato.data_fim = hoje - timedelta(days=7)
        self.contrato.save()
        self.assertTrue(self.contrato.precisa_atencao)

    def test_precisa_atencao_false_apos_8_dias_do_vencimento(self):
        # 8 dias depois do vencimento já passou da janela (fecha em +7).
        hoje = date.today()
        self.contrato.data_inicio = hoje - timedelta(days=190)
        self.contrato.data_fim = hoje - timedelta(days=8)
        self.contrato.save()
        self.assertFalse(self.contrato.precisa_atencao)

    def test_precisa_atencao_true_no_aniversario(self):
        hoje = date.today()
        self.contrato.data_inicio = date(hoje.year - 1, hoje.month, hoje.day)
        self.contrato.data_fim = date(hoje.year + 5, hoje.month, hoje.day)
        self.contrato.save()
        self.assertTrue(self.contrato.precisa_atencao)

    def test_precisa_atencao_true_no_aniversario_dentro_da_janela(self):
        # Aniversário 10 dias à frente (âncora de ciclo de índice), fim de vigência longe.
        hoje = date.today()
        aniversario = hoje + timedelta(days=10)
        self.contrato.data_inicio = date(hoje.year - 1, aniversario.month, aniversario.day)
        self.contrato.data_fim = date(hoje.year + 5, aniversario.month, aniversario.day)
        self.contrato.save()
        self.assertTrue(self.contrato.precisa_atencao)

    def test_precisa_atencao_false_aniversario_e_fim_de_vigencia_longe(self):
        # Ambas as âncoras fora da janela → sem aviso.
        hoje = date.today()
        distante = hoje + timedelta(days=120)
        self.contrato.data_inicio = date(hoje.year - 2, distante.month, distante.day)
        self.contrato.data_fim = hoje + timedelta(days=120)
        self.contrato.save()
        self.assertFalse(self.contrato.precisa_atencao)

    def test_renovacao_nao_desloca_referencia(self):
        # Renovação recente NÃO puxa a data de referência: as âncoras continuam sendo
        # data_inicio/data_fim do contrato original, ambas longe da janela → sem aviso.
        hoje = date.today()
        distante = hoje + timedelta(days=120)
        self.contrato.data_inicio = date(hoje.year - 2, distante.month, distante.day)
        self.contrato.data_fim = hoje + timedelta(days=120)
        self.contrato.save()
        RenovacaoContrato.objects.create(
            contrato=self.contrato, tipo='12_30', data_renovacao=hoje,
        )
        self.contrato.refresh_from_db()
        self.assertFalse(self.contrato.precisa_atencao)

    def test_precisa_atencao_false_quando_inativo(self):
        hoje = date.today()
        self.contrato.data_fim = hoje + timedelta(days=5)
        self.contrato.status = 'encerrado'
        self.contrato.save()
        self.assertFalse(self.contrato.precisa_atencao)

    def test_valor_cobranca_usa_valor_mensal_sem_reajuste(self):
        self.assertIsNone(self.contrato.valor_vigente)
        self.assertEqual(self.contrato.valor_cobranca, self.contrato.valor_mensal)

    def test_valor_cobranca_usa_valor_vigente_apos_reajuste(self):
        self.contrato.valor_vigente = Decimal('1800.00')
        self.assertEqual(self.contrato.valor_cobranca, Decimal('1800.00'))

    def test_view_bloqueia_reajuste_fora_da_janela(self):
        resp = self.client.get(reverse('contrato_reajuste', args=[self.contrato.pk]))
        self.assertRedirects(resp, reverse('contrato_detail', args=[self.contrato.pk]))
        self.contrato.refresh_from_db()
        self.assertIsNone(self.contrato.valor_vigente)

    def test_view_permite_reajuste_dentro_da_janela(self):
        hoje = date.today()
        self.contrato.data_fim = hoje + timedelta(days=5)
        self.contrato.save()
        resp = self.client.post(reverse('contrato_reajuste', args=[self.contrato.pk]), {
            'valor_vigente': '1800,00',
        })
        self.assertRedirects(resp, reverse('contrato_detail', args=[self.contrato.pk]))
        self.contrato.refresh_from_db()
        self.assertEqual(self.contrato.valor_vigente, Decimal('1800.00'))
        # valor contratual original nunca muda
        self.assertEqual(self.contrato.valor_mensal, Decimal('1500.00'))

    def test_view_permite_reajuste_contrato_vencido(self):
        # Contrato ativo com data_fim vencida (dentro da janela de +7) permite ajuste.
        hoje = date.today()
        self.contrato.data_inicio = hoje - timedelta(days=370)
        self.contrato.data_fim = hoje - timedelta(days=5)
        self.contrato.save()
        resp = self.client.post(reverse('contrato_reajuste', args=[self.contrato.pk]), {
            'valor_vigente': '1800,00',
        })
        self.assertRedirects(resp, reverse('contrato_detail', args=[self.contrato.pk]))
        self.contrato.refresh_from_db()
        self.assertEqual(self.contrato.valor_vigente, Decimal('1800.00'))

    def _colocar_no_aniversario(self, dias_ate_aniversario=10):
        # Posiciona o contrato dentro da janela do aniversário anual, com o fim de
        # vigência bem longe (para isolar a âncora de aniversário).
        hoje = date.today()
        aniversario = hoje + timedelta(days=dias_ate_aniversario)
        self.contrato.data_inicio = date(hoje.year - 1, aniversario.month, aniversario.day)
        self.contrato.data_fim = date(hoje.year + 5, aniversario.month, aniversario.day)
        self.contrato.save()

    def test_aviso_aniversario_some_apos_reajuste(self):
        # Reajuste dentro do ciclo do aniversário → badge/aviso desaparece.
        self._colocar_no_aniversario()
        self.assertTrue(self.contrato.precisa_atencao)
        self.contrato.data_ultimo_reajuste = date.today()
        self.contrato.save()
        self.assertFalse(self.contrato.precisa_atencao)

    def test_reajuste_permanece_disponivel_apos_aviso_sumir(self):
        # Mesmo com o aviso oculto, a opção de reajuste segue disponível dentro da janela.
        self._colocar_no_aniversario()
        self.contrato.data_ultimo_reajuste = date.today()
        self.contrato.save()
        self.assertFalse(self.contrato.precisa_atencao)
        self.assertTrue(self.contrato.pode_reajustar)
        # A view continua permitindo o POST (não redireciona por inelegibilidade).
        resp = self.client.post(reverse('contrato_reajuste', args=[self.contrato.pk]), {
            'valor_vigente': '2000,00',
        })
        self.assertRedirects(resp, reverse('contrato_detail', args=[self.contrato.pk]))
        self.contrato.refresh_from_db()
        self.assertEqual(self.contrato.valor_vigente, Decimal('2000.00'))

    def test_reajuste_carimba_data_ultimo_reajuste(self):
        self._colocar_no_aniversario()
        self.assertIsNone(self.contrato.data_ultimo_reajuste)
        self.client.post(reverse('contrato_reajuste', args=[self.contrato.pk]), {
            'valor_vigente': '2000,00',
        })
        self.contrato.refresh_from_db()
        self.assertEqual(self.contrato.data_ultimo_reajuste, date.today())

    def test_aviso_fim_de_vigencia_nao_some_apos_reajuste(self):
        # A supressão vale só para o aniversário; fim de vigência segue avisando.
        hoje = date.today()
        self.contrato.data_inicio = hoje - timedelta(days=365)
        self.contrato.data_fim = hoje + timedelta(days=5)
        self.contrato.data_ultimo_reajuste = hoje
        self.contrato.save()
        self.assertTrue(self.contrato.precisa_atencao)

    def test_aviso_aniversario_reaparece_no_proximo_ciclo(self):
        # Reajuste de um ciclo anterior não esconde o aviso do aniversário atual.
        self._colocar_no_aniversario()
        # Reajuste feito ~1 ano atrás (fora da janela do aniversário deste ano).
        self.contrato.data_ultimo_reajuste = date.today() - timedelta(days=365)
        self.contrato.save()
        self.assertTrue(self.contrato.precisa_atencao)

    def test_pdf_continua_usando_valor_mensal_apos_reajuste(self):
        self.contrato.valor_vigente = Decimal('1800.00')
        self.contrato.save()
        html = render_to_string('documentos/contrato_pdf.html', {
            'contrato': self.contrato,
            'locador': settings.SHELTER_LOCADOR,
            'prazo_meses': meses_entre(self.contrato.data_inicio, self.contrato.data_fim),
        })
        self.assertIn('1.500,00', html)
        self.assertNotIn('1.800,00', html)

    def test_list_filtro_atencao_sim(self):
        hoje = date.today()
        self.contrato.data_fim = hoje + timedelta(days=5)
        self.contrato.save()
        resp = self.client.get(reverse('contrato_list'), {'atencao': 'sim'})
        self.assertIn(self.contrato, resp.context['contratos'])

    def test_list_filtro_atencao_nao_exclui_contrato_em_atencao(self):
        hoje = date.today()
        self.contrato.data_fim = hoje + timedelta(days=5)
        self.contrato.save()
        resp = self.client.get(reverse('contrato_list'), {'atencao': 'nao'})
        self.assertNotIn(self.contrato, resp.context['contratos'])

    def test_list_filtro_atencao_sim_exclui_contrato_sem_atencao(self):
        resp = self.client.get(reverse('contrato_list'), {'atencao': 'sim'})
        self.assertNotIn(self.contrato, resp.context['contratos'])

    def test_list_sem_filtro_atencao_mostra_todos(self):
        resp = self.client.get(reverse('contrato_list'))
        self.assertIn(self.contrato, resp.context['contratos'])


class RenovacaoContratoTests(TestCase):
    """Múltiplas renovações por contrato ativo, sem campo de valor."""

    def setUp(self):
        self.user = User.objects.create_user('tester', password='x')
        self.client.force_login(self.user)
        _, self.imovel, self.inquilino, self.contrato = criar_base()
        self.url = reverse('renovacao_create', args=[self.contrato.pk])

    def _dados(self):
        return {'tipo': '12_12', 'data_renovacao': date.today().strftime('%d/%m/%Y'),
                'observacoes': ''}

    def test_registra_multiplas_renovacoes_no_mesmo_contrato(self):
        # Duas renovações no mesmo contrato ativo: acumulam sem erro nem bloqueio.
        self.client.post(self.url, self._dados())
        self.client.post(self.url, self._dados())
        self.assertEqual(self.contrato.renovacoes.count(), 2)

    def test_form_nao_grava_novo_valor_mensal(self):
        # Ainda que o cliente envie o campo removido, ele é ignorado (não existe no model).
        dados = self._dados()
        dados['novo_valor_mensal'] = '9999,00'
        self.client.post(self.url, dados)
        renovacao = self.contrato.renovacoes.get()
        self.assertFalse(hasattr(renovacao, 'novo_valor_mensal'))

    def test_botao_renovar_sempre_visivel_para_contrato_ativo(self):
        # Mesmo já havendo renovação registrada, a ação continua disponível no detalhe.
        RenovacaoContrato.objects.create(
            contrato=self.contrato, tipo='12_12', data_renovacao=date.today())
        resp = self.client.get(reverse('contrato_detail', args=[self.contrato.pk]))
        self.assertContains(resp, reverse('renovacao_create', args=[self.contrato.pk]))

    def test_detalhe_lista_todas_as_renovacoes(self):
        RenovacaoContrato.objects.create(
            contrato=self.contrato, tipo='12_12', data_renovacao=date.today())
        RenovacaoContrato.objects.create(
            contrato=self.contrato, tipo='12_30', data_renovacao=date.today())
        resp = self.client.get(reverse('contrato_detail', args=[self.contrato.pk]))
        self.assertEqual(len(resp.context['renovacoes']), 2)

    def test_contrato_nao_ativo_bloqueia_renovacao(self):
        # Guarda de status na view: contrato encerrado não cria renovação (defesa por URL).
        self.contrato.status = 'encerrado'
        self.contrato.save(update_fields=['status'])
        resp = self.client.post(self.url, self._dados())
        self.assertEqual(self.contrato.renovacoes.count(), 0)
        self.assertRedirects(resp, reverse('contrato_detail', args=[self.contrato.pk]))


class IdentidadeCodigoTests(TestCase):
    """codigo derivado do PK: PREFIXO-0001 (zero-padded a 4 dígitos)."""

    def setUp(self):
        _, self.imovel, self.inquilino, self.contrato = criar_base()

    def test_codigo_imovel(self):
        self.assertEqual(self.imovel.codigo, f'IMV-{self.imovel.pk:04d}')
        self.assertTrue(self.imovel.codigo.startswith('IMV-'))

    def test_codigo_contrato(self):
        self.assertEqual(self.contrato.codigo, f'CTR-{self.contrato.pk:04d}')

    def test_codigo_recibo(self):
        recibo = Recibo.objects.create(imovel=self.imovel, contrato=self.contrato)
        self.assertEqual(recibo.codigo, f'REC-{recibo.pk:04d}')

    def test_codigo_laudo(self):
        laudo = LaudoVistoria.objects.create(
            imovel=self.imovel, contrato=self.contrato, tipo='entrada',
            data=date(2026, 7, 1), responsavel='Carlos',
        )
        self.assertEqual(laudo.codigo, f'LAU-{laudo.pk:04d}')

    def test_codigo_objeto_nao_salvo_usa_placeholder(self):
        # acessar .codigo sem pk não deve levantar exceção
        self.assertEqual(Imovel().codigo, 'IMV-????')
        self.assertEqual(Contrato().codigo, 'CTR-????')


class IdentidadeRotulosTests(TestCase):
    """rotulo_curto / rotulo_longo das 4 entidades."""

    def setUp(self):
        _, self.imovel, self.inquilino, self.contrato = criar_base()

    def test_recibo_rotulo_curto_com_periodo_e_parcela(self):
        recibo = Recibo.objects.create(
            imovel=self.imovel, contrato=self.contrato,
            periodo_inicio=date(2026, 3, 1), parcela_atual=2, parcela_total=12,
        )
        rotulo = recibo.rotulo_curto
        self.assertIn('mar/2026', rotulo)
        self.assertIn('parcela 2/12', rotulo)
        self.assertIn(recibo.codigo, rotulo)

    def test_recibo_rotulo_curto_sem_campos_opcionais(self):
        # só imovel/contrato: não quebra e ainda mostra código + inquilino
        recibo = Recibo.objects.create(imovel=self.imovel, contrato=self.contrato)
        rotulo = recibo.rotulo_curto
        self.assertIn(recibo.codigo, rotulo)
        self.assertIn(self.inquilino.nome, rotulo)

    def test_contrato_rotulo_curto(self):
        rotulo = self.contrato.rotulo_curto
        self.assertIn(self.contrato.codigo, rotulo)
        self.assertIn(self.inquilino.nome, rotulo)
        self.assertIn(self.imovel.endereco, rotulo)
        self.assertIn('01/26–01/27', rotulo)  # período abreviado mm/aa–mm/aa
        self.assertIn(self.contrato.get_status_display(), rotulo)

    def test_laudo_rotulo_curto(self):
        laudo = LaudoVistoria.objects.create(
            imovel=self.imovel, contrato=self.contrato, tipo='entrada',
            data=date(2026, 7, 1), responsavel='Carlos',
        )
        rotulo = laudo.rotulo_curto
        self.assertIn(laudo.get_tipo_display(), rotulo)
        self.assertIn(self.imovel.endereco, rotulo)
        self.assertIn(laudo.locatario_nome(), rotulo)

    def test_imovel_rotulo_curto_usa_bairro_quando_presente(self):
        self.imovel.bairro = 'Centro'
        rotulo = self.imovel.rotulo_curto
        self.assertIn('Centro', rotulo)

    def test_imovel_rotulo_curto_cai_para_cidade_sem_bairro(self):
        self.imovel.bairro = ''
        rotulo = self.imovel.rotulo_curto
        self.assertIn(self.imovel.cidade, rotulo)


class NomeArquivoTests(TestCase):
    """nome_arquivo() — função pura, instâncias em memória (sem .save())."""

    def _instancias(self):
        inq = Inquilino(nome='João Sá')
        imv = Imovel(endereco='Rua Açaí', numero='10', cidade='Maringá')
        contrato = Contrato(inquilino=inq, imovel=imv,
                            data_inicio=date(2026, 1, 1), data_fim=date(2027, 1, 1))
        contrato.pk = 7
        laudo = LaudoVistoria(imovel=imv, contrato=contrato, tipo='entrada',
                              data=date(2026, 7, 1))
        laudo.pk = 7
        recibo = Recibo(imovel=imv, contrato=contrato, quem_pagou='João Sá',
                        periodo_inicio=date(2026, 3, 1))
        recibo.pk = 7
        return contrato, laudo, recibo

    def test_sem_acentos_e_apenas_chars_seguros(self):
        import re
        for instance in self._instancias():
            nome = nome_arquivo(instance)
            self.assertNotIn('ã', nome)
            self.assertNotIn('ç', nome)
            self.assertNotIn('í', nome)
            # slugify garante nome seguro no Windows: [A-Za-z0-9._-]
            self.assertRegex(nome, r'^[A-Za-z0-9._-]+$')

    def test_sufixo_de_versao(self):
        contrato, _, _ = self._instancias()
        self.assertIn('_v2', nome_arquivo(contrato, versao=2))
        self.assertNotIn('_v', nome_arquivo(contrato, versao=None))
        self.assertNotIn('_v', nome_arquivo(contrato))

    def test_nome_longo_e_truncado(self):
        inq = Inquilino(nome='João Sá')
        imv = Imovel(endereco='A' * 200, numero='10', cidade='Maringá')
        contrato = Contrato(inquilino=inq, imovel=imv,
                            data_inicio=date(2026, 1, 1), data_fim=date(2027, 1, 1))
        contrato.pk = 7
        nome = nome_arquivo(contrato, versao=2)
        self.assertLess(len(nome), 150)


class LabelSelectTests(TestCase):
    """ModelChoiceFields exibem rotulo_curto em vez de str(obj)."""

    def setUp(self):
        _, self.imovel, self.inquilino, self.contrato = criar_base()
        self.laudo = LaudoVistoria.objects.create(
            imovel=self.imovel, contrato=self.contrato, tipo='saida',
            data=date(2026, 7, 1), responsavel='Carlos',
        )

    def test_contrato_form_imovel_label(self):
        campo = ContratoForm().fields['imovel']
        self.assertEqual(campo.label_from_instance(self.imovel), self.imovel.rotulo_curto)

    def test_laudo_form_labels(self):
        form = LaudoVistoriaForm()
        self.assertEqual(form.fields['imovel'].label_from_instance(self.imovel),
                         self.imovel.rotulo_curto)
        self.assertEqual(form.fields['contrato'].label_from_instance(self.contrato),
                         self.contrato.rotulo_curto)

    def test_recibo_form_labels(self):
        form = ReciboForm()
        self.assertEqual(form.fields['imovel'].label_from_instance(self.imovel),
                         self.imovel.rotulo_curto)
        self.assertEqual(form.fields['contrato'].label_from_instance(self.contrato),
                         self.contrato.rotulo_curto)

    def test_lancamento_form_contrato_label(self):
        campo = LancamentoForm().fields['contrato']
        self.assertEqual(campo.label_from_instance(self.contrato), self.contrato.rotulo_curto)

    def test_notificacao_form_imovel_label(self):
        campo = NotificacaoForm().fields['imovel']
        self.assertEqual(campo.label_from_instance(self.imovel), self.imovel.rotulo_curto)

    def test_distrato_form_laudo_saida_label(self):
        campo = DistratoForm().fields['laudo_saida']
        self.assertEqual(campo.label_from_instance(self.laudo), self.laudo.rotulo_curto)


class NotificacaoUsuarioTests(TestCase):
    """Histórico de notificações por usuário: captura, isolamento e limite."""

    def setUp(self):
        self.user = User.objects.create_user('tester', password='x')
        self.client.force_login(self.user)
        self.factory = RequestFactory()

    def test_acao_crud_cria_notificacao_usuario(self):
        resp = self.client.post(reverse('proprietario_create'), {
            'nome': 'Maria Dona', 'cpf_cnpj': CPF_VALIDO_3,
        })
        self.assertRedirects(resp, reverse('proprietario_list'))
        notificacao = NotificacaoUsuario.objects.filter(usuario=self.user).latest('criado_em')
        self.assertEqual(notificacao.nivel, 'success')
        self.assertTrue(notificacao.mensagem)

    def test_isolamento_por_usuario(self):
        outro_user = User.objects.create_user('outro', password='x')
        NotificacaoUsuario.objects.create(usuario=self.user, mensagem='Minha notificação', nivel='success')
        NotificacaoUsuario.objects.create(usuario=outro_user, mensagem='Notificação do outro', nivel='success')

        request = self.factory.get('/')
        request.user = self.user
        contexto = notificacoes_usuario(request)

        mensagens = [n.mensagem for n in contexto['ultimas_notificacoes_usuario']]
        self.assertIn('Minha notificação', mensagens)
        self.assertNotIn('Notificação do outro', mensagens)

    def test_limite_de_n_no_context_processor(self):
        for i in range(LIMITE_NOTIFICACOES_TOPBAR + 3):
            NotificacaoUsuario.objects.create(
                usuario=self.user, mensagem=f'Notificação {i}', nivel='success')

        request = self.factory.get('/')
        request.user = self.user
        contexto = notificacoes_usuario(request)
        ultimas = list(contexto['ultimas_notificacoes_usuario'])

        self.assertEqual(len(ultimas), LIMITE_NOTIFICACOES_TOPBAR)
        criados_em = [n.criado_em for n in ultimas]
        self.assertEqual(criados_em, sorted(criados_em, reverse=True))

    def test_usuario_anonimo_nao_quebra(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        self.assertEqual(notificacoes_usuario(request), {})


class PerfisUsuarioTests(TestCase):
    """Matriz de perfis (Admin/Owner/Comum) x telas protegidas
    (Financeiro) + regras de precedência e migração de dados.

    Dashboard Imobiliário deixou de exigir permissão (aberto a todos os
    perfis logados) — ver landing.html / dashboard_imobiliario em
    imoveis/views.py."""

    @classmethod
    def setUpTestData(cls):
        cls.perm_dashboard = Permission.objects.get(codename='pode_acessar_dashboard')
        cls.perm_financeiro = Permission.objects.get(codename='pode_acessar_financeiro')
        cls.owner_group, _ = Group.objects.get_or_create(name='Owner')
        cls.owner_group.permissions.set([cls.perm_dashboard, cls.perm_financeiro])
        cls.comum_group, _ = Group.objects.get_or_create(name='Comum')

    def _login_admin(self):
        user = User.objects.create_superuser('admin', 'admin@x.com', 'x')
        self.client.force_login(user)
        return user

    def _login_owner(self):
        user = User.objects.create_user('owner', password='x')
        user.groups.add(self.owner_group)
        self.client.force_login(user)
        return user

    def _login_comum(self):
        user = User.objects.create_user('comum', password='x')
        user.groups.add(self.comum_group)
        self.client.force_login(user)
        return user

    # --- Matriz 3 perfis x 2 telas ---

    def test_admin_acessa_dashboard(self):
        self._login_admin()
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_admin_acessa_financeiro(self):
        self._login_admin()
        resp = self.client.get(reverse('lancamento_list'))
        self.assertEqual(resp.status_code, 200)

    def test_owner_acessa_dashboard(self):
        self._login_owner()
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_owner_acessa_financeiro(self):
        self._login_owner()
        resp = self.client.get(reverse('lancamento_list'))
        self.assertEqual(resp.status_code, 200)

    def test_comum_acessa_dashboard(self):
        self._login_comum()
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_comum_nao_acessa_financeiro(self):
        self._login_comum()
        resp = self.client.get(reverse('lancamento_list'))
        self.assertEqual(resp.status_code, 403)

    def test_anonimo_redireciona_para_login(self):
        resp = self.client.get(reverse('dashboard'))
        self.assertRedirects(resp, f"/login/?next={reverse('dashboard')}")

    # --- Precedência Owner + Comum ---

    def test_usuario_em_owner_e_comum_prevalece_owner(self):
        user = User.objects.create_user('ambos', password='x')
        user.groups.add(self.owner_group, self.comum_group)
        self.client.force_login(user)
        resp_dashboard = self.client.get(reverse('dashboard'))
        resp_financeiro = self.client.get(reverse('lancamento_list'))
        self.assertEqual(resp_dashboard.status_code, 200)
        self.assertEqual(resp_financeiro.status_code, 200)

    # --- Sidebar oculta os itens ---

    def test_sidebar_oculta_financeiro_para_comum(self):
        self._login_comum()
        resp = self.client.get(reverse('imovel_list'))
        self.assertNotContains(resp, reverse('lancamento_list'))

    def test_sidebar_mostra_financeiro_para_owner(self):
        self._login_owner()
        resp = self.client.get(reverse('imovel_list'))
        self.assertContains(resp, reverse('lancamento_list'))

    def test_sidebar_mostra_dashboard_para_comum(self):
        self._login_comum()
        resp = self.client.get(reverse('imovel_list'))
        self.assertContains(resp, reverse('dashboard'))

    # --- Landing (rota /) ---

    def test_comum_acessa_landing(self):
        self._login_comum()
        resp = self.client.get(reverse('landing'))
        self.assertEqual(resp.status_code, 200)

    def test_topbar_rotulo_comum(self):
        self._login_comum()
        resp = self.client.get(reverse('landing'))
        self.assertContains(resp, 'Comum')

    def test_topbar_rotulo_owner(self):
        self._login_owner()
        resp = self.client.get(reverse('landing'))
        self.assertContains(resp, 'Owner')

    # --- 403 usa o template certo, não stack trace ---

    def test_403_usa_template_proprio(self):
        self._login_comum()
        resp = self.client.get(reverse('lancamento_list'))
        self.assertTemplateUsed(resp, '403.html')

    # --- Migração de dados: reclassificação de usuários existentes ---

    def test_migration_reclassifica_usuarios_existentes(self):
        """Chama a função de RunPython da migration do módulo 2
        diretamente (importada do arquivo de migration via importlib),
        passando o registry real de apps, e valida is_superuser/Group
        resultantes. Não usa MigrationTestCase porque a migration já
        rodou na criação do banco de teste (sem usuários ainda
        existentes) — aqui testamos a função isoladamente contra
        usuários criados no próprio teste."""
        import importlib
        from django.apps import apps as real_apps

        mod_migration = importlib.import_module(
            'imoveis.migrations.0015_cria_grupos_e_reclassifica_usuarios'
        )

        staff_sem_super = User.objects.create_user('staffuser', password='x', is_staff=True)
        comum_qualquer = User.objects.create_user('qualquer', password='x')

        mod_migration.cria_grupos_e_permissoes(real_apps, None)

        staff_sem_super.refresh_from_db()
        comum_qualquer.refresh_from_db()
        self.assertTrue(staff_sem_super.is_superuser)
        self.assertFalse(comum_qualquer.groups.filter(name='Owner').exists())
        self.assertTrue(comum_qualquer.groups.filter(name='Comum').exists())


class HistoricoStatusImovelTests(TestCase):
    """Captura de histórico de status e KPI de tempo médio de vacância."""

    def _imovel_vago(self):
        prop = Proprietario.objects.create(nome='Dona P', cpf_cnpj=CPF_VALIDO_2)
        return Imovel.objects.create(
            proprietario=prop, tipo='casa', endereco='Rua V',
            numero='1', cidade='Maringá',
        )

    def test_imovel_novo_gera_periodo_aberto(self):
        imovel = self._imovel_vago()
        periodos = imovel.historico_status.all()
        self.assertEqual(periodos.count(), 1)
        p = periodos.first()
        self.assertEqual(p.status, 'vago')
        self.assertIsNone(p.data_fim)

    def test_transicao_via_contrato_fecha_e_abre_periodo(self):
        imovel = self._imovel_vago()
        inquilino = Inquilino.objects.create(nome='Loc', cpf=CPF_VALIDO)
        Contrato.objects.create(
            imovel=imovel, inquilino=inquilino, tipo_contrato='PF',
            data_inicio=date(2026, 1, 1), data_fim=date(2027, 1, 1),
            valor_mensal=Decimal('1500.00'), dia_vencimento=10,
        )
        imovel.refresh_from_db()
        self.assertEqual(imovel.status, 'ocupado')
        periodos = list(imovel.historico_status.order_by('data_inicio'))
        self.assertEqual(len(periodos), 2)
        self.assertEqual(periodos[0].status, 'vago')
        self.assertIsNotNone(periodos[0].data_fim)   # período de vacância fechado
        self.assertEqual(periodos[1].status, 'ocupado')
        self.assertIsNone(periodos[1].data_fim)

    def test_transicao_manual_manutencao(self):
        imovel = self._imovel_vago()
        imovel.status = 'manutencao'
        imovel.save()
        periodos = list(imovel.historico_status.order_by('data_inicio'))
        self.assertEqual(len(periodos), 2)
        self.assertEqual(periodos[-1].status, 'manutencao')
        self.assertIsNone(periodos[-1].data_fim)

    def test_save_sem_trocar_status_e_idempotente(self):
        imovel = self._imovel_vago()
        imovel.endereco = 'Rua V, editada'
        imovel.save()
        self.assertEqual(imovel.historico_status.count(), 1)

    def test_kpi_media_vacancia(self):
        imovel = self._imovel_vago()
        # Substitui o período seed por dois períodos vagos fechados de 10 e 20 dias.
        imovel.historico_status.all().delete()
        base = timezone.now() - timedelta(days=40)
        HistoricoStatusImovel.objects.create(
            imovel=imovel, status='vago',
            data_inicio=base, data_fim=base + timedelta(days=10),
        )
        HistoricoStatusImovel.objects.create(
            imovel=imovel, status='vago',
            data_inicio=base + timedelta(days=15), data_fim=base + timedelta(days=35),
        )
        user = User.objects.create_user('dash', password='x')
        self.client.force_login(user)
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['amostra_vacancia'], 2)
        self.assertEqual(resp.context['tempo_medio_vacancia'], 15.0)
        self.assertFalse(resp.context['vacancia_sem_dados'])

    def test_kpi_estado_vazio(self):
        # Só o período aberto do seed — nenhum período vago concluído.
        self._imovel_vago()
        user = User.objects.create_user('dash2', password='x')
        self.client.force_login(user)
        resp = self.client.get(reverse('dashboard'))
        self.assertIsNone(resp.context['tempo_medio_vacancia'])
        self.assertTrue(resp.context['vacancia_sem_dados'])

    def test_filtro_periodo_recorta_amostra(self):
        imovel = self._imovel_vago()
        imovel.historico_status.all().delete()
        # Um período vago antigo (fora da janela) e um recente (dentro).
        antigo_ini = timezone.now() - timedelta(days=300)
        HistoricoStatusImovel.objects.create(
            imovel=imovel, status='vago',
            data_inicio=antigo_ini, data_fim=antigo_ini + timedelta(days=5),
        )
        recente_ini = timezone.now() - timedelta(days=10)
        HistoricoStatusImovel.objects.create(
            imovel=imovel, status='vago',
            data_inicio=recente_ini, data_fim=recente_ini + timedelta(days=3),
        )
        user = User.objects.create_user('dash3', password='x')
        self.client.force_login(user)
        # Janela padrão (90 dias) captura só o recente.
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.context['amostra_vacancia'], 1)

    def test_drilldown_timeline_imovel_selecionado(self):
        imovel = self._imovel_vago()
        user = User.objects.create_user('dash4', password='x')
        self.client.force_login(user)
        resp = self.client.get(reverse('dashboard'), {'timeline_imovel_id': imovel.pk})
        self.assertIsNotNone(resp.context['imovel_timeline'])
        self.assertEqual(resp.context['imovel_selecionado'], imovel)

    def test_drilldown_usa_primeiro_imovel_por_padrao(self):
        imovel = self._imovel_vago()
        user = User.objects.create_user('dash5', password='x')
        self.client.force_login(user)
        resp = self.client.get(reverse('dashboard'))
        self.assertIsNotNone(resp.context['imovel_timeline'])
        self.assertEqual(resp.context['imovel_selecionado'], imovel)
