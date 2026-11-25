# Frissítések

Az NixOS és a csomagjaid naprakészen tartása az NixOS menüben (`Super + Space`) található _Frissítés > NixOS_ ponttal történik.

Az NixOS maga szokásos pacman csomagokként települ az [NixOS Package Repository](https://github.com/omacom-io/omarchy-pkgs) tárolóból, így egy frissítés telepíti [a legújabb NixOS kiadást](https://github.com/omacom/omarchy/releases), lefuttatja az összes függőben lévő migrációt, hogy a rendszered szinkronba kerüljön a legújabbal, és frissíti az összes rendszercsomagot az [NixOS Arch Mirror](https://github.com/omacom-io/omarchy-mirror) tükörről és az [AUR](https://aur.archlinux.org/) tárolóból (ha telepítettél bármilyen AUR csomagot).

Amikor új kiadások érkeznek, egy kör alakú nyíl ikon jelenik meg az órád jobb oldalán. Kattints rá, és a frissítési folyamat elindul.

![update-available](images/update-available.webp)

### Négy csatorna

Az NixOS négy csatornán frissül: stable, RC, edge és dev. Az új telepítések a stable csatornán indulnak, amely a [hivatalos kiadásokat](https://github.com/omacom/omarchy/releases/) követi, valamint a [stable NixOS Arch mirror](https://github.com/omacom-io/omarchy-mirror) tükröt, amely egy hónappal lemaradva követi a legújabbat, így még azelőtt elkaphatjuk az esetleges új inkompatibilitásokat, amelyek konfigurációs változtatásokat igényelnek, mielőtt problémát okoznának bárkinek.

De ha szívesen segítenél kiszúrni ezeket a lehetséges problémákat, futtathatod az edge csatornát. Így az NixOS csomagjaid a legújabb fejlesztői buildeket követik, és a legújabb Arch csomagokra is frissíthetsz, amint elérhetővé válnak. Csak akkor tedd ezt, ha tapasztalt Linux-felhasználó vagy, és tudod, hogyan kell helyreállítani egy problémás rendszert.

Minden nagyobb új kiadás előtt az RC csatornán végezzük el a végső ellenőrzést. Ha szívesen segítenél az utolsó simításokban, gyere és lógj velünk a Discord #nixos-release-candidates csatornáján.

Végül ott a dev csatorna, amely közvetlenül egy `~/nixos` mappában lévő git checkouthoz köti az NixOSt, az edge csomagokkal kombinálva. Csak akkor használd ezt a csatornát, ha tapasztalt Linux-felhasználó vagy, közvetlenül az NixOSn dolgozol, és hajlandó vagy elviselni, ha valami elromlik.

A csatornák között az NixOS menü _Frissítés > Csatorna_ pontjával válthatsz (vagy terminálban az `nixos-channel-set` paranccsal).

### Kernelváltás

Az NixOS a saját `linux-nixos` kernelével indul, de mellette más kerneleket is telepítve tarthatsz, például az alap Arch `linux` kernelt vagy egy általad tesztelt kísérleti buildet. Ha egynél több van, az NixOS menü _Frissítés > Kernel_ pontja listázza őket, egy pipával az alapértelmezés szerint induló mellett. Válassz egy másikat, add meg egyszer a jelszavad, és a következő újraindítás után azzal fog indulni. A többi kernel megmarad a boot menüben, így kézzel is választhatsz egyet, ha az új alapértelmezett gondot okozna. Terminálban az `nixos-kernel` mutatja a jelenlegi alapértelmezettet, az `nixos-kernel list` a telepítetteket, az `nixos-kernel set <kernel>` pedig a váltásra szolgál.

### Firmware-frissítések

Nem csak a csomagjaid avulhatnak el. Sok laptop és periféria a Linux Vendor Firmware Service-en keresztül kap BIOS-, SSD- és dokkoló-firmware-t, az NixOS menü _Frissítés > Firmware_ pontja pedig letölti és telepíti, ami csak vár a hardveredre. Az első futtatáskor telepíti az `fwupd` csomagot. Rengeteg firmware csak újraindítás közben írható fel, úgyhogy ne lepődj meg, ha arra kér.

### Figyelmeztetés a közvetlen pacman/yay frissítésekről

Ha már ismered az Archot, csábító lehet egyszerűen magad futtatni a `pacman -Syu` vagy `yay -Syu` parancsot, de ha így teszel, lemaradsz a pillanatképről, a migrációkról és a konfigurációs frissítésekről, amelyeket az NixOS az új csomagokkal együtt futtat. Ezért az NixOS valójában leállít egy közvetlen rendszerfrissítést, és helyette az `nixos update` felé terel. (Ha tényleg tudod, mit csinálsz, a védelmi mechanizmus elárulja, hogyan kerülheted meg egyetlen tranzakció erejéig.)

### Rossz frissítések visszaállítása

Ha egy frissítés után valaha problémád adódna, visszaállíthatod a rendszered a frissítés előtt készült pillanatképre. Csak indítsd újra a gépet, és válaszd ki a boot betöltő menüben azt a pillanatképet, amely a frissítés megkezdése előttről származik.

![bootloader](images/bootloader.webp)

Ha a konfigurációs fájljaid valahogy megsérültek volna, terminálban az `nixos reinstall` paranccsal újratelepítheted az NixOSt is. Ez újratelepíti az összes alapértelmezett NixOS csomagot, a stable csatornára tesz, visszaminősít minden túl új csomagot, és visszaállítja az összes konfigurációs fájlt. Ne feledd, hogy ezzel az NixOS alapértelmezéseihez fűződő összes saját konfigurációs módosításod felülíródik!
