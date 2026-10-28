#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""cu126 dependency identity, approved-release lookup and local layer evidence.

Only explicit recipe inputs affect the key. Publication never uses the local
bootstrap fallback. All inventories come from clean images without user data.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REPO = 'StormAvenger/buzz-unraid'
IMAGE = 'ghcr.io/stormavenger/buzz-unraid-deps'
API = f'https://api.github.com/repos/{REPO}'
WEB = f'https://github.com/{REPO}/releases/tag/'
INPUTS = ('Dockerfile.deps', 'scripts/collect-sources.py',
          'scripts/release-inventory.py', 'LICENSE', 'THIRD_PARTY_NOTICES.md')


def run(*args, **kwargs):
    return subprocess.check_output(args, text=True, **kwargs).strip()


def dependency_key(root=ROOT):
    paths = list(INPUTS)
    for directory in ('requirements/cu126', 'licenses'):
        paths.extend(str(p.relative_to(root)) for p in (root / directory).rglob('*') if p.is_file())
    digest = hashlib.sha256()
    for name in sorted(paths):
        data = (root / name).read_bytes()
        digest.update(name.encode() + b'\0' + str(len(data)).encode() + b'\0' + data)
    return digest.hexdigest()


def tag(key):
    if not re.fullmatch('[0-9a-f]{64}', key):
        raise ValueError('Invalid dependency key')
    return 'deps-cu126-' + key


def get(url):
    with urlopen(Request(url, headers={'User-Agent': 'buzz-unraid-release',
                                      'Accept': 'application/vnd.github+json'}), timeout=90) as response:
        return response.read()


def validate_record(record, key):
    if (record.get('schema') != 1 or record.get('key') != key or record.get('variant') != 'cu126'
            or record.get('sources') != WEB + tag(key)
            or not re.fullmatch(re.escape(IMAGE) + r'@sha256:[0-9a-f]{64}', record.get('image', ''))
            or not re.fullmatch('[0-9a-f]{40}', record.get('revision', ''))):
        raise ValueError('Invalid or mismatched immutable dependency record')
    return record


class MissingRelease(Exception):
    """Only a missing release permits an explicit local bootstrap."""


def approved(key):
    try:
        release = json.loads(get(API + '/releases/tags/' + tag(key)))
    except HTTPError as error:
        if error.code == 404:
            raise MissingRelease('Publish approved dependency sources and image first') from error
        raise
    if release.get('draft') or release.get('tag_name') != tag(key):
        raise ValueError('Dependency release is not published')
    assets = {a['name']: a for a in release['assets']}
    def asset(name):
        item = assets[name]
        expected_url = f'https://github.com/{REPO}/releases/download/{tag(key)}/{name}'
        if item['browser_download_url'] != expected_url:
            raise ValueError('Unexpected dependency asset origin')
        data = get(expected_url)
        expected = sums[name]
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('Dependency asset checksum mismatch: ' + name)
        return data
    checksum_url = f'https://github.com/{REPO}/releases/download/{tag(key)}/SHA256SUMS'
    if assets['SHA256SUMS']['browser_download_url'] != checksum_url:
        raise ValueError('Unexpected checksum origin')
    sums = {}
    for line in get(checksum_url).decode().splitlines():
        match = re.fullmatch(r'([0-9a-f]{64})  ([A-Za-z0-9_.-]+)', line)
        if not match or match[2] in sums:
            raise ValueError('Malformed dependency checksums')
        sums[match[2]] = match[1]
    record = validate_record(json.loads(asset('dependency-image.json')), key)
    inventory = json.loads(asset('inventory.json'))
    manifest = json.loads(asset('source-manifest.json'))
    if manifest.get('failures') != [] or not manifest.get('archives'):
        raise ValueError('Incomplete dependency sources')
    parts = sorted(n for n in assets if re.fullmatch(r'sources.tar.part\d{3}', n))
    if not parts or parts != [f'sources.tar.part{i:03d}' for i in range(len(parts))]:
        raise ValueError('Missing dependency source parts')
    # GitHub computes these digests from uploaded bytes. Do not download 3 GB on
    # every app build merely to compare the immutable source reference.
    for name in parts + ['notices.tar.gz']:
        if assets[name].get('digest') != 'sha256:' + sums[name] or assets[name]['size'] <= 0:
            raise ValueError('Missing or mismatched source asset digest: ' + name)
    return record, inventory


