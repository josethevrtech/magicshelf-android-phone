import os
#!/usr/bin/env python3
"""Make a private Lepton runtime; never edit Steam's installed runtime or user data."""
import hashlib,json,pathlib,shutil
base=pathlib.Path(os.environ['MAGICSHELF_DATA_DIR'])
source=pathlib.Path.home()/'.local/share/Steam/steamapps/common/Lepton'
runtime=pathlib.Path(os.environ['MAGICSHELF_CACHE_DIR'])/'lepton'
stamp=runtime.parent/'runtime-patches.json'
digest=hashlib.sha256((source/'lepton').read_bytes()).hexdigest()
if stamp.exists():
    assert json.loads(stamp.read_text())['upstream_launcher_sha256']==digest,'Lepton changed; review private runtime before upgrading'
    assert json.loads(stamp.read_text())['version']==(source/'version.txt').read_text().strip(),'Lepton image version changed; review before upgrading'
    assert json.loads(stamp.read_text()).get('tablet_schema')==2,'Private runtime needs tablet multi-app update'
    print('Private runtime already prepared')
    raise SystemExit(0)
assert not runtime.exists(),'Unfinished runtime exists; inspect it before retrying'
runtime.mkdir(parents=True)
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
    assert text.count(old)==1, f'Unexpected runtime source: {name}'
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
patch('liblepton/networking.sh',
      '''    if [[ "${LEPTON_NO_PORT_FORWARDING:-false}" != "false" ]]; then
        PODMAN_NETWORK_OPTIONS+=" -t $(adb_port) -t $(lldb_port) -t $(gdb_port)"
    else
        PODMAN_NETWORK_OPTIONS+=" -t auto"
        PODMAN_NETWORK_OPTIONS+=" -u auto"
    fi''',
      '    # Local tablet control uses podman exec, not network debugging.\n    PODMAN_NETWORK_OPTIONS+=" -t none -u none"')
patch('liblepton/properties.sh',
      'local TIMEZONE_STR="$(readlink /etc/localtime)"',
      'local TIMEZONE_STR="${TABLET_TIMEZONE:-UTC}"')
stamp.write_text(json.dumps({'upstream_launcher_sha256':digest,'version':(source/'version.txt').read_text().strip(),'tablet_schema':2,
    'patches':['persistent Android data','normal multi-app package installation','2 GiB container memory cap','no inbound port forwarding','timezone']},indent=2))
print('Private persistent runtime prepared')
