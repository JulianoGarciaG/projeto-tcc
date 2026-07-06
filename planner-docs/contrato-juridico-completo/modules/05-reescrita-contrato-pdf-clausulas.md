# Objetivo

Reescrever COMPLETAMENTE `templates/documentos/contrato_pdf.html`,
substituindo o layout de resumo em cards por um instrumento particular
de locação com preâmbulo + 21 cláusulas (I a XXI), texto jurídico
transcrito do `modelo-contrato.pdf` do cliente, com variáveis injetadas
nos pontos indicados (grifos amarelos do modelo).

---

# Arquivos afetados

- `templates/documentos/contrato_pdf.html` (reescrita completa)

NAO alterar `templates/documentos/base_pdf.html` -- esse arquivo e
compartilhado com Laudo e Recibo (fora de escopo). Toda a estrutura
juridica nova (clausulas, paragrafos, paginacao) fica isolada no CSS do
bloco estilos_extra do proprio contrato_pdf.html, assim como o laudo
e o recibo ja isolam seu CSS especifico.

---

## Fonte do texto jurídico (fora do repositório)

O texto literal do preâmbulo e das 21 cláusulas (títulos e corpo) NÃO
está neste plano e não deve ser inventado. Deve ser transcrito
diretamente do arquivo `modelo-contrato.pdf` fornecido pelo cliente
(anexado à conversa original com o Planner — confirmar acesso a esse
arquivo antes de iniciar a implementação). Os campos grifados em
amarelo no modelo são os pontos exatos de inserção de variável.

---

# O que muda em relação ao template atual

- Sai: estrutura de `.sec`/`.fields`/`.cards`/`.note-box`/`.flabel`/`.fval`
  (essas classes continuam em `base_pdf.html` e continuam usadas por
  Laudo/Recibo — não remover de lá).
- Entra: preâmbulo das partes + 21 blocos de cláusula (título + corpo em
  texto corrido justificado), bloco de assinaturas ampliado (Locador
  fixo + Locatário + Fiador(es) com qualificação completa).
- Título do documento (`{% block titulo_doc %}`) passa a depender de
  `contrato.finalidade`:
  `CONTRATO DE LOCAÇÃO {% if contrato.finalidade == 'comercial' %}COMERCIAL{% else %}RESIDENCIAL{% endif %}`
  (escrever literalmente em CAIXA ALTA — `text-transform` não funciona
  no xhtml2pdf, ver `docs/07_design_ui_ux.md` §17).
