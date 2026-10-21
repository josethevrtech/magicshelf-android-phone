import os
#!/usr/bin/env python3
"""Install the locally verified starter APKs without resetting Android data."""
import hashlib,json,pathlib,subprocess
base=pathlib.Path(os.environ['MAGICSHELF_DATA_DIR'])
container='lepton-magicshelf-phone'
def android(*args,timeout=120):
    return subprocess.run(['podman','exec',container,'/system/bin/'+args[0],*args[1:]],text=True,capture_output=True,check=True,timeout=timeout).stdout
records=json.loads((base/'apps/manifest.json').read_text())
for record in records:
    package=record['package']
    apk=base/'apps'/f"{package}_{record['versionCode']}.apk"
    with apk.open('rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=record['sha256']:raise RuntimeError('Hash mismatch: '+package)
    installed=android('dumpsys','package',package)
    if f"versionCode={record['versionCode']} " in installed:
        print(package+': already installed',flush=True)
        continue
    target='/data/local/tmp/'+apk.name
    subprocess.run(['podman','cp',str(apk),container+':'+target],check=True,timeout=90)
    try:
        result=android('cmd_real','package','install','-r','-i','org.fdroid.fdroid',target)
        if 'Success' not in result:raise RuntimeError(result)
        print(package+': installed',flush=True)
    finally:android('rm','-f',target)
methods=android('ime','list','-a','-s').splitlines()
keyboard=next(m.strip() for m in methods if m.startswith('rkr.simplekeyboard.inputmethod/'))
print(android('ime','enable',keyboard).strip(),flush=True)
print(android('ime','set',keyboard).strip(),flush=True)
android('settings','put','secure','show_ime_with_hard_keyboard','1')
android('cmd','uimode','night','yes')
for setting in ['animator_duration_scale','transition_animation_scale','window_animation_scale']:
    android('settings','put','global',setting,'0')
for package in ['org.fossify.gallery','org.fossify.musicplayer','org.videolan.vlc']:
    android('pm','grant',package,'android.permission.READ_EXTERNAL_STORAGE')
android('cmd','role','add-role-holder','--user','0','android.app.role.BROWSER','de.baumann.browser')
(base/'starter-apps-installed.json').write_text(json.dumps(records,indent=2)+'\n')
print('Starter apps, keyboard, and dark theme configured.',flush=True)
