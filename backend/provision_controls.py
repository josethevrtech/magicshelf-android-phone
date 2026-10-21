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

# The Lepton display has no DisplayPowerController: touching Android's stock
# slider crashes SystemUI. Use the slider on the phone's own settings screen.
slider_stamp=base/'phone-brightness-provisioned.json'
if not slider_stamp.exists():
 original=android('settings','--lineage','get','secure','qs_show_brightness_slider')
 android('settings','--lineage','put','secure','qs_show_brightness_slider','0')
 slider_stamp.write_text(json.dumps({'qs_show_brightness_slider':original})+'\n')
 print('Replaced unsupported Android brightness slider with VR phone control.')
