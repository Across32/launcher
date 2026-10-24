#!/usr/bin/env bash
# Across32 Launcher user-local installation for EndeavourOS / KDE Plasma.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "$(readlink -f -- "$0")")" && pwd)"
cd "$ROOT"
if ! command -v pacman >/dev/null 2>&1; then
  echo "Ez a telepítő EndeavourOS / Arch Linux rendszerhez készült." >&2
  exit 1
fi
need_packages=()
command -v git >/dev/null 2>&1 || need_packages+=(git)
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
Comment=Relief Studio, Filmadatbázis, Munkák és eladások, Laser Studio, Tankolás, Gázfogyasztás
Exec="$ROOT/run.sh"
Path=$ROOT
Icon=$ROOT/assets/across32-launcher.svg
Terminal=false
Categories=Utility;Development;
Keywords=Across32;CNC;Laser;GitHub;Frissítés;Telepítés;
StartupNotify=true
EOF
chmod +x "$ROOT/run.sh" "$desktop_file"
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$desktop_dir" || true
command -v kbuildsycoca6 >/dev/null 2>&1 && kbuildsycoca6 >/dev/null 2>&1 || true
echo
echo "Across32 Launcher telepítve!"
echo "A KDE alkalmazásindítóban: Across32 – Alkalmazáskezelő"
echo "Közvetlen indítás: $ROOT/run.sh"
echo "Telepített KDE indító: $desktop_file"
