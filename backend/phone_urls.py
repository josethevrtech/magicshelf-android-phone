"""Keep Lepton's intercepted web links inside this phone, using Android sharing."""
import shlex
import os
import stat
from urllib.parse import urlsplit, parse_qs, unquote
from pathlib import PurePosixPath, Path

BROWSER = 'de.baumann.browser/.activity.BrowserActivity'


def open_web(url, android):
    parsed = urlsplit(url)
    if len(url) > 8192 or any(ord(c) < 32 for c in url) or parsed.scheme not in ('https', 'http') or not parsed.hostname:
        raise ValueError('Unsupported phone web link')
    # Valve intercepts every ACTION_VIEW and forwards it to Steam. ACTION_SEND
    # is the browser's documented share target and stays inside Android.
    return android(shlex.join(['am', 'start', '-W', '-a', 'android.intent.action.SEND',
                              '-t', 'text/plain', '--es', 'android.intent.extra.TEXT', url,
                              '-n', BROWSER]))


def route(command, android):
    prefix = 'steam://openurl/'
    if not command.startswith(prefix):
        return False
    url = command[len(prefix):]
    if len(url)>8192 or any(ord(c)<32 for c in url):raise ValueError('Invalid phone link')
    parsed = urlsplit(url)
    suffix=PurePosixPath(unquote(parsed.path)).suffix.lower()
    media=suffix in ('.mp4','.mkv','.webm','.avi','.mov','.mp3','.aac','.m4a','.ogg','.wav','.flac','.m3u','.m3u8')
    local_file=parsed.scheme=='file' and parsed.netloc in ('','localhost') and parsed.path.startswith(('/sdcard/','/storage/emulated/0/','/data/media/0/'))
    local_content=parsed.scheme=='content' and parsed.netloc in ('org.fossify.filemanager.provider','org.fossify.gallery.provider','media','com.android.providers.media.documents','com.android.externalstorage.documents')
    if media and (local_file or local_content):
        android(shlex.join(['am','start','-W','-a','android.intent.action.MAIN','-f','0x10000001', '-d',url,'-n','org.videolan.vlc/.gui.video.VideoPlayerActivity']))
    elif parsed.scheme == 'market' and parsed.netloc == 'details':
        package = parse_qs(parsed.query).get('id', [''])[0]
        if not package or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._' for c in package):
            raise ValueError('Invalid store link')
        android(shlex.join(['am', 'start', '-W', '-f', '0x10008000', '-a', 'android.intent.action.SEND', '-t', 'text/plain',
                          '--es', 'android.intent.extra.TEXT', 'https://play.google.com/store/apps/details?id='+package,
                          '-n', 'com.aurora.store/.ComposeActivity']))
    else:
        open_web(url, android)
    return True


class Lines:
    def __init__(self):
        self.pending = b''

    def feed(self, chunk):
        self.pending += chunk
        if len(self.pending) > 16384:
            self.pending = b''
            raise ValueError('Phone link exceeds limit')
        parts = self.pending.split(b'\n')
        self.pending = parts.pop()
        return [part.decode('utf-8', errors='strict') for part in parts if part]

def prepare_pipe(runtime):
    # IPC is ephemeral. Keeping a FIFO in saved module data breaks rollback backups.
    pipe=Path(runtime)/'android-phone-url.pipe'
    if not pipe.exists():os.mkfifo(pipe,0o600)
    if not stat.S_ISFIFO(pipe.lstat().st_mode) or pipe.stat().st_uid!=os.getuid():
        raise RuntimeError('Invalid phone URL pipe')
    pipe.chmod(0o600)
    return pipe
