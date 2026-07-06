# Objetivo

Aplicar em contrato_pdf.html a convencao de uppercase literal (texto
estatico em CAIXA ALTA / valores dinamicos com filtro upper) estabelecida no
modulo 01, e adaptar o markup do bloco "Condicoes da Locacao" ao novo padrao
de .cards (sem o div.card wrapper).

---

# Arquivos afetados

- templates/documentos/contrato_pdf.html

---

## Documentacao relacionada

- docs/07_design_ui_ux.md
  Sem impacto direto (a secao 17 ja e atualizada pelo modulo 01, que e onde
  a mudanca estrutural de classes acontece).

---

# Dependencias

Depende do modulo 01 (base-pdf-fundamentos) - a nova estrutura CSS de
.cards/.card-label/.card-value precisa estar em base_pdf.html antes deste
modulo alterar o markup que a consome.

---

# Implementacao

## 1. Titulo do documento

Antes:

    {% block titulo_doc %}Contrato de Locacao de Imovel{% endblock %}

Depois:

    {% block titulo_doc %}CONTRATO DE LOCACAO DE IMOVEL{% endblock %}

(usar acentuacao correta do portugues ao aplicar: "CONTRATO DE LOCACAO DE
IMOVEL" -> escrever com os acentos originais do texto atual, apenas em caixa
alta.)

## 2. Cabecalhos de secao (.sec)

Trocar o texto estatico de cada div.sec por caixa alta. Onde ha conteudo
dinamico dentro do proprio .sec (o span.sec-note e o pluralize de
"Fiador"), aplicar upper tambem no valor dinamico, ja que text-transform
nao tem efeito e o .sec-note NAO reseta a caixa (so reseta peso/cor/
letter-spacing) - no mockup, em um navegador real, o texto do .sec-note
tambem sai em caixa alta por heranca do .sec pai; a paridade 1:1 exige
reproduzir isso manualmente.

Antes -> Depois (5 ocorrencias):

    <div class="sec">Informacoes do Imovel</div>
    -> <div class="sec">INFORMACOES DO IMOVEL</div>

    <div class="sec">Informacoes do Locatario <span class="sec-note">({{ contrato.get_tipo_contrato_display }})</span></div>
    -> <div class="sec">INFORMACOES DO LOCATARIO <span class="sec-note">({{ contrato.get_tipo_contrato_display|upper }})</span></div>

    <div class="sec">Condicoes da Locacao</div>
    -> <div class="sec">CONDICOES DA LOCACAO</div>

    <div class="sec">Fiador{{ contrato.fiadores.all|length|pluralize:"es" }}</div>
    -> <div class="sec">FIADOR{{ contrato.fiadores.all|length|pluralize:"ES" }}</div>

    <div class="sec">Observacoes</div>
    -> <div class="sec">OBSERVACOES</div>

(o segundo `pluralize` recebe diretamente a string ja maiuscula "ES" como
argumento - nao precisa de filtro upper adicional.)

## 3. Labels de campo (.flabel)

Trocar todo texto estatico dentro de div.flabel para caixa alta. Lista
completa de ocorrencias no arquivo (nao alterar os valores dentro de
div.fval, so os labels):

    Tipo -> TIPO
    Area privativa -> AREA PRIVATIVA
    Endereco -> ENDERECO
    Cidade -> CIDADE
    Matricula -> MATRICULA
    Locador / Proprietario -> LOCADOR / PROPRIETARIO
    CPF / CNPJ -> CPF / CNPJ (ja e caixa alta, sem mudanca)
    Nome{% if ... %} / Razao Social{% endif %} completo -> mesma logica, em caixa alta: NOME{% if contrato.tipo_contrato == 'PJ' %} / RAZAO SOCIAL{% else %} COMPLETO{% endif %}
    Qualificacao -> QUALIFICACAO
    CNPJ -> CNPJ (ja e caixa alta)
    CPF do Responsavel -> CPF DO RESPONSAVEL
    CPF -> CPF (ja e caixa alta)
    RG -> RG (ja e caixa alta)
    Telefone -> TELEFONE
    E-mail -> E-MAIL
    Nome (fiador) -> NOME
    RG / CPF -> RG / CPF (ja e caixa alta)
    Garantia oferecida -> GARANTIA OFERECIDA

Atencao ao label composto de Nome/Locatario (linha com if/else de
tipo_contrato) - manter a logica condicional existente, so envolver cada
ramo em caixa alta.

## 4. Bloco "Condicoes da Locacao" (cards)

Remover o div.card wrapper (classe removida no modulo 01) e colocar
card-label/card-value direto na td, com o label ja em caixa alta:

Antes:

    <table class="cards avoid-break">
      <tr>
        <td width="25%"><div class="card"><div class="card-label">Aluguel mensal</div><div class="card-value">R$ {{ contrato.valor_mensal|brl }}</div></div></td>
        <td width="25%"><div class="card"><div class="card-label">Vencimento</div><div class="card-value">Dia {{ contrato.dia_vencimento }}</div></div></td>
        <td width="25%"><div class="card"><div class="card-label">Inicio</div><div class="card-value">{{ contrato.data_inicio|date:"d/m/Y" }}</div></div></td>
        <td width="25%"><div class="card"><div class="card-label">Termino</div><div class="card-value">{{ contrato.data_fim|date:"d/m/Y" }}</div></div></td>
      </tr>
    </table>

Depois:

    <table class="cards avoid-break">
      <tr>
        <td width="25%"><div class="card-label">ALUGUEL MENSAL</div><div class="card-value">R$ {{ contrato.valor_mensal|brl }}</div></td>
        <td width="25%"><div class="card-label">VENCIMENTO</div><div class="card-value">Dia {{ contrato.dia_vencimento }}</div></td>
        <td width="25%"><div class="card-label">INICIO</div><div class="card-value">{{ contrato.data_inicio|date:"d/m/Y" }}</div></td>
        <td width="25%"><div class="card-label">TERMINO</div><div class="card-value">{{ contrato.data_fim|date:"d/m/Y" }}</div></td>
      </tr>
    </table>

(o valor "Dia {{ ... }}" nao precisa de upper - "Dia" no mockup permanece
em texto normal dentro do card-value, que nao tem text-transform.)

---

# Criterios de aceite

- [ ] Titulo, todos os headers .sec e todos os labels .flabel/.card-label
      aparecem em caixa alta no PDF gerado (nao dependem mais de CSS
      text-transform).
- [ ] Bloco "Condicoes da Locacao" renderiza como 4 cartoes separados (ver
      criterio equivalente do modulo 01).
- [ ] Nenhum texto de valor (.fval/.card-value) foi alterado - so labels e
      titulos estaticos/dinamicos indicados acima.
- [ ] venv/Scripts/python manage.py test imoveis continua passando.

---

# Riscos

- Editar contrato_pdf.html so com a ferramenta de edicao (Edit tool) -
  arquivo tem muitos acentos (titulo, secoes) e o risco de corromper UTF-8
  usando ferramentas de shell no Windows e real (ver CLAUDE.md).
- Facil esquecer um label na lista da secao 3 (sao ~15 ocorrencias) -
  conferir contra o arquivo atual linha a linha antes de finalizar.
