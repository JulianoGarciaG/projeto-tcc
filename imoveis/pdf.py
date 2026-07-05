"""Geração de PDF a partir de templates HTML (xhtml2pdf).

Helpers reutilizados pelas seções Contrato, Laudo de Vistoria e Recibo.
Toda a lógica de PDF vive aqui — as views apenas montam o contexto e chamam
gerar_e_anexar() / pdf_download_response().
"""
import io
import os

from django.conf import settings
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa


def link_callback(uri, rel):
    """Resolve URLs de STATIC/MEDIA para caminhos de arquivo locais.

    Obrigatório no xhtml2pdf: sem isso, imagens (ex: logo) não carregam no PDF.
    """
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ''))
        if os.path.isfile(path):
            return path
    elif uri.startswith(settings.STATIC_URL):
        rel_path = uri.replace(settings.STATIC_URL, '')
        if settings.STATIC_ROOT:
            path = os.path.join(settings.STATIC_ROOT, rel_path)
            if os.path.isfile(path):
                return path
        for static_dir in settings.STATICFILES_DIRS:
            path = os.path.join(static_dir, rel_path)
            if os.path.isfile(path):
                return path
    return uri


def html_to_pdf_bytes(html):
    """Converte HTML em bytes de PDF via pisa. Levanta ValueError em erro."""
    buffer = io.BytesIO()
    result = pisa.CreatePDF(html, dest=buffer, link_callback=link_callback, encoding='utf-8')
    if result.err:
        raise ValueError('Erro ao gerar o PDF do documento.')
    return buffer.getvalue()


def render_pdf(template_name, context):
    """Renderiza um template Django e converte o HTML resultante em PDF."""
    html = render_to_string(template_name, context)
    return html_to_pdf_bytes(html)


def pdf_download_response(pdf_bytes, filename):
    """Resposta HTTP de download (attachment) para o PDF gerado."""
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def save_pdf_to_field(instance, field_name, pdf_bytes, filename):
    """Grava o PDF no FileField do registro (passa a aparecer no GED)."""
    field = getattr(instance, field_name)
    field.save(filename, ContentFile(pdf_bytes), save=True)


def gerar_e_anexar(instance, template_name, context, field_name, filename):
    """Gera o PDF, anexa ao FileField do registro e retorna os bytes."""
    pdf_bytes = render_pdf(template_name, context)
    save_pdf_to_field(instance, field_name, pdf_bytes, filename)
    return pdf_bytes
