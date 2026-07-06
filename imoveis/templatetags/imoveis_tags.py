from django import template

from imoveis import extenso

register = template.Library()


@register.filter
def brl(value):
    """Formata um número como moeda brasileira: 1.500,00"""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value
    formatted = f"{value:,.2f}"          # 1,500.00  (locale inglês)
    # Trocar separadores: , → X, . → ,, X → .
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return formatted


@register.filter
def valor_extenso(value):
    """Valor monetário por extenso: 1500.00 → 'mil e quinhentos reais'."""
    try:
        return extenso.valor_por_extenso(value)
    except Exception:
        return value


@register.filter
def meses_extenso(value):
    """Quantidade de meses por extenso: 12 → 'doze meses'."""
    try:
        return extenso.meses_por_extenso(value)
    except Exception:
        return value


@register.filter
def dia_extenso(value):
    """Ordinal do dia por extenso: 1 → 'primeiro'."""
    try:
        return extenso.dia_ordinal_extenso(value)
    except Exception:
        return value
