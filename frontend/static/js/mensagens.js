/* Found.it - Avisos temporários (toasts)
 * Mostra os avisos criados pelo servidor (veja templates/_mensagens.html).
 * Os de erro ficam mais tempo na tela.
 */
(function () {
    'use strict';

    document.querySelectorAll('.toast[data-fi-toast]').forEach(function (el) {
        const ehErro = el.classList.contains('fi-toast-erro');
        new bootstrap.Toast(el, { delay: ehErro ? 9000 : 7000 }).show();
    });
})();
