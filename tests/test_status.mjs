// SPDX-License-Identifier: MIT
import test from 'node:test';
import assert from 'node:assert/strict';
import { buildDiagnostics } from '../rootfs/opt/noVNC/app/buzz-status.js';

test('diagnostics exclude unknown fields and raw logs at every level', () => {
    const privateValue = '/config/private-recording.wav';
    const report = buildDiagnostics({
        image_version: '0.1.2-dev', buzz_version: '1.4.5', desktop: privateValue,
        gpu: {state: 'available', uuid: 'private-device-id'}, uptime_seconds: 25,
        environment: {token: 'secret'}, logs: privateValue,
        events: [{seconds: 1, desktop: 'ready', gpu: 'available', transcript: privateValue}, null],
    }, true, true);
    const encoded = JSON.stringify(report);
    for (const value of [privateValue, 'private-device-id', 'secret', 'environment']) {
        assert.ok(!encoded.includes(value));
    }
    assert.equal(report.current.desktop, 'unknown');
    assert.equal(report.current.gpu, 'available');
    assert.equal(report.desktop_connected, true);
});

test('download remains useful before status is available and bounds event history', () => {
    const empty = buildDiagnostics(null, false, false);
    assert.equal(empty.image_version, 'unknown');
    assert.equal(empty.current.gpu, 'unknown');
    assert.equal(empty.status_received_recently, false);
    const report = buildDiagnostics({events: Array(100).fill({seconds: 3, desktop: 'ready'})}, true, false);
    assert.equal(report.events.length, 40);
});
