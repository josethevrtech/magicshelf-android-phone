# Android Phone (Virtual)

A free creation for [MagicShelf](https://github.com/josethevrtech/magicshelf),
for **SteamOS and Steam Frame only**. This repository owns the Android Phone (Virtual)'s
application code, controls, backend integration, settings and releases.

## Development

```sh
git clone --recurse-submodules https://github.com/josethevrtech/magicshelf-android-phone.git
cd magicshelf-android-phone
./build.sh
```

Requires C++17, pkg-config, EGL/GLES3, Cairo, json-c, PipeWire, X11/XTest and
SteamVR in `/opt/steamvr`. The `vendor/magicshelf` git submodule pins SDK 1.0.0
to an exact commit. For local SDK development, set `MAGICSHELF_SDK_DIR` to a
MagicShelf checkout; normal builds use the pin. `OPENVR_LIB_DIR` can point to
the matching architecture's OpenVR SDK library during CI.

The SDK owns rendering helpers, grabbing/depth, shake recovery and dock placement.
`src/creation_profile.h` owns this creation's identity and dimensions.
`src/main.cpp`, its controls and backend helpers belong to this repository.
The initial app loop retains compile-time inactive compatibility paths from the
shared prototype; subsequent changes here do not change the other creation.

`./build.sh` compiles this creation only and runs geometry, dock and keyboard
checks. It does not start a headset session or install anything. Build output:
`build/runtime/android-phone-vr`. The source was extracted from the working Frame build
on 2026-10-21, including the capture identity, grab direction, shake/reset and
keyboard fixes.

## Independent packages and updates

`module.json` owns this creation's version. A matching `vX.Y.Z` tag builds an
aarch64 `.magicshelf` package, catalog, checksums and GitHub Release here.
The release does not rebuild MagicShelf or the other creation. SDK upgrades
are explicit changes to the pinned submodule.

Requires MagicShelf **0.3.2 / module API 2**. The package owns its shell and
backend lifecycle. Off stops its processes and cleans up external runtimes;
On starts it using its private data directory. Configure and return-to-dock
commands are supplied by the creation rather than hard-coded in the host.
Readiness, rollback, free subscriptions and data preservation belong to MagicShelf.

Build: `./build.sh`, then `python3 tools/package.py`.
Catalog: `https://github.com/josethevrtech/magicshelf-android-phone/releases/latest/download/catalog.json`.

Runtime state is in `~/.local/share/magicshelf/module-data/` under the stable
creation ID. The old shared `Applications/DigitalPartner/vr` folder and legacy
services are not required by this package. Never run both generations together.

Version 0.2.5 updates the collection preview to show the Android home screen.
The capture is rendered with this creation's original phone model; runtime behavior
and permissions are unchanged.

## First use

Subscribe and download in MagicShelf 0.3.8 or newer. If Android support is not
installed, choose **Set up**, then **Install with Steam**. Finish the download
in Steam and return to MagicShelf. The card becomes ready automatically. Turn it
On to open your phone. No terminal or manual runtime copying is needed.

The creation prepares its own Android support files without modifying Steam's
installation. Interrupted preparation retries safely. Android apps and data stay
in their private directory across creation updates and runtime preparation.
Off stops Android and its audio; On resumes the saved Android environment.

The phone model and icon are original procedural assets. Steam supplies Lepton;
Android and user APKs retain their own licenses.

Project source is MIT licensed. Valve's OpenVR headers retain their included
license. All creations and subscriptions are free; artist support is optional.

## Everyday phone and media (0.2.14)

The phone prepares a curated starter set on first use: Notes, Calendar, Clock,
Calculator, Files, Gallery, Music, Keyboard, VLC, AntennaPod, RadioDroid,
NewPipe, FOSS Browser, Droid-ify and Aurora Store. This is about 214 MB of
initial downloads. APK URLs, versions and SHA-256 digests are pinned in
`backend/starter_apps.json`; binaries come directly from F-Droid over HTTPS
and are checked before Android installs them. APKs are not redistributed in
the creation package. Android checks package signatures on installation.

Open the bottom bezel's **Device settings → Apps & media** for streaming
shortcuts, the browser and stores. **Google web apps** opens Gmail, Maps,
Drive and Calendar in the phone browser. These are websites, not GApps.
Google Play Music has been replaced by YouTube Music. NewPipe is an independent
video client; it does not provide Google account sign-in.

The untouched home screen receives a utility grid and browser/music/video/store
dock. Customized layouts are left alone, and the original launcher database is
backed up before initial setup. The keyboard and browser receive initial defaults;
subsequent starts retain user choices. The phone clock follows the headset time
zone. External web links stay inside this creation through a private URL pipe
and the browser's share target, rather than Lepton opening host Steam browser tabs.
Unsupported non-web link schemes are not forwarded to other applications.

Downloads run independently of phone readiness. Interrupted or failed installs
retry on the next start or **Check app setup**. Successfully handled apps are
never force-reinstalled or downgraded: uninstalling an app is respected. Use
Droid-ify or Aurora for app discovery and updates; each store's normal setup,
permissions and installation confirmations apply. MagicShelf continues to own
creation On/Off, updates, rollback and removal. Saved Android apps and data keep
the same creation ID and paths. The private emulated SD card is preserved across
starts; existing media folders are never replaced by host-folder shortcuts.
On the checked Frame, Download, Movies and Documents link to the headset's
Downloads, Videos and Documents folders. Files receives its normal all-files
permission so you can browse and play your media.

### Compatibility and account limits

This is Valve's minimal Android 11 Lepton runtime, not a certified mainstream
Android phone. Google Play Services and the Play Store are not installed, and
there is no supported Google-certified image configured here. Apps that need
Play Integrity, missing system services or DRM may refuse to work. No device
identity or integrity result is spoofed.

On the checked Frame, F-Droid 2.0.2 and 1.23.2 crashed because Lepton omits the
clipboard service; Droid-ify 0.7.8 worked. Firefox/Fennec hit a native crash;
FOSS Browser uses the already-installed system WebView and rendered YouTube.
Apple Music 6.5.3 explicitly rejected the rooted runtime and was removed after
testing; its web shortcut remains, with subscription playback unverified.
Spotify 9.1.94.1929 installed from Google Play through Aurora and reached its
login activity. Account sign-in, subscription playback, protected video and
physical headset controls still require user testing. No user account was
signed in and no subscription was purchased during setup.

VLC decoded an original local H.264/AAC test clip and created an Android audio
stream into PipeWire. This verifies the playback route, not perceived sound or
latency in the headset. Radio and podcast apps launched; individual stations,
feeds and NewPipe video extraction can change with their upstream services.
Alarms and background media run only while the creation is On. Off stops Android
and its audio; it is not an always-on physical phone.

## Reviewer controls candidate (unpublished)

The default Steam Frame bindings are now explained on first use and in
**Device settings → Controls & display**:

- Point at the screen. The phone supplies a small pointer ring when needed.
  Trigger or A/X taps; the thumbstick scrolls vertically or horizontally.
- Press and hold the pointing hand's stick, then move it up/down to send a real
  two-contact pinch. Release the stick to lift both fingers. Apps must support
  pinch; this does not inject mouse-wheel or desktop zoom shortcuts.
- Grip picks up the housing. While holding, the free hand can still point,
  scroll and pinch. Holding-hand stick **plus press** changes pickup depth;
  ordinary scrolling is no longer automatically turned into depth adjustment.
- B goes Back; Y on the left controller opens Home. Release the stick to neutral
  after changing focus/hand so an existing deflection cannot leak into the phone.
  Default bindings can be reviewed in SteamVR; customized bindings may need the
  new Pinch action assigned.

**Wrist fit** offers left/right attachment with separate saved offsets, tilt,
roll, turn and scale. Changes preview on the selected tracked controller; reset
only resets that wrist's fit. Missing tracking retains the last valid pose or
uses the room fallback. Actual comfort and controller aim still need headset
review.

**Hide phone** now explains that Android and audio keep running, offers Return
to shelf, and requires an explicit Hide confirmation. Reopen through MagicShelf's
**Show creation** (or Configure on older hosts). Show restores visibility using
`--show` without restarting Android; use MagicShelf Off to stop Android/audio.

**Phone / tablet display** is an experimental startup choice. Tablet uses a wider
original shell, a 960 × 1280 Android surface and 240 dpi (640 dp wide); choose it,
then use MagicShelf Off/On to apply. Phone restores 720 × 1600 at 320 dpi. Both
share the same creation ID, apps and saves. This is the existing Android 11
Lepton runtime, not Android 17 or an OS upgrade. Some apps retain phone layouts
or reject this runtime regardless of display size. Native settings retain the
phone control layout in the wider prototype.

Docked size fits both object height and actual mesh width with a gap, including
12 cm slots. The fitted pose and scale also drive hit testing; free-held size
and the user's shelf spacing are unchanged.

Validation includes event-pipe tests for two contact IDs, positions, lift order,
timeout/disconnect cancellation, focus-neutral gating and depth ownership;
phone/tablet ray and actual-mesh-bound tests; wrist serialization; and display
selection regressions. On Frame, a WebView received two contacts with a 2.95x
change in span and zero remaining contacts after release; a scroll test moved
362 CSS pixels. Tablet boot, app persistence, separate wrist profiles and
hide/Show without shell or Android PID changes were checked. Physical controller
bindings, dashboard-open/closed use while docked/held/wrist, wrist comfort and
per-app zoom behavior still require headset feedback before publication.
