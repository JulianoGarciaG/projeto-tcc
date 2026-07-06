# Objetivo

Aplicar em recibo_pdf.html a mesma convencao de uppercase literal dos
modulos 02/03. Este documento nao usa o bloco .cards (nao ha mudanca
estrutural aqui, so texto).

---

# Arquivos afetados

- templates/documentos/recibo_pdf.html

---

## Documentacao relacionada

- docs/07_design_ui_ux.md
  Sem impacto.

---

# Dependencias

Depende do modulo 01 apenas pela convencao geral estabelecida (comentario
no CSS) - nao ha dependencia estrutural de CSS, ja que recibo_pdf.html nao
usa .cards nem .doc-title-underline (ambos ja neutralizados por overrides
proprios do template: `{% block titulo_underline %}{% endblock %}`).

---

# Implementacao

## 1. Titulo do documento

Antes:

    {% block titulo_doc %}Recibo{% if recibo.parcela_atual and recibo.parcela_total %} - Parcela {{ recibo.parcela_atual }}/{{ recibo.parcela_total }}{% endif %}{% endblock %}

Depois:

    {% block titulo_doc %}RECIBO{% if recibo.parcela_atual and recibo.parcela_total %} - PARCELA {{ recibo.parcela_atual }}/{{ recibo.parcela_total }}{% endif %}{% endblock %}

## 2. Cabecalho de secao (.sec)

    <div class="sec">Composicao do Valor</div>
    -> <div class="sec">COMPOSICAO DO VALOR</div>

## 3. Rotulo "Quantia recebida"

Antes:

    <div style="font-size: 9px; text-transform: uppercase; letter-spacing: 1.5px; color: #9A6B00; font-weight: bold;">Quantia recebida</div>

Depois (remover o text-transform inline inutil, texto ja em caixa alta):

    <div style="font-size: 9px; letter-spacing: 1.5px; color: #9A6B00; font-weight: bold;">QUANTIA RECEBIDA</div>

## 4. Labels de campo (.flabel)

    Imovel -> IMOVEL
    Recebemos de -> RECEBEMOS DE
    Periodo correspondente -> PERIODO CORRESPONDENTE
    Vencimento -> VENCIMENTO

---

# Criterios de aceite

- [ ] Titulo, header .sec "COMPOSICAO DO VALOR", rotulo "QUANTIA RECEBIDA"
      e todos os labels .flabel aparecem em caixa alta no PDF gerado.
- [ ] Nenhum valor (.fval, quantia, somatorio) foi alterado.
- [ ] venv/Scripts/python manage.py test imoveis continua passando.

---

# Riscos

- Mesma observacao de encoding dos modulos 02/03 (usar Edit tool, nunca
  Get-Content/Set-Content).
- Baixo risco geral - este e o modulo mais simples do plano (sem mudanca
  estrutural de CSS/markup, so texto).
