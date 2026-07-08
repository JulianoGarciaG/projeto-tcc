# Objetivo

Criar o módulo `imoveis/identidade.py` com:

1. `IdentificavelMixin` — fornece `codigo` (genérico, baseado em `PREFIXO_CODIGO`
   + PK) e declara o contrato de `rotulo_curto`/`rotulo_longo` que cada model
   implementa.
2. `nome_arquivo(instance, versao=None)` — nome de arquivo determinístico do
   PDF gerado, **totalmente implementado aqui**; o módulo `03-pdf-nomes-arquivo`
   apenas a importa e consome em `imoveis/pdf.py`/`imoveis/views.py`, sem
   reescrevê-la.
3. Aplicar o mixin e implementar `rotulo_curto`/`rotulo_longo` em `Imovel`,
   `Contrato`, `Recibo`, `LaudoVistoria` em `imoveis/models.py`.

Este módulo **não mexe em forms, views, templates ou pdf.py** — só cria a
fonte de verdade que os demais módulos consomem.

---

# Arquivos afetados

- `imoveis/identidade.py` (novo)
- `imoveis/models.py` — import do mixin + `class Imovel(IdentificavelMixin, models.Model)`
  (linha 28), `class Contrato(IdentificavelMixin, models.Model)` (linha 127),
  `class LaudoVistoria(IdentificavelMixin, models.Model)` (linha 212),
  `class Recibo(IdentificavelMixin, models.Model)` (linha 438) + properties
  `rotulo_curto`/`rotulo_longo` em cada um (logo após o `__str__` de cada
  classe; `__str__` **não muda**).

---

# Dependências

Nenhuma (módulo base).

---

# Leituras adicionais

Nenhuma (os campos usados abaixo já foram confirmados em `imoveis/models.py`
durante o planejamento; não é necessário abrir `/docs` para este módulo).

---

# Especificação

## `IdentificavelMixin` (`imoveis/identidade.py`)

```python
class IdentificavelMixin:
    """Fonte única de identidade legível das entidades de negócio.

    Cada subclasse define PREFIXO_CODIGO (3 letras) e implementa
    rotulo_curto/rotulo_longo. `codigo` é derivado do PK em runtime —
    não é persistido, não exige migration.
    """
    PREFIXO_CODIGO = None  # subclasse deve sobrescrever, ex.: 'IMV'

    @property
    def codigo(self):
        if self.pk is None:
            return f'{self.PREFIXO_CODIGO}-????'
        return f'{self.PREFIXO_CODIGO}-{self.pk:04d}'

    @property
    def rotulo_curto(self):
        raise NotImplementedError

    @property
    def rotulo_longo(self):
        raise NotImplementedError
```

Guarda `pk is None` é necessária: `label_from_instance` de um `ModelChoiceField`
só é chamado com instâncias já salvas (vindas do banco), mas o mixin deve ser
seguro mesmo se alguém acessar `codigo` num objeto ainda não salvo (ex.: shell,
testes, futuras previews).

## Helper de mês/ano abreviado (para `Recibo.rotulo_curto` e `nome_arquivo`)

Não depender de locale do Django (evitar surpresas de formatação) — usar
tabela fixa pt-BR, no mesmo estilo puro de `imoveis/extenso.py`:

```python
_MESES_ABREV = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun',
                'jul', 'ago', 'set', 'out', 'nov', 'dez']


def mes_ano_abreviado(data):
    """Ex.: date(2026, 3, 15) -> 'mar/2026'. None -> ''."""
    if data is None:
        return ''
    return f'{_MESES_ABREV[data.month - 1]}/{data.year}'
```

## `rotulo_curto` / `rotulo_longo` por entidade

### `Imovel` (`PREFIXO_CODIGO = 'IMV'`)

```python
@property
def rotulo_curto(self):
    end = self.endereco
    if self.numero:
        end = f'{end}, {self.numero}'
    local = self.bairro or self.cidade or ''
    if local:
        end = f'{end} – {local}'
    return f'{self.codigo} · {self.get_tipo_display()} · {end}'

@property
def rotulo_longo(self):
    base = self.rotulo_curto
    if self.cidade and self.cidade not in base:
        return f'{base}, {self.cidade}'
    return base
```

