/* ============================================================
   Shelter - Toggle de visualizacao da listagem de Imoveis
   (Modulo 06). Exclusivo de imovel_list.html.
   Alterna entre a vista Cards e a vista Tabela e persiste a
   escolha em localStorage (chave 'shelterImovelView'), aplicando
   a preferencia salva ao carregar a pagina.
   Escopado por IDs unicos (#imovel-view-toggle / #imovel-view-*)
   para nao interferir com outras paginas.
   ============================================================ */
(function () {
  'use strict';

  var STORAGE_KEY = 'shelterImovelView';
  var toggle = document.getElementById('imovel-view-toggle');
  var cardsView = document.getElementById('imovel-view-cards');
  var tableView = document.getElementById('imovel-view-table');

  if (!toggle || !cardsView || !tableView) { return; }

  var items = toggle.querySelectorAll('.segmented-item');

  function applyView(view) {
    var isTable = view === 'table';
    cardsView.style.display = isTable ? 'none' : '';
    tableView.style.display = isTable ? '' : 'none';

    items.forEach(function (btn) {
      var active = btn.getAttribute('data-view') === view;
      btn.classList.toggle('active', active);
      btn.setAttribute('aria-selected', active ? 'true' : 'false');
    });
  }

  function readSavedView() {
    try {
      var saved = localStorage.getItem(STORAGE_KEY);
      return saved === 'table' ? 'table' : 'cards';
    } catch (e) {
      return 'cards';
    }
  }

  items.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var view = btn.getAttribute('data-view');
      applyView(view);
      try { localStorage.setItem(STORAGE_KEY, view); } catch (e) {}
    });
  });

  applyView(readSavedView());
})();
