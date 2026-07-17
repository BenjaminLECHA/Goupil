document.addEventListener('DOMContentLoaded', function () {
    const menuButtons = document.querySelectorAll('.menu-button');
    if (menuButtons.length > 0) {
        menuButtons.forEach(button => {
            button.addEventListener('click', function () {
                const demandesFilters = document.getElementById('demandes-filters');
                const issuesFilters = document.getElementById('issues-filters');
                if (!demandesFilters || !issuesFilters) return;

                if (this.innerText.includes('Demandes')) {
                    demandesFilters.classList.remove('hidden');
                    issuesFilters.classList.add('hidden');
                } else {
                    demandesFilters.classList.add('hidden');
                    issuesFilters.classList.remove('hidden');
                }
            });
        });
    }
});

// Dropzone logic for issues list
if (typeof Dropzone !== 'undefined') {
    Dropzone.autoDiscover = false;
}

document.addEventListener('DOMContentLoaded', function () {
    const modalContent = document.querySelector("#formModal .modal-content");
    if (!modalContent || typeof Dropzone === 'undefined') return;

    const previewsContainer = document.getElementById('modal-dropzone-previews');

    function formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(1) + ' MB';
    }

    window.demandDropzone = new Dropzone(modalContent, {
        url: window.location.href,
        autoProcessQueue: false,
        uploadMultiple: true,
        parallelUploads: 10,
        maxFiles: 10,
        maxFilesize: 10,
        clickable: "#clickable-attach-modal",
        dictMaxFilesExceeded: "Limite de 10 fichiers atteinte.",
        paramName: "attachments",
        previewTemplate: '<div style="display:none"></div>',


        addedfile: function (file) {

            const pillHtml = `
                <div class="dz-file-pill">
                    <i class="fa-solid fa-paperclip"></i>
                    <span class="pill-name" title="${file.name}">${file.name}</span>
                    <span class="pill-size">${formatSize(file.size)}</span>
                    <button type="button" class="pill-remove" title="Retirer">&times;</button>
                </div>`.trim();

            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = pillHtml;
            file.previewElement = tempDiv.firstChild;

            file.previewElement.querySelector('.pill-remove').addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.removeFile(file);
            });

            if (previewsContainer) previewsContainer.appendChild(file.previewElement);
        },
        removedfile: function (file) {
            if (file.previewElement) file.previewElement.remove();
        },
        error: function (file, msg) {
            if (file.previewElement) {
                file.previewElement.classList.add('pill-error');
                file.previewElement.title = msg;
            }
            if (msg.includes("plus de 10") || msg.includes("limit")) {
                alert("Vous avez atteint la limite de 10 fichiers.");
            }
        },

        thumbnail: function () { },
        uploadprogress: function () { },
        sending: function () { },
        complete: function () { },
        success: function () { },

        init: function () {
            var myDropzone = this;
            var form = document.querySelector("#formModal form");
            var modalContent = document.querySelector("#formModal .modal-content");

            this.on("dragenter", function () {
                modalContent.classList.add("drag-active");
            });

            this.on("dragover", function () {
                modalContent.classList.add("drag-active");
            });

            this.on("dragleave", function () {
                modalContent.classList.remove("drag-active");
            });

            this.on("drop", function () {
                modalContent.classList.remove("drag-active");
            });

            if (form) {
                form.addEventListener("submit", function (e) {
                    const validFiles = myDropzone.getAcceptedFiles();
                    if (validFiles.length > 0) {
                        e.preventDefault();
                        e.stopPropagation();

                        const formData = new FormData(form);
                        validFiles.forEach(file => {
                            formData.append('attachments', file);
                        });

                        fetch(form.action || window.location.href, {
                            method: 'POST',
                            body: formData,
                            headers: { 'X-Requested-With': 'XMLHttpRequest' }
                        }).then(response => {
                            if (response.ok) {
                                window.location.reload();
                            } else {
                                alert("Erreur lors de l'envoi");
                            }
                        });
                    }
                });
            }
        }
    });
});

window.addEventListener("dragover", function (e) { e.preventDefault(); }, false);
window.addEventListener("drop", function (e) { e.preventDefault(); }, false);

