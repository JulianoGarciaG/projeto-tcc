"""Data migration: registra os PDFs ja existentes nos campos legados
(Contrato.documento_gerado, LaudoVistoria.documento_gerado, Recibo.arquivo)
retroativamente como versao 1 de DocumentoGerado.

O arquivo legado NAO e copiado: a versao 1 referencia o mesmo nome/caminho
no storage. O hash SHA-256 e calculado a partir do arquivo, quando legivel;
se o arquivo estiver ausente no storage, o registro e criado com hash vazio.
"""
import hashlib

from django.db import migrations


def registrar_versao_1(apps, schema_editor):
    DocumentoGerado = apps.get_model('imoveis', 'DocumentoGerado')
    Contrato = apps.get_model('imoveis', 'Contrato')
    LaudoVistoria = apps.get_model('imoveis', 'LaudoVistoria')
    Recibo = apps.get_model('imoveis', 'Recibo')

    def hash_arquivo(field_file):
        try:
            with field_file.open('rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except (OSError, ValueError):
            return ''

    origens = [
        ('contrato', Contrato, 'documento_gerado'),
        ('laudo', LaudoVistoria, 'documento_gerado'),
        ('recibo', Recibo, 'arquivo'),
    ]
    for tipo, modelo, campo in origens:
        qs = modelo.objects.exclude(**{campo: ''}).exclude(**{f'{campo}__isnull': True})
        for obj in qs:
            arquivo = getattr(obj, campo)
            doc = DocumentoGerado(tipo=tipo, numero_versao=1,
                                  sha256=hash_arquivo(arquivo),
                                  **{tipo: obj})
            # Referencia o arquivo legado existente, sem copiar.
            doc.arquivo.name = arquivo.name
            doc.save()


def desfazer(apps, schema_editor):
    DocumentoGerado = apps.get_model('imoveis', 'DocumentoGerado')
    DocumentoGerado.objects.filter(numero_versao=1).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('imoveis', '0009_documentogerado'),
    ]

    operations = [
        migrations.RunPython(registrar_versao_1, desfazer),
    ]
