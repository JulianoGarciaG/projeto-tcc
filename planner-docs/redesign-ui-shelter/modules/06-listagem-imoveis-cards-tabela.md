# Objetivo

Reskin de `templates/imoveis/imovel_list.html` conforme `DESIGN_BRIEF.md`
secao 3.3: restilizar a vista Cards ja existente (foto/placeholder
hachurado, badge de status, chips tipo/categoria, dono, acoes) e **criar**
a vista Tabela (hoje inexistente), com o segmented control Cards/Tabela e
persistencia da preferencia em localStorage via JS vanilla dedicado.

---

# Arquivos afetados

- `templates/imoveis/imovel_list.html`
- `static/js/imovel-view-toggle.js` (novo arquivo)

---

## Documentacao relacionada

- docs/07_design_ui_ux.md secao 10 (Tabelas)
  Documentar a nova vista Tabela de Imoveis (colunas: Endereco,
  Bairro/Cidade, Tipo, Proprietario, Status, Acoes).

- docs/01_visao_geral.md
  Sem impacto (nenhum requisito funcional novo -- e apenas alternativa de
  visualizacao da mesma listagem).

---

# Dependencias

- Modulo 01 (fundacoes -- inclui a classe utilitaria de placeholder
  hachurado `--ph`).
- Modulo 02 (chrome).

---

# Criterios de aceite

- [ ] Barra de filtros (Buscar/Status/Tipo + Filtrar/Limpar) preservada
      funcionalmente, com o novo visual.
- [ ] Result bar com contador "N imovel(is) encontrado(s)" + segmented
      toggle Cards/Tabela + botao primario laranja "Novo Imovel".
- [ ] Vista Cards (grid 3 colunas): imagem ou placeholder hachurado (usando
      `--ph` do modulo 01) + badge de status no canto; endereco (link para
      `imovel_detail`), bairro/cidade, chips tipo/categoria, proprietario;
      rodape com 3 botoes de acao (Ver neutro, Editar laranja-soft, Excluir
      danger-soft) -- preservando o modal de exclusao ja existente
      (`modalExcluir{{ im.pk }}`).
- [ ] Vista Tabela (nova, markup a ser criado): colunas Endereco,
      Bairro/Cidade, Tipo, Proprietario, Status (badge), Acoes (3 icones) --
      usando o mesmo queryset `imoveis` ja passado pela view, sem
      duplicar consultas (reutilizar o mesmo `{% for im in imoveis %}` em
      um segundo bloco visualmente oculto, ou uma unica iteracao que
      alimenta ambas as vistas via `display:none`/`display:block`).
- [ ] `static/js/imovel-view-toggle.js` alterna a exibicao entre os dois
      containers no clique dos itens do segmented, persiste a escolha em
      localStorage (ex. chave `shelterImovelView`) e aplica a preferencia
      salva ao carregar a pagina.
- [ ] Empty state (`{% empty %}`) presente em ambas as vistas.
- [ ] Nenhuma mudanca em `imoveis/views.py` (a view `imovel_list` continua
      passando o mesmo contexto: `imoveis`, `q`, `status`, `tipo`,
      `status_choices`, `tipo_choices`).

---

# Riscos

- Duplicar o loop Django (`{% for im in imoveis %}`) para gerar Cards e
  Tabela separadamente e mais simples de implementar mas roda o loop duas
  vezes -- para querysets pequenos (uso tipico do sistema) o impacto de
  performance e desprezivel; documentar a escolha no proprio template via
  comentario.
- Esta e a unica tela com toggle de vista -- garantir que o JS nao
  interfira com o JS de outras paginas (escopar por `id`/classe unica do
  container).
