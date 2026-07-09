# Objetivo

Atualizar a secao "10. Autenticacao e Controle de Acesso" de
docs/04_regras_de_negocio.md para descrever o modelo de 3 perfis
(Admin/Owner/Comum) implementado pelos modulos 1-4, substituindo a
descricao binaria atual (is_staff apenas).

Este modulo e deliberadamente o unico ponto de edicao dessa secao - os
modulos 1 a 5 nao fazem delta de documentacao proprio, para evitar edicoes
fragmentadas/conflitantes no mesmo paragrafo por janelas diferentes.

---

# Arquivos afetados

- docs/04_regras_de_negocio.md - secao 10 (paragrafo "Autenticacao e
  Controle de Acesso").

---

# Dependencias

Depende dos modulos 01, 02, 03 e 04 (documenta o comportamento final ja
implementado - conferir o codigo real antes de escrever, nao assumir).

---

# Leituras adicionais

Nenhuma alem do proprio docs/04_regras_de_negocio.md (secao 10 atual, ja
lida durante o planejamento - conteudo below deve ser adaptado ao texto
real encontrado la, nao sobrescrito as cegas).

---

# Delta sugerido

Substituir o conteudo atual da secao 10:

```
- Todas as views exigem autenticacao (@login_required).
- Usuarios nao autenticados sao redirecionados para /login/.
- O painel administrativo Django (/admin/) e restrito a usuarios com
  is_staff = True.
- Apos login bem-sucedido, o usuario e redirecionado para / (dashboard).
- Apos logout, o usuario e redirecionado para /login/.
```

por uma versao que preserva essas 5 regras (ainda validas) e acrescenta o
modelo de perfis:

```
- Todas as views exigem autenticacao (@login_required).
- Usuarios nao autenticados sao redirecionados para /login/.
- O painel administrativo Django (/admin/) e restrito a usuarios com
  is_staff = True.
- Apos login bem-sucedido, o usuario e redirecionado para / (dashboard).
- Apos logout, o usuario e redirecionado para /login/.

**Perfis de usuario** (Group do Django, atribuidos somente via /admin/):

| Perfil | Como e identificado | Acesso |
|---|---|---|
| Admin | is_superuser=True + is_staff=True | Irrestrito, incluindo /admin/ |
| Owner | Group "Owner" | Tudo, exceto /admin/ |
| Comum | Group "Comum", ou nenhum Group/superuser | Tudo, exceto Dashboard, Financeiro e /admin/ |

- Permissoes customizadas `imoveis.pode_acessar_dashboard` e
  `imoveis.pode_acessar_financeiro` sao ancoradas em um model
  "permission-only" sem tabela (`PermissaoTela`, `managed=False` em
  imoveis/models.py), desacoplado de qualquer model de negocio.
- As views de Dashboard e Financeiro (CRUD de Lancamento) sao protegidas
  por `permission_required(..., raise_exception=True)` - acesso direto por
  URL sem a permissao retorna 403 (templates/403.html), nunca stack trace.
- A sidebar (templates/base.html) oculta os itens Dashboard e Financeiro
  para quem nao tem a permissao correspondente - complementar a protecao
  de view, nunca a unica camada.
- Um usuario pertencente a Owner e Comum simultaneamente tem acesso de
  Owner (permissoes efetivas sao a uniao das permissoes de todos os
  Groups do usuario; Comum nao possui permissoes proprias para revogar
  nada).
```

Ajustar redacao conforme o texto real encontrado no arquivo no momento da
implementacao (o trecho acima e um guia, nao um diff literal).

---

# Criterios de aceite

- [ ] Secao 10 de docs/04_regras_de_negocio.md descreve os 3 perfis, a
      ancoragem das permissoes customizadas e a regra de precedencia
      Owner+Comum.
- [ ] Nenhuma outra secao do arquivo foi reescrita (delta pequeno,
      localizado).
- [ ] docs/01_visao_geral.md **nao** e tocado por este modulo (revisao das
      personas antigas e pendencia registrada em plan.md, fora de escopo).

---

# Riscos

- Nenhum risco tecnico - modulo e so documentacao. Risco principal e
  descrever um comportamento que diverge do que foi realmente
  implementado nos modulos 1-4; conferir o codigo antes de escrever, nao
  copiar o delta acima as cegas caso algo tenha mudado durante a
  implementacao.
