# Objetivo

Criar o model "permission-only" PermissaoTela (sem tabela real), que hospeda
as duas permissoes customizadas de acesso a tela usadas pelo resto do plano:
pode_acessar_dashboard e pode_acessar_financeiro. Este model nunca e
instanciado nem consultado via .objects - existe so para o Django registrar
o ContentType e as Permission em Meta.permissions.

---

# Arquivos afetados

- imoveis/models.py - novo model PermissaoTela.
- imoveis/migrations/ - nova migration de schema (gerar via makemigrations).

---

# Dependencias

Nenhuma. Modulo base.

---

# Leituras adicionais

Nenhuma.

---

# Especificacao do model

```python
class PermissaoTela(models.Model):
    """Model 'permission-only': nao possui tabela propria (managed=False).

    Existe apenas para ancorar permissoes customizadas de acesso a telas que
    nao pertencem naturalmente a nenhum model de negocio (ex.: Dashboard e
    uma agregacao sem model proprio; Financeiro nao deve ter sua permissao
    de acesso acoplada ao ciclo de vida do model Lancamento). Nunca
    instanciar, nunca consultar .objects - usado somente via
    permission_required('imoveis.pode_acessar_dashboard'/'...financeiro',
    raise_exception=True) nas views e via perms.imoveis.<codename> nos
    templates (perms ja disponivel globalmente via
    django.contrib.auth.context_processors.auth).
    """

    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ('pode_acessar_dashboard', 'Pode acessar o Dashboard'),
            ('pode_acessar_financeiro', 'Pode acessar o modulo Financeiro'),
        ]
```

Posicionar a classe no final de imoveis/models.py, depois de
NotificacaoUsuario (ultimo model do arquivo hoje).

`default_permissions = ()` remove as 4 permissoes padrao do Django
(add/change/delete/view) que nao fazem sentido para um model sem tabela e
sem instancias - so as 2 permissoes customizadas de Meta.permissions sao
criadas.

`managed = False` impede o Django de tentar criar uma tabela real para este
model nas migrations (nao ha CREATE TABLE); mas a migration de CreateModel
ainda precisa existir no historico de migrations, pois e ela que registra o
model no app state usado pelo Django para, depois (via signal post_migrate,
fora do controle desta migration), criar o ContentType e as Permission.

---

# Migration

Gerar com makemigrations normalmente. A migration resultante tera uma
CreateModel com options={'managed': False, 'default_permissions': (),
'permissions': [...]} e nenhum campo alem do id automatico - isso e
esperado e correto, nao e um erro de geracao.

---

# Criterios de aceite

- [ ] Model PermissaoTela criado exatamente como especificado acima.
- [ ] Migration gerada e aplicada sem erros (makemigrations + migrate).
- [ ] `venv/Scripts/python manage.py check` sem erros.
- [ ] Apos migrate, os 2 Permission existem no banco: verificar via shell
      (`python manage.py shell`) com
      `Permission.objects.filter(codename__in=['pode_acessar_dashboard','pode_acessar_financeiro'])`
      retornando 2 registros, cada um com content_type.app_label == 'imoveis'
      e content_type.model == 'permissaotela'.

---

# Riscos

- Nome do model (PermissaoTela) e usado literalmente pelo modulo 2 (para
  localizar o content_type) e pelos templates/decorators do modulo 3/4
  (codename via app_label imoveis) - nao renomear sem avisar os modulos
  seguintes.
- Um model managed=False sem nenhum campo alem do id automatico pode
  parecer um erro de implementacao a quem le o codigo pela primeira vez -
  o docstring extenso acima existe para prevenir isso; nao remover.
