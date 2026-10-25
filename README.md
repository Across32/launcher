# Across32 Launcher – EndeavourOS / KDE Plasma

Grafikus, magyar nyelvű alkalmazáskezelő az Across32 GitHub-fiók hét projektjéhez.
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
| Across Player – Lejátszó | `player` | Magyar nyelvű 4K/Full HD videólejátszó (mpv, feliratok, hangsávok) |

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
  Az **Across Player** kivétel: a rendszer saját `/usr/bin/python` + `pyside6` és `mpv`
  csomagjait használja. A launcher ezeket szükség esetén `pacman` segítségével telepíti.
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

Az **Across Player** korábbi Git-klónja a `~/.local/share/across-player/` mappából
is felismerhető. Ha a lejátszó más helyre került, a telepített
`~/.local/bin/across-player` indítóban szereplő `player.py` útvonalból is
felismeri az eredeti klónt. A KDE menüben **Across Player** néven jelenik meg.
A **Megnyitás**, **Frissítés**, **Frissítési előzmények**, saját ikon és
GitHub-link pontosan úgy működik a lejátszón, mint a többi alkalmazásnál.
A `player` repó külön kiadási verziófájlja jelenleg nem található;
ezért a launcher a valódi Git-revíziót jeleníti meg, nem talál ki verziószámot.

Ha az adott célkönyvtárban idegen fájl van Git-klón helyett, a művelet leáll,
nem írja felül automatikusan.


## Prémium szürkés-kék felület és ablakkezelés

- Prémium acélkék/sötétszürke kártyás megjelenés, világos kék gombokkal.
- **Minden kártyán Frissítési előzmények:** a projekt valós magyar `CHANGELOG.md` naplója, illetve
  ennek hiányában a Git commitok magyar nyelvű összefoglalója. A verzió,
  dátum és az eredeti fejlesztői bejegyzés ellenőrizhető GitHub-adatból származik.
  Ha a projekt adott bejegyzéshez nem adott ki verziószámot, **Git-azonosító** jelenik meg,
  nem kitalált verzió. A hiányzó dátumot is külön jelezzük.
- **Ikon csere:** kattints a programkártya bal felső ikonjára, válassz PNG/JPG/WEBP/BMP képet.
  A kép négyzetes PNG-másolata megmarad az
  `~/.local/share/across32-launcher/icons/` alatt, így újraindításkor is látszik.
  **Jobb kattintással** visszaállítható a gyári jelzés. Az ikonkép változtatása
  csak a Launcher kártyájára vonatkozik, a másik program saját KDE-ikonjára nem.
- **TÁLCÁRA:** ha a rendszer támogatja, elrejti az ablakot a KDE rendszertálcájára;
  a tálcaikon menüjében **Megnyitás** és **Teljes bezárás** használható.
  Ha nincs rendszertálca, normál KDE minimalizálás történik a feladatsorra.
  A hagyományos ablakminimalizálás is működik.
- A címsor **X / Bezárás** gombja ténylegesen kilép, nem hagy rejtett alkalmazást
  a tálcán. A program természetes Linux-ablak dekorációját nem cseréljük le.

## GitHub Backup – csak a privát repók

A fejlécben található **⬇ GITHUB BACKUP** gomb az Across32 fiók elérhető
**privát** GitHub-repóit menti az alábbi mappába:

```text
/Volumes/Data/Github backup/
```

Minden repóhoz pontosan két, állandó nevű adatmentés tartozik:

```text
Across32__relief.git/       # teljes, bare Git-tükör / commit- és ágtörténet
Across32__relief.bundle     # önálló, ellenőrzött Git bundle
Across32__player.git/       # Across Player – teljes Git-tükör
Across32__player.bundle     # Across Player – ellenőrzött Git bundle
```

A `player` projekt GitHub-repóneve **`Across32/player`** (az alkalmazás neve: Across Player).
A backup külön ellenőrzi a privát `player` repó jelenlétét a listában,
és ha a normál felsorolásból hiányzik, a GitHub CLI-vel külön megvizsgálja.
Csak privátként ellenőrzött repót ment; sikertelen ellenőrzésnél hibaüzenettel leáll,
nem jelzi tévesen teljesnek a mentést.

A többi repónál is ugyanez a névkonvenció. A mentés nem a programok
munkamappáinak adatbázisait vagy helyi, nem követett fájljait menti, hanem a GitHubon
tárolt repository teljes elérhető Git-történetét és ágait.

**Működés:**
1. `gh` hitelesítéssel lekéri az Across32 privát repóit.
2. A GitHubról egy ideiglenes friss **`git clone --mirror`** tükör készül.
3. `git fsck`, `git bundle create --all` és `git bundle verify` ellenőrzi a mentést.
4. **Csak sikeres ellenőrzés után** cseréli le az adott repó korábbi fix nevű
   tükrét és bundle fájlját. Hiba esetén az előző, sikeresen elkészített mentés marad.
5. A `backup-status.json` tartalmazza az utolsó futás időpontját,
   a mentett Git-revíziókat és az esetleges hibás repókat.

Ugyanarra a repóra **nem készülnek dátummal megsokszorozott mentésfájlok**.
A program külön Konsole ablakban jelzi a műveletet; a végén Enterrel zárhatod.
A célmappában már meglévő, más elnevezésű, ismeretlen tartalmú fájlokhoz nem nyúl.

A mentéshez telepítve kell lennie a `git`, `github-cli` (`gh`) és a
`konsole` parancsnak, valamint szükséges a GitHub-fiók hitelesítése:

```bash
sudo pacman -S --needed git github-cli konsole
gh auth login
```

**Fontos:** a `/Volumes/Data` csatolási pontnak már elérhetőnek kell lennie
a mentés indítása előtt; nem hozzuk létre automatikusan a hiányzó csatolási pontot.

## 5. Tesztek

```bash
python -m unittest discover -s tests -v
python -m compileall -q app_manager.py launcher.py release_history.py app_icons.py github_backup.py
QT_QPA_PLATFORM=offscreen .venv/bin/python launcher.py
```

GitHub Actions alatt automatikus backend egységtesztek és Qt offscreen indítási teszt futnak.

**Rendszerkövetelmény:** EndeavourOS / Arch Linux, KDE Plasma, Konsole, Git, Python 3.11+, internetkapcsolat a telepítéshez/frissítéshez.