def inspect(image):
    return json.loads(run('docker', 'image', 'inspect', image))[0]


def verify_image(record):
    run('docker', 'pull', '--platform', 'linux/amd64', record['image'])
    info = inspect(record['image'])
    labels = info['Config'].get('Labels', {})
    if labels.get('org.stormavenger.buzz.dependency-key') != record['key']:
        raise ValueError('Dependency image label does not match source identity')
    if labels.get('org.stormavenger.buzz.variant') != 'cu126':
        raise ValueError('Unsupported dependency variant')


def build(args):
    key = dependency_key()
    try:
        record, _ = approved(key)
        verify_image(record)
        image = record['image']
        sources = record['sources']
    except MissingRelease:
        if not args.bootstrap:
            raise
        # Explicitly local/CI only. Never a production publication fallback.
        image = 'buzz-unraid-deps:cu126-' + key
        subprocess.run(['docker', 'build', '--platform', 'linux/amd64', '-f', 'Dockerfile.deps',
                        '--build-arg', 'DEPENDENCY_KEY=' + key, '-t', image, '.'], cwd=ROOT, check=True)
        sources = WEB + tag(key)
    subprocess.run(['docker', 'build', '--platform', 'linux/amd64',
                    '--build-arg', 'DEPS_IMAGE=' + image,
                    '--build-arg', 'DEPENDENCY_KEY=' + key,
                    '--build-arg', 'DEPENDENCY_SOURCES=' + sources,
                    '--build-arg', 'IMAGE_VERSION=' + args.version,
                    '--build-arg', 'SOURCE_REVISION=' + args.revision,
                    '-t', args.image, '.'], cwd=ROOT, check=True)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps({'key': key, 'image': image, 'sources': sources}, indent=2) + '\n')


def package_identity(inventory):
    return {kind: sorted((p['name'].lower(), p['version']) for p in inventory[kind])
            for kind in ('python', 'ubuntu')}, inventory['pyav']


def checksums(directory):
    lines = []
    for path in sorted(directory.iterdir()):
        if path.is_file() and path.name != 'SHA256SUMS':
            with path.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            lines.append(digest + '  ' + path.name)
    (directory / 'SHA256SUMS').write_text('\n'.join(lines) + '\n')


def link_sources(directory):
    record, dep_inventory = approved(dependency_key())
    inventory = json.loads((directory / 'inventory.json').read_text())
    if package_identity(inventory) != package_identity(dep_inventory):
        raise ValueError('App packages differ from dependency sources; rebuild dependencies')
    (directory / 'dependency-image.json').write_text(json.dumps(record, indent=2) + '\n')
    (directory / 'SOURCE-README.txt').write_text(
        'Matching dependency sources, their checksums and extraction instructions:\n' + record['sources'] + '\n'
        'App patches, Dockerfiles and build recipes: this app release Source code archive.\n'
        'Keep both release records when redistributing the application.\n')
    import tarfile
    with tarfile.open(directory / 'notices.tar.gz', 'w:gz') as archive:
        archive.add(directory / 'notices', arcname='notices')
    checksums(directory)


