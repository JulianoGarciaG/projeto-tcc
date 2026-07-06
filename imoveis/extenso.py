r"""Utilitários puros de "número por extenso" (num2words, pt-BR).

Usados no PDF jurídico do contrato (templates/documentos/contrato_pdf.html,
via filtros de imoveis/templatetags/imoveis_tags.py). Sem dependência de
Django models/views — testável isoladamente.

Datas por extenso NÃO são tratadas aqui: o filtro nativo `date` do Django
com LANGUAGE_CODE = 'pt-br' já produz "1 de Junho de 2026" via
{{ valor|date:"j \d\e F \d\e Y" }}.
"""

from datetime import date
from decimal import Decimal, InvalidOperation

from num2words import num2words


def valor_por_extenso(valor):
    """Valor monetário por extenso em reais.

    Ex.: Decimal('1500.00') -> 'mil e quinhentos reais'.
    None/vazio retorna string vazia (padrão defensivo de imoveis_tags.brl).

    Nota: o conversor pt_BR do num2words 0.5.14 não aceita o kwarg
    `currency` em to_currency() — a moeda padrão já é o real (BRL).
    """
    if valor in (None, ''):
        return ''
    try:
        valor = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        return ''
    return num2words(valor, lang='pt_BR', to='currency')


def meses_entre(data_inicio, data_fim):
    """Total de meses inteiros entre duas datas (sem dateutil).

    Ex.: 01/01/2026 a 01/01/2027 -> 12; 15/01/2026 a 10/01/2027 -> 11.
    """
    if not isinstance(data_inicio, date) or not isinstance(data_fim, date):
        return 0
    meses = (data_fim.year - data_inicio.year) * 12 + (data_fim.month - data_inicio.month)
    if data_fim.day < data_inicio.day:
        meses -= 1
    return meses


def meses_por_extenso(quantidade):
    """Quantidade de meses por extenso. Ex.: 12 -> 'doze meses'; 1 -> 'um mês'."""
    if quantidade in (None, ''):
        return ''
    try:
        quantidade = int(quantidade)
    except (ValueError, TypeError):
        return ''
    unidade = 'mês' if quantidade == 1 else 'meses'
    return f"{num2words(quantidade, lang='pt_BR')} {unidade}"


def dia_ordinal_extenso(dia):
    """Ordinal por extenso do dia de vencimento. Ex.: 1 -> 'primeiro'; 10 -> 'décimo'."""
    if dia in (None, ''):
        return ''
    try:
        dia = int(dia)
    except (ValueError, TypeError):
        return ''
    return num2words(dia, lang='pt_BR', to='ordinal')
