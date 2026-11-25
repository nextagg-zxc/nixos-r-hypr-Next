# Actualizări

NixOS și pachetele tale sunt menținute la zi prin _Update > NixOS_ din meniul NixOS (`Super + Space`).

NixOS în sine este instalat ca pachete pacman obișnuite din [NixOS Package Repository](https://github.com/omacom-io/omarchy-pkgs), așa că o actualizare instalează [cea mai recentă versiune NixOS](https://github.com/omacom/omarchy/releases), rulează toate migrările în așteptare pentru a-ți sincroniza sistemul cu cea mai recentă versiune și actualizează toate pachetele de sistem din [NixOS Arch Mirror](https://github.com/omacom-io/omarchy-mirror) și [AUR](https://aur.archlinux.org/) (dacă ai instalat vreun pachet AUR).

Când apar versiuni noi, o pictogramă cu săgeată circulară va apărea în dreapta ceasului. Dă clic pe ea și procesul de actualizare va începe.

![update-available](images/update-available.webp)

### Patru canale

NixOS este actualizat pe patru canale: stable, RC, edge și dev. Instalările noi încep pe canalul stable, care urmărește [versiunile oficiale](https://github.com/omacom/omarchy/releases/), precum și [oglinda stabilă NixOS Arch](https://github.com/omacom-io/omarchy-mirror) care rămâne cu o lună în urma celei mai recente, ca să putem depista orice incompatibilități noi care necesită modificări de configurare înainte ca acestea să cauzeze probleme oamenilor.

Dar dacă vrei să ajuți la depistarea acelor probleme potențiale, poți rula pe canalul edge. Asta va face ca pachetele tale NixOS să urmărească cele mai recente build-uri de dezvoltare și îți permite să actualizezi la cele mai recente pachete Arch de îndată ce devin disponibile. Ar trebui să faci asta doar dacă ai experiență cu Linux și știi cum să recuperezi un sistem care are probleme.

Înainte de orice versiune majoră nouă, vom face validarea finală folosind canalul RC. Dacă te interesează să ajuți la retușurile finale, vino pe #nixos-release-candidates pe Discord.

În fine, există canalul dev, care leagă NixOS direct la un git checkout al codului sursă din `~/nixos`, combinat cu pachetele edge. Ar trebui să folosești acest canal doar dacă ești un utilizator Linux experimentat, lucrezi direct la NixOS și ești dispus să tolerezi defecțiuni.

Poți comuta între canale folosind _Update > Channel_ din meniul NixOS (sau `nixos-channel-set` în terminal).

### Schimbarea kernelurilor

NixOS pornește cu propriul kernel `linux-nixos`, dar poți păstra altele instalate alături de el, cum ar fi kernelul `linux` standard din Arch sau un build experimental pe care îl testezi. Când există mai multe, _Update > Kernel_ din meniul NixOS le listează cu o bifă lângă cel care pornește implicit. Alege altul, introdu parola o singură dată și va porni după următoarea repornire. Celelalte kerneluri rămân în meniul de pornire, așa că poți alege în continuare unul manual dacă noua opțiune implicită îți face probleme. În terminal, este `nixos-kernel` pentru a vedea opțiunea implicită curentă, `nixos-kernel list` pentru ce este instalat și `nixos-kernel set <kernel>` pentru a comuta.

### Actualizări de firmware

Pachetele tale nu sunt singurul lucru care rămâne în urmă. Multe laptopuri și periferice furnizează firmware pentru BIOS, SSD și dock prin Linux Vendor Firmware Service, iar _Update > Firmware_ din meniul NixOS va prelua și instala tot ce așteaptă pentru hardware-ul tău. Instalează `fwupd` prima dată când îl rulezi. Mult firmware poate fi scris doar în timpul unei reporniri, așa că nu te mira dacă ți se cere una.

### Avertisment despre actualizările directe cu pacman/yay

Dacă ești deja familiarizat cu Arch, ai putea fi tentat să rulezi pur și simplu `pacman -Syu` sau `yay -Syu` pe cont propriu, dar dacă faci asta, vei rata snapshot-ul, migrările și actualizările de configurare pe care NixOS le rulează împreună cu pachetele noi. De aceea, NixOS va opri de fapt o actualizare directă a sistemului și te va îndruma în schimb spre `nixos update`. (Dacă chiar știi ce faci, protecția îți va spune cum să o ocolești pentru o singură tranzacție.)

### Revenirea după actualizări nereușite

Dacă ai vreodată o problemă după ce ai făcut o actualizare, poți reveni cu sistemul la snapshot-ul făcut înainte de actualizare. Repornește pur și simplu și alege snapshot-ul din meniul de încărcare la pornire de dinainte să fi început actualizarea.

![bootloader](images/bootloader.webp)

Dacă, cumva, fișierele tale de configurare au fost corupte, poți efectua și o reinstalare NixOS folosind `nixos reinstall` în terminal. Aceasta va reinstala toate pachetele NixOS implicite, te va trece pe stable și va face downgrade la orice pachete care sunt prea noi și va reseta toate fișierele de configurare. Reține că toate modificările tale de configurare de utilizator aduse valorilor implicite NixOS vor fi suprascrise făcând asta!
