# SPDX-License-Identifier: MIT
"""Small, allowlisted status snapshots. Never read application logs or media."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

STATE = Path('/tmp/buzz-status')
GPU_CODES = {'checking', 'available', 'unavailable', 'failed', 'timeout', 'cpu'}


def write_json(path, value):
    temporary = path.with_suffix(f'.{os.getpid()}.tmp')
    temporary.write_text(json.dumps(value))
    temporary.replace(path)


def install_readiness(application, window):
    """Only the live Qt event loop can mark a displayed Buzz window ready."""
    from PyQt6.QtCore import QTimer
    timer = QTimer(application)
    displayed = False

    def beat():
        nonlocal displayed
        displayed = displayed or window.isVisible()
        if displayed:
            write_json(STATE / 'heartbeat.json', {
                'pid': os.getpid(),
                'cpu_mode': os.getenv('BUZZ_FORCE_CPU', 'false').lower() == 'true',
            })

    timer.timeout.connect(beat)
    timer.start(2000)
    application._container_readiness_timer = timer


def ui_ready(pid, directory=STATE, now=None):
    path = directory / 'heartbeat.json'
    try:
        data = json.loads(path.read_text())
        fresh = 0 <= (time.time() if now is None else now) - path.stat().st_mtime < 20
        return data.get('pid') == pid and fresh, data.get('cpu_mode') is True
    except (OSError, ValueError, TypeError, AttributeError):
        return False, False


def gpu_probe():
    # All output is generated here. No nvidia-smi serials, UUIDs, paths, or raw
    # exception messages can enter the browser report.
    import torch
    import ctranslate2
    if not torch.cuda.is_available():
        return {'state': 'unavailable'}
    a = torch.ones((32, 32), device='cuda', dtype=torch.float32)
    result = a @ a
    torch.cuda.synchronize()
    if result[0, 0].item() != 32:
        return {'state': 'failed'}
    supported = ctranslate2.get_supported_compute_types('cuda', 0)
    if 'int8_float32' not in supported:
        return {'state': 'failed'}
    return {'state': 'available'}


def finish_probe(process, started, now):
    if process.poll() is None:
        if now - started < 45:
            return None
        process.kill()
        process.communicate()
        return {'state': 'timeout'}
    output, _ = process.communicate()
    try:
        data = json.loads(output) if process.returncode == 0 else {}
        code = data.get('state')
        return {'state': code if code in {'available', 'unavailable', 'failed'} else 'failed'}
    except (ValueError, AttributeError):
        return {'state': 'failed'}


def monitor(pid):
    version = Path('/usr/share/buzz-container/VERSION').read_text().strip()
    version = version if re.fullmatch(r'[0-9A-Za-z.+-]{1,48}', version) else 'unknown'
    started = time.monotonic()
    gpu = {'state': 'checking'}
    process = subprocess.Popen([sys.executable, __file__, '--probe'],
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    events = []
    previous = None
    try:
        while True:
            elapsed = int(time.monotonic() - started)
            alive = Path(f'/proc/{pid}').exists()
            ready, cpu_mode = ui_ready(pid)
            state = 'ready' if ready else ('starting' if elapsed < 120 else 'delayed')
            if not alive:
                state = 'stopped'
            if gpu['state'] == 'checking':
                result = finish_probe(process, started, time.monotonic())
                if result:
                    gpu = result
            current = (state, gpu['state'], cpu_mode)
            if current != previous:
                events.append({'seconds': elapsed, 'desktop': state,
                               'gpu': gpu['state'], 'cpu_mode': cpu_mode})
                events = events[-40:]
                previous = current
            write_json(STATE / 'public.json', {
                'schema': 1, 'image_version': version, 'buzz_version': '1.4.5',
                'desktop': state, 'gpu': gpu, 'cpu_mode': cpu_mode,
                'uptime_seconds': elapsed, 'updated_at': int(time.time()),
                'events': events,
            })
            if not alive:
                return
            time.sleep(2)
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate()


if __name__ == '__main__':
    if sys.argv[1] == '--probe':
        try:
            print(json.dumps(gpu_probe()))
        except Exception:
            print(json.dumps({'state': 'failed'}))
    else:
        monitor(int(sys.argv[1]))
