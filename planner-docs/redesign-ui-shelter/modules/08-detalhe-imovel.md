# Objetivo

Reskin de `templates/imoveis/imovel_detail.html` conforme
`DESIGN_BRIEF.md` secao 3.4 (padrao Detalhe): action bar, cards de
Informacoes (com badge de status), Galeria de Fotos, Planta/Projeto,
Notificacoes (tabela + modal de exclusao) e, na coluna direita, Contratos e
Laudos de Vistoria (tabelas com empty-state). Nenhum campo, condicional de
categoria (urbano/rural) ou acao e adicionado/removido.

---

# Arquivos afetados

- `templates/imoveis/imovel_detail.html`

---

## Documentacao relacionada

- docs/03_modelagem_dados.md
  Sem impacto (nenhum campo novo exibido).

- docs/07_design_ui_ux.md secao 9 (Cards e Superficies)
  Atualizar com o novo padrao de card (header/body) usado nas telas de
  detalhe.

---

# Dependencias

- Modulo 01 (fundacoes).
- Modulo 02 (chrome).

---

# Criterios de aceite

- [ ] Action bar no topo: Voltar, Editar, Nova Notificacao -- preservados
      exatamente como hoje (mesmas urls/condicoes).
- [ ] Galeria de fotos (quando `fotos` existir) restilizada, mantendo o
      link para abrir a imagem original.
- [ ] Card "Informacoes do Imovel" com badge de status
      (`badge-{{ imovel.status }}`) no header e a lista label-valor (`<dl>`)
      preservando TODOS os campos condicionais atuais: tipo, categoria,
      endereco+numero+complemento, bairro, cidade, area_m2, aluguel do
      contrato ativo (`contrato_ativo.valor_mensal`), proprietario,
      matricula, data/valor de aquisicao, e o bloco condicional
      urbano (`cadastro_prefeitura`) vs. rural (`nirf`/`incra`/`car`),
      descricao.
- [ ] Card "Planta/Projeto" (quando `imovel.planta_projeto` existir),
      preview de imagem (`planta_e_imagem`) e botao de abrir/baixar.
- [ ] Card "Notificacoes" com tabela (Tipo/Titulo/Recebida/Status/Acoes),
      botao "+ Nova", modal de exclusao por notificacao preservado
      (`delNotif{{ n.pk }}`), empty-state.
- [ ] Coluna direita: card "Contratos" (tabela + botao "+ Novo" +
      empty-state) e card "Laudos de Vistoria" (tabela + botao "+ Novo" +
      empty-state), preservando os links (`contrato_detail`, download do
      `l.arquivo`).
- [ ] Nenhuma view, url, form, model ou signal alterada.

---

# Riscos

- Muitos campos condicionais (categoria urbano/rural, planta_projeto,
  fotos) -- testar manualmente com um imovel urbano e um rural para
  garantir que nenhum bloco condicional foi perdido no reskin.
