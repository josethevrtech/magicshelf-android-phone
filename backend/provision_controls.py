import os
#!/usr/bin/env python3
from pathlib import Path
import json,subprocess
base=Path(os.environ['MAGICSHELF_DATA_DIR'])
vr=Path(os.environ['MAGICSHELF_DATA_DIR'])
def android(*args):return subprocess.check_output(['podman','exec','lepton-magicshelf-phone','/system/bin/'+args[0],*args[1:]],text=True).strip()
stamp=base/'phone-controls-provisioned.json'
if not stamp.exists():
 original={'quick_tiles':android('settings','get','secure','sysui_qs_tiles'),'brightness':android('settings','get','system','screen_brightness')}
 level=json.loads((vr/'android-settings.json').read_text()).get('brightness',.7)
 value=round((max(.25,min(1,level))-.25)/.75*255)
 android('settings','put','system','screen_brightness_mode','0')
 android('settings','put','system','screen_brightness',str(value))
 android('settings','put','secure','sysui_qs_tiles','dark,dnd')
 stamp.write_text(json.dumps(original,indent=2)+'\n')
 print('Phone controls configured; previous tile list and brightness recorded.')
else:print('Phone controls already configured; user preferences retained.')

# Lepton omits LineageParts. Android Display settings crashes while inflating
# its LiveDisplay preference. Hide only that unsupported page in this private
# tablet; text size and brightness remain available on the VR phone itself.
parts=subprocess.run(['podman','exec','lepton-magicshelf-phone','/system/bin/pm','path','org.lineageos.lineageparts'],text=True,capture_output=True,timeout=15)
if parts.returncode not in (0,1):raise RuntimeError(parts.stderr.strip() or 'Could not inspect Android display support')
if not parts.stdout.strip():
 component='com.android.settings/.Settings$DisplaySettingsActivity'
 display_stamp=base/'phone-display-compatibility.json'
 if not display_stamp.exists():
  android('pm','disable','--user','0',component)
  display_stamp.write_text(json.dumps({'component':component,'reason':'missing-lineageparts','restore_command':'pm default-state --user 0 '+component})+'\n')
  print('Unsupported Android Display page hidden; use Text size on the phone.')

# The Lepton display has no DisplayPowerController: touching Android's stock
# slider crashes SystemUI. Use the slider on the phone's own settings screen.
slider_stamp=base/'phone-brightness-provisioned.json'
if not slider_stamp.exists():
 original=android('settings','--lineage','get','secure','qs_show_brightness_slider')
 android('settings','--lineage','put','secure','qs_show_brightness_slider','0')
 slider_stamp.write_text(json.dumps({'qs_show_brightness_slider':original})+'\n')
 print('Replaced unsupported Android brightness slider with VR phone control.')
