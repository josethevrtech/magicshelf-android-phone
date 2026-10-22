#!/usr/bin/env python3
"""Prepare Android support atomically without touching Android's saved data."""
import fcntl
import hashlib
import json
import os
import pathlib
import shutil
import tempfile


def build(source, runtime):
    shutil.copytree(source/'liblepton',runtime/'liblepton',symlinks=True)
    for name in ['lepton','LICENSE.md','README.md']:
        shutil.copy2(source/name,runtime/name)
    for name in ['sysbake','sysbake.xattrs','version.txt','LICENSES']:
        (runtime/name).symlink_to(source/name)
    (runtime/'images').mkdir()
    for entry in (source/'images').iterdir():
        if entry.name=='rootfs_overlay':shutil.copytree(entry,runtime/'images'/entry.name,symlinks=True)
        else:(runtime/'images'/entry.name).symlink_to(entry)
    # Lepton's cmd wrapper moves every installed app into one game's directory.
    # A tablet needs Android's normal per-package paths and permission handling.
    (runtime/'images/rootfs_overlay/system/bin/cmd').write_text('#!/system/bin/sh\nexec /system/bin/cmd_real "$@"\n')
    def patch(name,old,new):
        path=runtime/name
        text=path.read_text()
        if text.count(old)!=1: raise RuntimeError('Android support changed. Update Android Phone, then try again.')
        path.write_text(text.replace(old,new))
    patch('liblepton/liblepton.sh',
          'LEPTON_DATA_DIR="${HOME}/.local/share/lepton/contexts"',
          'LEPTON_DATA_DIR="${MAGICSHELF_BACKEND_DATA_DIR}/android"')
    patch('liblepton/liblepton.sh',
          'function remove_prefix()\n{\n    if [[ -n "${LEPTON_PREFIX:-}" ]]; then\n        prepare_baked_data_for_removal',
          'function remove_prefix()\n{\n    if [[ -n "${LEPTON_PREFIX:-}" ]]; then\n        # Persistent tablet owns its Android data across sessions.\n        :')
    patch('liblepton/mounting.sh',
          'function setup_podman_base()\n{',
          'function setup_podman_base()\n{\n    podman_cmdline --memory=2g --memory-swap=2304m')
    patch('liblepton/networking.sh', '    if [[ "${LEPTON_NO_PORT_FORWARDING:-false}" != "false" ]]; then\n        PODMAN_NETWORK_OPTIONS+=" -t $(adb_port) -t $(lldb_port) -t $(gdb_port)"\n    else\n        PODMAN_NETWORK_OPTIONS+=" -t auto"\n        PODMAN_NETWORK_OPTIONS+=" -u auto"\n    fi', '    # Local tablet control uses podman exec, not network debugging.\n    PODMAN_NETWORK_OPTIONS+=" -t none -u none"')
    patch('liblepton/properties.sh',
          'local TIMEZONE_STR="$(readlink /etc/localtime)"',
          'local TIMEZONE_STR="${TABLET_TIMEZONE:-UTC}"')


def prepare():
    source=pathlib.Path(os.environ.get('MAGICSHELF_STEAM_APP_3029110_DIR',pathlib.Path.home()/'.local/share/Steam/steamapps/common/Lepton'))
    cache=pathlib.Path(os.environ['MAGICSHELF_CACHE_DIR']);cache.mkdir(parents=True,exist_ok=True)
    runtime=cache/'lepton';previous=cache/'lepton.previous';stamp=cache/'runtime-patches.json'
    with (cache/'prepare.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if not runtime.exists() and previous.exists(): previous.rename(runtime)
        if not (source/'lepton').is_file():
            raise RuntimeError('Android support is not installed yet. Open this creation in MagicShelf and choose Set up.')
        digest=hashlib.sha256((source/'lepton').read_bytes()).hexdigest()
        expected={'upstream_launcher_sha256':digest,'version':(source/'version.txt').read_text().strip(),'tablet_schema':2}
        try:
            saved=json.loads(stamp.read_text())
            if runtime.is_dir() and all(saved.get(k)==v for k,v in expected.items()):
                return
        except (OSError,ValueError):
            pass
        with tempfile.TemporaryDirectory(prefix='lepton-prepare-',dir=cache) as temp:
            staged=pathlib.Path(temp)/'lepton';staged.mkdir()
            build(source,staged)
            if previous.exists():shutil.rmtree(previous)
            if runtime.exists():runtime.rename(previous)
            try:
                staged.rename(runtime)
                next_stamp=cache/'runtime-patches.next'
                next_stamp.write_text(json.dumps(expected,indent=2)+'\n')
                next_stamp.replace(stamp)
            except BaseException:
                if runtime.exists():shutil.rmtree(runtime)
                if previous.exists():previous.rename(runtime)
                raise
        if previous.exists():shutil.rmtree(previous)


if __name__=='__main__':
    prepare()
    print('Android support is ready.')
