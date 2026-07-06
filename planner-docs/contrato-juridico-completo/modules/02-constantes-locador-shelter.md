# Objetivo

Definir os dados fixos do locador jurídico (Shelter) como constante em
`core/settings.py`, para uso no PDF de contrato — o locador exibido no
documento deixa de ser `contrato.imovel.proprietario` e passa a ser
sempre a Shelter.

---

# Arquivos afetados

- `core/settings.py` (nova constante)

---

# Especificação

Adicionar em `core/settings.py`, próximo às demais constantes de
configuração (não precisa ser `.env`-driven — são dados fixos de
identidade jurídica da empresa, não configuração de ambiente/infra,
diferente de `DB_ENGINE`/`STORAGE_BACKEND`):

```python
# Dados fixos do locador jurídico (Shelter) — usados no PDF de contrato
# (imoveis/views.py:_gerar_pdf_contrato). O locador do contrato gerado é
# sempre a Shelter, independentemente do Proprietario cadastrado do imóvel.
SHELTER_LOCADOR = {
    'razao_social': 'SHELTER ADMINISTRADORA DE BENS PRÓPRIOS LTDA.',
    'cnpj': '65.764.617/0001-29',
    'representante_nome': 'JOSÉ MÍLTON GARCIA',
    'representante_rg': '19.249.055',
    'representante_cpf': '493.583.406-49',
    'endereco': 'Rua São Paulo, 134, Centro, Poços de Caldas/MG',
    'telefone': '035-3722-1838',
    'pix_chave': '65.764.617/0001-29',
    'foro': 'Comarca de Poços de Caldas, MG',
}
```

O valor exato de cada chave já foi definido pelo usuário e não deve ser
alterado. `pix_chave` replica o CNPJ (mesma chave PIX informada).

---

## Documentação relacionada

- docs/03_modelagem_dados.md
  Adicionar uma nota curta explicando que o "locador" do contrato NÃO é
  um model/tabela — é uma constante fixa em `core/settings.py`
  (`SHELTER_LOCADOR`), consumida só pelo PDF do contrato.
- docs/04_regras_de_negocio.md
  Documentar a regra: o locador exibido no contrato gerado é sempre a
  Shelter (dados fixos), não o `Proprietario` cadastrado do imóvel — o
  `Proprietario` continua sendo usado normalmente no resto do sistema.
- docs/07_design_ui_ux.md
  Sem impacto.

---

# Dependências

Nenhuma — módulo independente.

---

# Critérios de aceite

- [ ] `SHELTER_LOCADOR` definida em `core/settings.py` com as 9 chaves
      acima, valores exatamente como especificado.
- [ ] Nenhum outro arquivo alterado neste módulo (o consumo da constante
      é feito no módulo 06 — view — e no módulo 05 — template).

---

# Riscos

- Nenhum risco técnico relevante — é uma constante estática. Único
  cuidado: se os dados fixos da Shelter mudarem no futuro (novo
  endereço, novo representante), será necessário editar código
  (`core/settings.py`) em vez de um cadastro via admin — aceitável pela
  natureza pouco mutável desses dados, mas vale registrar como
  observação de manutenção.
