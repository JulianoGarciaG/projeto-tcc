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


def validate_cnpj(value):
    """Valida um CNPJ pelo algoritmo dos dígitos verificadores.

    Aceita com máscara (00.000.000/0000-00) ou sem (00000000000000).
    Levanta ValidationError se o CNPJ for inválido.
    """
    cnpj = re.sub(r'\D', '', str(value))

    if len(cnpj) != 14:
        raise ValidationError('CNPJ deve conter 14 dígitos.')

    if cnpj == cnpj[0] * 14:
        raise ValidationError('CNPJ inválido.')

    pesos = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for posicao in (12, 13):
        soma = sum(int(cnpj[i]) * pesos[len(pesos) - posicao + i] for i in range(posicao))
        digito = soma % 11
        digito = 0 if digito < 2 else 11 - digito
        if digito != int(cnpj[posicao]):
            raise ValidationError('CNPJ inválido.')


def validate_cpf_cnpj(value):
    """Valida CPF ou CNPJ conforme a quantidade de dígitos (11 → CPF, 14 → CNPJ)."""
    digitos = re.sub(r'\D', '', str(value))
    if len(digitos) == 11:
        validate_cpf(value)
    elif len(digitos) == 14:
        validate_cnpj(value)
    else:
        raise ValidationError('Informe um CPF (11 dígitos) ou CNPJ (14 dígitos) válido.')


def validate_rg(value):
    """Validação de formato genérico do RG (não há dígito verificador nacional único).

    Aceita letras, números e os separadores "." e "-".
    """
    if not re.fullmatch(r'[A-Za-z0-9.\-]*', str(value)):
        raise ValidationError('RG deve conter apenas letras, números, "." e "-".')
