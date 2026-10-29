#!/usr/bin/env bash
# Across32 Launcher user-local installation for EndeavourOS / KDE Plasma.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "$(readlink -f -- "$0")")" && pwd)"
cd "$ROOT"
# Print exact local checkout and release so users can distinguish a stale
# running instance from the newly installed one.
launcher_version="$(tr -d '\\r\\n' < "$ROOT/VERSION")"
launcher_sha="$(git -C "$ROOT" rev-parse --short=8 HEAD 2>/dev/null || printf 'nincs-git')"
echo "Across32 Launcher telepítés: v$launcher_version · Git $launcher_sha"
echo "Forrásmappa: $ROOT"
if ! command -v pacman >/dev/null 2>&1; then
  echo "Ez a telepítő EndeavourOS / Arch Linux rendszerhez készült." >&2
  exit 1
fi
need_packages=()
command -v git >/dev/null 2>&1 || need_packages+=(git)
command -v gh >/dev/null 2>&1 || need_packages+=(github-cli)
command -v python3 >/dev/null 2>&1 || need_packages+=(python)
command -v konsole >/dev/null 2>&1 || need_packages+=(konsole)
if (("${#need_packages[@]}" > 0)); then
  echo "Hiányzó rendszercsomagok: ${need_packages[*]}"
  sudo pacman -S --needed "${need_packages[@]}"
fi

python3 -m venv "$ROOT/.venv"
"$ROOT/.venv/bin/python" -m pip install --upgrade 'pip>=24'
"$ROOT/.venv/bin/python" -m pip install 'PySide6-Essentials>=6.7,<7'

desktop_dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$desktop_dir"
desktop_file="$desktop_dir/across32-launcher.desktop"
cat > "$desktop_file" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Across32 – Alkalmazáskezelő
GenericName=GitHub alkalmazások telepítése és frissítése
Comment=Relief Studio, Filmadatbázis, Munkák és eladások, Laser Studio, Tankolás, Gázfogyasztás, Across Player, Csomagkezelő
Exec="$ROOT/run.sh"
Path=$ROOT
Icon=$ROOT/assets/across32-launcher.svg
Terminal=false
Categories=Utility;Development;
Keywords=Across32;CNC;Laser;GitHub;Frissítés;Telepítés;
StartupNotify=true
EOF
chmod +x "$ROOT/run.sh" "$desktop_file"
# An existing KDE Settings -> Autostart entry must start hidden in the tray.
# Do not turn on autostart if the user has not already enabled it.
if ! python3 "$ROOT/autostart.py" --repair "$ROOT/run.sh"; then
  echo "Figyelem: a meglévő KDE automatikus indítás frissítése nem sikerült." >&2
fi
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$desktop_dir" || true
command -v kbuildsycoca6 >/dev/null 2>&1 && kbuildsycoca6 >/dev/null 2>&1 || true
echo
echo "Across32 Launcher telepítve!"
echo "A KDE alkalmazásindítóban: Across32 – Alkalmazáskezelő"
echo "Közvetlen indítás: $ROOT/run.sh"
echo "Telepített KDE indító: $desktop_file"
echo "Telepített indítóparancs: $(grep '^Exec=' "$desktop_file" | cut -d= -f2-)"
echo "Verzió lekérdezése: $ROOT/run.sh --version"
echo "FONTOS: Ha a Launcher még fut, teljesen zárd be, majd indítsd újra."