- `{% block doc_meta %}` continua igual ao atual (`{{ contrato.pk }}` +
  `{{ contrato.criado_em|date:"d/m/Y" }}` — não existe campo de "número
  de contrato" formatado, decisão já confirmada na Rodada 4).

---

# Estrutura sugerida do template

```
{% extends 'documentos/base_pdf.html' %}
{% load imoveis_tags %}

{% block estilos_extra %}
  /* CSS exclusivo das cláusulas do contrato — ver seção "CSS e paginação" abaixo */
{% endblock %}

{% block doc_meta %} ... {% endblock %}
{% block titulo_doc %} ... {% endblock %}

{% block conteudo %}
  <!-- Preâmbulo: LOCADOR (locador fixo) + LOCATÁRIO + FIADOR(ES) -->
  <div class="preambulo">...</div>

  <!-- Cláusulas I a XXI -->
  <div class="clausula">
    <div class="clausula-titulo">CLÁUSULA I — ...</div>
    <p class="clausula-texto">... {{ variavel }} ...</p>
  </div>
  ... (repetir para II a XXI) ...

  <!-- Local/data + assinaturas -->
  <table class="sign-table avoid-break"> ... </table>
{% endblock %}
```

---

# Mapeamento de variáveis → fonte (para os pontos grifados do modelo)

| Dado | Variável Django |
|---|---|
| Locador (fixo, Shelter) | `locador.razao_social`, `locador.cnpj`, `locador.representante_nome`, `locador.representante_rg`, `locador.representante_cpf`, `locador.endereco`, `locador.telefone`, `locador.pix_chave`, `locador.foro` (contexto `locador`, ver módulo 06) |
| Locatário | `contrato.inquilino.nome`, `.qualificacao`, `.cpf`, `.rg` (PF) ou `.cnpj` (PJ, mesma lógica condicional por `contrato.tipo_contrato` já usada no template atual) |
| Imóvel | `contrato.imovel.endereco`, `.numero`, `.complemento`, `.bairro`, `.cidade`; código cadastral = `contrato.imovel.cadastro_prefeitura` |
| Finalidade | `contrato.finalidade` / `contrato.get_finalidade_display` |
| Prazo em meses | `prazo_meses` (contexto calculado pela view, módulo 06) + filtro `meses_extenso` (módulo 01) |
| Valor do aluguel | `contrato.valor_mensal` com filtro `brl` (numérico) e com filtro `valor_extenso` (por extenso, módulo 01) |
| Dia de vencimento | `contrato.dia_vencimento` (numeral) + filtro `dia_extenso` (ordinal por extenso, módulo 01) |
| Local/data de assinatura | `contrato.local_assinatura`, `contrato.data_assinatura` |
| Fiador(es) — cláusula XX | loop sobre `contrato.fiadores.all`: `nome`, `qualificacao`, `endereco`, dados do cônjuge (condicionais — só exibir bloco do cônjuge se preenchido); RG/CPF com fallback de compatibilidade (ver abaixo) |

## Fallback de RG/CPF do fiador (retrocompatibilidade)

Fiadores criados antes da migration do módulo 04 podem não ter `rg`/`cpf`
discretos preenchidos (só o campo legado `rg_cpf`). Usar:

```
{% if f.rg and f.cpf %}
  portador do RG nº {{ f.rg }} e CPF nº {{ f.cpf }}
{% else %}
  portador do RG/CPF nº {{ f.rg_cpf }}
{% endif %}
```

## Múltiplos fiadores

O modelo do cliente pode assumir um único fiador na cláusula XX — manter
o loop sobre `contrato.fiadores.all` (como o template atual já faz) para
não regredir o suporte a múltiplos fiadores já existente; repetir o
bloco de qualificação completa para cada fiador, com espaçamento claro
entre eles (não empilhar tudo sem separação visual). A seção de fiador
(cláusula XX e trecho correspondente do preâmbulo) só aparece se
`contrato.fiadores.all` não for vazio — se o modelo do cliente não
prevê contrato sem fiador, validar esse ponto durante a transcrição
(pode exigir texto condicional adicional não coberto pelo modelo
original).

---

# CSS e paginação A4

Todo o CSS abaixo é específico deste template (`estilos_extra`), não vai
para `base_pdf.html`:

- `.clausula-titulo` — negrito, tamanho levemente maior que o corpo;
  usar `page-break-after: avoid` para não deixar o título "órfão" no
  fim de uma página, separado do início do texto (funcionalidade a
  validar manualmente no xhtml2pdf — módulo 08).
- `.clausula-texto` — `text-align: justify` (parágrafo justificado,
  como um contrato impresso); validar visualmente que o xhtml2pdf
  respeita a justificação (risco, ver abaixo).
- Não aplicar `page-break-inside: avoid` no bloco `.clausula` inteiro —
  cláusulas mais longas que o espaço restante da página gerariam página
  em branco ou comportamento imprevisível no xhtml2pdf. Deixar o texto
  fluir naturalmente entre páginas.
- Reduzir o `font-size` só localmente (`.clausula-texto`, por exemplo
  `10px` ou `9.5px`) se o volume de texto das 21 cláusulas não couber em
  um número razoável de páginas — não alterar o `font-size` do `body`
  em `base_pdf.html` (afetaria Laudo/Recibo).
- Preâmbulo e bloco de assinaturas finais devem usar `avoid-break`
  (classe já definida em `base_pdf.html`) — são blocos curtos, cabem
  inteiros numa página sem risco de página em branco.
- Seguir as armadilhas já documentadas do motor (docs/07_design_ui_ux.md
  §17): text-transform ignorado (escrever CAIXA ALTA literal nos
  títulos das cláusulas e usar o filtro upper em valores dinâmicos em
  maiúsculas), margin com auto não suportado (usar tabela com
  align="center" se algum elemento precisar ser centralizado), célula
  de tabela vazia não desenha borda (usar um espaço protegido se alguma
  tabela for usada dentro de uma cláusula).

---

## Documentação relacionada

- docs/03_modelagem_dados.md
  Sem impacto adicional (campos já documentados pelos módulos 03/04).
- docs/04_regras_de_negocio.md
  Documentar: (1) o PDF de contrato passa a ser um instrumento jurídico
  completo de 21 cláusulas, não mais um resumo; (2) o locador exibido é
  sempre a Shelter (`SHELTER_LOCADOR`), nunca `imovel.proprietario`;
  (3) o título do documento depende de `Contrato.finalidade`.
- docs/07_design_ui_ux.md
  Atualizar a seção 17 (Documentos PDF Gerados) explicando que o PDF de
  Contrato agora tem um layout jurídico próprio (texto corrido,
  cláusulas numeradas, paginação natural) diferente do padrão de cards
  usado por Laudo/Recibo — registrar as armadilhas de paginação/
  justificação encontradas durante a implementação, se houver alguma
  nova além das já catalogadas.

---

# Dependências

- `01-utilitarios-extenso-num2words.md` — filtros valor_extenso,
  meses_extenso, dia_extenso.
- `02-constantes-locador-shelter.md` — dados do locador fixo.
- `03-contrato-model-form-finalidade-assinatura.md` — campos
  finalidade, local_assinatura, data_assinatura.
- `04-fiador-model-form-qualificacao-completa.md` — campos novos de
  Fiador usados na cláusula XX.
- `06-view-context-gerar-pdf.md` — contexto locador e prazo_meses
  precisam existir na view para este template funcionar; pode ser
  implementado em paralelo, mas a validação final depende dos dois.

---

# Critérios de aceite

- [ ] Preâmbulo e 21 cláusulas (I a XXI) presentes no template, com
      títulos e corpo transcritos do modelo-contrato.pdf.
- [ ] Todas as variáveis da tabela de mapeamento inseridas nos pontos
      corretos (conferir contra os grifos amarelos do modelo).
- [ ] Título do documento reflete contrato.finalidade (residencial ou
      comercial).
- [ ] Locador exibido é sempre locador.* (Shelter) — nenhuma referência
      a contrato.imovel.proprietario como locador no PDF.
- [ ] Cláusula XX exibe qualificação completa de cada fiador, com
      fallback de RG/CPF para fiadores antigos (só rg_cpf preenchido).
- [ ] PF vs PJ do locatário continua condicional (mesma lógica do
      template atual: CPF/RG para PF, CNPJ/CPF do responsável para PJ).
- [ ] `python manage.py test imoveis.tests.ContratoPdfTests` — ver
      módulo 07 — 100% verde ao final.
- [ ] Geração manual do PDF (contrato_gerar_pdf) produz um arquivo A4
      com quebras de página limpas entre cláusulas, sem títulos de
      cláusula isolados no rodapé de uma página e sem página em branco
      no meio do documento (validação detalhada no módulo 08).

---

# Riscos

- Volume de texto: 21 cláusulas de texto jurídico podem gerar um
  documento de várias páginas — aceitável (contratos de locação
  impressos normalmente têm múltiplas páginas), mas a paginação precisa
  ficar limpa (sem títulos órfãos, sem cláusulas cortadas de forma
  estranha). Validar manualmente (módulo 08).
- text-align justify no xhtml2pdf: o motor já demonstrou limitações com
  outras propriedades CSS neste projeto (text-transform, margin auto,
  borda por filho em div) — validar visualmente que a justificação de
  parágrafos longos realmente funciona antes de considerar o módulo
  concluído; se não funcionar bem, usar text-align left como fallback
  (documentar a decisão em docs/07_design_ui_ux.md §17 se isso ocorrer).
- page-break-after avoid em .clausula-titulo: suporte do xhtml2pdf a
  controle fino de quebra de página é conhecido por ser limitado — se o
  título continuar "grudando" no rodapé da página anterior, uma
  alternativa é envolver título + primeira linha do corpo num mesmo
  bloco avoid-break pequeno (só o cabeçalho, não a cláusula inteira).
- Retrocompatibilidade do GED: PDFs de contrato já gerados
  (DocumentoGerado com tipo='contrato') permanecem no layout antigo
  para sempre — este módulo não migra documentos já emitidos (ver
  plan.md, Observações gerais).
- Fonte do texto jurídico: se o modelo-contrato.pdf não estiver
  disponível no momento da implementação deste módulo, o trabalho não
  pode prosseguir — sinalizar o bloqueio em vez de inventar texto
  jurídico genérico.
