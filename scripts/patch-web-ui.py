#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Add Buzz's toolbar and a small file-manager API to the pinned GUI base."""
from pathlib import Path
import argparse


PATCHES = (
    ("service-worker.js", "    // File-manager downloads are large, one-off GETs; do not cache them.", """    // Status is live data, not an offline shell asset.
    if (url.pathname.endsWith('/buzz-status.json')) return false;

    // File-manager downloads are large, one-off GETs; do not cache them."""),
    ("../base/etc/nginx/default_site.conf", "\troot /opt/noVNC;", """\troot /opt/noVNC;
    # Same authentication as the desktop. Only this allowlisted snapshot is public.
    location = /buzz-status.json {
        alias /tmp/buzz-status/public.json;
        default_type application/json;
        add_header Cache-Control "no-store" always;
    }"""),
    ("index.html", "<body>", """<body>
    <section id="buzz-startup" role="status" aria-live="polite">
        <div class="buzz-startup-card">
            <h1 id="buzz-startup-title">Starting Buzz…</h1>
            <p id="buzz-startup-message">Preparing your transcription workspace. First startup can take a little longer.</p>
            <button id="buzz-retry" type="button" hidden>Retry connection</button>
            <p>You can leave this page open while Buzz starts.</p>
        </div>
    </section>"""),
    ("index.html", "</head>", """    <!-- Buzz file-transfer toolbar -->
    <link rel="stylesheet" href="app/buzz-toolbar.css?v=UNIQUE_VERSION">
    <script type="module" src="app/buzz-toolbar.js?v=UNIQUE_VERSION"></script>
</head>"""),
    ("app/fileManager.js", "        'disabled': [],", "        'disabled': [],\n        'directory': [],"),
    ("app/fileManager.js", "    function openFileManager() {", "    function openFileManager(initialPath = '/') {"),
    ("app/fileManager.js", "            currentPath = '/';", "            currentPath = initialPath;"),
    ("app/fileManager.js", "                        renderFileList(data.req.path, data.files);", """                        renderFileList(data.req.path, data.files);
                        moduleEventCallbacks['directory'].forEach(func => func(data.req.path));"""),
    ("app/fileManager.js", """        open: function() {
            return openFileManager();
        },""", """        open: function(initialPath = '/') {
            return openFileManager(initialPath);
        },

        upload: function(files) {
            if (!webSocketConnected || !fileManagerOpened || !files.length) return false;
            if (activeUpload) return false;
            uploadFiles(files);
            return true;
        },"""),
)


def patch(root):
    # Validate every anchor before writing: upstream drift must fail the build.
    changes = {}
    for relative, old, new in PATCHES:
        path = root / relative
        source = changes.get(path, path.read_text())
        if source.count(old) != 1:
            raise ValueError(f"GUI base changed: expected one patch anchor in {relative}")
        changes[path] = source.replace(old, new, 1)
    for path, source in changes.items():
        path.write_text(source)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path("/opt/noVNC"))
    patch(parser.parse_args().root)
