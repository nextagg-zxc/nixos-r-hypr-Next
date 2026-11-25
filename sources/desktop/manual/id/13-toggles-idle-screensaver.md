# Toggle, Idle & Screensaver

Banyak hal yang kamu ubah sehari-hari sebenarnya bukan sebuah pengaturan. Itu adalah mode yang kamu aktifkan selama satu jam lalu kamu matikan lagi: cahaya malam saat kamu bekerja sampai larut, jangan ganggu saat kamu presentasi, tetap terjaga saat kamu sedang menonton sesuatu. NixOS menyebutnya toggle, dan semuanya bekerja dengan cara yang sama — sebuah hotkey, sebuah entri menu, dan sebuah perintah, semuanya menyentuh sakelar yang sama.

### Menu toggle

`Super + Ctrl + O` membuka _Trigger > Toggle_ secara langsung, atau kamu bisa berjalan ke sana dari menu NixOS (`Super + Space`). Semua yang ada di daftar itu adalah sakelar yang bisa kamu balik tanpa memikirkan di mana statusnya tinggal. Sakelar untuk tampilan desktop berada di sampingnya, di bawah _Appearance_.

Dari terminal, sakelar yang sama adalah `nixos toggle <thing>`. Jalankan `nixos toggle` sendiri untuk melihat seluruh grupnya.

