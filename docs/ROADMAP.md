# Planned improvements

## Current development: startup and troubleshooting

- A startup screen waits for the real Buzz window and the browser desktop connection. A delayed or disconnected desktop shows guidance and a connection retry button.
- A GPU availability indicator checks CUDA computation and Faster Whisper capabilities once per application start. It also distinguishes Buzz's Force CPU setting. This is not live per-job GPU usage tracking.
- A Diagnostics button downloads a local JSON report of version numbers, readiness, GPU check outcomes, and a bounded status-event history. Reports deliberately exclude raw logs, media, transcripts, credentials, environment dumps, hostnames, IP addresses, private paths, and GPU UUIDs/serials. Nothing is uploaded automatically.

## Saved for later

1. Automatically import browser uploads into Buzz, removing the extra import step.
2. Clearer job status for queued, transcribing, completed, and failed tasks, with easier access to completed downloads.
