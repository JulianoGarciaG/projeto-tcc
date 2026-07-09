# Objetivo

Criar o model `NotificacaoUsuario`, sua migration e o registro somente-leitura
no admin. Este model é a base de persistência do histórico de notificações
por usuário — não tem UI própria além do admin (a UI do sino é o módulo 4).

---

# Arquivos afetados

- `imoveis/models.py` — novo model `NotificacaoUsuario`.
- `imoveis/admin.py` — novo `NotificacaoUsuarioAdmin`.
- `imoveis/migrations/` — nova migration (gerar via `makemigrations`).

---

# Dependências

Nenhuma. Módulo base.

---

# Leituras adicionais

Nenhuma (o padrão de referência `DocumentoGerado`/`DocumentoGeradoAdmin` já
está descrito em plan.md).

---

# Especificação do model

```python
class NotificacaoUsuario(models.Model):
    """Histórico persistido das mensagens do django.contrib.messages, por
    usuário. Alimentado automaticamente pelo storage backend customizado
    (imoveis/message_storage.py) — nunca criado manualmente em views.

    Não possui estado de lida/não lida nem referência ao objeto de origem:
    é um espelho append-only do texto e nível (tag) da mensagem exibida.
    """

    NIVEL_CHOICES = [
        ('success', 'Sucesso'),
        ('error', 'Erro'),
        ('warning', 'Aviso'),
        ('info', 'Informação'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='notificacoes')
    mensagem = models.TextField()
    nivel = models.CharField(max_length=10, choices=NIVEL_CHOICES)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificação de Usuário'
        verbose_name_plural = 'Notificações de Usuário'
        ordering = ['-criado_em', '-pk']

    def __str__(self):
        return f'{self.usuario} — {self.get_nivel_display()} — {self.mensagem[:50]}'
```

Posicionar a classe próxima a `DocumentoGerado` (final do arquivo) ou em local
coerente com a organização atual de `imoveis/models.py` — verificar se o
arquivo agrupa por domínio antes de decidir a posição exata.

`settings` já está importado em `imoveis/models.py` (usado por
`DocumentoGerado.gerado_por`) — não precisa adicionar import novo.

---

# Admin

Seguir o padrão de `DocumentoGeradoAdmin` (`imoveis/admin.py:107-120`):
somente leitura, sem permissão de criação/edição manual.

```python
@admin.register(NotificacaoUsuario)
class NotificacaoUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'nivel', 'mensagem', 'criado_em')
    list_filter = ('nivel', 'criado_em')
    date_hierarchy = 'criado_em'
    readonly_fields = ('usuario', 'mensagem', 'nivel', 'criado_em')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
```

---

# Critérios de aceite

- [ ] Model `NotificacaoUsuario` criado com os campos e `Meta` acima.
- [ ] Migration gerada e aplicada sem erros (`makemigrations` + `migrate`).
- [ ] `NotificacaoUsuarioAdmin` registrado, somente leitura (sem add/change).
- [ ] `venv/Scripts/python manage.py check` sem erros.

---

# Riscos

- Nome do model pode colidir mentalmente com `Notificacao` (entidade de
  negócio já existente) — manter o nome `NotificacaoUsuario` exatamente como
  especificado para diferenciar claramente nos dois admins/models.
