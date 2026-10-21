#!/usr/bin/env bash
set -euo pipefail
package=$(cd -- "$(dirname -- "$0")/.." && pwd)
export TERM=dumb IS_PARENT=true LEPTON_NO_CLEANUP=true
unset SteamAppId STEAM_COMPAT_INSTALL_PATH STEAM_COMPAT_DATA_PATH
python3 "$package/backend/publish_source.py"
python3 "$package/backend/initialize.py" &
exec "$MAGICSHELF_CACHE_DIR/lepton/lepton" start magicshelf-phone
