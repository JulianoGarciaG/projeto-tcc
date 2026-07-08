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


def _tipo_de(instance):
    """'contrato' | 'laudo' | 'recibo' a partir da classe da instância."""
    from .models import Contrato, LaudoVistoria, Recibo

    if isinstance(instance, Contrato):
        return 'contrato'
    if isinstance(instance, LaudoVistoria):
        return 'laudo'
    if isinstance(instance, Recibo):
        return 'recibo'
    raise ValueError(f'Origem não suportada para DocumentoGerado: {type(instance).__name__}')


def _proxima_versao(instance, tipo):
    """Próximo numero_versao sequencial (1, 2, 3...) da origem no GED."""
    from .models import DocumentoGerado

    ultima = (DocumentoGerado.objects.filter(**{tipo: instance})
              .aggregate(m=Max('numero_versao'))['m']) or 0
    return ultima + 1


def registrar_documento_gerado(instance, pdf_bytes, filename, usuario=None, versao=None):
    """Cria a próxima versão imutável de DocumentoGerado para a origem.

    Fonte de verdade do GED versionado: numero_versao sequencial por origem
    (1, 2, 3...), hash SHA-256 do arquivo e autor da geração. `versao` pode ser
    passada por quem já a calculou (gerar_e_anexar) para não repetir a query.
    """
    from .models import DocumentoGerado

    tipo = _tipo_de(instance)
    versao = versao or _proxima_versao(instance, tipo)
    doc = DocumentoGerado(
        tipo=tipo,
        numero_versao=versao,
        sha256=hashlib.sha256(pdf_bytes).hexdigest(),
        gerado_por=usuario if getattr(usuario, 'is_authenticated', False) else None,
        **{tipo: instance},
    )
    doc.arquivo.save(filename, ContentFile(pdf_bytes), save=False)
    doc.save()
    return doc


def gerar_e_anexar(instance, template_name, context, field_name, usuario=None):
    """Gera o PDF, registra a versão no GED e espelha no FileField legado.

    Retorna (pdf_bytes, filename) — filename é determinístico (via
    nome_arquivo) e já inclui o número de versão, para o chamador reaproveitar
    no download (Content-Disposition).
    """
    from .identidade import nome_arquivo

    pdf_bytes = render_pdf(template_name, context)
    tipo = _tipo_de(instance)
    versao = _proxima_versao(instance, tipo)
    filename = nome_arquivo(instance, versao=versao)
    registrar_documento_gerado(instance, pdf_bytes, filename, usuario, versao=versao)
    save_pdf_to_field(instance, field_name, pdf_bytes, filename)
    return pdf_bytes, filename
