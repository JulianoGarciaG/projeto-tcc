/* ============================================================
   Shelter — Máscaras (IMask) e datepickers (Flatpickr)
   Inicialização automática por atributo:
     - data-mask="telefone" | data-mask="moeda"
     - data-flatpickr  (datas em dd/mm/aaaa)
   ============================================================ */
document.addEventListener('DOMContentLoaded', function () {

  /* ---------- Máscaras (IMask) ---------- */
  if (window.IMask) {
    document.querySelectorAll('[data-mask="telefone"]').forEach(function (el) {
      IMask(el, {
        mask: [
          { mask: '(00) 0000-0000' },
          { mask: '(00) 00000-0000' },
        ],
      });
    });

    // Sem separador de milhar: o backend (Django, localize) espera "1500,00".
    document.querySelectorAll('[data-mask="moeda"]').forEach(function (el) {
      IMask(el, {
        mask: Number,
        scale: 2,
        radix: ',',
        mapToRadix: ['.'],
        thousandsSeparator: '',
        padFractionalZeros: true,
        normalizeZeros: true,
        min: 0,
      });
    });
  }

  /* ---------- Datepicker (Flatpickr) ---------- */
  if (window.flatpickr) {
    if (flatpickr.l10ns && flatpickr.l10ns.pt) {
      flatpickr.localize(flatpickr.l10ns.pt);
    }
    document.querySelectorAll('[data-flatpickr]').forEach(function (el) {
      flatpickr(el, {
        dateFormat: 'd/m/Y',
        allowInput: true,
        disableMobile: true,
      });
    });
  }
});
