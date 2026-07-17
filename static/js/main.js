
function setupFlashAutoClose() {
    const flashes = document.querySelectorAll('.flash-message:not(.fade-out-setup)');
    flashes.forEach(flash => {
        flash.classList.add('fade-out-setup');

        flash.addEventListener('animationend', () => flash.remove());
    });
}

document.addEventListener('DOMContentLoaded', setupFlashAutoClose);
document.body.addEventListener('htmx:load', setupFlashAutoClose);
