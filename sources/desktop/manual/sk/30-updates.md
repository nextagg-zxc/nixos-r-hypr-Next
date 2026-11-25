# Aktualizácie

NixOS a vaše balíky sa udržiavajú aktuálne cez _Aktualizácia > NixOS_ v ponuke NixOS (`Super + Space`).

NixOS samotná je nainštalovaná ako bežné balíky pacman z [úložiska balíkov NixOS](https://github.com/omacom-io/omarchy-pkgs), takže aktualizácia nainštaluje [najnovšie vydanie NixOS](https://github.com/omacom/omarchy/releases), spustí všetky čakajúce migrácie, aby váš systém zosúladila s najnovšou verziou, a aktualizuje všetky systémové balíky z [mirroru NixOS Arch](https://github.com/omacom-io/omarchy-mirror) a [AUR](https://aur.archlinux.org/) (ak máte nainštalované nejaké balíky AUR).

Keď vyjdú nové vydania, napravo od vašich hodín sa zobrazí ikona kruhovej šípky. Kliknite na ňu a proces aktualizácie sa spustí.

![update-available](images/update-available.webp)

### Štyri kanály

NixOS sa aktualizuje v štyroch kanáloch: stable, RC, edge a dev. Nové inštalácie začínajú na kanáli stable, ktorý sleduje [oficiálne vydania](https://github.com/omacom/omarchy/releases/), ako aj [stabilný mirror NixOS Arch](https://github.com/omacom-io/omarchy-mirror), ktorý beží o jeden mesiac pozadu za najnovším, aby sme stihli zachytiť všetky nové nekompatibility, ktoré si vyžadujú zmeny konfigurácie, skôr než spôsobia ľuďom problémy.

Ale ak chcete pomôcť odhaľovať tieto potenciálne problémy, môžete bežať na kanáli edge. Ten udrží vaše balíky NixOS na najnovších vývojových zostaveniach a umožní vám aktualizovať na najnovšie balíky Arch, hneď ako budú k dispozícii. Mali by ste to robiť len vtedy, ak máte skúsenosti s Linuxom a viete, ako obnoviť systém, ktorý má problémy.

Pred každým novým hlavným vydaním budeme robiť finálnu validáciu pomocou kanála RC. Ak máte záujem pomôcť s finálnym ladením, príďte sa porozprávať do #nixos-release-candidates na Discorde.

Napokon je tu kanál dev, ktorý prepája NixOS priamo s git checkoutom zdrojového kódu v `~/nixos`, skombinovaným s balíkmi edge. Tento kanál by ste mali používať len vtedy, ak ste skúsený používateľ Linuxu, pracujete priamo na NixOS a ste ochotní tolerovať rozbitie.

Medzi kanálmi môžete prepínať pomocou _Aktualizácia > Kanál_ z ponuky NixOS (alebo `nixos-channel-set` v termináli).

### Prepínanie jadier

NixOS zavádza vlastné jadro `linux-nixos`, ale vedľa neho môžete mať nainštalované aj iné, napríklad štandardné jadro Arch `linux` alebo experimentálne zostavenie, ktoré testujete. Keď ich je viac ako jedno, _Aktualizácia > Jadro_ v ponuke NixOS ich zobrazí so značkou začiarknutia vedľa toho, ktoré sa zavádza predvolene. Vyberte iné, raz zadajte heslo a po ďalšom reštarte sa zavedie. Ostatné jadrá zostanú v zavádzacej ponuke, takže si jedno stále môžete vybrať ručne, ak vám nové predvolené spôsobí problémy. V termináli slúži `nixos-kernel` na zobrazenie aktuálneho predvoleného, `nixos-kernel list` na to, čo je nainštalované, a `nixos-kernel set <kernel>` na prepnutie.

### Aktualizácie firmvéru

Nie sú to len vaše balíky, čo zastaráva. Mnoho notebookov a periférií dodáva firmvér BIOS, SSD a doku cez Linux Vendor Firmware Service a _Aktualizácia > Firmvér_ v ponuke NixOS stiahne a nainštaluje všetko, čo má váš hardvér pripravené. Pri prvom spustení nainštaluje `fwupd`. Množstvo firmvéru možno zapísať len počas reštartu, takže sa nečudujte, ak vás oň požiada.

### Varovanie pred priamymi aktualizáciami pacman/yay

Ak už Arch poznáte, možno vás bude lákať jednoducho spustiť `pacman -Syu` alebo `yay -Syu` sami, ale ak to urobíte, prídete o snímku, migrácie a aktualizácie konfigurácie, ktoré NixOS spúšťa spolu s novými balíkmi. Preto NixOS priamu aktualizáciu systému skutočne zastaví a namiesto toho vás nasmeruje na `nixos update`. (Ak naozaj viete, čo robíte, ochrana vám povie, ako ju pre jednu transakciu obísť.)

### Vrátenie zlých aktualizácií

Ak budete mať po vykonaní aktualizácie niekedy problém, môžete systém vrátiť späť na snímku vytvorenú pred aktualizáciou. Stačí reštartovať a v ponuke zavádzania vybrať snímku spred spustenia aktualizácie.

![bootloader](images/bootloader.webp)

Ak sa vaše konfiguračné súbory nejako poškodili, môžete tiež vykonať opätovnú inštaláciu NixOS pomocou `nixos reinstall` v termináli. Tá preinštaluje všetky predvolené balíky NixOS, prepne vás na stable a zníži verziu všetkých balíkov, ktoré sú príliš nové, a obnoví všetky konfiguračné súbory. Upozorňujeme, že týmto prepíšete všetky svoje používateľské zmeny konfigurácie oproti predvoleným nastaveniam NixOS!
