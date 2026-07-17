document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('.menu-button');

    buttons.forEach(button => {
        button.addEventListener('click', function() {
            // Retire la classe 'active' de tous les boutons
            buttons.forEach(btn => btn.classList.remove('active'));

            // Ajoute la classe 'active' au bouton cliqué
            this.classList.add('active');
        });
    });

    const search = document.querySelector('.search-input');
    search.addEventListener('keyup', function() {
        buttons.forEach(btn => btn.classList.remove('active'));
    });
});