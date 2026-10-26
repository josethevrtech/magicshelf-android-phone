# Reviewer update: Android Phone 0.2.9

- On restores visibility. If the Steam Bar dock is unavailable at startup, the
  phone opens in room space after one second of tracked operation. Configure in
  MagicShelf is no longer needed to make it appear.
- Hold a controller grip while pointing at the phone or reaching near it to pick
  it up; release to place it. Trigger pickup remains available. Tracking loss
  releases the grab, and buttons from the other creation are not globally bound.
- Use the phone's bottom bezel button for its own settings. Left wrist attaches
  the phone using the left controller pose. MagicShelf only manages its lifecycle.
- Text size is a separate page on the phone, with smaller/larger/default controls
  applied to Android's font_scale. The accepted range is 85–150 percent.

The development Frame reproduced a stock Android Display-settings crash caused
by a missing LineageParts LiveDisplay component. When that optional package is
absent, provisioning disables only the unsupported Display activity inside this
creation's private Android container. Its compatibility record includes the
command for restoring the component's default state. Runtimes supplying
LineageParts retain the stock page. This is a compatibility workaround, not a
replacement for all Android Display settings. Brightness and text size are
available on the VR phone without that page; no Android data is reset.

Validation includes native geometry/settings/dock/keyboard checks, Python runtime
preparation and display-control tests, and a source build against the Frame's
libraries. Model assets were generated in the WSL development environment; a
Frame build can use MAGICSHELF_SKIP_MODEL=1 with those generated assets instead
of installing pycairo into SteamOS. The Frame's OS package set was not changed.

Physical grip behavior and wrist comfort await headset testing. Frametop hand
tracking is not advertised by this controller update.

Fallback room positions use separate shelf slots rather than stacking creations
at one location. Up to four creations share a row, with additional rows below.
