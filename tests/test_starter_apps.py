import hashlib
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'backend'))
import provision_apps as apps
import starter_home
import app_launch


class StarterAppsTests(unittest.TestCase):
    def test_corrupt_download_never_replaces_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'app.apk';target.write_bytes(b'old')
            record={'url':'https://f-droid.org/repo/app.apk','size':3,
                    'sha256':hashlib.sha256(b'yes').hexdigest(),'package':'test.app'}
            response=io.BytesIO(b'bad');response.url=record['url']
            with patch.object(apps.urllib.request,'urlopen',return_value=response), self.assertRaises(RuntimeError):
                apps.download(record,target)
            self.assertEqual(target.read_bytes(),b'old')
            self.assertEqual(list(Path(directory).glob('*.partial')),[])

    def test_removed_app_and_store_updated_app_are_not_reinstalled(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);(base/'starter-apps-state.json').write_text(json.dumps({'test.removed':{'status':'installed'}}))
            catalog=base/'catalog.json';catalog.write_text(json.dumps({'apps':[{'package':'test.removed'}, {'package':'test.updated','label':'Already present'}]}))
            with patch.object(apps,'CATALOG',catalog), patch.object(apps,'android',return_value='package:test.updated\n'), patch.object(apps,'download') as download, patch.object(apps,'configure'), patch.object(apps,'seed'):
                self.assertEqual(apps.provision(base),{})
            download.assert_not_called()
            self.assertEqual(json.loads((base/'starter-apps-state.json').read_text())['test.updated']['status'],'already-installed')

    def test_failed_app_does_not_block_remaining_apps(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);catalog=base/'catalog.json';catalog.write_text(json.dumps({'apps':[{'package':'test.failed','label':'Failed'}, {'package':'test.good','label':'Good'}]}))
            with patch.object(apps,'CATALOG',catalog),patch.object(apps,'android',side_effect=['','package:test.good\n']),patch.object(apps,'download',side_effect=OSError('offline')),patch.object(apps,'configure'),patch.object(apps,'seed'):
                errors=apps.provision(base)
            self.assertIn('test.failed',errors)
            self.assertIn('test.good',json.loads((base/'starter-apps-state.json').read_text()))
            self.assertNotIn('test.failed',json.loads((base/'starter-apps-state.json').read_text()))

    def test_custom_home_is_preserved(self):
        c=sqlite3.connect(':memory:')
        c.execute('create table favorites(title text,intent text)')
        c.execute('insert into favorites values (?,?)',('My app','component=my.custom/.Main'))
        self.assertFalse(starter_home.populate(c,{}))
        self.assertEqual(c.execute('select title from favorites').fetchone()[0],'My app')

    def test_seed_creates_unique_positions_on_untouched_home(self):
        c=sqlite3.connect(':memory:')
        c.execute('create table favorites(title,intent,container,screen,cellX,cellY,spanX,spanY,itemType,rank)')
        c.execute('insert into favorites values (?,?,?,?,?,?,?,?,?,?)',('Settings','component=com.android.settings/.Settings',-100,1,3,4,1,1,0,0))
        components={row[1]:row[1]+'/.Main' for row in starter_home.ITEMS}
        self.assertTrue(starter_home.populate(c,components))
        cells=c.execute('select container,screen,cellX,cellY from favorites').fetchall()
        self.assertEqual(len(cells),len(set(cells)))
        self.assertFalse(starter_home.populate(c,components))

    def test_web_fallback_is_allowlisted_and_native_launch_resolves_alias(self):
        commands=[]
        def android(command):
            commands.append(command)
            if 'list packages' in command:return 'package:org.fossify.musicplayer\n' if 'musicplayer' in command else ''
            if 'resolve-activity' in command:return 'priority=0\norg.fossify.musicplayer/.activities.SplashActivity.Green\n'
            return 'Status: ok'
        app_launch.launch('music',android)
        self.assertIn('-n org.fossify.musicplayer/.activities.SplashActivity.Green',commands[-1])
        app_launch.launch('spotify',android)
        self.assertIn('https://open.spotify.com/',commands[-1])
        with self.assertRaises(KeyError):app_launch.launch('spotify; reboot',android)



