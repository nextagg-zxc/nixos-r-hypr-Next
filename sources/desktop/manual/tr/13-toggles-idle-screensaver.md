# Açma/Kapama Düğmeleri, Boşta Kalma ve Ekran Koruyucu

Günlük olarak değiştirdiğiniz şeylerin çoğu aslında bir ayar değildir. Bir saatliğine açıp sonra tekrar kapattığınız bir moddur: geç saatlere kadar çalışırken gece ışığı, sunum yaparken rahatsız etme, bir şey izlerken uyanık kalma. NixOS bunlara açma/kapama düğmeleri diyor ve hepsi aynı şekilde çalışıyor — bir kısayol tuşu, bir menü girdisi ve bir komut, hepsi aynı düğmeye basıyor.

### Açma/kapama menüsü

`Super + Ctrl + O` doğrudan _Trigger > Toggle_ menüsünü açar ya da NixOS menüsünden (`Super + Space`) oraya yürüyebilirsiniz. O listedeki her şey, durumun nerede yaşadığını düşünmeden çevirebileceğiniz bir düğmedir. Masaüstünün nasıl göründüğüne dair düğmeler onun yanında, _Appearance_ altında yer alır.

Terminalden aynı düğmeler `nixos toggle <thing>` şeklindedir. Grubun tamamını görmek için tek başına `nixos toggle` çalıştırın.

