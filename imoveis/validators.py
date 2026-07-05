import re

from django.core.exceptions import ValidationError


def validate_cpf(value):
    """Valida um CPF pelo algoritmo dos dígitos verificadores.

    Aceita com máscara (000.000.000-00) ou sem (00000000000).
    Levanta ValidationError se o CPF for inválido.
    """
    cpf = re.sub(r'\D', '', str(value))

    if len(cpf) != 11:
        raise ValidationError('CPF deve conter 11 dígitos.')

    if cpf == cpf[0] * 11:  # 111.111.111-11 etc. passam no cálculo mas são inválidos
        raise ValidationError('CPF inválido.')

    for posicao in (9, 10):
        soma = sum(int(cpf[i]) * ((posicao + 1) - i) for i in range(posicao))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != int(cpf[posicao]):
            raise ValidationError('CPF inválido.')
