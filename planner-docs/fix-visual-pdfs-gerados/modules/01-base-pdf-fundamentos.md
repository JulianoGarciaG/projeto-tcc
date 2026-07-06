# Objetivo

Corrigir em base_pdf.html os dois problemas estruturais confirmados por
teste (sublinhado do titulo invisivel; bloco de cartoes renderizando como
grade de tabela) e documentar, via comentario no CSS, a convencao obrigatoria
de usar texto literal em CAIXA ALTA (ou filtro upper) em vez de depender de
text-transform: uppercase, ja que essa propriedade e ignorada pelo
xhtml2pdf. Este modulo e a base da qual os modulos 02/03/04 dependem.

---

# Arquivos afetados

- templates/documentos/base_pdf.html

---

## Documentacao relacionada

- docs/07_design_ui_ux.md
  Secao 17 (Documentos PDF Gerados) lista as classes CSS comuns dos PDFs,
  incluindo .card (singular). Apos este modulo essa classe deixa de existir
  (o estilo passa a viver em .cards td) - atualizar a lista de classes.

---

# Dependencias

Nenhuma. Este e o modulo raiz.

---

# Implementacao

## 1. Sublinhado do titulo (.doc-title-underline)

Causa confirmada por teste: margin: 10px auto 0 auto nao e suportado pelo
xhtml2pdf - o token auto e convertido para 0 (xhtml2pdf/util.py, funcao
getSize). Um div vazio com width fixo e margin automatico nao e
centralizado nem desenhado - em teste isolado a barra nao aparece em lugar
nenhum da pagina.

Padrao comprovado por teste (renderizado localmente e validado
visualmente): trocar o div vazio por uma table align="center" de uma
celula - o atributo HTML align em table E suportado nativamente pelo
xhtml2pdf (tables.py, repassado como hAlign do flowable) e centraliza a
tabela corretamente.

Antes (base_pdf.html, dentro de .doc-title-wrap):

    <div class="doc-title-wrap">
      <div class="doc-title">{% block titulo_doc %}{% endblock %}</div>
      {% block titulo_underline %}<div class="doc-title-underline"></div>{% endblock %}
    </div>

Depois:

    <div class="doc-title-wrap">
      <div class="doc-title">{% block titulo_doc %}{% endblock %}</div>
      {% block titulo_underline %}
      <table align="center" class="doc-title-underline-table"><tr>
        <td class="doc-title-underline">&nbsp;</td>
      </tr></table>
      {% endblock %}
    </div>

