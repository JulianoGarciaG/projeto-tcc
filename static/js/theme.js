/* Shelter - Toggle de tema claro/escuro (modulo 02 do redesign)
   ------------------------------------------------------------------
   - O script inline no <head> do base.html ja aplicou data-theme="dark"
     no <html> antes do primeiro paint (anti-FOUC); aqui so cuidamos do
     toggle, do icone e da persistencia.
   - Persistencia: localStorage, chave 'shelterTheme' ('dark' | 'light').
   - A cada troca dispara 'shelter:theme-changed' no document (detail:
     { theme }) - consumido pelo dashboard para redesenhar os graficos
     Chart.js com as CSS vars do novo tema. */
(function () {
  'use strict';

  var STORAGE_KEY = 'shelterTheme';
  var root = document.documentElement;
  var btn = document.getElementById('theme-toggle');
  var icon = btn ? btn.querySelector('i') : null;

  function currentTheme() {
    return root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  }

  function updateIcon() {
    if (!icon) return;
    // bi-moon-stars no claro (convida ao escuro) / bi-sun no escuro
    icon.className = currentTheme() === 'dark' ? 'bi bi-sun' : 'bi bi-moon-stars';
  }

  function applyTheme(theme) {
    if (theme === 'dark') {
      root.setAttribute('data-theme', 'dark');
    } else {
      root.removeAttribute('data-theme');
    }
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (e) { /* localStorage indisponivel: tema vale so para a pagina */ }
    updateIcon();
    document.dispatchEvent(new CustomEvent('shelter:theme-changed', { detail: { theme: theme } }));
  }

  // Estado inicial do icone (o tema em si ja foi aplicado no <head>)
  updateIcon();

  if (btn) {
    btn.addEventListener('click', function () {
      applyTheme(currentTheme() === 'dark' ? 'light' : 'dark');
    });
  }
})();
