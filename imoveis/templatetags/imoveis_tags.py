from django import template

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
