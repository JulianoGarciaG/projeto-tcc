# Objetivo

Validar visualmente, gerando PDFs reais via `pisa`/`xhtml2pdf`, que a
réplica fiel do layout dos mockups (`docs/pdf-models/*.html`) renderiza
identicamente nos três documentos, cobrindo casos com dados mínimos e dados
completos/múltiplos, e confirmando especificamente os 2 pontos de risco real
do motor pisa identificados no módulo 01 (não há "problemas de CSS não
suportado" a resolver -- os mockups já são CSS 2.1 puro -- mas sim 2
combinações que precisam ser vistas no PDF de fato).

---

# Arquivos afetados

Nenhum arquivo de código é alterado neste módulo — é uma etapa de verificação
manual/exploratória. Pode gerar arquivos de PDF temporários fora do
versionamento (ex.: baixados via navegador, não commitados).

---

## Documentação relacionada

- Nenhuma. Se a validação revelar necessidade de ajuste de CSS, o ajuste
  volta para os módulos 01-04 (não é um módulo de documentação).

---

# Dependências

- `05-ajuste-testes.md` — só validar manualmente depois que a suíte
  automatizada estiver 100% verde (evita retrabalho).

---

# Roteiro de validação

1. Com o servidor rodando (`venv/Scripts/python manage.py runserver`), logar
   no sistema e navegar até um Contrato existente (ou criar um com fiador(es),
   observações preenchidas, imóvel com `numero`/`complemento`/`area_m2`/
   `matricula` preenchidos) → clicar em "Regerar PDF" → abrir o PDF baixado.
2. Repetir com um Contrato **mínimo** (sem fiador, sem observações, sem
   `area_m2`/`matricula` no imóvel, tipo PJ) → conferir que as seções
   condicionais somem corretamente e nada quebra.
3. Repetir para um Laudo de Vistoria:
   - Um laudo usando o catálogo completo (5 cômodos / 32 itens, seed da
     migração 0004) com pelo menos um item em cada estado (bom/regular/ruim),
     2+ testemunhas e observações gerais preenchidas → conferir paginação,
     badges coloridos, resumo com números corretos, quebra de página entre
     cômodos.
   - Um laudo mínimo (poucos itens, 0 testemunhas, sem observações gerais,
     sem local/data de assinatura) → conferir que as seções condicionais
     somem.
4. Repetir para um Recibo:
   - Recibo completo (todas as composições de valor, parcela X/Y, assinante
     preenchido, período completo).
   - Recibo mínimo (só quantia e imóvel) → conferir que "Composição do Valor"
     e "Assinatura" somem quando vazios.
5. Conferir em todos os PDFs, comparando lado a lado com o mockup
   correspondente:
   - Logo aparece corretamente (não fica quebrada/ausente).
   - Régua dourada, cores de seção e badges renderizam com as cores exatas do
     mockup (que já correspondem à paleta de `docs/07_design_ui_ux.md`).
   - **Ponto de risco 1**: `letter-spacing` combinado com
     `text-transform: uppercase` (título, `.sec`, `.flabel`, `.card-label`)
     não estoura a largura da célula nem difere visualmente do mockup. Se
     divergir, ajustar pontualmente (reduzir/remover `letter-spacing` naquele
     seletor específico) sem alterar a estrutura de tabelas.
   - **Ponto de risco 2**: `border-collapse: collapse` em tabelas aninhadas
     (`.fields` dentro de célula de `.cards`; `.data-table` dentro do bloco de
     cômodo do laudo) não introduz bordas duplicadas/desalinhadas. Se
     divergir, ajustar pontualmente a tabela aninhada específica.
   - Quebras de página não cortam uma seção "no meio" (checar `avoid-break`
     nos blocos relevantes, especialmente cômodos do laudo).
   - PDF continua sendo salvo no campo correto do model (`documento_gerado`
     para Contrato/Laudo, `arquivo` para Recibo) — conferir na tela de
     detalhe/GED (`/documentos/`) que o arquivo gerado aparece. **Se o
     módulo 09 (GED versionado) já tiver sido implementado nesta rodada**,
     conferir também que uma nova versão em `DocumentoGerado` foi criada a
     cada regeração (ver `10-ged-listagem-versoes.md`).

---

# Critérios de aceite

- [ ] Os 3 documentos (cenário completo e mínimo, total de 6 PDFs) foram
      gerados e inspecionados visualmente, batendo 1:1 com o mockup
      correspondente (mesmas cores, espaçamentos e estrutura).
- [ ] Os 2 pontos de risco (letter-spacing+uppercase; border-collapse em
      tabelas aninhadas) foram checados no PDF real e, se necessário,
      ajustados pontualmente.
- [ ] Logo carrega em todos os PDFs.
- [ ] GED (`/documentos/`) continua listando os documentos gerados
      normalmente.

---

# Riscos

- Diferenças sutis de renderização entre o preview HTML (navegador) e o PDF
  real do pisa só aparecem nesta etapa — reservar tempo para pequenos ajustes
  de CSS pontuais nos módulos 01-04 caso os 2 pontos de risco (letter-spacing
  +uppercase; border-collapse em tabelas aninhadas) não renderizem fielmente
  ao mockup.
