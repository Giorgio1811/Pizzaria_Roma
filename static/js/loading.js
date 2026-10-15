// 'pageshow' também dispara ao voltar com o botão Voltar do navegador,
// evitando que a tela de carregamento fique presa
window.addEventListener('pageshow', function () {
    var overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.classList.add('hidden');
});

document.querySelectorAll('form').forEach(function (form) {
    form.addEventListener('submit', function () {
        var overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.classList.remove('hidden');
    });
});
