# Objetivo

Criar o model `DocumentoGerado`: um registro imutável por geração de PDF,
com versionamento sequencial por origem (Contrato, LaudoVistoria ou Recibo),
hash do arquivo e autor. Este model é a nova fonte de verdade do histórico
de documentos gerados pelo sistema (contratos, laudos e recibos gerados
pela própria aplicação — não inclui uploads manuais como `Fiador.certidao_onus`
ou `LaudoVistoria.arquivo`, que continuam sendo simples `FileField` avulsos).

---

# Arquivos afetados

- `imoveis/models.py` (novo model `DocumentoGerado`)
- `imoveis/migrations/0009_documentogerado.py` (nova migration)
- `imoveis/admin.py` (registrar `DocumentoGerado` — leitura/consulta, sem
  permitir edição manual do arquivo/hash, ver critérios de aceite)

---

## Documentação relacionada

- docs/03_modelagem_dados.md
  Adicionar a entidade `DocumentoGerado` à lista de entidades: campos, tipos,
  relacionamentos (com Contrato/LaudoVistoria/Recibo) e caminho de upload
  (`documentos/<tipo>/<ano>/<mes>/<nome>.pdf`).
- docs/04_regras_de_negocio.md
  Documentar a regra de versionamento: "regerar PDF nunca sobrescreve, sempre
  cria uma nova versão; o documento atual é a versão mais alta; versões
  antigas nunca são apagadas nem editadas".

---

# Dependências

Nenhuma (pode ser implementado em paralelo à trilha visual 01-06).

---

# Detalhamento técnico

## Campos propostos

```python
class DocumentoGerado(models.Model):
    TIPO_CHOICES = [
        ('contrato', 'Contrato'),
        ('laudo', 'Laudo de Vistoria'),
        ('recibo', 'Recibo'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)

    # Origem: exatamente um dos três deve estar preenchido (validar em clean()).
    # FKs diretas (não GenericForeignKey) para manter simplicidade de query
    # e integridade referencial nativa do banco, já que só existem 3 origens
    # possíveis e isso não deve crescer com frequência.
    contrato = models.ForeignKey('Contrato', null=True, blank=True,
                                 on_delete=models.CASCADE, related_name='versoes_documento')
    laudo = models.ForeignKey('LaudoVistoria', null=True, blank=True,
                              on_delete=models.CASCADE, related_name='versoes_documento')
    recibo = models.ForeignKey('Recibo', null=True, blank=True,
                               on_delete=models.CASCADE, related_name='versoes_documento')

    numero_versao = models.PositiveIntegerField()
    arquivo = models.FileField(upload_to=caminho_documento_gerado)
    hash_sha256 = models.CharField(max_length=64, editable=False)
    gerado_em = models.DateTimeField(auto_now_add=True)
    gerado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='documentos_gerados')

    class Meta:
        verbose_name = 'Documento Gerado'
        verbose_name_plural = 'Documentos Gerados'
        ordering = ['-gerado_em']
        constraints = [
            models.UniqueConstraint(
                fields=['tipo', 'contrato', 'laudo', 'recibo', 'numero_versao'],
                name='versao_unica_por_origem',
            ),
        ]

    def origem(self):
        return self.contrato or self.laudo or self.recibo
```

Decisões a registrar no código (docstring do model):
- Exatamente uma das FKs (`contrato`/`laudo`/`recibo`) deve estar preenchida
  — validar em `clean()`/`full_clean()`, não apenas confiar na aplicação
  (proteção de integridade a nível de model).
- **Imutabilidade**: sobrescrever `save()` para impedir updates após a
  criação inicial (permitir apenas `INSERT`; um `UPDATE` em instância já
  persistida deve levantar exceção). Isso é o que torna a versão "imutável"
  de fato, e não apenas por convenção de uso.
- `numero_versao` é calculado pela camada de geração (módulo 09), não pelo
  model — o model apenas armazena e garante unicidade via `UniqueConstraint`.
- `related_name='versoes_documento'` idêntico nas 3 FKs é proposital: permite
  que o template de detalhe (módulo 10) use a mesma sintaxe
  `objeto.versoes_documento.all` independentemente do tipo de origem.

## Função de upload determinística

```python
def caminho_documento_gerado(instance, filename):
    agora = instance.gerado_em or timezone.now()
    origem = instance.origem()
    nome = f"{instance.tipo}_{origem.pk}_v{instance.numero_versao}.pdf"
    return f"documentos/{instance.tipo}/{agora:%Y}/{agora:%m}/{nome}"
```

Nota: `instance.gerado_em` ainda não existe no momento do `upload_to` (é
`auto_now_add`, só populado no `save()`) — usar `timezone.now()` como
fallback é aceitável aqui, já que a diferença entre o instante de geração e o
instante de salvamento é de milissegundos e não afeta a pasta ano/mês em
99,99% dos casos. Documentar essa limitação no docstring da função.

## Admin

Registrar `DocumentoGerado` no `imoveis/admin.py` como somente leitura
(`readonly_fields` cobrindo todos os campos, sem `add`/`change` manual) —
serve para auditoria/consulta, não para operação manual (a criação é sempre
via `imoveis/pdf.py`, módulo 09).

---

# Critérios de aceite

- [ ] Model `DocumentoGerado` criado com as 3 FKs opcionais, `numero_versao`,
      `arquivo`, `hash_sha256`, `gerado_em`, `gerado_por`.
- [ ] `clean()` rejeita registros com 0 ou 2+ FKs de origem preenchidas.
- [ ] Tentativa de `save()` em instância já persistida (update) levanta
      exceção — imutabilidade garantida a nível de model, não só de convenção.
- [ ] `UniqueConstraint` impede duas versões com o mesmo `numero_versao` para
      a mesma origem.
- [ ] Migration `0009_documentogerado.py` criada e aplicável
      (`manage.py migrate` sem erros).
- [ ] `python manage.py check` sem erros.
- [ ] Admin mostra `DocumentoGerado` em modo somente leitura.

---

# Riscos

- `UniqueConstraint` com múltiplas FKs nullable exige atenção: bancos SQL
  tratam `NULL` como distinto entre si por padrão, então a constraint só
  protege corretamente a combinação onde as FKs não usadas ficam
  consistentemente `NULL` nas 3 linhas comparadas — validar com teste
  dedicado (módulo 11) que tentar duplicar `numero_versao` para a mesma
  origem realmente falha.
- Impedir `UPDATE` via `save()` pode conflitar com padrões internos do Django
  (ex.: `full_clean()` chamado antes de salvar, sinais `pre_save`) — testar
  explicitamente a criação (deve funcionar) e a tentativa de edição (deve
  falhar) no módulo 11.
