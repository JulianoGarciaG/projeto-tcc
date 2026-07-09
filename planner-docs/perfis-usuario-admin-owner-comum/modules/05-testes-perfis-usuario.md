# Objetivo

Cobrir com testes automatizados a matriz dos 3 perfis (Admin/Owner/Comum) x
2 telas protegidas (Dashboard, Financeiro), a precedencia de Group quando um
usuario esta em Owner e Comum simultaneamente, a logica de reclassificacao
de usuarios existentes da migration de dados do modulo 2, e o tratamento de
403.

---

# Arquivos afetados

- imoveis/tests.py - nova classe de testes (adicionar no final do arquivo,
  seguindo o padrao das classes existentes, ex.: FluxoViewTests ~linha 404).

---

# Dependencias

Depende dos modulos 01, 02, 03 e 04 (testa o comportamento integrado dos
quatro).

---

# Leituras adicionais

Nenhuma.

---

# Estrutura de testes sugerida

Seguir o padrao ja usado em imoveis/tests.py (import de User de
django.contrib.auth.models, self.client.force_login(self.user), helper
criar_base() para fixtures minimas de imovel/contrato quando necessario).

```python
from django.contrib.auth.models import Group, Permission, User


class PerfisUsuarioTests(TestCase):
    """Matriz de perfis (Admin/Owner/Comum) x telas protegidas
    (Dashboard, Financeiro) + regras de precedencia e migracao de dados."""

    @classmethod
    def setUpTestData(cls):
        cls.perm_dashboard = Permission.objects.get(codename='pode_acessar_dashboard')
        cls.perm_financeiro = Permission.objects.get(codename='pode_acessar_financeiro')
        cls.owner_group, _ = Group.objects.get_or_create(name='Owner')
        cls.owner_group.permissions.set([cls.perm_dashboard, cls.perm_financeiro])
        cls.comum_group, _ = Group.objects.get_or_create(name='Comum')

    def _login_admin(self):
        user = User.objects.create_superuser('admin', 'admin@x.com', 'x')
        self.client.force_login(user)
        return user

    def _login_owner(self):
        user = User.objects.create_user('owner', password='x')
        user.groups.add(self.owner_group)
        self.client.force_login(user)
        return user

    def _login_comum(self):
        user = User.objects.create_user('comum', password='x')
        user.groups.add(self.comum_group)
        self.client.force_login(user)
        return user
```

Testes da matriz e casos de borda (mesma classe, metodos adicionais):

```python
    # --- Matriz 3 perfis x 2 telas ---

    def test_admin_acessa_dashboard(self):
        self._login_admin()
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_admin_acessa_financeiro(self):
        self._login_admin()
        resp = self.client.get(reverse('lancamento_list'))
        self.assertEqual(resp.status_code, 200)

    def test_owner_acessa_dashboard(self):
        self._login_owner()
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_owner_acessa_financeiro(self):
        self._login_owner()
        resp = self.client.get(reverse('lancamento_list'))
        self.assertEqual(resp.status_code, 200)

    def test_comum_nao_acessa_dashboard(self):
        self._login_comum()
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 403)

    def test_comum_nao_acessa_financeiro(self):
        self._login_comum()
        resp = self.client.get(reverse('lancamento_list'))
        self.assertEqual(resp.status_code, 403)

    def test_anonimo_redireciona_para_login(self):
        resp = self.client.get(reverse('dashboard'))
        self.assertRedirects(resp, f"/login/?next={reverse('dashboard')}")
```

Precedencia Owner+Comum, sidebar e template 403:

```python
    # --- Precedencia Owner + Comum ---

    def test_usuario_em_owner_e_comum_prevalece_owner(self):
        user = User.objects.create_user('ambos', password='x')
        user.groups.add(self.owner_group, self.comum_group)
        self.client.force_login(user)
        resp_dashboard = self.client.get(reverse('dashboard'))
        resp_financeiro = self.client.get(reverse('lancamento_list'))
        self.assertEqual(resp_dashboard.status_code, 200)
        self.assertEqual(resp_financeiro.status_code, 200)

    # --- Sidebar oculta os itens ---

    def test_sidebar_oculta_financeiro_para_comum(self):
        self._login_comum()
        resp = self.client.get(reverse('imovel_list'))
        self.assertNotContains(resp, reverse('lancamento_list'))

    def test_sidebar_mostra_financeiro_para_owner(self):
        self._login_owner()
        resp = self.client.get(reverse('imovel_list'))
        self.assertContains(resp, reverse('lancamento_list'))

    # --- 403 usa o template certo, nao stack trace ---

    def test_403_usa_template_proprio(self):
        self._login_comum()
        resp = self.client.get(reverse('lancamento_list'))
        self.assertTemplateUsed(resp, '403.html')
```

Teste da migracao de dados (reclassificacao de usuarios existentes):

```python
    # --- Migracao de dados: reclassificacao de usuarios existentes ---

    def test_migration_reclassifica_usuarios_existentes(self):
        """Chama a funcao de RunPython da migration do modulo 2
        diretamente (importada do arquivo de migration via importlib),
        passando o registry real de apps, e valida is_superuser/Group
        resultantes. Nao usa MigrationTestCase porque a migration ja
        rodou na criacao do banco de teste (sem usuarios ainda
        existentes) - aqui testamos a funcao isoladamente contra
        usuarios criados no proprio teste."""
        import importlib
        from django.apps import apps as real_apps

        mod_migration = importlib.import_module(
            'imoveis.migrations.NOME_REAL_DO_ARQUIVO_MODULO_2'
        )

        staff_sem_super = User.objects.create_user('staffuser', password='x', is_staff=True)
        comum_qualquer = User.objects.create_user('qualquer', password='x')

        mod_migration.cria_grupos_e_permissoes(real_apps, None)

        staff_sem_super.refresh_from_db()
        comum_qualquer.refresh_from_db()
        self.assertTrue(staff_sem_super.is_superuser)
        self.assertFalse(comum_qualquer.groups.filter(name='Owner').exists())
        self.assertTrue(comum_qualquer.groups.filter(name='Comum').exists())
```

Substituir `NOME_REAL_DO_ARQUIVO_MODULO_2` pelo nome real do arquivo de
migration criado no modulo 2 (sem a extensao .py).

---

# Criterios de aceite

- [ ] Matriz completa 3 perfis x 2 telas (6 combinacoes de acesso) coberta.
- [ ] Teste de usuario anonimo (redirect para login) presente.
- [ ] Teste de precedencia Owner+Comum presente e passando.
- [ ] Testes de sidebar ocultando/mostrando Financeiro presentes.
- [ ] Teste de template 403 correto presente.
- [ ] Teste da logica de reclassificacao da migration de dados presente,
      chamando a funcao diretamente (nao via MigrationTestCase).
- [ ] `venv/Scripts/python manage.py test imoveis` passa 100% (incluindo os
      testes preexistentes ajustados no modulo 3, ex.: DashboardFiltroTests).

---

# Riscos

- Nome exato do arquivo de migration do modulo 2 precisa ser conferido
  antes de escrever o teste de reclassificacao (import literal do arquivo
  gerado, via importlib por causa do prefixo numerico no nome do arquivo).
- `assertContains`/`assertNotContains` verificando `reverse('lancamento_list')`
  no HTML da sidebar pode dar falso negativo se a URL aparecer em outro
  lugar da pagina por coincidencia - conferir o HTML renderizado se o teste
  falhar de forma inesperada.
