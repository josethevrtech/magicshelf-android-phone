import os
#!/usr/bin/env python3
import pathlib,subprocess,time
base=pathlib.Path(os.environ['MAGICSHELF_DATA_DIR'])
def android(*args):
    return subprocess.run(['podman','exec','lepton-magicshelf-phone','/system/bin/sh','-c',*args],capture_output=True,text=True,timeout=15)
for _ in range(120):
    if android('getprop sys.boot_completed').stdout.strip()=='1':break
    time.sleep(1)
else:raise RuntimeError('Android did not finish booting')
android('setprop persist.sys.pcmode.enabled false; setprop persist.waydroid.multi_windows false')
# Keep approximately 360 dp of width after increasing the physical capture.
android('wm size reset; wm density 320; settings put system accelerometer_rotation 0; settings put system user_rotation 0')
# Lepton boots as a game runtime rather than completing a tablet setup wizard.
# Home navigation and night mode require a completed Android user setup.
android('settings put global device_provisioned 1; settings put secure user_setup_complete 1; cmd uimode night yes')
if not (base/'initialized').exists():
    r=android('settings put system time_12_24 12; settings put system screen_off_timeout 2147483647; settings put global stay_on_while_plugged_in 7; settings put system sound_effects_enabled 0; settings put secure show_ime_with_hard_keyboard 1')
    if r.returncode:raise RuntimeError(r.stderr)
    apk=base/'F-Droid.apk'
    if apk.exists():
        subprocess.run(['podman','cp',str(apk),'lepton-magicshelf-phone:/data/local/tmp/F-Droid.apk'],check=True,timeout=30)
        r=android('cmd_real package install -r /data/local/tmp/F-Droid.apk')
        if 'Success' not in r.stdout:raise RuntimeError(r.stdout+r.stderr)
        android('rm -f /data/local/tmp/F-Droid.apk')
    (base/'initialized').write_text('Lineage tablet initialized\n')
# Match the headset clock without changing its system timezone.
zone=os.environ.get('TABLET_TIMEZONE')
if not zone:
    resolved=str(pathlib.Path('/etc/localtime').resolve())
    zone=resolved.split('/zoneinfo/',1)[-1] if '/zoneinfo/' in resolved else 'UTC'
android('setprop persist.sys.timezone '+__import__('shlex').quote(zone))
android('am broadcast -a android.intent.action.TIMEZONE_CHANGED --es time-zone '+__import__('shlex').quote(zone))
android('am start -a android.intent.action.MAIN -c android.intent.category.HOME -p com.android.launcher3')
print('Persistent Android tablet ready',flush=True)

subprocess.run(["python3",str(pathlib.Path(__file__).resolve().parent/"provision_controls.py")],check=True)

# Downloads are independent of phone readiness and retry safely next start.
subprocess.run(['python3', str(pathlib.Path(__file__).resolve().parent/'provision_apps.py')], check=True)
