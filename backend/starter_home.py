"""Seed the untouched Lepton home once; leave customized launchers alone."""
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile

DATABASE = '/data/user/0/com.android.launcher3/databases/launcher.db'
HOME = 'com.android.launcher3'
ITEMS = [
    ('Web browser', 'de.baumann.browser', -101, 0, 0, 0),
    ('Music', 'org.fossify.musicplayer', -101, 1, 1, 0),
    ('Video', 'org.videolan.vlc', -101, 2, 2, 0),
    ('Get apps', 'com.aurora.store', -101, 3, 3, 0),
    ('Notes', 'org.fossify.notes', -100, 1, 0, 0),
    ('Calendar', 'org.fossify.calendar', -100, 1, 1, 0),
    ('Clock', 'org.fossify.clock', -100, 1, 2, 0),
    ('Calculator', 'com.darkempire78.opencalculator', -100, 1, 3, 0),
    ('Files', 'org.fossify.filemanager', -100, 1, 0, 1),
    ('Gallery', 'org.fossify.gallery', -100, 1, 1, 1),
    ('Podcasts', 'de.danoeh.antennapod', -100, 1, 2, 1),
    ('Radio', 'net.programmierecke.radiodroid2', -100, 1, 3, 1),
    ('F-Droid apps', 'com.looker.droidify', -100, 1, 0, 2),
    ('Video streams', 'org.schabi.newpipe', -100, 1, 2, 2),
]


def populate(connection, components):
    rows = connection.execute('select title,intent from favorites').fetchall()
    if len(rows) > 1 or any('com.android.settings/' not in (row[1] or '') for row in rows):
        return False
    connection.execute('update favorites set cellX=1,cellY=2 where intent like ?', ('%com.android.settings/%',))
    for title, package, container, screen, x, y in ITEMS:
        component = components[package]
        intent = ('#Intent;action=android.intent.action.MAIN;category=android.intent.category.LAUNCHER;'
                  'launchFlags=0x10200000;component=' + component + ';end')
        connection.execute('insert into favorites (title,intent,container,screen,cellX,cellY,spanX,spanY,itemType,rank) '
                           'values (?,?,?,?,?,?,1,1,0,?)', (title, intent, container, screen, x, y, x))
    connection.commit()
    return True


def seed(base, android, container):
    marker = base/'starter-home-configured.json'
    if marker.exists():
        return
    components = {}
    for _, package, *_ in ITEMS:
        output = android('cmd_real', 'package', 'resolve-activity', '--brief', '-a',
                         'android.intent.action.MAIN', '-c', 'android.intent.category.LAUNCHER', '-p', package)
        component = next((line.strip() for line in output.splitlines() if line.startswith(package + '/')), None)
        if not component:
            return
        components[package] = component
    owner = android('stat', '-c', '%u:%g', DATABASE).strip()
    android('am', 'force-stop', HOME)
    try:
        with tempfile.TemporaryDirectory(prefix='phone-home-', dir=base) as directory:
            db = Path(directory)/'launcher.db'
            subprocess.run(['podman', 'cp', container + ':' + DATABASE, str(db)], check=True, capture_output=True)
            # Keep the untouched database for recovery without resetting user data.
            backup = base/'starter-home-original.db'
            if not backup.exists():
                backup.write_bytes(db.read_bytes())
                backup.chmod(0o600)
            connection = sqlite3.connect(db)
            try:
                changed = populate(connection, components)
            finally:
                connection.close()
            if changed:
                subprocess.run(['podman', 'cp', str(db), container + ':' + DATABASE], check=True, capture_output=True)
                android('chown', owner, DATABASE)
                android('restorecon', DATABASE)
            marker.write_text(json.dumps({'seeded': changed}) + '\n')
    finally:
        android('am', 'start', '-a', 'android.intent.action.MAIN', '-c', 'android.intent.category.HOME', '-p', HOME)