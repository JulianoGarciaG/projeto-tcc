# Objetivo

Aplicar em laudo_pdf.html a mesma convencao de uppercase literal do modulo
02, adaptar o bloco "Resumo da Vistoria" ao novo padrao de .cards (sem
div.card), incluindo a migracao do border-top colorido por estado para a
td, e corrigir os cabecalhos de .data-table e o rotulo "Testemunhas".

---

# Arquivos afetados

- templates/documentos/laudo_pdf.html

---

## Documentacao relacionada

- docs/07_design_ui_ux.md
  Sem impacto direto (classes atualizadas pelo modulo 01).

---

# Dependencias

Depende do modulo 01 (base-pdf-fundamentos) - mesma razao do modulo 02:
precisa da nova estrutura CSS de .cards antes de alterar o markup.

---

# Implementacao

## 1. Titulo do documento

Antes:

    {% block titulo_doc %}Laudo de Vistoria - {% if laudo.tipo == 'entrada' %}Entrada{% else %}Saida{% endif %}{% endblock %}

Depois:

    {% block titulo_doc %}LAUDO DE VISTORIA - {% if laudo.tipo == 'entrada' %}ENTRADA{% else %}SAIDA{% endif %}{% endblock %}

## 2. Cabecalhos de secao (.sec)

    <div class="sec">Identificacao</div>
    -> <div class="sec">IDENTIFICACAO</div>

    <div class="sec">Resumo da Vistoria</div>
    -> <div class="sec">RESUMO DA VISTORIA</div>

    <div class="sec">Observacoes Gerais</div>
    -> <div class="sec">OBSERVACOES GERAIS</div>

## 3. Labels de campo (.flabel) da secao "Identificacao"

    Tipo de vistoria -> TIPO DE VISTORIA
    Data da vistoria -> DATA DA VISTORIA
    Endereco do imovel -> ENDERECO DO IMOVEL
    Locador -> LOCADOR
    Locatario -> LOCATARIO
    Responsavel pela vistoria -> RESPONSAVEL PELA VISTORIA

## 4. Cabecalhos da tabela de itens (.data-table th)

Antes:

    <tr><th width="34%">Item</th><th width="20%">Estado</th><th>Observacao</th></tr>

Depois:

    <tr><th width="34%">ITEM</th><th width="20%">ESTADO</th><th>OBSERVACAO</th></tr>

(as demais celulas da tabela - nome do item, badge de estado, observacao -
ja usam texto dinamico ou ja estao em caixa alta via filtro upper existente
no template; nao precisam de mudanca.)

## 5. Bloco "Resumo da Vistoria" (cards com borda colorida por estado)

Remover o div.card wrapper. A cor de borda especial de cada cartao (Bom /
Regular / Ruim), que hoje esta em `style="border-top: 3px solid ...;"` no
div.card, passa para a propria td (mantendo tambem o card-label em caixa
alta):

Antes:

    <table class="cards avoid-break">
      <tr>
        <td width="25%"><div class="card"><div class="card-label">Total de itens</div><div class="card-value">{{ resumo.total }}</div></div></td>
        <td width="25%"><div class="card" style="border-top: 3px solid #2E7D32;"><div class="card-label">Bom</div><div class="card-value" style="color: #2E7D32;">{{ resumo.bom }}</div></div></td>
        <td width="25%"><div class="card" style="border-top: 3px solid #9A6B00;"><div class="card-label">Regular</div><div class="card-value" style="color: #9A6B00;">{{ resumo.regular }}</div></div></td>
        <td width="25%"><div class="card" style="border-top: 3px solid #C62828;"><div class="card-label">Ruim</div><div class="card-value" style="color: #C62828;">{{ resumo.ruim }}</div></div></td>
      </tr>
    </table>

Depois:

    <table class="cards avoid-break">
      <tr>
        <td width="25%"><div class="card-label">TOTAL DE ITENS</div><div class="card-value">{{ resumo.total }}</div></td>
        <td width="25%" style="border-top: 3px solid #2E7D32;"><div class="card-label">BOM</div><div class="card-value" style="color: #2E7D32;">{{ resumo.bom }}</div></td>
        <td width="25%" style="border-top: 3px solid #9A6B00;"><div class="card-label">REGULAR</div><div class="card-value" style="color: #9A6B00;">{{ resumo.regular }}</div></td>
        <td width="25%" style="border-top: 3px solid #C62828;"><div class="card-label">RUIM</div><div class="card-value" style="color: #C62828;">{{ resumo.ruim }}</div></td>
      </tr>
    </table>

Este ponto (border-top inline por celula, sobrepondo o border padrao de
.cards td definido no modulo 01) e o unico com risco tecnico especifico
deste modulo - validar visualmente no modulo 05 que a borda colorida de
cima aparece junto com a borda cinza padrao nos outros 3 lados.

## 6. Rotulo "Testemunhas"

Antes:

    <div style="font-size: 9px; text-transform: uppercase; letter-spacing: 1px; color: #888888; margin-top: 44px; margin-bottom: 8px;">Testemunhas</div>

Depois (remover o text-transform inline inutil e escrever o texto ja em
caixa alta):

    <div style="font-size: 9px; letter-spacing: 1px; color: #888888; margin-top: 44px; margin-bottom: 8px;">TESTEMUNHAS</div>

---

# Criterios de aceite

- [ ] Titulo, headers .sec, labels da secao "Identificacao" e cabecalhos da
      tabela de itens aparecem em caixa alta no PDF gerado.
- [ ] Bloco "Resumo da Vistoria" renderiza como 4 cartoes separados, com o
      cartao "Bom"/"Regular"/"Ruim" mantendo a barra superior colorida por
      cima da borda cinza padrao.
- [ ] Rotulo "TESTEMUNHAS" aparece em caixa alta.
- [ ] Nenhuma badge (.badge-bom/.badge-reg/.badge-ruim) ou legenda foi
      alterada - ja estavam corretas antes deste modulo.
- [ ] venv/Scripts/python manage.py test imoveis continua passando.

---

# Riscos

- Mesma observacao de encoding do modulo 02 (usar Edit tool, nunca
  Get-Content/Set-Content).
- O item 5 (border-top colorido na td) e o unico ponto deste modulo sem
  teste isolado previo - conferir com atencao extra no modulo 05.
