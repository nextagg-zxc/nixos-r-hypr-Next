# Aloittaminen

NixOS asennetaan ISO:n avulla. Voit valita koko levyn asennuksen, joka ottaa koko aseman haltuunsa, tai vapaan tilan asennuksen, joka sijoittaa NixOSn asemalla olevaan varaamattomaan tilaan — näin teet kaksoiskäynnistyksen Windowsin tai toisen käyttöjärjestelmän rinnalla (katso [kaksoiskäynnistysasennus](50-dual-boot-install.md) — huomaa, että sinun täytyy ensin poistaa BitLocker käytöstä Windowsissa). Kummassakin tapauksessa asennus käyttää oletusarvoisesti täyttä salausta, ja koko levyn vaihtoehto pyyhkii valitun aseman, joten muista ottaa varmuuskopio ennen kuin käytät jo käytössä olevaa asemaa!

[Lataa NixOS ISO](https://omarchy.org/) ensin, laita se USB-tikulle (käytä Windowsissa [Rufus](https://rufus.ie/), Macissa [balenaEtcher](https://etcher.balena.io/) tai Linuxissa [caligula](https://github.com/ifd3f/caligula)) ja käynnistä tikulta.

_Sinun on poistettava Secure Boot ja/tai TPM käytöstä BIOSissa. Sinun on poistettava nämä käytöstä, jotta voit asentaa NixOSn. Ne ovat Microsoftin tietoturvajärjestelmiä, jotka on tarkoitettu Windowsille ja Microsoftiin kytköksissä oleville Linux-jakeluille._

Vastaa sitten määrityskysymyksiin ja vahvista ne näin:

 ![install-config](images/install-config.webp)

Valitse sitten asema asennusta varten, istu alas ja katso asennusesitystä. Se voi valmistua alle minuutissa nopeimmilla nykyaikaisilla koneilla, mutta sen ei pitäisi kestää yli 5 minuuttia edes vanhemmalla tietokoneella.

 ![install-done](images/install-done.webp)

Nyt olet valmis NixOSyn!

### Käytä langallista tai 2.4ghz-näppäimistöä!

Koko levyn salaus ei anna sinun syöttää salasanaa Bluetooth-näppäimistöltä käynnistyksen yhteydessä. Aivan kuten et voi käyttää Bluetooth-näppäimistöä BIOSiin siirtymiseen PC:llä. Tarvitset näppäimistön, joka käyttää joko 2.4ghz-vastaanotinta tai kaapelia (joka on muutenkin paljon mukavampi viiveen kannalta!). Itse rakastan [Lofree Flow84](https://www.lofree.co/products/lofree-flow-the-smoothest-mechanical-keyboard)!

### Asentaminen toiselle omistajalle

Jos valmistelet konetta jollekin toiselle — perheenjäsenelle, uudelle työntekijälle, ostajalle — sinun ei pitäisi vastata henkilökohtaisiin kysymyksiin heidän puolestaan. Paina `Ctrl + C` asentimen aivan ensimmäisellä näytöllä (näppäimistön valinta), niin NixOS tarjoaa sen sijaan koneen valmistelua toiselle omistajalle. Järjestelmä asentuu heti, mutta kaikki henkilökohtainen määritys — näppäimistöasettelu, käyttäjätunnus, salasana — lykätään siihen asti, kun kone käynnistyy ensimmäisen kerran. Asema salataan silti oletusarvoisesti, ja salasanasta, jonka uusi omistaja valitsee ensimmäisellä käynnistyksellä, tulee myös salaussalasana. (Myös jo käyttämäsi kone voidaan luovuttaa ilman uudelleenasennusta — katso [tietokoneen nollaaminen](48-security.md).)

### Valvomattomat asennukset

ISO voi myös asentaa täysin itsenäisesti — ilman näppäimistöä, ilman ohjattua toimintoa — kun sille annetaan määrityksensä toisella asemalla. Näin NixOSa kannattaa käsitellä VM:ien ja konelaivueiden peruslevykuvana. Katso [valvomattomat asennukset](51-unattended-installs.md).

### Asennukset ilman salausta

NixOS asennetaan oletusarvoisesti salauksen kanssa. Se on turvallinen ja vastuullinen valinta mille tahansa tietokoneelle, joka voi mahdollisesti kadota tai tulla varastetuksi. Et halua kenenkään, jolla on pääsy laitteistoosi, voivan saada tietojasi!

Mutta erityistilanteissa, kuten NixOSn etäasennuksissa suojatuille tietokoneille tai kertakäyttöasennuksissa ilman arkaluonteisia tietoja, saatat haluta asentaa ilman salausta. Voit painaa `Ctrl + C` levyn alustuksen vahvistuksessa vaihtaaksesi salauksettoman asennuksen.

### Kieli

NixOS puhuu 50 kieltä — samaa valikoimaa kuin nixos.org — ja englanti on oletus. Vaihtaaksesi avaa NixOS-valikko ja siirry kohtaan _Setup > Language_ tai aja päätteessä `nixos language <code>` (`nixos language list` näyttää koodit). Valikko, työpöytä ja NixOSn omat ilmoitukset vaihtavat kielen välittömästi, ja jokainen sen jälkeen avaamasi sovellus tekee samoin. Jo auki olleet sovellukset vaihtavat, kun käynnistät ne uudelleen.

### Apua, jos jäät jumiin

Jos jäät jumiin, löydät yleensä jonkun, joka on valmis auttamaan, _#nixos-help_-kanavalta [yhteisön Discordissa](https://omarchy.org/discord).