Exemplo: `IMV-0042 · Casa · Rua das Flores, 123 – Centro`.

### `Contrato` (`PREFIXO_CODIGO = 'CTR'`)

```python
@property
def rotulo_curto(self):
    periodo = f'{self.data_inicio:%m/%y}–{self.data_fim:%m/%y}'
    end = self.imovel.endereco
    if self.imovel.numero:
        end = f'{end} {self.imovel.numero}'
    return (f'{self.codigo} · {self.inquilino.nome} · {end} · '
            f'{periodo} · {self.get_status_display()}')

@property
def rotulo_longo(self):
    end = self.imovel.endereco
    if self.imovel.numero:
        end = f'{end}, {self.imovel.numero}'
    if self.imovel.bairro:
        end = f'{end} – {self.imovel.bairro}'
    periodo = f'{self.data_inicio:%d/%m/%Y} a {self.data_fim:%d/%m/%Y}'
    return (f'Contrato {self.codigo} — {self.inquilino.nome} — {end} — '
            f'{periodo} — {self.get_status_display()}')
```

Exemplo curto: `CTR-0042 · João Silva · Rua das Flores 123 · 01/26–12/26 · Ativo`.

### `Recibo` (`PREFIXO_CODIGO = 'REC'`)

```python
@property
def rotulo_curto(self):
    quem = self.quem_pagou or self.contrato.inquilino.nome
    partes = [self.codigo, quem]
    periodo = mes_ano_abreviado(self.periodo_inicio)
    if periodo:
        partes.append(periodo)
    if self.parcela_atual and self.parcela_total:
        partes.append(f'parcela {self.parcela_atual}/{self.parcela_total}')
    return ' · '.join(partes)

@property
def rotulo_longo(self):
    return f'Recibo {self.rotulo_curto}'
```

Exemplo: `REC-0231 · João Silva · mar/2026 · parcela 3/12`. Se `periodo_inicio`
e `parcela_atual/total` estiverem vazios (campos opcionais — só `imovel` e
`contrato` são obrigatórios), o rótulo cai graciosamente para
`REC-0231 · João Silva`.

### `LaudoVistoria` (`PREFIXO_CODIGO = 'LAU'`)

```python
@property
def rotulo_curto(self):
    end = self.imovel.endereco
    if self.imovel.numero:
        end = f'{end} {self.imovel.numero}'
    return (f'{self.codigo} · {self.get_tipo_display()} · {end} · '
            f'{self.locatario_nome()}')

@property
def rotulo_longo(self):
    return f'{self.rotulo_curto} · {self.data:%d/%m/%Y}'
```

Exemplo curto: `LAU-0055 · Vistoria de Entrada · Rua das Flores 123 · João Silva`
(reaproveita `locatario_nome()`, já existente no model, linha 249-250).


## `nome_arquivo(instance, versao=None)` (`imoveis/identidade.py`)

Monta `{Tipo}_{codigo}_{quem/onde}_{quando}[_vN].pdf`. Usa
`django.utils.text.slugify` (sem `allow_unicode`, ou seja, `allow_unicode=False`
— o padrão) para remover acentos e caracteres especiais: seguro como nome de
arquivo no Windows. Cada segmento textual é truncado em 40 caracteres antes de
concatenar, para o nome final não estourar limites de path no Windows.