class PhoneLinkTests(unittest.TestCase):
    def test_browser_uses_send_instead_of_intercepted_view(self):
        from phone_urls import open_web, route
        commands=[]
        open_web('https://music.youtube.com/',commands.append)
        self.assertIn('android.intent.action.SEND',commands[-1])
        self.assertNotIn('android.intent.action.VIEW',commands[-1])
        self.assertTrue(route('steam://openurl/market://details?id=com.spotify.music',commands.append))
        self.assertIn('com.aurora.store/.ComposeActivity',commands[-1])
        self.assertFalse(route('steam://run/123',commands.append))
        route('steam://openurl/file:///sdcard/Movies/demo.mp4',commands.append)
        self.assertIn('org.videolan.vlc/.gui.video.VideoPlayerActivity',commands[-1])
        with self.assertRaises(ValueError):route('steam://openurl/file:///etc/secret.mp4',commands.append)

    def test_ipc_stays_outside_saved_data_and_rejects_regular_files(self):
        from phone_urls import prepare_pipe
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);runtime=root/'run';runtime.mkdir();data=root/'saved';data.mkdir()
            (data/'settings.json').write_text('{}')
            pipe=prepare_pipe(runtime)
            self.assertTrue(pipe.is_fifo())
            self.assertEqual(pipe.stat().st_mode & 0o777,0o600)
            shutil.copytree(data,root/'backup')
            self.assertTrue((root/'backup/settings.json').exists())
            pipe.unlink();pipe.write_text('keep my file')
            with self.assertRaises(RuntimeError):prepare_pipe(runtime)
            self.assertEqual(pipe.read_text(),'keep my file')

    def test_invalid_links_and_split_writes_are_handled(self):
        from phone_urls import open_web, Lines
        for url in ['file:///etc/passwd','javascript:alert(1)','https://example.com/\nreboot','https://'+'a'*8200]:
            with self.subTest(url=url[:40]),self.assertRaises(ValueError):open_web(url,lambda _:None)
        lines=Lines()
        self.assertEqual(lines.feed(b'steam://openurl/https://example.'),[])
        self.assertEqual(lines.feed(b'com/\n'),['steam://openurl/https://example.com/'])
        with self.assertRaises(ValueError):lines.feed(b'x'*16385)
        self.assertEqual(lines.feed(b'ok\n'),['ok'])

class MediaPersistenceTests(unittest.TestCase):
    def fixture(self, root):
        scripts=root/'liblepton';scripts.mkdir()
        text='        rm -rf "$(data_mount_path)/media/0"\n        local TARGET_PATH="$(data_mount_path)/media/0"\n'
        for host,phone in [('Documents','Documents'),('Downloads','Download'),('Videos','Movies')]:
            text+=(f'        if [[ -d "${{HOME}}/{host}" ]]; then\n'
                   f'            rm -rf "${{TARGET_PATH}}/{phone}"\n'
                   f'            ln -s "${{HOME}}/{host}" "${{TARGET_PATH}}/{phone}"\n'
                   '        fi\n')
        path=scripts/'mounting.sh';path.write_text(text);return path

    def test_repeated_boot_keeps_private_media_and_existing_downloads(self):
        import subprocess
        import prepare_runtime
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=self.fixture(root)
            media=root/'overlay/media/0';(media/'Music').mkdir(parents=True);(media/'Music/keep.mp3').write_bytes(b'my music')
            (media/'Download').mkdir();(media/'Download/keep.txt').write_text('private download')
            home=root/'host';home.mkdir()
            for name in ['Documents','Downloads','Videos']:(home/name).mkdir()
            prepare_runtime.preserve_media(root)
            body=path.read_text().replace('${HOME}','${TEST_PHONE_HOME}')
            command='set -eu\ndata_mount_path(){ printf "%s" "$TEST_PHONE_OVERLAY"; }\nprepare(){\n'+body+'\n}\nprepare\nprepare\n'
            import os
            env=dict(os.environ,TEST_PHONE_HOME=str(home),TEST_PHONE_OVERLAY=str(root/'overlay'))
            subprocess.run(['bash','-c',command],env=env,check=True)
            self.assertEqual((media/'Music/keep.mp3').read_bytes(),b'my music')
            self.assertEqual((media/'Download/keep.txt').read_text(),'private download')
            self.assertEqual((media/'Movies').resolve(),home/'Videos')

    def test_changed_upstream_is_rejected_without_writing_a_partial_patch(self):
        import prepare_runtime
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=self.fixture(root)
            original=path.read_text().replace('rm -rf "${TARGET_PATH}/Movies"','changed-upstream')
            path.write_text(original)
            with self.assertRaises(RuntimeError):prepare_runtime.preserve_media(root)
            self.assertEqual(path.read_text(),original)
if __name__=='__main__':unittest.main()