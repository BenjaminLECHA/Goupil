// Récupère les éléments
const modal = document.getElementById('formModal');
const openBtns = [document.getElementById('openModalBtn'), document.getElementById('openModalBtnFab')];
const closeBtn = document.querySelector('.close-modal');

openBtns.forEach(btn => {
    if (btn) {
        btn.onclick = function () {
            modal.style.display = 'block';
        };
    }
});

// Ferme le modal
if (closeBtn) {
    closeBtn.onclick = function () {
        modal.style.display = 'none';
    };
}

// Ferme le modal si on clique en dehors
window.onclick = function (event) {
    if (event.target == modal) {
        modal.style.display = 'none';
    }
};
