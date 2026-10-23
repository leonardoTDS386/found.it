
(function () {
    'use strict';

    const form = document.getElementById('cadastro-item-form');
    if (!form) return;

    const campoData = document.getElementById('data');
    const botao = document.getElementById('salvar-cadastro');

    function dataLocalISO() {
        const agora = new Date();
        agora.setMinutes(
            agora.getMinutes() - agora.getTimezoneOffset()
        );
        return agora.toISOString().slice(0, 10);
    }

    campoData.max = dataLocalISO();

    form.addEventListener('submit', function (evento) {
        if (!form.checkValidity()) {
            evento.preventDefault();
            form.reportValidity();
            return;
        }

        if (campoData.value > dataLocalISO()) {
            evento.preventDefault();
            campoData.setCustomValidity(
                'A data da perda não pode ser futura.'
            );
            campoData.reportValidity();
            campoData.setCustomValidity('');
            return;
        }

        botao.disabled = true;
        botao.innerHTML =
            '<span class="spinner-border spinner-border-sm me-2" ' +
            'aria-hidden="true"></span> Salvando...';
    });

    campoData.addEventListener('change', function () {
        campoData.setCustomValidity('');
    });
})();
