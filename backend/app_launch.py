"""Allowlisted app launches for the phone's own media page."""
import shlex
from phone_urls import open_web

APPS = {
    'browser': ('de.baumann.browser', 'https://www.google.com/'),
    'fdroid': ('com.looker.droidify', None),
    'aurora': ('com.aurora.store', None),
    'spotify': ('com.spotify.music', 'https://open.spotify.com/'),
    'apple_music': ('com.apple.android.music', 'https://music.apple.com/'),
    'youtube_music': ('com.google.android.apps.youtube.music', 'https://music.youtube.com/'),
    'youtube': ('org.schabi.newpipe', 'https://www.youtube.com/'),
    'gmail': ('com.google.android.gm', 'https://mail.google.com/'),
    'maps': ('com.google.android.apps.maps', 'https://maps.google.com/'),
    'drive': ('com.google.android.apps.docs', 'https://drive.google.com/'),
    'google_calendar': ('com.google.android.calendar', 'https://calendar.google.com/'),
    'music': ('org.fossify.musicplayer', None),
    'video': ('org.videolan.vlc', None),
    'podcasts': ('de.danoeh.antennapod', None),
    'radio': ('net.programmierecke.radiodroid2', None),
}


def launch(app, android):
    package, url = APPS[app]
    installed = android(shlex.join(['cmd_real', 'package', 'list', 'packages', package]))
    if 'package:' + package in installed.splitlines():
        resolved = android(shlex.join(['cmd_real', 'package', 'resolve-activity', '--brief',
                           '-a', 'android.intent.action.MAIN', '-c', 'android.intent.category.LAUNCHER', '-p', package]))
        component = next((line.strip() for line in resolved.splitlines() if line.startswith(package + '/')), None)
        if not component:
            raise RuntimeError('App has no launcher activity')
        args = ['am', 'start', '-W', '-n', component]
    elif url:
        return open_web(url, android)
    else:
        raise RuntimeError('App is still downloading. Check starter apps in Apps & media.')
    result = android(shlex.join(args))
    if 'Error:' in result or 'Exception' in result:
        raise RuntimeError(result)
    return result