import hashlib
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse

from .extenso import (
    dia_ordinal_extenso, meses_entre, meses_por_extenso, valor_por_extenso,
)
from .forms import (
    ContratoForm, DistratoForm, FiadorForm, LancamentoForm, LaudoVistoriaForm,
    NotificacaoForm, ReciboForm,
)
from .identidade import nome_arquivo
from .models import (
    Contrato, DocumentoGerado, Fiador, FotoItemVistoria, Imovel, Inquilino,
    ItemVistoria, Lancamento, LaudoVistoria, Notificacao, Proprietario,
    Recibo, TestemunhaLaudo,
)


def limpar_arquivos_gerados():
    """Remove do storage os PDFs criados durante os testes (versões + espelhos)."""
    for doc in DocumentoGerado.objects.all():
        doc.arquivo.delete(save=False)
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
            contrato=self.contrato, tipo='aluguel', valor=Decimal('1500.00'),
            data_vencimento=date(2026, 8, 10),
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
        # nome de arquivo determinístico: contém o código e a versão
        disp = resp['Content-Disposition']
        self.assertIn(self.contrato.codigo, disp)
        self.assertIn('_v1.pdf', disp)
        self.contrato.refresh_from_db()
        self.assertTrue(self.contrato.documento_gerado)
        # segunda geração incrementa a versão para _v2
        resp2 = self.client.get(reverse('contrato_gerar_pdf', args=[self.contrato.pk]))
        self.assertIn('_v2.pdf', resp2['Content-Disposition'])

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
        self.assertIn('_v1.pdf', disp)
        laudo.refresh_from_db()
        self.assertTrue(laudo.documento_gerado)
        resp2 = self.client.get(reverse('laudo_gerar_pdf', args=[laudo.pk]))
        self.assertIn('_v2.pdf', resp2['Content-Disposition'])

    def test_recibo_gerar_pdf_view(self):
        recibo = Recibo.objects.create(imovel=self.imovel, contrato=self.contrato,
                                       quantia=Decimal('1500.00'))
        resp = self.client.get(reverse('recibo_gerar_pdf', args=[recibo.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
        self.assertTrue(resp.content.startswith(b'%PDF-'))
        disp = resp['Content-Disposition']
        self.assertIn(recibo.codigo, disp)
        self.assertIn('_v1.pdf', disp)
        recibo.refresh_from_db()
        self.assertTrue(recibo.arquivo)
        resp2 = self.client.get(reverse('recibo_gerar_pdf', args=[recibo.pk]))
        self.assertIn('_v2.pdf', resp2['Content-Disposition'])

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
        # aparecer no GED — que agora lista versões de DocumentoGerado.
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


class DocumentoGeradoTests(TestCase):
    """GED versionado — DocumentoGerado (versões imutáveis por geração de PDF)."""

    def setUp(self):
        self.user = User.objects.create_user('tester', password='x')
        self.client.force_login(self.user)
        _, self.imovel, self.inquilino, self.contrato = criar_base()

    def tearDown(self):
        limpar_arquivos_gerados()

    def test_gerar_pdf_cria_versao_com_hash_e_autor(self):
        resp = self.client.get(reverse('contrato_gerar_pdf', args=[self.contrato.pk]))
        doc = DocumentoGerado.objects.get(contrato=self.contrato)
        self.assertEqual(doc.tipo, 'contrato')
        self.assertEqual(doc.numero_versao, 1)
        self.assertEqual(doc.gerado_por, self.user)
        self.assertEqual(doc.sha256, hashlib.sha256(resp.content).hexdigest())
        with doc.arquivo.open('rb') as f:
            self.assertEqual(f.read(), resp.content)

    def test_versoes_incrementam_por_origem(self):
        self.client.get(reverse('contrato_gerar_pdf', args=[self.contrato.pk]))
        self.client.get(reverse('contrato_gerar_pdf', args=[self.contrato.pk]))
        recibo = Recibo.objects.create(imovel=self.imovel, contrato=self.contrato,
                                       quantia=Decimal('100.00'))
        self.client.get(reverse('recibo_gerar_pdf', args=[recibo.pk]))
        versoes_contrato = list(
            DocumentoGerado.objects.filter(contrato=self.contrato)
            .order_by('numero_versao').values_list('numero_versao', flat=True))
        self.assertEqual(versoes_contrato, [1, 2])
        # A sequência é independente por origem: o recibo começa em 1
        doc_recibo = DocumentoGerado.objects.get(recibo=recibo)
        self.assertEqual(doc_recibo.numero_versao, 1)
        self.assertEqual(doc_recibo.tipo, 'recibo')

    def test_laudo_gerar_pdf_cria_versao(self):
        laudo = LaudoVistoria.objects.create(
            imovel=self.imovel, contrato=self.contrato, tipo='entrada',
            data=date(2026, 7, 1), responsavel='Carlos',
        )
        self.client.get(reverse('laudo_gerar_pdf', args=[laudo.pk]))
        doc = DocumentoGerado.objects.get(laudo=laudo)
        self.assertEqual((doc.tipo, doc.numero_versao), ('laudo', 1))

    def test_registro_imutavel(self):
        self.client.get(reverse('contrato_gerar_pdf', args=[self.contrato.pk]))
        doc = DocumentoGerado.objects.get(contrato=self.contrato)
        doc.sha256 = 'x' * 64
        with self.assertRaises(ValueError):
            doc.save()

    def test_campo_legado_espelha_ultima_versao(self):
        self.client.get(reverse('contrato_gerar_pdf', args=[self.contrato.pk]))
        self.client.get(reverse('contrato_gerar_pdf', args=[self.contrato.pk]))
        self.contrato.refresh_from_db()
        self.assertTrue(self.contrato.documento_gerado)
        ultima = (DocumentoGerado.objects.filter(contrato=self.contrato)
                  .order_by('-numero_versao').first())
        self.assertEqual(ultima.numero_versao, 2)
        with self.contrato.documento_gerado.open('rb') as f:
            conteudo_legado = f.read()
        self.assertEqual(hashlib.sha256(conteudo_legado).hexdigest(), ultima.sha256)

    def test_ged_lista_todas_as_versoes(self):
        self.client.get(reverse('contrato_gerar_pdf', args=[self.contrato.pk]))
        self.client.get(reverse('contrato_gerar_pdf', args=[self.contrato.pk]))
        resp = self.client.get(reverse('documentos'))
        self.assertEqual(resp.status_code, 200)
        docs = list(resp.context['contratos_gerados'])
        self.assertEqual(len(docs), 2)
        self.assertEqual(sorted(d.numero_versao for d in docs), [1, 2])


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
        self.client.force_login(self.user)
        _, self.imovel, self.inquilino, self.contrato = criar_base()
        self.lanc_junho = Lancamento.objects.create(
            contrato=self.contrato, tipo='aluguel', status='pago',
            valor=Decimal('1500.00'), data_vencimento=date(2026, 6, 15),
        )
        self.lanc_agosto = Lancamento.objects.create(
            contrato=self.contrato, tipo='aluguel', status='pendente',
            valor=Decimal('1500.00'), data_vencimento=date(2026, 8, 15),
        )

    def test_filtro_datas_ddmmyyyy(self):
        resp = self.client.get(reverse('dashboard'),
                               {'data_inicio': '01/06/2026', 'data_fim': '30/06/2026'})
        self.assertEqual(resp.status_code, 200)
        ultimos = list(resp.context['ultimos_lancamentos'])
        self.assertIn(self.lanc_junho, ultimos)
        self.assertNotIn(self.lanc_agosto, ultimos)

    def test_sem_filtro_lista_todos(self):
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)
        ultimos = list(resp.context['ultimos_lancamentos'])
        self.assertIn(self.lanc_junho, ultimos)
        self.assertIn(self.lanc_agosto, ultimos)

    def test_campos_usam_flatpickr(self):
        resp = self.client.get(reverse('dashboard'))
        form = resp.context['filtro_form']
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
