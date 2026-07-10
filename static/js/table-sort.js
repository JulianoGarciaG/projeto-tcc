/* ============================================================
   Shelter — Ordenacao client-side de tabelas
   Inicializacao automatica por atributo: <table data-sortable-table>

   Reordena as <tr> ja renderizadas do <tbody> ao clicar em um <th
   data-sort="text|date|currency">, sem requisicao de rede e sem
   interferir nos filtros server-side (querystring/GET): a ordenacao
   atua sobre o resultado que ja veio filtrado do backend e nao e
   persistida (recarregar a pagina volta a ordem original).
   ============================================================ */
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('table[data-sortable-table]').forEach(function (table) {
    initSortableTable(table);
  });
});

function initSortableTable(table) {
  var thead = table.querySelector('thead');
  var tbody = table.querySelector('tbody');
  if (!thead || !tbody) return;

  var headers = Array.prototype.slice.call(thead.querySelectorAll('tr:first-child > th[data-sort]'));
  if (!headers.length) return;

  headers.forEach(function (th) {
    th.classList.add('table-sort-th');
    th.tabIndex = 0;
    th.setAttribute('role', 'button');

    var icon = document.createElement('span');
    icon.className = 'table-sort-icon';
    icon.innerHTML = '<i class="bi"></i>';
    th.appendChild(icon);

    th.addEventListener('click', function () {
      ordenarPorColuna(table, th, headers);
    });
    th.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        ordenarPorColuna(table, th, headers);
      }
    });
  });
}

function ordenarPorColuna(table, th, headers) {
  var tbody = table.querySelector('tbody');
  var allHeaders = Array.prototype.slice.call(th.parentNode.children);
  var columnIndex = allHeaders.indexOf(th);
  var type = th.getAttribute('data-sort');

  var direction = 'asc';
  if (table.dataset.sortColumn === String(columnIndex) && table.dataset.sortDirection === 'asc') {
    direction = 'desc';
  }
  table.dataset.sortColumn = String(columnIndex);
  table.dataset.sortDirection = direction;

  var rows = Array.prototype.filter.call(tbody.querySelectorAll(':scope > tr'), function (tr) {
    return !tr.querySelector('.empty-state');
  });

  var items = rows.map(function (tr) {
    var td = tr.children[columnIndex];
    var extracted = extrairValor(td, type);
    return { tr: tr, value: extracted.value, isNull: extracted.isNull };
  });

  items.sort(function (a, b) {
    if (a.isNull && b.isNull) return 0;
    if (a.isNull) return 1;
    if (b.isNull) return -1;

    var result;
    if (type === 'text') {
      result = a.value.localeCompare(b.value, 'pt-BR', { numeric: true, sensitivity: 'base' });
    } else {
      result = a.value < b.value ? -1 : a.value > b.value ? 1 : 0;
    }
    return direction === 'desc' ? -result : result;
  });

  items.forEach(function (item) {
    tbody.appendChild(item.tr);
  });

  headers.forEach(function (h) {
    h.classList.remove('table-sort-active');
    var i = h.querySelector('.table-sort-icon i');
    if (i) i.className = 'bi';
  });
  th.classList.add('table-sort-active');
  var activeIcon = th.querySelector('.table-sort-icon i');
  if (activeIcon) activeIcon.className = direction === 'asc' ? 'bi bi-sort-up' : 'bi bi-sort-down';
}

function extrairValor(td, type) {
  if (!td) return { value: '', isNull: true };

  var clone = td.cloneNode(true);
  var secundario = clone.querySelector('.small.text-muted');
  if (secundario) secundario.remove();
  var texto = clone.textContent.trim();

  if (texto === '' || texto === '—') {
    return { value: '', isNull: true };
  }

  if (type === 'date') {
    var partes = texto.split('/');
    if (partes.length !== 3) return { value: '', isNull: true };
    var comparavel = partes[2] + partes[1].padStart(2, '0') + partes[0].padStart(2, '0');
    return { value: comparavel, isNull: false };
  }

  if (type === 'currency') {
    var numerico = texto.replace(/[^\d,.-]/g, '').replace(/\./g, '').replace(',', '.');
    var num = parseFloat(numerico);
    if (isNaN(num)) return { value: 0, isNull: true };
    return { value: num, isNull: false };
  }

  return { value: texto.toLocaleLowerCase('pt-BR'), isNull: false };
}
