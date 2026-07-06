# Objetivo

Checklist de validação manual do PDF de contrato gerado, comparando
com o `modelo-contrato.pdf` do cliente e conferindo o comportamento em
folha A4, antes de considerar o plano concluído.

---

# Arquivos afetados

Nenhum (módulo de validação — não produz código).

---

# Checklist

## Conteúdo jurídico

- [ ] Preâmbulo e as 21 cláusulas (I a XXI) presentes, na mesma ordem e
      com os mesmos títulos do `modelo-contrato.pdf`.
- [ ] Nenhum campo grifado em amarelo do modelo ficou sem variável
      (conferir cláusula por cláusula contra o PDF original do cliente).
- [ ] Locador exibido é sempre a Shelter (razão social, CNPJ,
      representante, endereço, telefone, PIX, foro) — gerar o PDF de um
      contrato cujo imóvel tenha um `Proprietario` diferente e confirmar
      que o proprietário NÃO aparece como locador.
- [ ] Título do documento muda corretamente entre
      "CONTRATO DE LOCAÇÃO RESIDENCIAL" e "... COMERCIAL" ao alternar
      `Contrato.finalidade`.

## Valores e extenso

- [ ] Valor do aluguel aparece corretamente em número (`R$ 1.500,00`) e
      por extenso (`"mil e quinhentos reais"`) no ponto do texto onde o
      modelo pede.
- [ ] Prazo do contrato em meses aparece corretamente por extenso
      (conferir contra `data_inicio`/`data_fim` de um contrato de teste
      com prazo conhecido, ex.: 12 meses).
- [ ] Dia de vencimento aparece como numeral + ordinal por extenso
      (ex.: `"5º (quinto)"`), testando pelo menos um valor de 1 dígito e
      um de 2 dígitos (ex.: dia 1 e dia 25).
- [ ] Datas do preâmbulo/cláusulas e da assinatura aparecem por extenso
      com o mês em maiúscula inicial (ex.: `"1 de Junho de 2026"`).

## Fiador(es)

- [ ] Contrato com um fiador — qualificação completa aparece na
      cláusula XX (nome, RG, CPF, endereço, cônjuge se houver).
- [ ] Contrato com dois ou mais fiadores — todos aparecem, com
      separação visual clara entre eles.
- [ ] Contrato sem fiador — a seção correspondente não aparece
      (nem no preâmbulo nem na cláusula XX), sem deixar título "solto".
- [ ] Fiador legado (só `rg_cpf` preenchido, sem `rg`/`cpf` discretos)
      — o fallback do módulo 05 exibe o RG/CPF combinado sem gerar erro
      nem texto quebrado.

## Paginação A4

- [ ] Documento imprime/exporta corretamente em folha A4
      (`@page { size: A4; margin: 2cm; }` de `base_pdf.html`).
- [ ] Nenhum título de cláusula fica isolado no rodapé de uma página,
      separado do início do seu próprio texto.
- [ ] Nenhuma página em branco no meio do documento.
- [ ] Texto justificado (`text-align: justify`) renderiza de forma
      legível, sem espaçamento estranho entre palavras — se não
      funcionar bem, confirmar que o fallback (`text-align: left`) foi
      aplicado e documentado em `docs/07_design_ui_ux.md` §17.
- [ ] Bloco de assinaturas (Locador, Locatário, Fiador(es)) não é
      cortado ao meio entre duas páginas.

## Regressão e retrocompatibilidade

- [ ] `python manage.py test imoveis` — 100% verde.
- [ ] PDFs de Laudo e Recibo continuam idênticos a antes (nenhuma
      alteração visual, já que `base_pdf.html` não foi tocado).
- [ ] Um `DocumentoGerado` de contrato já existente (gerado antes deste
      plano) continua acessível na central GED (`/documentos/`) e abre
      normalmente no layout antigo — confirma que o versionamento não
      tenta "atualizar" documentos antigos para o novo layout.
- [ ] Gerar um novo PDF do mesmo contrato (botão "Regerar PDF") cria uma
      nova versão no GED, agora no layout jurídico novo, sem afetar a
      versão anterior.

---

## Documentação relacionada

- docs/03_modelagem_dados.md
  Sem impacto (checklist não altera modelagem).
- docs/04_regras_de_negocio.md
  Sem impacto adicional além do já coberto pelos módulos 02/05.
- docs/07_design_ui_ux.md
  Registrar nesta seção qualquer achado novo de compatibilidade do
  xhtml2pdf encontrado durante esta validação (ex.: comportamento real
  de `text-align: justify` e `page-break-after: avoid`), seguindo o
  mesmo padrão de documentação das armadilhas já catalogadas na seção 17.

---

# Dependências

- `05-reescrita-contrato-pdf-clausulas.md`
- `06-view-context-gerar-pdf.md`
- `07-atualizacao-testes.md`

---

# Critérios de aceite

- [ ] Todos os itens do checklist acima marcados.
- [ ] Qualquer desvio encontrado frente ao `modelo-contrato.pdf` foi
      corrigido no módulo 05 antes de finalizar (ou formalmente
      registrado como decisão consciente, se for um ajuste necessário
      por limitação do xhtml2pdf).

---

# Riscos

- Validação manual depende de acesso ao `modelo-contrato.pdf` original
  para comparação lado a lado — sem ele, a validação fica limitada a
  "o documento é consistente/legível", sem garantir fidelidade 1:1 ao
  modelo do cliente.
- Limitações do xhtml2pdf com CSS (já documentadas em
  `docs/07_design_ui_ux.md` §17) podem exigir mais uma rodada de ajuste
  fino no template do módulo 05 depois desta validação — se isso
  ocorrer, é esperado e não indica falha de planejamento.