```python
from datetime import date
from django.utils.text import slugify

_TIPO_LABEL = {'contrato': 'Contrato', 'laudo': 'Laudo', 'recibo': 'Recibo'}


def _endereco_curto(imovel):
    end = imovel.endereco
    if imovel.numero:
        end = f'{end} {imovel.numero}'
    return end


def nome_arquivo(instance, versao=None):
    """Nome de arquivo determinístico do PDF gerado (GED + download).

    instance: Contrato | LaudoVistoria | Recibo (import local evita ciclo
    com models.py, igual ao padrão já usado em pdf.py).
    """
    from .models import Contrato, LaudoVistoria, Recibo

    if isinstance(instance, Contrato):
        tipo = 'contrato'
        quem = instance.inquilino.nome
        onde = _endereco_curto(instance.imovel)
        quando = date.today().strftime('%Y%m%d')
    elif isinstance(instance, LaudoVistoria):
        tipo = 'laudo'
        quem = instance.get_tipo_display()
        onde = _endereco_curto(instance.imovel)
        quando = (instance.data or date.today()).strftime('%Y%m%d')
    elif isinstance(instance, Recibo):
        tipo = 'recibo'
        quem = instance.quem_pagou or instance.contrato.inquilino.nome
        onde = mes_ano_abreviado(instance.periodo_inicio).replace('/', '-') or 'sem-periodo'
        quando = None  # já embutido em "onde" (mes-ano)
    else:
        raise ValueError(f'Tipo não suportado para nome_arquivo: {type(instance).__name__}')

    partes = [_TIPO_LABEL[tipo], instance.codigo, slugify(quem)[:40], slugify(onde)[:40]]
    if quando:
        partes.append(quando)
    if versao:
        partes.append(f'v{versao}')
    return '_'.join(p for p in partes if p) + '.pdf'
```

Exemplos:
- Contrato: `Contrato_CTR-0042_joao-silva_rua-das-flores-123_20260708_v2.pdf`
- Laudo: `Laudo_LAU-0055_vistoria-de-entrada_rua-das-flores-123_20260301_v1.pdf`
- Recibo: `Recibo_REC-0231_joao-silva_mar-2026_v1.pdf`

Import circular: `identidade.py` importa `Contrato`/`LaudoVistoria`/`Recibo` de
`.models` **dentro da função** (não no topo do módulo) — mesmo padrão já usado
em `imoveis/pdf.py:registrar_documento_gerado` (linha 75), porque
`models.py` vai importar `IdentificavelMixin` de `identidade.py` no topo do
arquivo (import no sentido oposto).

---

# Critérios de aceite

- [ ] `imoveis/identidade.py` criado com `IdentificavelMixin`, `mes_ano_abreviado`
      e `nome_arquivo(instance, versao=None)` totalmente implementados.
- [ ] `nome_arquivo` produz nomes sem acentos/caracteres especiais (só
      `[a-z0-9-_.]`) para os 3 tipos (Contrato, Laudo, Recibo).
- [ ] `Imovel`, `Contrato`, `Recibo`, `LaudoVistoria` herdam de
      `IdentificavelMixin` e definem `PREFIXO_CODIGO` + `rotulo_curto` +
      `rotulo_longo`.
- [ ] `__str__` de todos os models permanece inalterado.
- [ ] `python manage.py check` sem erros; nenhuma migration gerada
      (`makemigrations --check` não deve acusar mudança de schema).
- [ ] `codigo` de um objeto não salvo (`pk=None`) não levanta exceção.

---

# Riscos

- **Ordem de herança**: `class Imovel(IdentificavelMixin, models.Model)` —
  o mixin vem antes de `models.Model` no MRO para não conflitar com métodos
  do Django; `IdentificavelMixin` não define `__init__` nem mexe em `Meta`,
  então é seguro.
- **Formatação de data em `rotulo_curto`/`rotulo_longo`**: usar f-string com
  `:%m/%y`/`:%d/%m/%Y` direto no Python (não depende de `USE_L10N`/locale do
  Django) — evita divergência entre ambientes.
- **`slugify` e truncagem em `nome_arquivo`**: `django.utils.text.slugify`
  (padrão, sem `allow_unicode=True`) já remove acentos — não usar
  `allow_unicode=True` por engano (voltaria a gerar caracteres não-ASCII no
  Windows). Truncar cada segmento em 40 chars antes de montar o nome evita
  path muito longo com endereços extensos.
- **Campos opcionais do Recibo**: `periodo_inicio`, `parcela_atual`,
  `parcela_total` podem ser `None` — o rótulo precisa degradar sem quebrar
  (já coberto acima); não assumir que estarão preenchidos.