E no CSS (substituir a regra .doc-title-underline atual):

    /* antes */
    .doc-title-underline { width: 54px; height: 2px; background-color: #F2B441; margin: 10px auto 0 auto; font-size: 1px; }

    /* depois */
    .doc-title-underline-table { margin-top: 10px; }
    .doc-title-underline { width: 54pt; height: 2px; background-color: #F2B441; font-size: 1px; line-height: 1px; }

Importante: manter o "&nbsp;" dentro do td (celula sem nenhum conteudo pode
nao alocar altura). O bloco titulo_underline continua sobrescrevivel -
recibo_pdf.html ja faz um override em branco desse bloco para suprimir a
barra e NAO precisa de nenhuma mudanca por causa deste modulo.

## 2. Bloco de cartoes (.cards / .card / .card-label / .card-value)

Causa confirmada por teste: quando um div.card com border envolve dois
divs filhos (.card-label e .card-value), o xhtml2pdf desenha uma borda ao
redor de cada filho individualmente (dois retangulos empilhados) em vez de
uma unica caixa ao redor dos dois - visualmente indistinguivel de uma
tabela HTML generica com grade em todas as celulas. Reproduzido em teste
isolado com o CSS/HTML atual, byte a byte.

Correcao comprovada por teste: mover border/padding para a td da tabela
.cards (celula de tabela usa o comando BOX do TableStyle do ReportLab -
trata a celula inteira como uma unica caixa, sem esse problema) e remover
o div.card - .card-label/.card-value passam a ser filhos diretos da td.

CSS antes:

    .cards { width: 100%; border-collapse: collapse; text-align: center; }
    .cards td { padding: 2px; }
    .card { border: 1px solid #E0E0E0; padding: 10px 6px; }
    .card-label { font-size: 8px; letter-spacing: 0.5px; color: #888888; text-transform: uppercase; }
    .card-value { font-size: 14px; font-weight: bold; color: #3A3A3A; margin-top: 4px; }

CSS depois (valores confirmados por teste local - manter exatamente):

    .cards { width: 100%; border-collapse: separate; border-spacing: 2px; text-align: center; }
    .cards td { border: 1px solid #E0E0E0; padding: 10px 6px; }
    .card-label { font-size: 8px; letter-spacing: 0.5px; color: #888888; text-transform: uppercase; }
    .card-value { font-size: 14px; font-weight: bold; color: #3A3A3A; margin-top: 4px; }

A regra .card e removida (classe deixa de ser usada em qualquer template).

Markup HTML de exemplo (o div.card unificador desaparece; os templates
filhos que usam .cards - modulos 02 e 03 - precisam remover esse wrapper):

    <!-- antes -->
    <td width="25%"><div class="card"><div class="card-label">Aluguel mensal</div><div class="card-value">R$ 2.500,00</div></div></td>

    <!-- depois -->
    <td width="25%"><div class="card-label">ALUGUEL MENSAL</div><div class="card-value">R$ 2.500,00</div></td>

Nota: no laudo, alguns cartoes do "Resumo da Vistoria" aplicam uma cor de
borda superior por estado (style com border-top). Esse style inline deve
migrar do antigo div.card style="..." para a td style="..." - detalhado no
modulo 03.

## 3. Convencao de uppercase (comentario no CSS, sem mudanca de regra)

text-transform nao e reconhecido pelo xhtml2pdf (confirmado: a propriedade
nao consta na lista attrNames do parser da lib). As regras CSS que ja usam
text-transform: uppercase (.doc-title, .sec, .flabel, .card-label,
.data-table th) permanecem no CSS sem alteracao (inofensivas, documentam a
intencao visual e nao quebram nada caso uma versao futura do xhtml2pdf
passe a suportar a propriedade) - mas todo texto inserido nesses
elementos, nos templates filhos, deve estar literalmente em caixa alta
(texto estatico) ou usar o filtro Django upper (valor dinamico).

Adicionar este comentario logo acima do bloco style de base_pdf.html
(proximo ao comentario existente sobre a paleta):

    IMPORTANTE (xhtml2pdf nao suporta text-transform):
    as regras text-transform: uppercase abaixo (.doc-title, .sec, .flabel,
    .card-label, .data-table th) NAO tem efeito no PDF gerado - a propriedade
    e ignorada silenciosamente pelo motor. Os templates filhos (contrato/laudo/
    recibo) devem escrever o texto ja em caixa alta (literal, para conteudo
    estatico) ou aplicar o filtro upper (para valores dinamicos). As regras
    CSS foram mantidas como documentacao da intencao visual.

---

# Criterios de aceite

- [ ] .doc-title-underline renderiza como barra laranja centralizada sob o
      titulo, em Contrato e Laudo (recibo continua sem barra, sem mudancas).
- [ ] Bloco de cartoes (.cards) renderiza como caixas individuais separadas
      (uma borda por cartao, com espacamento visivel entre elas), sem efeito
      de grade de tabela generica.
- [ ] Classe .card nao existe mais em base_pdf.html.
- [ ] Comentario sobre a limitacao de text-transform presente no CSS.
- [ ] venv/Scripts/python manage.py test imoveis continua passando (72 testes).

---

# Riscos

- Templates filhos (contrato_pdf.html, laudo_pdf.html) ainda usam
  div.card ate que os modulos 02/03 sejam aplicados - este modulo sozinho
  quebra visualmente o bloco de cartoes desses dois documentos (a div orfa
  sem CSS correspondente perde padding/borda). Implementar 01 e 02/03 na
  mesma sessao de trabalho, sem gerar PDF real entre um e outro.
- Editar base_pdf.html so com a ferramenta de edicao (Edit tool) - nunca
  Get-Content/Set-Content do PowerShell (risco de corromper UTF-8, ver
  CLAUDE.md).
