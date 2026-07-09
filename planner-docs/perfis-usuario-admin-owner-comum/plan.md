# Plano: Perfis de Usuario (Admin / Owner / Comum)

## Objetivo

Substituir o modelo de acesso binario atual (is_staff/autenticado) por 3
perfis efetivos:

- **Admin** - is_superuser=True + is_staff=True. Acesso irrestrito,
  incluindo /admin/ do Django. Nao usa Group.
- **Owner** - Django Group Owner. Acesso a todas as telas do sistema,
  exceto /admin/. is_staff=False.
- **Comum** - Django Group Comum (ou nenhum group/superuser - ver
  "Casos de borda"). Acesso a tudo, exceto Dashboard, Financeiro (CRUD de
  Lancamento) e /admin/.

Atribuicao de perfil continua sendo feita somente pelo /admin/ do
Django (superuser/staff flags e membership de Group) - sem tela nova no
sistema.

## Estado atual

- Todas as views sao FBVs com @login_required apenas - nenhuma view usa
  permission_required/Group/Permission hoje (imoveis/views.py).
- Dashboard: FBV unica dashboard (imoveis/views.py:91), @login_required,
  url name dashboard, path ''.
- Financeiro: 4 FBVs lancamento_list/create/edit/delete
  (imoveis/views.py:677-733), todas @login_required, paths financeiro/*
  (imoveis/urls.py:69-72).
- Sidebar (templates/base.html): item Dashboard linha 42-45, item
  Financeiro linha 77-81 - sem guarda hoje. Secao "Administracao" (link
  para /admin/) guardada por {% if user.is_staff %} linhas 96-103
  (nao muda - Owner ja fica de fora por ter is_staff=False). Label
  user-role (linha 148) hoje e binario is_staff -> "Administrador"/
  "Usuario".
- Context processor django.contrib.auth.context_processors.auth
  (core/settings.py:45) ja esta ativo -> perms ja disponivel em todo
  template que estende base.html, sem processor novo necessario.
- Nao existe handler403 nem template de erro (403/404/500) no projeto.
  DEBUG=True em dev - mas PermissionDenied (403) nao e afetado pelo
  modo debug do Django (so Http404 ganha pagina tecnica com DEBUG=True);
  handler403 funciona em dev e prod igualmente.
- /admin/ ja restringe por is_staff via comportamento padrao do Django -
  nenhuma mudanca extra necessaria para bloquear Owner/Comum la.
- AUTH_USER_MODEL nao e customizado (User padrao do django.contrib.auth).
- Personas antigas (Funcionario/Gestor/Vistoriador/Auditor/Administrador) em
  docs/01_visao_geral.md linhas 32-35 ficam desatualizadas por este plano.
  Revisao desse documento e FORA de escopo desta implementacao - ver
  "Observacoes gerais".

## Decisao de arquitetura: onde ancorar as permissoes customizadas

Django exige que toda Permission esteja associada a um ContentType, ou
seja, a um model concreto declarado em Meta.permissions. Duas opcoes foram
avaliadas:

1. **Ancorar em Lancamento** (pode_acessar_financeiro em
   Lancamento.Meta.permissions) - rejeitada. Acopla uma permissao de
   acesso a tela ao ciclo de vida de um model de negocio; se o financeiro
   for remodelado/substituido no futuro (ex.: Lancamento renomeado ou
   quebrado em outros models), a permissao herdada ficaria orfa ou exigiria
   migracao de dados so para preservar o codename. Alem disso, o Dashboard
   nao tem model proprio (e uma agregacao de Lancamento/Contrato) - nao
   haveria onde ancorar pode_acessar_dashboard de forma simetrica.

2. **Model dedicado "permission-only", managed=False** - RECOMENDADA.
   Um model PermissaoTela sem tabela real (Meta.managed = False,
   default_permissions = ()), existindo so para hospedar
   Meta.permissions = [('pode_acessar_dashboard', ...),
   ('pode_acessar_financeiro', ...)]. Django cria o ContentType e os
   Permission associados normalmente (a criacao de permissoes via signal
   post_migrate nao depende de managed=True; so depende do model estar
   registrado no app). Desacopla completamente as permissoes de qualquer
   model de negocio - sobrevive a qualquer refactor futuro do financeiro ou
   do dashboard.

Detalhes de implementacao no modulo 01-modelo-permissao-host.

## Estrategia de migracao de dados

Ver modulo 02-migration-dados-grupos-usuarios para o codigo completo.
Resumo:

1. Criar (ou obter) os Permission pode_acessar_dashboard e
   pode_acessar_financeiro no ContentType de PermissaoTela - criados
   diretamente na migration (nao da para confiar no signal post_migrate
   rodar a tempo dentro do mesmo migrate, pois esse signal so dispara
   depois que todas as migrations do comando terminam).
2. Criar (ou obter) os Group Owner (com as 2 permissoes acima) e Comum
   (sem permissoes).
3. Reclassificar usuarios existentes no banco no momento da migracao:
   - is_staff=True -> tambem is_superuser=True (vira Admin).
   - Todos os demais (is_staff=False) -> adicionados ao Group Comum.
4. Reclassificacao para Owner e manual, depois, via /admin/ - fora desta
   migracao.

Esta migracao de dados e parcialmente irreversivel por design: o
reverse remove os Groups/Permissions criados, mas nao desfaz
is_superuser=True nem memberships de Comum atribuidas a usuarios reais
(nao ha como saber, ao reverter, quais contas ja eram superuser antes da
migracao). Documentado como risco aceito no modulo 2.

## Casos de borda (regra de precedencia)

- **Sem Group e sem superuser** -> tratado como Comum. Isso ja e o
  comportamento natural do sistema de permissoes do Django (sem
  Permission atribuida via nenhum Group = nenhum acesso extra) - nao
  requer logica nova, so e preciso nao esquecer de refletir isso no label
  de UI (modulo 4) mesmo para usuarios sem membership explicita em Comum.
- **createsuperuser** -> sempre Admin (is_superuser=True nativo do
  comando), sem Group. Nenhuma acao necessaria.
- **Usuario em Owner + Comum simultaneamente** -> prevalece Owner. Isso
  tambem e automatico: permissoes efetivas de um usuario sao a uniao
  das permissoes de todos os seus Groups; Comum nao tem permissoes, entao
  nao pode revogar nada que Owner concede. Nenhuma logica de desempate e
  necessaria no codigo - so precisa ser testado explicitamente (modulo
  5) para documentar a garantia, ja que e uma regra que depende do
  entendimento correto do framework, nao de codigo escrito por nos.

## Resumo dos modulos

| # | Modulo | Responsabilidade |
|---|---|---|
| 1 | modelo-permissao-host | Model PermissaoTela (managed=False) + migration de schema |
| 2 | migration-dados-grupos-usuarios | Migration de dados: Groups, Permissions, reclassificacao de usuarios existentes |
| 3 | protecao-views-dashboard-financeiro | permission_required(..., raise_exception=True) nas 5 views (dashboard + 4 de lancamento) |
| 4 | sidebar-403 | Guardas na sidebar, label de perfil, handler403 + templates/403.html |
| 5 | testes-perfis-usuario | Matriz 3 perfis x 2 telas, precedencia Owner+Comum, migracao de dados, 403 |
| 6 | delta-documentacao | Atualiza docs/04_regras_de_negocio.md paragrafo 10 com o novo modelo de 3 perfis |

## Ordem de implementacao

1 -> 2 -> 3 -> 4 -> 5 -> 6

- Modulo 2 depende do modulo 1 (usa o ContentType/codenames do
  PermissaoTela criado ali; a migration de dados declara dependencia
  explicita na migration de schema do modulo 1).
- Modulo 3 depende do modulo 1 (usa os codenames das permissoes nos
  decorators - nao depende do modulo 2, mas sem ele nao ha usuario Owner
  real para testar manualmente).
- Modulo 4 depende do modulo 1 (usa os codenames nos templates via perms).
  Nao depende tecnicamente de 2 ou 3, mas validacao manual completa
  (sidebar realmente ocultando Financeiro para um Comum) fica mais facil com
  2 e 3 ja prontos.
- Modulo 5 depende de 1, 2, 3 e 4 (testa o comportamento integrado).
- Modulo 6 depende de 1, 2, 3 e 4 (descreve o comportamento final ja
  implementado); pode ser feito em paralelo ao 5.

## Afinidade de cache

- Modulos 3 e 4 tocam ambos imoveis/views.py (modulo 3 decora as 5 views
  existentes; modulo 4 adiciona a view erro_403). Baixa sobreposicao real
  (funcoes diferentes), mas ha ganho de cache em fazer os dois na mesma
  janela se o usuario preferir reduzir releituras do arquivo.
- Modulos 1 e 2 tocam imoveis/migrations/ (arquivos novos e distintos) e
  modulo 1 tambem toca imoveis/models.py. Baixo ganho de cache - arquivos
  pequenos, releitura barata; podem ser feitos em janelas separadas sem
  custo relevante.
- Modulo 5 toca imoveis/tests.py (arquivo grande, editado por adicao no
  final) - sem sobreposicao de arquivos-fonte com os modulos 1-4, entao nao
  ha ganho real em junta-lo com outro modulo.
- Modulo 6 toca so docs/04_regras_de_negocio.md - isolado.

## Observacoes gerais

- Nenhuma migration e criada pelo Planner - os modulos 1 e 2 instruem a
  rodar makemigrations/migrate como parte da implementacao.
- Pendencia registrada, fora de escopo: docs/01_visao_geral.md linhas
  32-35 descrevem personas antigas (Funcionario/Gestor/Vistoriador/
  Auditor) que este plano torna desatualizadas. A revisao desse documento
  nao faz parte de nenhum modulo aqui - deve ser tratada em uma rodada
  propria de revisao de documentacao, depois que os 3 perfis estiverem
  estaveis em producao.
- Fora de escopo (nao implementar): tela de gestao de perfis dentro do
  sistema (atribuicao continua so pelo /admin/), granularidade adicional
  de permissoes alem de Dashboard/Financeiro, revogacao automatica de
  Comum ao promover para Owner (Comum nao atrapalha Owner, entao nao
  precisa ser removido).
