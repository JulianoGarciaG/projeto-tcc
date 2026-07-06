"""Geração de PDF a partir de templates HTML (xhtml2pdf).

Helpers reutilizados pelas seções Contrato, Laudo de Vistoria e Recibo.
Toda a lógica de PDF vive aqui — as views apenas montam o contexto e chamam
gerar_e_anexar() / pdf_download_response().
"""
import hashlib
import io
import os

from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Max
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
    """Grava o PDF no FileField legado do registro (espelho da última versão)."""
    field = getattr(instance, field_name)
    field.save(filename, ContentFile(pdf_bytes), save=True)


def registrar_documento_gerado(instance, pdf_bytes, filename, usuario=None):
    """Cria a próxima versão imutável de DocumentoGerado para a origem.

    Fonte de verdade do GED versionado: numero_versao sequencial por origem
    (1, 2, 3...), hash SHA-256 do arquivo e autor da geração.
    """
    from .models import Contrato, DocumentoGerado, LaudoVistoria, Recibo

    if isinstance(instance, Contrato):
        tipo = 'contrato'
    elif isinstance(instance, LaudoVistoria):
        tipo = 'laudo'
    elif isinstance(instance, Recibo):
        tipo = 'recibo'
    else:
        raise ValueError(f'Origem não suportada para DocumentoGerado: {type(instance).__name__}')

    ultima = (DocumentoGerado.objects.filter(**{tipo: instance})
              .aggregate(m=Max('numero_versao'))['m']) or 0
    doc = DocumentoGerado(
        tipo=tipo,
        numero_versao=ultima + 1,
        sha256=hashlib.sha256(pdf_bytes).hexdigest(),
        gerado_por=usuario if getattr(usuario, 'is_authenticated', False) else None,
        **{tipo: instance},
    )
    doc.arquivo.save(filename, ContentFile(pdf_bytes), save=False)
    doc.save()
    return doc


def gerar_e_anexar(instance, template_name, context, field_name, filename, usuario=None):
    """Gera o PDF, registra uma versão imutável no GED (DocumentoGerado) e
    espelha o arquivo no FileField legado do registro. Retorna os bytes."""
    pdf_bytes = render_pdf(template_name, context)
    registrar_documento_gerado(instance, pdf_bytes, filename, usuario)
    save_pdf_to_field(instance, field_name, pdf_bytes, filename)
    return pdf_bytes
