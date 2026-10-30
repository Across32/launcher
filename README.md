# Across32 Launcher – EndeavourOS / KDE Plasma

Grafikus, magyar nyelvű alkalmazáskezelő az Across32 GitHub-fiók nyolc projektjéhez.
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
| Csomagkezelő | `csomagkezelo` | Pacman, AUR/külső csomagok és árva függőségek áttekintése és törlése |

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

## Olvasható GitHub-frissítésjelentés – v1.4.2

Kijavítva a KDE Plasma sötét témával előforduló hiba, amelynél a
\`QMessageBox\` szövege sötét maradt a sötét háttéren. A **↻**
manuális verzióellenőrzés eredménye ezentúl saját, egységes
szürkés-kék párbeszédablakban jelenik meg:

- világos (#eef6ff), jól olvasható jelentésszöveg és címsor;
- görgethető, sorokra tördelő, kijelölhető szövegmező mind a 8 repóhoz;
- **JELENTÉS MÁSOLÁSA** gomb a teljes eredmény vágólapra másolásához;
- **BEZÁRÁS** gomb; a hibás és a sikeres vizsgálat ugyanezt az ablakot használja.

Az alkalmazáskártyák, a verziófigyelés háttere, valamint a korábban
felismert piros frissítési jelzések működése változatlan. Az új ablak
megjelenését, explicit világos szövegszínét és másolását automatikus
Qt-regressziós tesztek ellenőrzik.

## GitHub-verziófigyelés és hibajelzés – v1.4.1

A fejléc alatti **GitHub verzióellenőrzés** sor azonnal jelzi, ha
a háttérben indul a repók vizsgálata, hány repó válaszolt és hány
új kiadás érhető el. A felső **↻** gombbal indított kézi ellenőrzés
**mindig megmutatja a nyolc alkalmazás eredményét**: az aktuális helyi
verziót, a GitHubon látott verziót vagy a lekérési hibát.
Ha éppen automatikus ellenőrzés zajlik, a kézi lekérés nem indul
duplán, hanem a folyamat végén megjeleníti annak részletes eredményét.

A GitHub CLI már nem rejti el a hitelesítési, HTTP- és hálózati
hibákat. A hibaszövegben szerepelhet például az
\`HTTP 401\`, \`HTTP 403\`, \`gh auth status\`, vagy a
\`sudo pacman -S github-cli\` telepítési javaslat.
A vizsgálat legfeljebb 120 másodpercig tart; hiba esetén a
korábban ismert frissítésjelzés **nem törlődik**.

Ha nem jelenik meg a várható piros „FRISSÍTÉS ELÉRHETŐ” felirat,
először nyomd meg a **↻** gombot, majd nézd meg a
részletes nyolcalkalmazásos eredménylistát. A privát repo
elérését külön ellenőrizheted terminálból:

~~~bash
gh auth status
gh api repos/Across32/laser --jq '.full_name'
~~~

A helyi és a távoli verziót **továbbra is numerikusan**
hasonlítjuk össze; a távoli lekérési hiba nem adhat hamis frissítésjelzést.

## Új verzió figyelése – Launcher v1.4.0

A Launcher induláskor, a fejléc **↻** frissítőgombjára kattintva,
sikeres telepítés/frissítés után és 30 percenként ellenőrzi a nyolc
Across32 GitHub-repó legújabb kiadását. Minden ellenőrzés **külön
háttérfolyamatban** történik; a Qt grafikus felület nem vár a hálózatra.

A program helyi verziószámát összehasonlítja a GitHub \`main\` ágában
tárolt eredeti verziófájllal. A \`0.8.50\` és \`0.8.9\`, illetve a
\`2026.10.24-95\` és \`2026.10.25-96\` kiadásokat **számszerűen**
hasonlítja össze. Ha valóban újabb távoli kiadás van, a meglévő
**zöld „TELEPÍTVE” mellett piros „● FRISSÍTÉS ELÉRHETŐ”** állapot
jelenik meg. A jelzés az alkalmazás következő újraindításakor vagy
hálózati kimaradás esetén is megmarad. Csak akkor tűnik el,
amikor a helyileg ténylegesen telepített kiadás eléri vagy meghaladja
a GitHubon utoljára ellenőrzött verziót.

A privát GitHub-repókhoz a korábban már beállított
\`gh auth login\` hozzáférés szükséges. Sikeres lekéréseknél a legutóbbi
távoli verziót a
\`~/.cache/across32-launcher/remote_versions.json\` fájl tárolja.
Hiba vagy offline állapot esetén a korábbi ismert frissítésjelzést
nem töröljük és nem jelezünk hamis új verziót. Az Across Player
repóban nincs számozott verziófájl, ezért **csak ennél**
a tényleges Git-revízió különbségét ellenőrizzük.

**Munkák és eladások verziószám:** a Git-klón eltérhet a futtatott
telepítéstől, mert a program saját \`install.sh\` fájlja másik könyvtárba
másolhatja a \`main.py\` fájlt. A kártya mostantól a KDE-indítóból
felismert, **ténylegesen telepített \`main.py\` fájl
\`UI_VERSION\`** értékét mutatja; ha ez nem található, a forrás
verziószámát használja.

## A futó Launcher pontos verziójának ellenőrzése

A Launcher saját kiadási verziószáma a gyökérben lévő `VERSION` fájlban van.
**v1.2.0-tól a KDE ablak címsora és a fejléc is megmutatja** a futó
alkalmazás verzióját és a tényleges helyi Git-revízió első nyolc karakterét,
például: `Across32 – Alkalmazáskezelő | v1.2.0 · Git abc12345`.
A Git-azonosító minden új forrásfrissítéssel változhat, a kiadási szám csak
verzióváltáskor. Így pontosan azonosítható, melyik alkalmazáspéldány fut.

A KDE menüben szereplő példány verzióját terminálból így ellenőrizheted:

```bash
desktop="${XDG_DATA_HOME:-$HOME/.local/share}/applications/across32-launcher.desktop"
folder="$(sed -n 's/^Path=//p' "$desktop" | head -n 1)"
echo "KDE menüben telepített forrásmappa: $folder"
"$folder/run.sh" --version
```

Az indító által kiírt verziót hasonlítsd össze az ablak címsorában láthatóval.
Ha eltérnek, **egy régebbi, még futó Launcher-ablakot nézel**: teljes
bezárás után indítsd újra a KDE menüből. Ha az új címsor sem látszik,
valószínűleg más forrásmappából indítottál egy másik klónt.

A `bash install.sh` telepítéskor kiírja a verziót, a Git SHA-t, a forrásmappát,
a létrehozott `.desktop` fájlt és a pontos indítási parancsot is.

## Csomagkezelő – a nyolcadik alkalmazás (Launcher v1.3.0)

Az `Across32/csomagkezelo` privát GitHub-repó ugyanolyan alkalmazáskártyát kapott,
mint a korábbi programok:

- **Telepítés / Megnyitás / Frissítés:** a GitHub-repót klónozza vagy biztonságosan
  frissíti, majd az eredeti `install.sh` telepítőt használja. A program
  az EndeavourOS rendszerszintű `/usr/bin/python`, `pyside6` és `qt6-svg`
  csomagjaival működik, nem igényel a Launcher által létrehozott külön venv-et.
- **Valódi verzió:** a forrás `csomagkezelo/__init__.py` fájljában szereplő
  `__version__` értékből. A helyi Git-azonosító is megjelenik.
- **Frissítési előzmények:** a projekt valós Git commitjaiból és a meglévő
  changelogból (ha van). A verziót a Gitben tárolt `__version__` fájlból
  is felismeri, nem talál ki verziószámokat.
- **Ikon:** az eredeti `csomagkezelo.desktop` KDE ikon, amely a Launcher
  kártyáján tetszőleges képre cserélhető és újraindítás után megmarad.
- **Meglévő telepítés:** a KDE `csomagkezelo.desktop` fájl alapján felismeri
  az eredeti Git-klónt; ugyanígy a `~/csomagkezelo` mappából is, ha annak
  Git-originje valóban az `Across32/csomagkezelo` repóra mutat.
- **GitHub Backup:** a privát Csomagkezelő repo kötelezően ellenőrzött mentése
  a `/Volumes/Data/Github backup/` mappába két, állandó nevű fájlban:
  `Across32__csomagkezelo.git/` és `Across32__csomagkezelo.bundle`.
  Az új sikeres mentés felülírja a régi párt, duplikáció nélkül.

**Fontos:** a GitHub Backup a forráskódot menti, nem a számítógép telepített
csomagjait vagy a pacman adatbázisát. A Csomagkezelő programban egy csomag
törlése külön jóváhagyást és rendszergazdai hitelesítést igényel.

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

## Automatikus indítás közvetlenül a KDE rendszertálcára

A Launcher **külön automatikus indítási móddal** rendelkezik: Plasma bejelentkezéskor
nem mutatja a főablakot az Asztalon, hanem rögtön a rendszertálcán fut.
A rendszertálca ikonjára kattintva a főablak megnyitható; az ikon jobb gombos
menüjében **Megnyitás** és **Teljes bezárás** érhető el.

- A fejlécben jelöld be az **INDÍTÁS A RENDSZERREL · TÁLCÁRA** kapcsolót.
  Ez létrehozza a felhasználói \`~/.config/autostart/across32-launcher.desktop\`
  KDE autostart bejegyzést, amely a \`--start-in-tray\` kapcsolót használja.
  A kapcsoló kikapcsolása törli a bejegyzést.
- **Ha az automatikus indítás már a KDE Rendszerbeállításokban be volt
  kapcsolva**, a \`bash install.sh\` frissíti a meglévő, azonos nevű autostart
  bejegyzést, és tálcás indításra állítja át. Nem engedélyezi magától az
  automatikus indítást, ha az korábban ki volt kapcsolva.
- A szokásos KDE alkalmazásmenüből vagy \`./run.sh\` paranccsal kézzel indítva
  továbbra is **normál főablak** jelenik meg.
- Közvetlen parancssori indítás látható ablak nélkül:
  \`./run.sh --start-in-tray\`
- Ha a Plasma rendszertálcája még nem áll készen a bejelentkezés pillanatában,
  az ablak csak **minimalizálva** indul (nem jelenik meg az asztalon), majd a
  rendszertálca elérhetővé válásakor rejtve marad a tálcán.
- A **TÁLCÁRA** gomb továbbra is használható, az **X** gomb pedig a teljes
  alkalmazást bezárja.

**KDE Rendszerbeállítások → Indítás és leállítás → Automatikus indítás** alatt
ugyanez a bejegyzés látható. A felhasználói menüindítót és a rendszerindítási
parancsot külön kezeljük, így a kézi megnyitás nem válik rejtett indítássá.

A beállítás külön teljes szélességű fejlécsorban látható, nem bújik el a
keresés és az állapotszűrő között. A legfrissebb telepítő a KDE által
**eltérő fájlnéven** létrehozott autostart bejegyzést is felismeri, és
az esetleges duplikált Across32 Launcher indítókat egyetlen tálcás
bejegyzésre egyesíti. A többi alkalmazás automatikus indítását nem módosítja.

Ha a KDE továbbra is korábbi teljes ablakot nyit bejelentkezéskor,
ellenőrizd a **Rendszerbeállítások → Indítás és leállítás → Asztali munkamenet**
beállításánál a **munkamenet-visszaállítást** is. A Plasma képes a korábban
nyitva hagyott ablakot külön visszaállítani, még akkor is, ha az
autostart bejegyzés már kizárólag a tálcán indul.

Ha a frissítés után sem látszik az új kapcsoló, nézd meg az aktuálisan
telepített KDE menüindító `Path=` értékét, és **azt** a Git-klónt frissítsd,
ne egy esetleg másik mappában lévő `~/launcher` klónt.


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
Across32__csomagkezelo.git/ # Csomagkezelő – teljes Git-tükör
Across32__csomagkezelo.bundle # Csomagkezelő – ellenőrzött Git bundle
```

A `player` projekt GitHub-repóneve **`Across32/player`** (az alkalmazás neve: Across Player).
A backup külön ellenőrzi a privát `player` és `csomagkezelo` repók jelenlétét a listában,
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
python -m compileall -q app_manager.py launcher.py release_history.py app_icons.py github_backup.py autostart.py
QT_QPA_PLATFORM=offscreen .venv/bin/python launcher.py
```

GitHub Actions alatt automatikus backend egységtesztek és Qt offscreen indítási teszt futnak.

**Rendszerkövetelmény:** EndeavourOS / Arch Linux, KDE Plasma, Konsole, Git, Python 3.11+, internetkapcsolat a telepítéshez/frissítéshez.
