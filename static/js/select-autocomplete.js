/* ============================================================
   Shelter — Autocomplete por substring sobre <select> nativo
   Inicialização automática por atributo: data-autocomplete="true"

   O <select> original permanece no DOM (oculto) e continua sendo a
   fonte de verdade: submissão do form, `required` e a dependência
   Imóvel→Contrato (fetch que repopula as <option> de contrato) não
   mudam — este script só adiciona uma "casca" de busca por texto que
   lê as <option> do select a cada digitação (nunca as cacheia), por
   isso funciona tanto em selects estáticos quanto nos repopulados via
   fetch em laudo_form.html / recibo_form.html.
   ============================================================ */
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('select[data-autocomplete]').forEach(function (select) {
    enhanceSelectAutocomplete(select);
  });
});

function enhanceSelectAutocomplete(select) {
  const wrap = document.createElement('div');
  wrap.className = 'autocomplete-wrap';
  select.parentNode.insertBefore(wrap, select);
  wrap.appendChild(select);
  select.classList.add('autocomplete-source');

  const input = document.createElement('input');
  input.type = 'text';
  input.className = select.className.replace('autocomplete-source', '').trim();
  input.autocomplete = 'off';
  input.placeholder = 'Digite para buscar...';
  if (select.disabled) input.disabled = true;

  const list = document.createElement('div');
  list.className = 'autocomplete-list';
  list.hidden = true;

  wrap.appendChild(input);
  wrap.appendChild(list);

  function rotuloDaOpcaoSelecionada() {
    const opt = select.options[select.selectedIndex];
    return opt && opt.value ? opt.textContent : '';
  }

  input.value = rotuloDaOpcaoSelecionada();

  function fecharLista() {
    list.hidden = true;
    list.innerHTML = '';
  }

  function abrirLista(query) {
    const termo = query.trim().toLowerCase();
    const opcoes = Array.prototype.filter.call(select.options, function (opt) {
      return opt.value && opt.textContent.toLowerCase().includes(termo);
    }).slice(0, 30);

    list.innerHTML = '';
    if (!opcoes.length) {
      fecharLista();
      return;
    }
    opcoes.forEach(function (opt) {
      const item = document.createElement('button');
      item.type = 'button';
      item.className = 'autocomplete-item';
      item.textContent = opt.textContent;
      item.addEventListener('mousedown', function (e) {
        // mousedown (não click) dispara antes do blur do input.
        e.preventDefault();
        select.value = opt.value;
        input.value = opt.textContent;
        fecharLista();
        select.dispatchEvent(new Event('change', { bubbles: true }));
      });
      list.appendChild(item);
    });
    list.hidden = false;
  }

  input.addEventListener('input', function () {
    if (select.disabled) return;
    abrirLista(input.value);
  });

  input.addEventListener('focus', function () {
    if (select.disabled) return;
    abrirLista(input.value);
  });

  input.addEventListener('blur', function () {
    // Sem seleção via mousedown: reverte para o rótulo da opção
    // atualmente selecionada no select (evita texto "órfão").
    input.value = rotuloDaOpcaoSelecionada();
    fecharLista();
  });

  input.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      input.blur();
    }
  });

  // Quando o select é repopulado/habilitado por outro script (ex.: fetch
  // de contratos dependente do imóvel em laudo_form.html/recibo_form.html),
  // mantém o input em sincronia com o novo estado.
  select.addEventListener('change', function () {
    if (document.activeElement !== input) {
      input.value = rotuloDaOpcaoSelecionada();
    }
  });

  const observer = new MutationObserver(function () {
    input.disabled = select.disabled;
    if (document.activeElement !== input) {
      input.value = rotuloDaOpcaoSelecionada();
    }
  });
  observer.observe(select, { attributes: true, attributeFilter: ['disabled'], childList: true });
}
