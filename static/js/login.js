function switchView(viewName) {
    // 1. Gestion des boutons (visuel)
    const btnInfo = document.getElementById('btn-info');
    const btnDev = document.getElementById('btn-dev');
    
    if (btnInfo) btnInfo.classList.remove('active');
    if (btnDev) btnDev.classList.remove('active');

    const activeBtn = document.getElementById('btn-' + viewName);
    if (activeBtn) activeBtn.classList.add('active');

    // 2. Gestion du contenu (Afficher/Cacher)
    const viewInfo = document.getElementById('view-info');
    const viewDev = document.getElementById('view-dev');

    if (viewName === 'info') {
        if (viewDev) viewDev.style.display = 'none';
        if (viewInfo) {
            viewInfo.style.display = 'block';
            viewInfo.style.opacity = 0;
            setTimeout(() => viewInfo.style.opacity = 1, 50);
        }
    } else {
        if (viewInfo) viewInfo.style.display = 'none';
        if (viewDev) {
            viewDev.style.display = 'block';
            viewDev.style.opacity = 0;
            setTimeout(() => viewDev.style.opacity = 1, 50);
        }
    }
}

function togglePassword() {
    let passwordInput = document.getElementById("password-field");
    let icon = document.getElementById("password-icon");
    let btn = document.getElementById("toggle-btn");

    if (passwordInput.type === "password") {
        passwordInput.type = "text";
        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");
    } else {
        passwordInput.type = "password";
        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");
    }

    btn.blur();
}
