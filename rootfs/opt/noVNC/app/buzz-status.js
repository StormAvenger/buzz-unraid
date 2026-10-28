// SPDX-License-Identifier: MIT
// These are availability checks, not a claim about the backend of a running job.
const gpuMessages = {
    checking: ['Checking GPU…', 'Running a small CUDA computation. No model download is needed.'],
    available: ['GPU available', 'CUDA computation and Faster Whisper capability checks passed. Individual jobs still use the backend selected in Buzz.'],
    unavailable: ['GPU unavailable', 'Check the Unraid NVIDIA Driver plugin and the container’s GPU selection, then restart the container.'],
    failed: ['GPU check failed', 'The GPU could not complete its compatibility check. Check the NVIDIA driver and GPU selection.'],
    timeout: ['GPU check timed out', 'The GPU did not respond within 45 seconds. Check the NVIDIA driver, then restart the container.'],
    cpu: ['CPU mode', 'Force CPU is enabled in Buzz. Turn it off in Buzz settings to use an available GPU.'],
    unknown: ['GPU status unavailable', 'The container status service is not responding. Retry the connection or download diagnostics.'],
};

export function setupStatus(toolbar, UI) {
    const gpu = document.createElement('details');
    gpu.className = 'buzz-gpu';
    const summary = document.createElement('summary');
    const description = document.createElement('p');
    gpu.append(summary, description);
    toolbar.querySelector('nav').before(gpu);
    const diagnostics = document.createElement('button');
    diagnostics.type = 'button';
    diagnostics.id = 'buzz-diagnostics';
    diagnostics.textContent = 'Diagnostics';
    diagnostics.title = 'Download a technical status report. No recordings, transcripts, credentials, or private paths.';
    toolbar.querySelector('nav').append(diagnostics);
    const overlay = document.getElementById('buzz-startup');
    const title = document.getElementById('buzz-startup-title');
    const message = document.getElementById('buzz-startup-message');
    const retry = document.getElementById('buzz-retry');
    const started = Date.now();
    let latest = null;
    let everReady = false;
    let lastSuccess = 0;
    let lastAdvance = 0;

    function render() {
        const fresh = latest && Date.now() - lastSuccess < 15000 && Date.now() - lastAdvance < 20000;
        const ready = fresh && latest.desktop === 'ready' && UI.connected;
        const state = fresh ? (latest.cpu_mode ? 'cpu' : latest.gpu?.state) : 'unknown';
        const [label, explanation] = gpuMessages[state] || gpuMessages.unknown;
        summary.textContent = label;
        description.textContent = explanation;
        gpu.dataset.state = state;
        overlay.hidden = Boolean(ready);
        if (ready) everReady = true;
        const delayed = Date.now() - started > 30000;
        retry.hidden = !delayed && !everReady;
        title.textContent = everReady ? 'Reconnecting to Buzz…' : 'Starting Buzz…';
        if (!fresh) {
            message.textContent = 'Waiting for container status. Keep this page open; if it stays here, retry or download diagnostics from the top bar.';
        } else if (latest.desktop === 'stopped') {
            message.textContent = 'Buzz has stopped. Its supervisor should reopen it automatically. If this repeats, download diagnostics.';
        } else if (latest.desktop === 'delayed') {
            message.textContent = 'Buzz is taking longer than expected. You can retry the connection or download diagnostics without restarting your jobs.';
        } else if (latest.desktop === 'ready') {
            message.textContent = 'Buzz is ready. Connecting your browser to the desktop…';
        } else {
            message.textContent = 'Preparing Buzz’s window. First startup can take a little longer.';
        }
    }

    async function poll() {
        try {
            const response = await fetch(`./buzz-status.json?t=${Date.now()}`, {
                cache: 'no-store', credentials: 'same-origin', signal: AbortSignal.timeout(5000),
            });
            if (!response.ok) throw new Error('Status unavailable');
            const data = await response.json();
            if (data.schema !== 1) throw new Error('Unsupported status');
            if (data.updated_at !== latest?.updated_at) lastAdvance = Date.now();
            latest = data;
            lastSuccess = Date.now();
        } catch {
            // Never include exception text, URLs, or browser history in reports.
        }
        render();
        window.setTimeout(poll, 2000);
    }
    retry.addEventListener('click', () => window.location.reload());
    diagnostics.addEventListener('click', () => {
        // Deliberately export a schema, not raw logs or a DOM/environment dump.
        const report = buildDiagnostics(latest, UI.connected,
            Date.now() - lastSuccess < 15000 && Date.now() - lastAdvance < 20000);
        const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], {type: 'application/json'}));
        const link = document.createElement('a');
        link.href = url;
        link.download = 'buzz-diagnostics.json';
        link.click();
        window.setTimeout(() => URL.revokeObjectURL(url), 10000);
    });
    new MutationObserver(render).observe(document.documentElement,
        {attributes: true, attributeFilter: ['class']});
    render();
    poll();
}

export function buildDiagnostics(latest, connected, recent) {
    const cleanState = (value, allowed) => allowed.includes(value) ? value : 'unknown';
    const cleanVersion = value => typeof value === 'string' && /^[0-9A-Za-z.+-]{1,48}$/.test(value) ? value : 'unknown';
    const cleanEvent = (event = {}) => ({
        seconds: Number.isSafeInteger(event.seconds) && event.seconds >= 0 ? event.seconds : 0,
        desktop: cleanState(event.desktop, ['starting', 'ready', 'delayed', 'stopped']),
        gpu: cleanState(event.gpu, Object.keys(gpuMessages)),
        cpu_mode: event.cpu_mode === true,
    });
    return {
        schema: 1,
        privacy: 'Technical checks only. No raw logs, media, transcripts, credentials, private paths, hostnames, IP addresses, or GPU identifiers.',
        image_version: cleanVersion(latest?.image_version),
        buzz_version: cleanVersion(latest?.buzz_version),
        status_received_recently: recent === true,
        desktop_connected: connected === true,
        current: cleanEvent({seconds: latest?.uptime_seconds, desktop: latest?.desktop,
            gpu: latest?.gpu?.state, cpu_mode: latest?.cpu_mode}),
        events: Array.isArray(latest?.events) ? latest.events.slice(-40).map(event => cleanEvent(event || {})) : [],
    };
}
