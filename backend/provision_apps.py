#!/usr/bin/env python3
"""Install a curated phone once, preserving user removals and store updates."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import urllib.request
from starter_home import seed
from browser_defaults import configure as configure_browser

CONTAINER = 'lepton-magicshelf-phone'
CATALOG = Path(__file__).with_name('starter_apps.json')


def android(*args, timeout=120):
    result = subprocess.run(['podman', '--events-backend', 'none', 'exec', CONTAINER,
                             '/system/bin/' + args[0], *args[1:]],
                            capture_output=True, text=True, timeout=timeout, check=True)
    return result.stdout


def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def download(record, target):
    """Only publish a complete APK matching the release's pinned digest."""
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == record['sha256']:
        return
    request = urllib.request.Request(record['url'], headers={'User-Agent': 'MagicShelf-Android-Phone/1'})
    with tempfile.NamedTemporaryFile(dir=target.parent, suffix='.partial', delete=False) as output:
        temporary = Path(output.name)
        try:
            digest = hashlib.sha256()
            size = 0
            with urllib.request.urlopen(request, timeout=30) as response:
                if not response.url.startswith('https://'):
                    raise RuntimeError('Insecure APK redirect')
                while chunk := response.read(1024 * 1024):
                    size += len(chunk)
                    if size > record['size']:
                        raise RuntimeError('APK exceeds pinned size')
                    digest.update(chunk)
                    output.write(chunk)
            output.close()
            if size != record['size'] or digest.hexdigest() != record['sha256']:
                raise RuntimeError('APK integrity check failed: ' + record['package'])
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)


def provision(base):
    base.mkdir(parents=True, exist_ok=True)
    with (base/'starter-apps.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        ledger = base/'starter-apps-state.json'
        try:
            state = json.loads(ledger.read_text())
        except FileNotFoundError:
            state = {}
        cache = base/'apps'
        cache.mkdir(exist_ok=True)
        errors = {}
        records = json.loads(CATALOG.read_text())['apps']
        def progress():
            write_json(base/'starter-apps-progress.json', {'ready': sum(r['package'] in state for r in records),
                       'total': len(records), 'errors': errors})
        progress()
        for record in records:
            package = record['package']
            # A successfully handled app belongs to the user from then on.
            # In particular, never reinstall something they chose to uninstall.
            if package in state:
                continue
            try:
                installed = android('cmd_real', 'package', 'list', 'packages', package)
                if 'package:' + package in installed.splitlines():
                    state[package] = {'status': 'already-installed'}
                else:
                    print('Preparing ' + record['label'], flush=True)
                    apk = cache/(package + '.apk')
                    download(record, apk)
                    destination = '/data/local/tmp/magicshelf-' + package + '.apk'
                    try:
                        subprocess.run(['podman', 'cp', str(apk), CONTAINER + ':' + destination],
                                       check=True, timeout=90, capture_output=True)
                        result = android('cmd_real', 'package', 'install', '-r', '-i', 'com.looker.droidify', destination)
                        if 'Success' not in result:
                            raise RuntimeError(result.strip())
                    finally:
                        android('rm', '-f', destination)
                    apk.unlink(missing_ok=True)
                    state[package] = {'status': 'installed', 'versionCode': record['versionCode']}
                write_json(ledger, state)
                print(record['label'] + ': ready', flush=True)
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
                errors[package] = str(error)
                print(record['label'] + ': retry next start: ' + str(error), flush=True)
            progress()
        configure(base)
        if not errors:
            seed(base, android, CONTAINER)
        return errors


def configure(base):
    marker = base/'starter-apps-configured'
    if marker.exists():
        return
    # Set only initial defaults; future launches preserve the user's choices.
    methods = android('ime', 'list', '-a', '-s').splitlines()
    keyboard = next((line.strip() for line in methods if line.startswith('org.fossify.keyboard/')), None)
    if keyboard:
        android('ime', 'enable', keyboard)
        android('ime', 'set', keyboard)
    else:
        return  # Retry configuration once the keyboard has downloaded.
    android('settings', 'put', 'secure', 'show_ime_with_hard_keyboard', '1')
    android('settings', 'put', 'secure', 'immersive_mode_confirmations', 'confirmed')
    for setting in ('animator_duration_scale', 'transition_animation_scale', 'window_animation_scale'):
        android('settings', 'put', 'global', setting, '0')
    android('cmd', 'uimode', 'night', 'yes')
    # Use the current system WebView through a tested lightweight browser.
    browser = android('cmd_real', 'package', 'list', 'packages', 'de.baumann.browser')
    if 'package:de.baumann.browser' not in browser.splitlines():
        return
    android('cmd', 'role', 'add-role-holder', '--user', '0', 'android.app.role.BROWSER', 'de.baumann.browser')
    ledger=json.loads((base/'starter-apps-state.json').read_text())
    if ledger.get('de.baumann.browser',{}).get('status')=='installed':
        configure_browser(base, android, CONTAINER)
    for package in ('com.looker.droidify', 'com.aurora.store'):
        android('appops', 'set', package, 'REQUEST_INSTALL_PACKAGES', 'allow')
    for package in ('org.fossify.gallery', 'org.fossify.musicplayer', 'org.fossify.filemanager', 'org.videolan.vlc'):
        android('pm', 'grant', package, 'android.permission.READ_EXTERNAL_STORAGE')
    android('appops', 'set', '--uid', 'org.fossify.filemanager', 'MANAGE_EXTERNAL_STORAGE', 'allow')
    android('appops', 'write-settings')
    marker.touch()


if __name__ == '__main__':
    provision(Path(os.environ['MAGICSHELF_DATA_DIR']))