| Açma/Kapama | Kısayol Tuşu | Komut |
| ------ | ------ | ------- |
| Gece ışığı | — | `nixos toggle nightlight` |
| Bildirimleri sessize al | `Super + Ctrl + Alt + ,` | `nixos toggle notification silencing` |
| Uyanık kal (boşta kilidi yok) | `Super + Ctrl + I` | `nixos toggle idle` |
| Çökme yakalama | — | `nixos toggle crash-capture` |
| Ekran koruyucu | — | `nixos toggle screensaver` |
| [Herdr](https://herdr.dev) tema senkronizasyonu | — | `nixos toggle theme sync` |
| Menü çubuğu | `Super + Shift + Space` | `nixos toggle bar` |
| Dokunmatik yüzey | `XF86TouchpadToggle` | `nixos toggle touchpad` |
| Dokunmatik ekran | — | `nixos toggle touchscreen` |
| Askıya al | — | `nixos toggle suspend` |
| Hibrit GPU | — | `nixos toggle hybrid gpu` |

Dokunmatik yüzey, dokunmatik ekran ve hibrit GPU düğmeleri Toggle altında değil, _Trigger > Hardware_ (`Super + Ctrl + H`) altında yaşar, çünkü yalnızca o donanıma gerçekten sahipseniz görünürler. Dokunmatik yüzey ve dokunmatik ekran düğmeleri bir Hyprland yeniden yüklemesinden sağ çıkar — devre dışı bırakılan cihazın adı, Hyprland'ın başlangıçta okuyup cihazı yeniden devre dışı bırakmak için kullandığı küçük bir durum dosyasına kaydedilir.

_Appearance_ menü çubuğunu ve animasyonları barındırır, ayrıca `nixos toggle` komutu olmayan ama aynı şekilde davranan birkaç şeyi de: çubuktaki pil yüzdesi, varsayılan çalışma alanı düzeni ve _Windows_ altında pencere boşlukları (`Super + Shift + Backspace`) ile 1 pencerelik kare en-boy oranı (`Super + Ctrl + Backspace`).

Bunların çoğu `~/.local/state/nixos/toggles/` altında bir bayrak dosyasından ibarettir. Bir betikte birine göre dallanmak isterseniz, `nixos-toggle-enabled` size gidip aramak zorunda kalmadan bir çıkış kodu verir:

```bash
nixos-toggle-enabled screensaver-off && echo "screensaver is off"
```

Bayraklar kapalı durum için adlandırılır — `screensaver-off`, `suspend-off`, `bar-off` — yani varlıkları özelliğin devre dışı olduğu anlamına gelir.

### Çubuktaki göstergeler

Bir mod açık olduğunda, üst çubuğun ortasında saatin yanında küçük bir simge alırsınız. Bu, göstergeler aracıdır ve dikteyi, ekran kaydını, bekleyen hatırlatıcıları, gece ışığını, rahatsız etmeyi ve uyanık kalmayı taşır.

Etkin olmayan göstergeler gizlidir. Çubuğun herhangi bir yerinde fareyle üzerine gelin, soluk şekilde belirirler; böylece kısayol tuşunu bilmeden birine tıklayıp açabilirsiniz. Etkin birine tıklamak onu tekrar kapatır. Hepsini her zaman görmek isterseniz, `~/.config/nixos/shell.json` içindeki `nixos.indicators` girdisinde `alwaysShow` değerini `true` olarak ayarlayın — çubuk araçlarının nasıl yapılandırıldığı için bkz. [üst çubuk](05-the-top-bar.md).

### Gece ışığı

Gece ışığı ekranı 4000K'ye ısıtır ve tekrar açıp kapamak onu 6500K'ye geri getirir. Açma/kapama menüsünden (`Super + Ctrl + O`) ya da `nixos toggle nightlight` ile çevirin. hyprsunset tarafından çalıştırılır ve düğme, zaten çalışmıyorsa onu sizin için başlatır.

Varsayılan olarak hyprsunset ekranınıza hiçbir şey yapmaz. `~/.config/hypr/hyprsunset.conf` tam olarak bir kimlik profiliyle gelir, böylece siz sıcaklık istemedikçe ekran el değmemiş kalır. Saate göre değişmesini tercih ederseniz, bunu bir zaman profiliyle değiştirin:

```
profile {
    time = 20:00
    temperature = 4000
}
```

Ardından `~/.config/hypr/autostart.lua` dosyasına `o.launch_on_start("hyprsunset")` ekleyerek hyprsunset'i oturum açışta başlatın. Düğmenin kullandığı 4000K/6500K çifti sabittir, yani farklı bir sıcaklık istiyorsanız gideceğiniz yer yapılandırma dosyasıdır.

### Rahatsız etme

`Super + Ctrl + Alt + ,` bildirimleri sessize alır. Açıkken hiçbir bildirim baloncuğu çıkmaz ve üstü çizili zil göstergesi, masaüstünün neden sessizliğe gömüldüğünü hatırlatmak için çubukta oturur.

Yine de hiçbir şey kaybolmaz. Sessize alınan bildirimler geri tutulur: son birkaçını `Super + Shift + Alt + ,` ile tekrar ekrana getirin. Geri kalanı için bkz. [bildirimler](10-notices.md).

İki tür mesaj yine de geçer: NixOS'nin az önce yaptığınız bir şey için kendi onay baloncukları ("Theme changed", "Screenshot saved") ve komut satırından gönderilen kritik uyarılar. Her şeyi önünüze zorla çıkmak için kritik olarak işaretleyen sohbet uygulamaları buna hak kazanmaz.

### Boşta kalma

Boşta kalma davranışının sahibi NixOS kabuğudur ve zamanlamalar `~/.config/nixos/shell.json` içinde üst düzey bir `idle` bloğudur:

```json
{
  "version": 1,
  "idle": {
    "screensaver": 150,
    "lock": 300
  }
}
```

Her iki sayı da boşta kaldığınız andan itibaren sayılan saniyelerdir — birbirlerinden itibaren değil. Yani varsayılanlarla ekran koruyucu iki buçuk dakika sonra çıkar ve ekran koruyucu çalışmış olsun ya da olmasın kilit ekranı beş dakikada devralır. Dosyayı kaydedin, kabuk yeni zamanlamaları hemen alır.

Kilit son tarihinden önce ekran koruyucuyu kapatırsanız, bu etkinlik sayılır ve bekleyen kilit iptal edilir. Makinenize göz attığınız için dışarıda kilitli kalmazsınız.

Boşta kilitlemeyi tamamen durdurmak için `Super + Ctrl + I` — ya da `nixos toggle idle` — uyanık kalmayı açar ve çubukta kahve fincanı göstergesi belirir. Uzun bir sunumdan ya da izlemek istediğiniz bir derlemeden önce basılacak düğme budur. Normale dönmek için tekrar basın. Bir betikten ihtiyacınız olursa `nixos toggle idle status` geçerli durumu JSON olarak yazdırır.

Bu, güçle değil kilitleme ve ekran koruyucuyla ilgilidir. Askıya alma ve hazırda bekletmenin [sistem uykusu](36-system-sleep.md) içinde kendi kurulumları vardır.

### Ekran koruyucu

NixOS'nin ekran koruyucusu, rastgele metin efektlerinden geçen ASCII sanatıdır, monitör başına bir örnek çalışır. Herhangi bir tuş ya da fare hareketi ondan çıkar.

Onu _System > Screensaver_ (`Super + Esc`) üzerinden isteğe bağlı başlatabilirsiniz; bu, boşta ekran koruyucuyu kapatmış olsanız bile onu zorla çıkarır. Varsayılan olarak ona bağlı bir kısayol tuşu yoktur.

Çalışmaktan doğrudan kilitli duruma geçmeyi tercih ederseniz, boşta olanı kapatan şey `nixos toggle screensaver` komutudur. Nasıl yapılandıracağını bildiği bir terminale ihtiyacı vardır — Alacritty, Foot, Ghostty ya da Kitty — ve varsayılan terminaliniz başka bir şeyse size bunu söyler.

Çizdiği logo değiştirmeniz için sizindir, _Appearance > Branding > Screensaver_ altındadır. Bir png ya da svg yükleyin, NixOS onu ASCII'ye dönüştürür. Bkz. [markalama](41-branding.md).

### Kilit ekranı

`Super + Ctrl + L` makineyi kilitler. Bu, NixOS kabuğundan kilit ekranını çalıştırır, ekranı karartır, parolanızı yanlış alfabede yazmamanız için klavye düzeninizi ilk düzene sıfırlar ve — çalıştırıyorsanız — çıkış yolunda 1Password'ü kilitler.

Kilit ekranı bir parola alır ve bir parmak izi ayarladıktan sonra onu da alır. Bu ve kimlik doğrulamanın diğer yolları [donanım kimlik doğrulaması](37-hardware-authentication.md) içinde ele alınır.
