document.addEventListener('DOMContentLoaded', function () {
    const attachments = document.getElementById('attachments');
    const fileChosen = document.getElementById('file-chosen');
    if (attachments && fileChosen) {
        attachments.addEventListener('change', function () {
            if (this.files && this.files.length > 0) {
                if (this.files.length === 1) {
                    fileChosen.textContent = this.files[0].name;
                } else {
                    fileChosen.textContent = this.files.length + ' fichiers sélectionnés';
                }
            } else {
                fileChosen.textContent = '';
            }
        });
    }
});

// Dropzone logic for messages list
if (typeof Dropzone !== 'undefined') {
    Dropzone.autoDiscover = false;
}

document.addEventListener('DOMContentLoaded', function () {
    if (typeof Dropzone === 'undefined') return;

    function formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(1) + ' MB';
    }

    function initDropzone() {
        window.myDropzone = new Dropzone("#my-dropzone", {
            url: "/add_message",
            autoProcessQueue: false,
            uploadMultiple: true,
            parallelUploads: 10,
            maxFiles: 10,
            maxFilesize: 10,
            clickable: "#clickable-attach",
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

                const previews = document.getElementById('dropzone-previews');
                if (previews) previews.appendChild(file.previewElement);
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
        });
    }

    initDropzone();

    document.body.addEventListener('htmx:configRequest', (event) => {
        if (event.detail.elt.id === 'message-form' && window.myDropzone) {
            let formData = event.detail.formData;
            const validFiles = window.myDropzone.getAcceptedFiles();
            validFiles.forEach(file => {
                formData.append('attachments', file);
            });
        }
    });
});

