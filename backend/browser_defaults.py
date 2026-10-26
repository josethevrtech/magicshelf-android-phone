"""Initial browser defaults for a phone, without replacing user choices later."""
from pathlib import Path
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET

PACKAGE = 'de.baumann.browser'
PREFERENCES = '/data/user/0/'+PACKAGE+'/shared_prefs/'+PACKAGE+'_preferences.xml'


def configure(base, android, container):
    marker = base/'starter-browser-configured'
    if marker.exists():
        return
    android('am', 'start', '-W', '-n', PACKAGE+'/.activity.BrowserActivity')
    time.sleep(.3)
    android('am', 'force-stop', PACKAGE)
    owner = android('stat', '-c', '%u:%g', PREFERENCES).strip()
    with tempfile.TemporaryDirectory(prefix='phone-browser-', dir=base) as directory:
        path = Path(directory)/'preferences.xml'
        subprocess.run(['podman', 'cp', container+':'+PREFERENCES, str(path)], check=True, capture_output=True)
        tree=ET.parse(path);root=tree.getroot()
        values = {'customRedirects':'[]', 'saved_redirect_ok':'yes',
                  'favoriteURL':'https://www.google.com/', 'openTabs':'https://www.google.com/',
                  'mCurrentUrl':'https://www.google.com/'}
        for name, value in values.items():
            element=next((e for e in root if e.get('name')==name),None)
            if element is None:
                element=ET.SubElement(root,'string',{'name':name})
            element.text=value
        # Preserve browser defaults, tracking protection and permission prompts.
        # Only disable third-party URL substitution for the mainstream services.
        tree.write(path,encoding='utf-8',xml_declaration=True)
        subprocess.run(['podman', 'cp', str(path), container+':'+PREFERENCES], check=True, capture_output=True)
        android('chown',owner,PREFERENCES)
        android('restorecon',PREFERENCES)
    marker.touch()