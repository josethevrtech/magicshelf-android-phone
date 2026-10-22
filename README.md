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
