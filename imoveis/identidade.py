"""Camada única de identidade/nomenclatura das entidades de negócio.

Fonte de verdade para:
- `codigo` legível derivado do PK em runtime (não persistido, sem migration);
- `rotulo_curto`/`rotulo_longo` consumidos por selects e templates;
- `nome_arquivo()` determinístico usado no GED e no download de PDF.
"""

from datetime import date

from django.utils.text import slugify


class IdentificavelMixin:
    """Fonte única de identidade legível das entidades de negócio.

    Cada subclasse define PREFIXO_CODIGO (3 letras) e implementa
    rotulo_curto/rotulo_longo. `codigo` é derivado do PK em runtime —
    não é persistido, não exige migration.
    """
    PREFIXO_CODIGO = None  # subclasse deve sobrescrever, ex.: 'IMV'

    @property
    def codigo(self):
        if self.pk is None:
            return f'{self.PREFIXO_CODIGO}-????'
        return f'{self.PREFIXO_CODIGO}-{self.pk:04d}'

    @property
    def rotulo_curto(self):
        raise NotImplementedError

    @property
    def rotulo_longo(self):
        raise NotImplementedError


_MESES_ABREV = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun',
                'jul', 'ago', 'set', 'out', 'nov', 'dez']


def mes_ano_abreviado(data):
    """Ex.: date(2026, 3, 15) -> 'mar/2026'. None -> ''."""
    if data is None:
        return ''
    return f'{_MESES_ABREV[data.month - 1]}/{data.year}'


_TIPO_LABEL = {'contrato': 'Contrato', 'laudo': 'Laudo', 'recibo': 'Recibo'}


def _endereco_curto(imovel):
    end = imovel.endereco
    if imovel.numero:
        end = f'{end} {imovel.numero}'
    return end


def nome_arquivo(instance, versao=None):
    """Nome de arquivo determinístico do PDF gerado (GED + download).

    instance: Contrato | LaudoVistoria | Recibo (import local evita ciclo
    com models.py, igual ao padrão já usado em pdf.py).
    """
    from .models import Contrato, LaudoVistoria, Recibo

    if isinstance(instance, Contrato):
        tipo = 'contrato'
        quem = instance.inquilino.nome
        onde = _endereco_curto(instance.imovel)
        quando = date.today().strftime('%Y%m%d')
    elif isinstance(instance, LaudoVistoria):
        tipo = 'laudo'
        quem = instance.get_tipo_display()
        onde = _endereco_curto(instance.imovel)
        quando = (instance.data or date.today()).strftime('%Y%m%d')
    elif isinstance(instance, Recibo):
        tipo = 'recibo'
        quem = instance.quem_pagou or instance.contrato.inquilino.nome
        onde = mes_ano_abreviado(instance.periodo_inicio).replace('/', '-') or 'sem-periodo'
        quando = None  # já embutido em "onde" (mes-ano)
    else:
        raise ValueError(f'Tipo não suportado para nome_arquivo: {type(instance).__name__}')

    partes = [_TIPO_LABEL[tipo], instance.codigo, slugify(quem)[:40], slugify(onde)[:40]]
    if quando:
        partes.append(quando)
    if versao:
        partes.append(f'v{versao}')
    return '_'.join(p for p in partes if p) + '.pdf'
