# Aktualizacje

NixOS i Twoje pakiety są na bieżąco aktualizowane przez _Aktualizacja > NixOS_ w menu NixOS (`Super + Space`).

Samo NixOS jest instalowane jako zwykłe pakiety pacman z [NixOS Package Repository](https://github.com/omacom-io/omarchy-pkgs), więc aktualizacja instaluje [najnowsze wydanie NixOS](https://github.com/omacom/omarchy/releases), uruchamia wszelkie oczekujące migracje, aby zsynchronizować Twój system z najnowszą wersją, oraz aktualizuje wszystkie pakiety systemowe z [NixOS Arch Mirror](https://github.com/omacom-io/omarchy-mirror) i [AUR](https://aur.archlinux.org/) (jeśli masz zainstalowane jakiekolwiek pakiety AUR).

Gdy pojawią się nowe wydania, po prawej stronie zegara pojawi się ikona strzałki w okręgu. Kliknij ją, a proces aktualizacji się rozpocznie.

![update-available](images/update-available.webp)

### Cztery kanały

NixOS jest aktualizowane w czterech kanałach: stable, RC, edge i dev. Nowe instalacje zaczynają na kanale stable, który śledzi [oficjalne wydania](https://github.com/omacom/omarchy/releases/), a także [stabilne mirror NixOS Arch](https://github.com/omacom-io/omarchy-mirror), które jest opóźnione o miesiąc względem najnowszego, dzięki czemu możemy wyłapać wszelkie nowe niezgodności wymagające zmian w konfiguracji, zanim sprawią komuś problemy.

Jeśli jednak chcesz pomóc w wykrywaniu tych potencjalnych problemów, możesz korzystać z kanału edge. Dzięki temu Twoje pakiety NixOS będą śledzić najnowsze buildy deweloperskie, a Ty będziesz mógł aktualizować do najnowszych pakietów Arch, gdy tylko staną się dostępne. Powinieneś to robić tylko wtedy, gdy masz doświadczenie z Linux i wiesz, jak odzyskać system, w którym wystąpiły problemy.

Przed każdym nowym większym wydaniem będziemy przeprowadzać finalną walidację przy użyciu kanału RC. Jeśli chcesz pomóc w finalnym dopracowywaniu, wpadnij na #nixos-release-candidates na Discord.

Na koniec jest kanał dev, który łączy NixOS bezpośrednio z checkout git kodu źródłowego w `~/nixos`, w połączeniu z pakietami edge. Powinieneś używać tego kanału tylko wtedy, gdy jesteś doświadczonym użytkownikiem Linux, pracujesz bezpośrednio nad NixOS i jesteś gotów tolerować awarie.

Możesz przełączać się między kanałami za pomocą _Aktualizacja > Kanał_ w menu NixOS (lub `nixos-channel-set` w terminalu).

### Przełączanie kerneli

NixOS uruchamia własny kernel `linux-nixos`, ale możesz mieć obok niego zainstalowane inne, takie jak standardowy kernel Arch `linux` lub eksperymentalny build, który testujesz. Gdy jest ich więcej niż jeden, _Aktualizacja > Kernel_ w menu NixOS wyświetla je z zaznaczeniem obok tego, który uruchamia się domyślnie. Wybierz inny, raz wpisz swoje hasło, a uruchomi się po następnym restarcie. Pozostałe kernele pozostają w menu rozruchowym, więc nadal możesz wybrać jeden ręcznie, jeśli nowy domyślny sprawi Ci problemy. W terminalu `nixos-kernel` pokazuje bieżący domyślny, `nixos-kernel list` pokazuje, co jest zainstalowane, a `nixos-kernel set <kernel>` służy do przełączania.

### Aktualizacje firmware

Nie tylko Twoje pakiety się starzeją. Wiele laptopów i urządzeń peryferyjnych dostarcza firmware BIOS, SSD i stacji dokujących przez Linux Vendor Firmware Service, a _Aktualizacja > Firmware_ w menu NixOS pobierze i zainstaluje wszystko, co czeka na Twój sprzęt. Przy pierwszym uruchomieniu instaluje `fwupd`. Sporo firmware można zapisać tylko podczas restartu, więc nie zdziw się, jeśli zostaniesz o niego poproszony.

### Ostrzeżenie o bezpośrednich aktualizacjach pacman/yay

Jeśli znasz już Arch, może Cię kusić, aby po prostu samemu uruchomić `pacman -Syu` lub `yay -Syu`, ale jeśli to zrobisz, pominiesz snapshot, migracje i aktualizacje konfiguracji, które NixOS uruchamia razem z nowymi pakietami. Dlatego NixOS faktycznie zatrzyma bezpośrednią aktualizację systemu i zamiast tego wskaże Ci `nixos update`. (Jeśli naprawdę wiesz, co robisz, zabezpieczenie powie Ci, jak je ominąć dla jednej transakcji.)

### Wycofywanie złych aktualizacji

Jeśli kiedykolwiek będziesz mieć problem po wykonaniu aktualizacji, możesz wycofać system do snapshotu wykonanego przed aktualizacją. Po prostu uruchom ponownie i wybierz w menu ładowania bootloadera snapshot sprzed rozpoczęcia aktualizacji.

![bootloader](images/bootloader.webp)

Jeśli w jakiś sposób Twoje pliki konfiguracyjne zostały uszkodzone, możesz także wykonać ponowną instalację NixOS za pomocą `nixos reinstall` w terminalu. Spowoduje to ponowną instalację wszystkich domyślnych pakietów NixOS, przełączenie Cię na stable i obniżenie wersji wszelkich pakietów, które są zbyt nowe, oraz zresetowanie wszystkich plików konfiguracyjnych. Pamiętaj, że wszystkie zmiany konfiguracji użytkownika wprowadzone do domyślnych ustawień NixOS zostaną przy tym nadpisane!
