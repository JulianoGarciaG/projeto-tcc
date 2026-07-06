# Objetivo

Atualizar as telas que hoje exibem apenas o "documento gerado atual"
(`documento_gerado`/`arquivo`) para também listar o histórico de versões
disponível em `DocumentoGerado`, permitindo abrir qualquer versão anterior
além da mais recente.

---

# Arquivos afetados

- `templates/contratos/contrato_detail.html`
- `templates/laudos/laudo_detail.html`
- `templates/recibos/recibo_detail.html`
- `templates/ged/documentos.html`
- `imoveis/views.py` (`documentos` — view do GED — e as views `*_detail` de
  Contrato/Laudo/Recibo, para passar as versões ao contexto se ainda não
  vierem via `related_name`)

---

## Documentação relacionada

- docs/04_regras_de_negocio.md
  Documentar que as telas de detalhe/GED agora exibem histórico de versões,
  não apenas o documento mais recente.
- docs/07_design_ui_ux.md
  Sem impacto obrigatório — se o Engineer introduzir um componente visual
  novo (ex.: dropdown/accordion de versões), avaliar se merece registro na
  seção de componentes; caso reutilize elementos já documentados (tabelas,
  botões `btn-outline-*`), sem impacto.

---

# Dependências

- `09-integracao-pdf-versionamento.md` — só há versões para listar depois que
  a geração passar a criá-las.

---

# Detalhamento técnico

## Telas de detalhe (Contrato/Laudo/Recibo)

Hoje (`contrato_detail.html` linha 12-13, `laudo_detail.html` linha 11-12,
`recibo_detail.html` linha 12-13) cada tela mostra um único link:
```html
{% if contrato.documento_gerado %}
<a href="{{ contrato.documento_gerado.url }}">Contrato Gerado (PDF)</a>
{% endif %}
```

Substituir por um bloco que:
1. Mantém o link do documento atual (última versão) em destaque, como hoje
   (não regride a experiência principal).
2. Adiciona uma lista/tabela pequena com o histórico
   (`contrato.versoes_documento.all` — já vem ordenado por `-gerado_em` pela
   `Meta.ordering` do model, ver módulo 07), mostrando: nº da versão, data,
   autor (`gerado_por` — exibir "—" se `None`, caso da migração retroativa),
   link de download.
3. Se `versoes_documento` estiver vazio (nenhum PDF gerado ainda), manter o
   estado atual (nenhum link, sem quebrar o template).

## GED (`templates/ged/documentos.html` + view `documentos`)

Hoje a view `documentos` (`imoveis/views.py`) monta querysets separados por
tipo, filtrando `exclude(documento_gerado='')`/`exclude(arquivo='')`. Duas
opções, decidir com base na complexidade real ao implementar:

- **Opção A (mínima)**: manter a listagem atual (1 linha por
  contrato/laudo/recibo, mostrando a última versão) e adicionar uma coluna
  "Versões" com um link/badge (`{{ objeto.versoes_documento.count }}`) que
  leva à tela de detalhe (onde o histórico completo já está, via item
  anterior).
- **Opção B (completa)**: a view passa a consultar `DocumentoGerado`
  diretamente e listar cada versão como uma linha própria, com filtro por
  tipo/origem.

Recomendação: **Opção A** — menor mudança de estrutura na tela de GED
(que já está organizada por seções de tipo de documento, não por versão),
e o histórico completo já fica acessível via detalhe. A Opção B só se
justifica se houver demanda futura de auditoria centralizada de todas as
versões numa única tela.

## Consideração sobre laudos com anexo manual

`LaudoVistoria.arquivo` é um anexo manual (upload do laudo assinado,
independente do PDF gerado pelo sistema, ver `laudo_anexar_arquivo` em
`imoveis/views.py`) — **não é** o mesmo campo que vira `DocumentoGerado`
(quem vira histórico é `LaudoVistoria.documento_gerado`, o PDF gerado pelo
sistema). Não confundir os dois fluxos ao atualizar `laudo_detail.html`: o
bloco de "Anexo Manual" continua como está, só o bloco de "Laudo Gerado
(PDF)" ganha o histórico de versões.

---

# Critérios de aceite

- [ ] Tela de detalhe de Contrato, Laudo e Recibo mostra o documento atual
      (última versão) e uma lista com o histórico completo de versões
      (número, data, autor, link).
- [ ] Anexo manual do laudo (`LaudoVistoria.arquivo`) não é afetado por esta
      mudança.
- [ ] GED (`/documentos/`) continua funcionando para quem nunca gerou mais de
      1 versão (comportamento idêntico ao atual nesse caso).
- [ ] Nenhuma quebra visual quando `versoes_documento` está vazio (objeto
      criado antes da migração de dados do módulo 09, ou nunca teve PDF
      gerado).

---

# Riscos

- Se a migração de dados do módulo 09 não rodar antes deste módulo em algum
  ambiente, `versoes_documento.all` estará vazio para documentos antigos
  mesmo que `documento_gerado`/`arquivo` esteja preenchido — garantir que o
  bloco "documento atual" sempre usa o campo legado como fallback visual
  (não depende exclusivamente de `versoes_documento` existir).