| Toggle | Hotkey | Perintah |
| ------ | ------ | ------- |
| Cahaya malam | — | `nixos toggle nightlight` |
| Senyapkan notifikasi | `Super + Ctrl + Alt + ,` | `nixos toggle notification silencing` |
| Tetap terjaga (tanpa kunci idle) | `Super + Ctrl + I` | `nixos toggle idle` |
| Penangkapan crash | — | `nixos toggle crash-capture` |
| Screensaver | — | `nixos toggle screensaver` |
| Sinkronisasi tema [Herdr](https://herdr.dev) | — | `nixos toggle theme sync` |
| Bilah menu | `Super + Shift + Space` | `nixos toggle bar` |
| Touchpad | `XF86TouchpadToggle` | `nixos toggle touchpad` |
| Layar sentuh | — | `nixos toggle touchscreen` |
| Suspend | — | `nixos toggle suspend` |
| Hybrid GPU | — | `nixos toggle hybrid gpu` |

Sakelar touchpad, layar sentuh, dan hybrid GPU tinggal di bawah _Trigger > Hardware_ (`Super + Ctrl + H`) bukan di bawah Toggle, karena mereka hanya muncul saat kamu benar-benar memiliki perangkat keras tersebut. Sakelar touchpad dan layar sentuh bertahan setelah Hyprland dimuat ulang — nama perangkat yang dinonaktifkan disimpan ke file status kecil yang dibaca Hyprland saat startup untuk menonaktifkannya lagi.

_Appearance_ menampung bilah menu dan animasi, ditambah beberapa hal yang bukan perintah `nixos toggle` tetapi berperilaku sama: persentase baterai di bilah, tata letak workspace default, dan di bawah _Windows_, celah jendela (`Super + Shift + Backspace`) dan aspek persegi 1-jendela (`Super + Ctrl + Backspace`).

Sebagian besar dari ini hanyalah file flag di bawah `~/.local/state/nixos/toggles/`. Jika kamu ingin bercabang berdasarkan salah satunya dalam sebuah skrip, `nixos-toggle-enabled` memberimu kode keluar alih-alih membuatmu mencarinya:

```bash
nixos-toggle-enabled screensaver-off && echo "screensaver is off"
```

Flag-flag tersebut dinamai untuk status mati — `screensaver-off`, `suspend-off`, `bar-off` — jadi keberadaannya berarti fitur tersebut dinonaktifkan.

### Indikator di bilah

Saat sebuah mode aktif, kamu mendapatkan glyph kecil di tengah bilah atas di samping jam. Itu adalah widget indikator, dan ia membawa dikte, perekaman layar, pengingat yang tertunda, cahaya malam, jangan ganggu, dan tetap terjaga.

Indikator yang tidak aktif disembunyikan. Arahkan kursor ke mana saja di bilah dan mereka memudar masuk dalam keadaan redup, jadi kamu bisa mengklik salah satunya untuk menyalakannya tanpa mengetahui hotkey-nya. Mengklik yang aktif akan mematikannya kembali. Jika kamu lebih suka melihat semuanya setiap saat, atur `alwaysShow` ke `true` pada entri `nixos.indicators` di `~/.config/nixos/shell.json` — lihat [bilah atas](05-the-top-bar.md) untuk cara widget bilah dikonfigurasi.

### Cahaya malam

Cahaya malam menghangatkan layar ke 4000K, dan men-toggle-nya lagi mengembalikannya ke 6500K. Balik dari menu toggle (`Super + Ctrl + O`) atau dengan `nixos toggle nightlight`. Ini digerakkan oleh hyprsunset, yang akan dimulai oleh toggle untukmu jika belum berjalan.

Secara default hyprsunset tidak melakukan apa pun sama sekali pada layarmu. `~/.config/hypr/hyprsunset.conf` disertai dengan profil identitas tepat agar tampilan tetap tidak tersentuh sampai kamu meminta kehangatan. Jika kamu lebih suka ia beralih mengikuti jam, ganti itu dengan profil waktu:

```
profile {
    time = 20:00
    temperature = 4000
}
```

Lalu mulai hyprsunset saat login dengan menambahkan `o.launch_on_start("hyprsunset")` ke `~/.config/hypr/autostart.lua`. Pasangan 4000K/6500K yang digunakan oleh toggle bersifat tetap, jadi file konfigurasi adalah tempat yang kamu tuju jika kamu menginginkan suhu yang berbeda.

### Jangan ganggu

`Super + Ctrl + Alt + ,` membungkam notifikasi. Tidak ada toast yang muncul saat ini aktif, dan indikator bel yang dicoret berada di bilah untuk mengingatkanmu mengapa desktop menjadi sunyi.

Namun tidak ada yang hilang. Notifikasi yang dibungkam ditahan: tampilkan kembali beberapa yang terakhir di layar dengan `Super + Shift + Alt + ,`. Lihat [pemberitahuan](10-notices.md) untuk sisanya.

Dua jenis pesan tetap bisa menembus: toast konfirmasi NixOS sendiri untuk sesuatu yang baru saja kamu lakukan ("Theme changed", "Screenshot saved"), dan peringatan kritis yang dikirim dari baris perintah. Aplikasi chat yang menandai semuanya kritis untuk memaksakan diri di depanmu tidak memenuhi syarat.

### Idle

Shell NixOS memiliki perilaku idle, dan waktunya adalah blok `idle` tingkat atas di `~/.config/nixos/shell.json`:

```json
{
  "version": 1,
  "idle": {
    "screensaver": 150,
    "lock": 300
  }
}
```

Kedua angka adalah detik yang dihitung dari saat kamu menjadi idle — bukan dari satu sama lain. Jadi dengan default, screensaver muncul setelah dua setengah menit dan layar kunci mengambil alih pada lima menit, terlepas dari apakah screensaver berjalan atau tidak. Simpan file dan shell mengambil waktu baru tersebut segera.

Jika kamu menutup screensaver sebelum batas waktu kunci, itu dihitung sebagai aktivitas dan kunci yang tertunda dibatalkan. Kamu tidak terkunci hanya karena melirik mesimu.

Untuk berhenti mengunci saat idle sepenuhnya, `Super + Ctrl + I` — atau `nixos toggle idle` — membalik tetap terjaga menjadi aktif, dan indikator cangkir kopi muncul di bilah. Itu yang harus ditekan sebelum presentasi panjang atau build yang ingin kamu tonton. Tekan lagi untuk kembali normal. `nixos toggle idle status` mencetak status saat ini sebagai JSON jika kamu membutuhkannya dari sebuah skrip.

Ini tentang penguncian dan screensaver, bukan daya. Suspend dan hibernasi memiliki pengaturannya sendiri di [tidur sistem](36-system-sleep.md).

### Screensaver

Screensaver NixOS adalah seni ASCII yang berjalan melalui efek teks acak, satu instans per monitor. Tombol apa pun atau gerakan mouse akan keluar darinya.

Kamu bisa memulainya sesuai permintaan dari _System > Screensaver_ (`Super + Esc`), yang memaksanya muncul bahkan jika kamu telah mematikan screensaver idle. Tidak ada hotkey yang terikat padanya secara default.

`nixos toggle screensaver` adalah yang mematikan yang idle, jika kamu lebih suka langsung dari bekerja ke terkunci. Ia membutuhkan terminal yang ia tahu cara mengkonfigurasinya — Alacritty, Foot, Ghostty, atau Kitty — dan akan memberitahumu demikian jika terminal default-mu adalah sesuatu yang lain.

Logo yang digambarnya adalah milikmu untuk diubah, di bawah _Appearance > Branding > Screensaver_. Unggah png atau svg dan NixOS mengubahnya menjadi ASCII. Lihat [branding](41-branding.md).

### Layar kunci

`Super + Ctrl + L` mengunci mesin. Itu menjalankan layar kunci dari shell NixOS, mengosongkan tampilan, mengatur ulang tata letak keyboard-mu ke yang pertama agar kamu tidak mengetik kata sandimu dalam alfabet yang salah, dan — jika kamu menjalankannya — mengunci 1Password dalam perjalanan keluar.

Layar kunci menerima kata sandi, dan ia juga akan menerima sidik jari setelah kamu mengaturnya. Itu, dan cara lain untuk mengautentikasi, dibahas di [autentikasi perangkat keras](37-hardware-authentication.md).
