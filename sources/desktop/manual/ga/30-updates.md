# Nuashonruithe

Coinnítear NixOS agus do phacáistí cothrom le dáta trí _Nuashonrú > NixOS_ sa roghchlár NixOS (`Super + Space`).

Suiteáiltear NixOS féin mar ghnáthphacáistí pacman ó [Stór Pacáistí NixOS](https://github.com/omacom-io/omarchy-pkgs), mar sin suiteálann nuashonrú [an eisiúint is déanaí de NixOS](https://github.com/omacom/omarchy/releases), ritheann sé aon aistrithe atá ar feitheamh chun do chóras a chur i gcomhréir leis an leagan is déanaí, agus nuashonraíonn sé gach pacáiste córais ó [Scáthán Arch NixOS](https://github.com/omacom-io/omarchy-mirror) agus [AUR](https://aur.archlinux.org/) (má tá aon phacáistí AUR suiteáilte agat).

Nuair a dhéantar eisiúintí nua, beidh deilbhín saigheade ciorclaí le feiceáil ar thaobh na láimhe deise de do chlog. Cliceáil é agus tosóidh an próiseas nuashonraithe.

![update-available](images/update-available.webp)

### Ceithre chainéal

Nuashonraítear NixOS ar cheithre chainéal: stable, RC, edge, agus dev. Tosaíonn suiteálacha nua ar an gcainéal stable, a leanann na [heisiúintí oifigiúla](https://github.com/omacom/omarchy/releases/), chomh maith leis an [scáthán cobhsaí Arch NixOS](https://github.com/omacom-io/omarchy-mirror) atá mí amháin taobh thiar den leagan is déanaí, ionas gur féidir linn aon neamh-chomhoiriúnachtaí nua a dteastaíonn athruithe cumraíochta uathu a aimsiú sula gcruthaíonn siad fadhbanna do dhaoine.

Ach más mian leat cabhrú leis na fadhbanna féideartha sin a aimsiú, is féidir leat rith ar an gcainéal edge. Coinneoidh sé sin do phacáistí NixOS ag leanúint na leaganacha forbartha is déanaí, agus ligfidh sé duit nuashonrú chuig na pacáistí Arch is déanaí a luaithe a bhíonn siad ar fáil. Níor cheart duit é seo a dhéanamh ach amháin má tá taithí agat ar Linux, agus má tá a fhios agat conas córas a bhfuil fadhbanna aige a athshlánú.

Roimh aon mhóreisiúint nua, déanfaimid an bailíochtú deiridh ag baint úsáide as an gcainéal RC. Má tá suim agat cabhrú leis an snas deiridh, tar ag caitheamh ama in #nixos-release-candidates ar an Discord.

Ar deireadh, tá an cainéal dev ann, a nascann NixOS go díreach le cóip git den chód foinse in `~/nixos`, in éineacht leis na pacáistí edge. Níor cheart duit an cainéal seo a úsáid ach amháin má tá taithí agat mar úsáideoir Linux, má tá tú ag obair go díreach ar NixOS, agus má tá tú sásta glacadh le briseadh.

Is féidir leat aistriú idir cainéil ag baint úsáide as _Nuashonrú > Cainéal_ ón roghchlár NixOS (nó `nixos-channel-set` sa teirminéal).

### Eithní a athrú

Tosaíonn NixOS lena eithne féin `linux-nixos`, ach is féidir leat cinn eile a choinneáil suiteáilte in aice leis, cosúil leis an eithne stoc Arch `linux` nó leagan turgnamhach atá á thástáil agat. Nuair a bhíonn níos mó ná ceann amháin ann, liostaíonn _Nuashonrú > Eithne_ sa roghchlár NixOS iad le tic in aice leis an gceann a thosaíonn de réir réamhshocraithe. Roghnaigh ceann eile, cuir isteach d'fhocal faire uair amháin, agus tosóidh sé tar éis an chéad atosaigh eile. Fanann na heithní eile sa roghchlár tosaithe, mar sin is féidir leat ceann a roghnú de láimh fós má chruthaíonn an réamhshocrú nua trioblóid duit. Sa teirminéal, is é `nixos-kernel` é chun an réamhshocrú reatha a fheiceáil, `nixos-kernel list` le haghaidh a bhfuil suiteáilte, agus `nixos-kernel set <kernel>` chun athrú.

### Nuashonruithe dochtearraí

Ní hiad do phacáistí an t-aon rud a théann i léig. Seolann go leor ríomhairí glúine agus forimeallaigh dochtearraí BIOS, SSD, agus duga tríd an Linux Vendor Firmware Service, agus gheobhaidh agus suiteálfaidh _Nuashonrú > Dochtearraí_ sa roghchlár NixOS cibé rud atá ag fanacht le do chrua-earraí. Suiteálann sé `fwupd` an chéad uair a ritheann tú é. Ní féidir go leor dochtearraí a scríobh ach amháin le linn atosaigh, mar sin ná bíodh iontas ort má iarrtar ceann ort.

### Rabhadh faoi nuashonruithe díreacha pacman/yay

Má tá tú eolach ar Arch cheana féin, b'fhéidir go mbeidh cathú ort `pacman -Syu` nó `yay -Syu` a rith tú féin, ach má dhéanann tú é sin, caillfidh tú an seat, na haistrithe, agus na nuashonruithe cumraíochta a ritheann NixOS in éineacht le pacáistí nua. Sin é an fáth go stopfaidh NixOS uasghrádú díreach córais i ndáiríre agus go dtreoróidh sé thú chuig `nixos update` ina áit. (Má tá a fhios agat i ndáiríre cad atá á dhéanamh agat, inseoidh an garda duit conas é a sheachaint d'aon idirbheart amháin.)

### Drochnuashonruithe a rolladh ar ais

Má bhíonn fadhb agat riamh tar éis nuashonrú a dhéanamh, is féidir leat do chóras a rolladh ar ais chuig an seat a tógadh roimh an nuashonrú. Níl le déanamh ach atosú agus an seat a roghnú sa roghchlár lódála tosaithe ón am sular thosaigh tú an nuashonrú.

![bootloader](images/bootloader.webp)

Má tá do chomhaid chumraíochta truaillithe ar bhealach éigin, is féidir leat athshuiteáil NixOS a dhéanamh freisin ag baint úsáide as `nixos reinstall` sa teirminéal. Athshuiteálfaidh sé seo gach pacáiste réamhshocraithe NixOS, cuirfidh sé ar stable thú agus íosghrádóidh sé aon phacáistí atá ró-nua, agus athshocróidh sé na comhaid chumraíochta go léir. Tabhair faoi deara go bhforscríobhfar gach athrú cumraíochta úsáideora a rinne tú ar réamhshocruithe NixOS agus é seo á dhéanamh agat!