def layer_proof(args):
    record = json.loads(Path(args.reference).read_text())
    base = inspect(record['image'])
    first = inspect(args.image)
    # Copy only tracked, public build sources. Ignored appdata never enters this context.
    names = run('git', 'ls-files', '-z', cwd=ROOT).split('\0')
    import shutil
    with tempfile.TemporaryDirectory(prefix='buzz-layer-proof-') as temporary:
        context = Path(temporary)
        for name in names:
            source = ROOT / name
            if not source.is_file():
                continue
            target = context / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            shutil.copymode(source, target)
        css = context / 'rootfs/opt/buzz/toolbar.css'
        if not css.exists():
            candidates = list((context / 'rootfs').rglob('*.css'))
            if len(candidates) != 1:
                raise ValueError('Choose the toolbar stylesheet explicitly')
            css = candidates[0]
        css.write_text(css.read_text() + '\n/* Disposable layer reuse verification. */\n')
        command = ['docker', 'build', '--platform', 'linux/amd64', '-t', 'buzz-unraid:layer-proof']
        labels = first['Config']['Labels']
        for name, value in {'DEPS_IMAGE': record['image'], 'DEPENDENCY_KEY': record['key'],
                            'DEPENDENCY_SOURCES': record['sources'],
                            'IMAGE_VERSION': labels['org.opencontainers.image.version'],
                            'SOURCE_REVISION': labels['org.opencontainers.image.revision']}.items():
            command.extend(['--build-arg', name + '=' + value])
        subprocess.run(command + [str(context)], check=True)
    second = inspect('buzz-unraid:layer-proof')
    layers = base['RootFS']['Layers']
    if not layers or any(i['RootFS']['Layers'][:len(layers)] != layers for i in (first, second)):
        raise ValueError('Dependency layers were not reused byte-for-byte')
    if first['RootFS']['Layers'] == second['RootFS']['Layers']:
        raise ValueError('Rootfs-only change did not produce a different app image')
    sizes = [i['Size'] - base['Size'] for i in (first, second)]
    if any(size < 0 or size > 64 * 1024 * 1024 for size in sizes):
        raise ValueError('App overhead exceeds 64 MiB; inspect accidental dependency writes')
    output = {'schema': 1, 'key': record['key'], 'dependency_layers': layers,
              'app_layers': first['RootFS']['Layers'], 'changed_rootfs_layers': second['RootFS']['Layers'],
              'dependency_bytes': base['Size'], 'app_overhead_bytes': sizes,
              'dependency_prefix_identical': True, 'change': 'toolbar CSS comment only'}
    Path(args.output).write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps({'dependency_prefix_identical': True, 'app_overhead_bytes': sizes}))


def main():
    parser = argparse.ArgumentParser(__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('key')
    commands.add_parser('resolve')
    build_parser = commands.add_parser('build')
    build_parser.add_argument('--bootstrap', action='store_true', help='Allow a local unpublished dependency build in CI/development only')
    build_parser.add_argument('--image', default='buzz-unraid:ci')
    build_parser.add_argument('--version', default='0.1.2-dev')
    build_parser.add_argument('--revision', default='unknown')
    build_parser.add_argument('--output', default='release-output/dependency-reference.json')
    link = commands.add_parser('link')
    link.add_argument('directory', type=Path)
    sums = commands.add_parser('checksums')
    sums.add_argument('directory', type=Path)
    record = commands.add_parser('record')
    record.add_argument('digest')
    record.add_argument('revision')
    record.add_argument('output', type=Path)
    proof = commands.add_parser('layer-proof')
    proof.add_argument('--reference', default='release-output/dependency-reference.json')
    proof.add_argument('--image', default='buzz-unraid:ci')
    proof.add_argument('--output', default='release-output/layer-proof.json')
    args = parser.parse_args()
    if args.command == 'key':
        print(dependency_key())
    elif args.command == 'resolve':
        record, _ = approved(dependency_key())
        verify_image(record)
        print(json.dumps(record))
    elif args.command == 'build':
        build(args)
    elif args.command == 'link':
        link_sources(args.directory)
    elif args.command == 'checksums':
        checksums(args.directory)
    elif args.command == 'record':
        key = dependency_key()
        record = validate_record({'schema': 1, 'key': key, 'variant': 'cu126', 'image': IMAGE + '@' + args.digest,
                                  'revision': args.revision, 'sources': WEB + tag(key)}, key)
        args.output.write_text(json.dumps(record, indent=2) + '\n')
    elif args.command == 'layer-proof':
        layer_proof(args)


if __name__ == '__main__':
    main()
