# Objetivo

Exibir a Planta/Projeto do imovel (`Imovel.planta_projeto`) diretamente na tela de visualizacao (`imovel_detail.html`), sem exigir que o usuario entre em "Editar" para ver o arquivo.

---

# Arquivos afetados

- `imoveis/templatetags/imoveis_tags.py`
  - Adicionar dois filtros novos, reaproveitando o padrao ja existente no arquivo (filtro `brl`): `is_pdf(arquivo)` e `is_imagem(arquivo)`, que recebem um `FieldFile` (ou `None`) e retornam `True`/`False` conforme a extensao do nome do arquivo (`.pdf` para `is_pdf`; `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp` para `is_imagem`). Tratar o caso de `arquivo` vazio/`None` retornando `False` sem levantar excecao.

- `templates/imoveis/imovel_detail.html`
  - Adicionar uma nova secao `section-card` "Planta/Projeto", condicionada a `{% if imovel.categoria == "urbano" and imovel.planta_projeto %}` (o campo so existe para imoveis urbanos — ver `imoveis/models.py:58` e `docs/04_regras_de_negocio.md` secao 4). Posicionar logo apos a secao "Informacoes do Imovel" (dentro da coluna `col-lg-4`) ou como card independente na coluna principal — escolher o local que melhor se encaixe visualmente ao lado das demais secoes existentes.
  - Dentro do card: se `is_pdf`, renderizar um `<iframe>` apontando para `imovel.planta_projeto.url` (altura fixa, ex. 500px, `class="w-100"`); se `is_imagem`, renderizar uma miniatura clicavel (`<img>` dentro de `<a target="_blank">`, mesmo padrao ja usado na galeria de fotos do proprio template, linhas 26-33); caso nenhum dos dois, exibir apenas um link de download ("Formato nao suportado para pre-visualizacao" + botao "Abrir em nova aba").
  - O template ja tem `{% load imoveis_tags %}` na linha 2 — nao e necessario adicionar novo `{% load %}`.

---

## Documentacao relacionada

- `docs/07_design_ui_ux.md`
  Sem impacto obrigatorio; se o mantenedor documentar os componentes de visualizacao de arquivo (galeria de fotos, anexos), este e um bom ponto de referencia futuro para incluir o preview de planta/projeto no mesmo padrao.

- `docs/03_modelagem_dados.md`
  Sem impacto (nenhum campo novo; `planta_projeto` ja documentado na secao 2.2).

- `docs/04_regras_de_negocio.md`
  Sem impacto (regra de campo condicional por categoria, secao 4, ja documentada e nao muda).

---

# Dependencias

Nenhuma. Modulo independente.

---

# Criterios de aceite

- [ ] Imovel urbano com `planta_projeto` do tipo PDF: a tela de detalhe exibe o PDF embutido (iframe), sem precisar entrar em "Editar".
- [ ] Imovel urbano com `planta_projeto` do tipo imagem (jpg/png/etc.): a tela de detalhe exibe uma miniatura clicavel que abre o arquivo em nova aba.
- [ ] Imovel urbano sem `planta_projeto`: a secao nao aparece (sem card vazio).
- [ ] Imovel rural: a secao nunca aparece (campo nao existe para essa categoria).
- [ ] `python manage.py check` sem erros; nenhum teste existente quebra (`python manage.py test imoveis`).
- [ ] (Opcional, recomendado) novo teste simples renderizando `imovel_detail.html` com um `Imovel` urbano com `planta_projeto` setado (via `SimpleUploadedFile`) e verificando que a URL do arquivo aparece no HTML.

---

# Riscos

- Baixo: arquivos muito grandes (PDFs de planta com muitas paginas/alta resolucao) podem deixar o iframe lento para carregar — nao ha novo processamento no servidor, o arquivo e servido como estatico via `MEDIA_URL`, entao o impacto e so no navegador do usuario.
- Nomes de arquivo com extensao em maiusculas (ex.: `.PDF`) devem ser tratados via `.lower()` no filtro, para nao cair no caso "formato nao suportado" incorretamente.
