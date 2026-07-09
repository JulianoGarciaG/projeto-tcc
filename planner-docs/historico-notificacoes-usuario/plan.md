# Plano: Histórico de notificações por usuário

## Objetivo

Persistir, por usuário, um histórico das mensagens que o sistema já emite hoje
via `django.contrib.messages` (sucesso de CRUD, geração de PDF, erros,
avisos). Sino da topbar (hoje decorativo) passa a ser clicável e abre um
dropdown com as últimas N notificações do usuário logado. **Sem estado de
lida/não lida. Sem novos gatilhos ou categorias** — apenas as 4 tags que já
existem (`success`, `error`, `warning`, `info`, sendo `info` atualmente não
usada).

## Estado atual

- `imoveis/views.py` dispara `messages.success/error/warning` em 36 pontos
  (28 success, 6 error, 2 warning). Nenhum uso de `info`.
- `templates/base.html:143-156` renderiza `messages` como toasts Bootstrap
  efêmeros (1 request, sem persistência) — esse bloco **não muda**.
- Sino da topbar em `templates/base.html:124-126` é um `<span>` estático,
  sem link, sem dropdown, sem JS.
- `core/settings.py:43-47` só tem os 3 context processors padrão do Django.
  Nenhum customizado no projeto até hoje.
- Model `Notificacao` (`imoveis/models.py:463-492`) é entidade de negócio
  distinta (avisos de órgãos públicos sobre um imóvel) — **não usar, não
  confundir**. O model novo desta feature chama-se `NotificacaoUsuario`.
- Sem `Paginator` no projeto; precedente de "últimas N" é slicing simples de
  queryset ordenado (`imoveis/views.py:124`).
- Padrão de model "gerado pelo sistema, somente leitura" a seguir:
  `DocumentoGerado` (`imoveis/models.py:625-698`) e `DocumentoGeradoAdmin`
  (`imoveis/admin.py:107-120`).

## Arquitetura decidida

1. **Model novo `NotificacaoUsuario`** — FK `usuario` (`CASCADE`, notificação
   só existe em função do destinatário), `mensagem` (texto), `nivel`
   (choices espelhando as tags do Django messages: `success`/`error`/
   `warning`/`info`), `criado_em` (`auto_now_add`). Sem campo de
   lida/não-lida, sem FK genérica para objeto de origem (fora de escopo).

2. **Captura central via storage backend customizado do Django messages** —
   único ponto que intercepta as 36 chamadas existentes sem editá-las.
   Classe `imoveis/message_storage.py:PersistentFallbackStorage(FallbackStorage)`
   sobrescreve `add()` para, além do comportamento padrão (guardar na sessão/
   cookie para o toast), criar um `NotificacaoUsuario` quando
   `request.user.is_authenticated`. Ativado via `MESSAGE_STORAGE` em
   `core/settings.py`. Os toasts em `base.html` continuam funcionando
   inalterados (mesmo fluxo do Django messages).

3. **Context processor novo** `imoveis/context_processors.py:notificacoes_usuario`
   — popula `ultimas_notificacoes_usuario` (últimas N via slicing, seguindo
   o precedente do dashboard) em todo template que estende `base.html`,
   registrado em `TEMPLATES['OPTIONS']['context_processors']`. Evita
   popular manualmente em cada view (padrão 100% view-based seria
   trabalhoso e frágil para 36+ pontos).

4. **UI do sino** — `templates/base.html` ganha um Bootstrap dropdown nativo
   (`data-bs-toggle="dropdown"`) no `<span class="icon-btn">` do sino,
   listando `ultimas_notificacoes_usuario`. CSS novo em `shelter.css`
   reaproveitando tokens existentes (`--ok`/`--danger`/`--warn`/`--info` e
   pares `-bg`, mesmos usados pelos badges). Sem JS novo além do que o
   bundle do Bootstrap já fornece para dropdowns.

## Resumo dos módulos

| # | Módulo | Responsabilidade |
|---|---|---|
| 1 | `modelo-notificacao-usuario` | Model `NotificacaoUsuario` + migration + admin somente-leitura |
| 2 | `storage-captura-mensagens` | Storage backend customizado + `MESSAGE_STORAGE` em settings |
| 3 | `context-processor-sino` | Context processor + registro em `TEMPLATES` |
| 4 | `dropdown-sino-topbar` | Dropdown na topbar (`base.html`) + CSS em `shelter.css` |
| 5 | `testes-notificacao-usuario` | Testes cobrindo persistência, últimas N, isolamento por usuário |

## Ordem de implementação

1 → 2 → 3 → 4 → 5

Módulo 2 depende do model do módulo 1 (usa `NotificacaoUsuario.objects.create`).
Módulo 3 depende do model do módulo 1 (faz a query das últimas N).
Módulo 4 depende do contexto populado pelo módulo 3.
Módulo 5 depende de 1, 2 e 3 estarem implementados (testa o fluxo ponta a ponta
de captura + leitura).

## Afinidade de cache

- Módulos 1 e 5 tocam `imoveis/models.py`, `imoveis/admin.py` e
  `imoveis/tests.py` de forma relacionada — mas 5 só deve ser feito depois de
  2/3 existirem, então não há ganho real em juntá-los na mesma janela.
- Módulos 2 e 3 são independentes entre si (arquivos totalmente diferentes:
  `imoveis/message_storage.py` vs `imoveis/context_processors.py`), mas ambos
  editam `core/settings.py` (blocos diferentes: `MESSAGE_STORAGE` vs
  `TEMPLATES`). Baixo ganho de cache — arquivo pequeno, releitura barata.
  Podem ser feitos em janelas separadas sem custo relevante.
- Módulo 4 é isolado (`templates/base.html` + `static/css/shelter.css`), sem
  sobreposição de arquivos-fonte com os demais.

## Observações gerais

- Nenhuma migration é criada pelo Planner — o módulo 1 instrui a rodar
  `makemigrations`/`migrate` como parte da implementação.
- Toasts efêmeros em `base.html:143-156` continuam existindo e inalterados;
  o histórico persistido é um mecanismo adicional, não substitui os toasts.
- Fora de escopo (não implementar): estado lida/não lida, novos
  gatilhos/categorias de notificação, paginação (Paginator), link da
  notificação para o objeto de origem, expiração/purga automática de
  notificações antigas.
