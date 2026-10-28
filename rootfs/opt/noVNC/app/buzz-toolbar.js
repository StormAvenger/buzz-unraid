// SPDX-License-Identifier: MIT
// Reuse the base's file manager, transfer progress, and server-side path checks.
import FileManager from './fileManager.js';
// Match index.html's versioned URL so this is the active desktop connection.
import UI from './ui.js?v=UNIQUE_VERSION';
import KeyTable from '../core/input/keysym.js';

const toolbar = document.createElement('header');
toolbar.id = 'buzz-toolbar';
toolbar.innerHTML = `
    <a class="buzz-brand" href="./" aria-label="Buzz home">Buzz</a>
    <span class="buzz-toolbar-hint">Your transcription workspace</span>
    <nav aria-label="Workspace controls">
        <button id="buzz-home" type="button" disabled title="Close live recording and return to the main page">
            <i class="fas fa-arrow-left" aria-hidden="true"></i> Back to main page
        </button>
        <button id="buzz-upload" type="button" disabled>
            <i class="fas fa-upload" aria-hidden="true"></i> Upload files
        </button>
        <button id="buzz-download" type="button" disabled>
            <i class="fas fa-download" aria-hidden="true"></i> Download transcripts
        </button>
    </nav>
    <input id="buzz-upload-input" type="file" multiple hidden>
    <span id="buzz-transfer-status" role="status" class="visually-hidden">Connecting to file tools</span>`;
document.body.prepend(toolbar);

const uploadButton = document.getElementById('buzz-upload');
const homeButton = document.getElementById('buzz-home');
const downloadButton = document.getElementById('buzz-download');
const picker = document.getElementById('buzz-upload-input');
const status = document.getElementById('buzz-transfer-status');
const modal = document.getElementById('fmgr_modal');
const title = document.getElementById('fmgr_modal_label');
const sidebarButton = document.getElementById('noVNC_file_manager_button');
const help = document.createElement('p');
help.id = 'buzz-transfer-help';
help.className = 'text-body-secondary mb-3';
modal.querySelector('.fmgr-dialog').prepend(help);
modal.querySelector('.fmgr-current-path').parentElement.classList.add('buzz-folder-path');

let mode = null;
let pendingFiles = null;
const updateReady = () => {
    const ready = !sidebarButton.classList.contains('noVNC_hidden');
    uploadButton.disabled = downloadButton.disabled = !ready;
    status.textContent = ready ? 'File tools ready' : 'File tools unavailable';
};
new MutationObserver(updateReady).observe(sidebarButton, {attributes: true, attributeFilter: ['class']});
updateReady();

const updateDesktopReady = () => {
    homeButton.disabled = !UI.connected || !UI.rfb || UI.rfb.viewOnly;
};
new MutationObserver(updateDesktopReady).observe(document.documentElement,
    {attributes: true, attributeFilter: ['class']});
updateDesktopReady();

homeButton.addEventListener('click', () => {
    if (!UI.connected || !UI.rfb || UI.rfb.viewOnly) return;
    const desktop = UI.rfb;
    // Buzz handles this shortcut itself; no page reload or process restart.
    try {
        desktop.sendKey(KeyTable.XK_Control_L, 'ControlLeft', true);
        desktop.sendKey(KeyTable.XK_Alt_L, 'AltLeft', true);
        desktop.sendKey(KeyTable.XK_Home, 'Home', true);
    } finally {
        desktop.sendKey(KeyTable.XK_Home, 'Home', false);
        desktop.sendKey(KeyTable.XK_Alt_L, 'AltLeft', false);
        desktop.sendKey(KeyTable.XK_Control_L, 'ControlLeft', false);
    }
    desktop.focus();
});

// Keep the desktop below the toolbar and resize it on narrow screens as well.
new ResizeObserver(() => {
    document.documentElement.style.setProperty('--buzz-toolbar-height', `${toolbar.offsetHeight}px`);
    window.dispatchEvent(new Event('resize'));
}).observe(toolbar);

function openManager(nextMode, files = null) {
    mode = nextMode;
    pendingFiles = files;
    modal.classList.add('buzz-transfer-mode');
    modal.classList.toggle('buzz-download-mode', mode === 'download');
    title.textContent = mode === 'upload' ? 'Upload files' : 'Download transcripts';
    help.textContent = mode === 'upload'
        ? 'After uploading, click + in Buzz and open your recordings from /uploads.'
        : 'Choose a transcript or subtitle below to save it to your computer.';
    // Open first so the base's shown.bs.modal handler cannot reset the folder.
    FileManager.open(mode === 'upload' ? '/uploads' : '/output');
    bootstrap.Modal.getOrCreateInstance(modal).show();
}

uploadButton.addEventListener('click', () => {
    picker.value = '';
    picker.click();
});
picker.addEventListener('change', () => {
    if (picker.files.length) openManager('upload', picker.files);
});
downloadButton.addEventListener('click', () => openManager('download'));

// Wait for the server to confirm /uploads before starting any selected files.
FileManager.addEventListener('directory', path => {
    if (mode === 'upload' && path === '/uploads' && pendingFiles) {
        const files = pendingFiles;
        pendingFiles = null;
        if (!FileManager.upload(files)) {
            status.textContent = 'Upload could not start. Close this window and try again.';
            help.textContent = status.textContent;
        }
    }
    const list = modal.querySelector('.fmgr-file-list');
    let empty = modal.querySelector('.buzz-empty-files');
    if (!list.children.length && mode) {
        if (!empty) {
            empty = document.createElement('p');
            empty.className = 'buzz-empty-files text-body-secondary py-4 text-center';
            list.after(empty);
        }
        empty.textContent = mode === 'download'
            ? 'No transcripts yet. Completed exports will appear here.'
            : 'Your uploaded recordings will appear here.';
    } else if (empty) {
        empty.remove();
    }
    for (const button of list.querySelectorAll('[data-fmgr-file-action="download"]')) {
        const name = button.closest('.fmgr-file-list-entry').getAttribute('data-fmgr-file-name');
        button.textContent = 'Download';
        button.setAttribute('aria-label', `Download ${name}`);
    }
});

modal.addEventListener('hidden.bs.modal', () => {
    mode = null;
    pendingFiles = null;
    modal.classList.remove('buzz-transfer-mode', 'buzz-download-mode');
    title.textContent = 'File Manager';
    help.textContent = '';
    modal.querySelector('.buzz-empty-files')?.remove();
});

// Give the existing picker a visible label too; the sidebar remains available.
const chooseFiles = modal.querySelector('.fmgr-upload-btn');
chooseFiles.append(document.createTextNode(' Choose files'));
