# Objetivo

Corrigir o dimensionamento da logo dentro da sidebar para que ela preencha visualmente toda a largura disponível do container `.sidebar-brand`, eliminando o espaço vazio à direita causado pela combinação atual de `object-fit: contain` + `object-position: left center` + padding do container.

---

# Arquivos afetados

- `static/css/custom.css`
  - Ajustar o bloco `#sidebar .sidebar-brand` (padding do container) e `#sidebar .sidebar-brand img` (regras de dimensionamento da imagem), atualmente:
    ```css
    #sidebar .sidebar-brand {
      padding: .75rem 1rem;
      border-bottom: 1px solid rgba(255,255,255,.08);
      display: block;
      height: 72px;
      box-sizing: border-box;
    }

    #sidebar .sidebar-brand img {
      display: block;
      width: 100%;
      height: 100%;
      object-fit: contain;
      object-position: left center;
    }
    ```
  - Causa raiz: `object-fit: contain` respeita a proporção do SVG e é limitado pela altura do container (72px menos padding vertical); como a logo é proporcionalmente mais larga que alta, o `contain` a redimensiona por altura e sobra espaço horizontal — que o `object-position: left center` empurra para a direita, tornando visível o vazio.
  - Correção proposta (a validar visualmente pelo Engineer com o asset real `Shelter_LOGO_white.svg`):
    1. Trocar `object-position: left center` por `object-position: center center` (ou remover a propriedade, já que o padrão é `50% 50%`), para eliminar a ancoragem à esquerda que expõe o vazio.
    2. Avaliar reduzir o padding horizontal do `.sidebar-brand` (ex.: de `1rem` para `.5rem`–`.75rem`) para dar mais espaço horizontal à imagem.
    3. Caso o objetivo seja a logo ocupar toda a largura mesmo que corte levemular a altura, considerar `object-fit: cover` combinado com `width: 100%; height: 100%` — só usar se o corte vertical não deformar/cortar elementos importantes do SVG (validar visualmente).
    4. Alternativa mais segura (recomendada): manter `object-fit: contain`, remover o `object-position` fixo (deixar centralizado) e aumentar a altura do container `.sidebar-brand` (ex.: de `72px` para `88px`–`96px`) se o layout permitir, dando mais área vertical para a imagem crescer proporcionalmente até preencher melhor a largura.
  - Escolher **uma** das alternativas acima (2+4 recomendadas em conjunto) e aplicar; validar visualmente no navegador comparando com a proporção real do arquivo `static/assets/Shelter_LOGO_white.svg`.

---

## Documentação relacionada

- `docs/07_design_ui_ux.md`
  Seção 1 ("Diretrizes de Aplicação da Logo") e Seção 5 ("Sidebar"): atualizar caso os valores de padding/altura do container da marca sejam alterados de forma a divergir do que está implícito na documentação atual (a documentação não especifica dimensões exatas do container da logo, portanto o impacto é baixo/opcional).

---

# Dependências

Nenhuma. Módulo independente dos módulos 01 e 02 (mexe em seletores distintos), mas caso o módulo 02 renomeie a classe `brand-full`, este módulo deve usar o nome de classe final da tag `<img>`.

---

# Critérios de aceite

- [ ] A logo preenche visualmente a largura útil do container `.sidebar-brand` (sem espaço vazio perceptível à direita ou à esquerda) na sidebar expandida (260px).
- [ ] A logo não é distorcida (proporção original do SVG preservada) nem cortada de forma que remova elementos gráficos importantes.
- [ ] Validado visualmente em pelo menos duas larguras de tela desktop (>=769px) e observado que o comportamento é consistente (sidebar não colapsa mais, conforme módulos 01-02).

---

# Riscos

- Médio: ajustes de `object-fit`/`object-position`/padding podem exigir iteração visual manual (o Planner não pode validar renderização); o Engineer deve inspecionar no navegador antes de finalizar.
- Se `object-fit: cover` for escolhido, há risco de corte de partes do logo em telas com proporções diferentes — preferir a alternativa 4 (contain + centralizado + ajuste de altura) como padrão mais seguro caso não haja tempo para validação visual extensiva.
