# Across32 Launcher – EndeavourOS / KDE Plasma

Grafikus, magyar nyelvű alkalmazáskezelő az Across32 GitHub-fiók hat projektjéhez.
A felület külön kártyán jeleníti meg az alkalmazást, a rövid leírást, a helyi verziót és Git-revíziót,
valamint a **Telepítés / Megnyitás / Frissítés** gombokat.

| Alkalmazás | Repository | Feladat |
| --- | --- | --- |
| Relief Studio | `relief` | CNC domborművek, STL, 3D / rotary |
| Filmadatbázis | `Movie_database` | Filmek, sorozatok, feliratok |
| Munkák és eladások | `Munkak_eladasok` | CNC / lézer termékek és eladások |
| Laser Studio | `laser` | Lézergravírozási CAM és G-kód |
| Tankolás | `tankolas` | Tankolás, fogyasztás és szerviz |
| Gázfogyasztás | `gas` | Gázfogyasztás és rezsiköltségek |

## 1. A launcher telepítése

Az EndeavourOS Terminál / Konsole alkalmazásában:

```bash
git clone https://github.com/Across32/launcher.git
cd launcher
bash install.sh
```

A telepítő ellenőrzi a Python, Git és Konsole jelenlétét (hiány esetén az Arch `pacman` csomagkezelőjét használja, sudo jóváhagyással), a launcheren belül saját `.venv` környezetet készít,
és létrehozza a **Across32 – Alkalmazáskezelő** KDE menüindítót.

Kézi indítás: `./run.sh`, menüből: **Across32 – Alkalmazáskezelő**.

A launcher későbbi frissítése a saját repójából:

```bash
cd ~/launcher  # ha ide klónoztad; egyébként a saját launcher mappád
git pull --ff-only
bash install.sh
```

## 2. Privát repók hitelesítése

A launcher **nem tárol hozzáférési tokent vagy jelszót**, és a GitHubnál meglévő hozzáférésedet használja.
Ha valamelyik projekt privát, a `git clone` / `git pull` csak sikeres Git-hitelesítés után működik.
EndeavourOS alatt ajánlott:

```bash
sudo pacman -S --needed github-cli
gh auth login
gh auth setup-git
```

Az `gh auth login` parancs során válaszd a GitHub.com és HTTPS opciókat. Az `gh auth setup-git` segít,
hogy a Git klónozás a GitHub CLI hitelesítését használhassa.

## 3. Használat

- **Telepítés:** a megfelelő GitHub repót klónozza, majd a projekt saját, meglévő `install.sh`
  (Filmadatbázisnál `install_kde_menu.sh`) telepítőjét futtatja.
- **Frissítés:** csak helyes Across32 Git-origin és módosítatlan követett fájlok esetén
  `git pull --ff-only origin main`, majd újra lefuttatja a projekt telepítőjét.
- **Megnyitás:** lehetőség szerint a már létező KDE `.desktop` indítóparancsot használja.
- **Github ↗:** az adott projekt GitHub oldalát nyitja meg.
- Keresés, telepített/nem telepített szűrő, kézi frissítés és automatikus állapotkövetés telepítés közben.

A telepítéshez vagy frissítéshez **Konsole** ablak nyílik meg, ahol a `sudo` kérdés,
a Git-hitelesítés, a futási napló és az esetleges hibák is láthatók. A művelet lezárása után
Enterrel zárható be a Konsole ablak.

## 4. Meglévő telepítések / adatok megőrzése

A launcher felismeri az alkalmazások saját KDE-indítóit és ha a hozzájuk tartozó eredeti
Git-munkakönyvtár felismerhető, azt használja frissítéshez. A Filmadatbázis saját telepítése
továbbra is a `~/.local/share/filmadatbazis-app` mappát használja.

A launcher által kezelt új forrásklónok alapértelmezett helye:
`~/.local/share/across32-launcher/sources/<repo>`. A `Munkak_eladasok` új telepítése
kivétel: ha nincs korábbi telepítése, az alkalmazás meglévő telepítőjéhez igazodva
`~/.local/share/cnc-eladasok` mappába klónozunk. Ha meglévő régi telepítést talál,
az eredeti telepítő választási logikája érvényes.

A három költségnyilvántartó közül a `Munkak_eladasok`, a `tankolas` és a `gas`
a projekt saját előírásai alapján **/Volumes/Data** alatt tartja az adatait.
**A meghajtót / mappát telepítés előtt elérhetővé kell tenni.**
A launcher nem töröl adatbázist és nem futtat `git reset --hard` parancsot.
Mindegyik alkalmazás telepítője eltérő rendszerfüggőségeket telepíthet; a Konsole
ablakban követhető, mit végez.

Ha az adott célkönyvtárban idegen fájl van Git-klón helyett, a művelet leáll,
nem írja felül automatikusan.

## 5. Tesztek

```bash
python -m unittest discover -s tests -v
python -m compileall -q app_manager.py launcher.py
QT_QPA_PLATFORM=offscreen .venv/bin/python launcher.py
```

GitHub Actions alatt automatikus backend egységtesztek és Qt offscreen indítási teszt futnak.

**Rendszerkövetelmény:** EndeavourOS / Arch Linux, KDE Plasma, Konsole, Git, Python 3.11+, internetkapcsolat a telepítéshez/frissítéshez.
