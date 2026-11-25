// nextagg-queue — Spotify для меню Win+B (24.11).
// По WebSocket на 127.0.0.1:47823 (служба nextagg-spotify-queue пишет это в файл для меню):
//   текущий трек, следующие/предыдущие, «в любимых» (liked).
// Локальные файлы (spotify:local:…) тоже идут в меню: обложку из самого файла достаёт мост,
// расширение передаёт только путь к файлу, если Spotify его знает (localfile).
// Команды от меню: play (трек из очереди), heart (лайк).
(function nextaggQueue() {
  if (!(window.Spicetify && Spicetify.Player && Spicetify.Platform && Spicetify.Platform.PlayerAPI)) {
    setTimeout(nextaggQueue, 500);
    return;
  }

  const URL = "ws://127.0.0.1:47823";
  let ws = null;

  const image = (u) => {
    u = String(u || "");
    if (u.startsWith("spotify:image:")) return "https://i.scdn.co/image/" + u.slice(14);
    return u.startsWith("https://") ? u : "";
  };

  // путь локального файла: spotify:localfileimage:<путь в URL-кодировке> или file://…
  const localPath = (m) => {
    for (const k of Object.keys(m)) {
      const v = String(m[k] || "");
      try {
        if (v.startsWith("spotify:localfileimage:")) return decodeURIComponent(v.slice(23));
        if (v.startsWith("file://")) return decodeURIComponent(v.slice(7));
      } catch (e) { /* битая кодировка */ }
    }
    return "";
  };

  const meta = (t) => {
    if (!t) return null;
    const ct = t.contextTrack || t;
    const m = ct.metadata || t.metadata || {};
    const uri = String(ct.uri || t.uri || "");
    const local = uri.startsWith("spotify:local:");
    if (!uri.startsWith("spotify:track:") && !uri.startsWith("spotify:episode:") && !local) return null;
    return {
      uri,
      uid: String(ct.uid || t.uid || ""),
      title: String(m.title || ""),
      artist: String(m.artist_name || ""),
      image: local ? "" : image(m.image_url || m.image_small_url),
      localfile: local ? localPath(m) : "",
    };
  };

  const liked = () => {
    try { return !!Spicetify.Player.getHeart(); } catch (e) { return false; }
  };

  const snapshot = () => {
    const q = Spicetify.Queue || {};
    const list = (a) => (Array.isArray(a) ? a : []).map(meta).filter(Boolean);
    return {
      type: "queue",
      current: meta(q.track),
      next: list(q.nextTracks).slice(0, 100),
      prev: list(q.prevTracks).slice(-50),
      liked: liked(),
    };
  };

  const send = () => {
    if (ws && ws.readyState === 1) {
      try { ws.send(JSON.stringify(snapshot())); } catch (e) { /* соединение закрылось */ }
    }
  };

  const play = async (m) => {
    const uri = String(m.uri || "");
    if (!uri.startsWith("spotify:")) return;
    try {
      await Spicetify.Platform.PlayerAPI.skipTo({ uid: String(m.uid || ""), uri });
    } catch (e) {
      try { await Spicetify.Player.playUri(uri); } catch (e2) { console.warn("nextagg-queue: play failed", e2); }
    }
    setTimeout(send, 500);
  };

  const heart = () => {
    try { Spicetify.Player.toggleHeart(); } catch (e) { console.warn("nextagg-queue: heart failed", e); }
    setTimeout(send, 400);
  };

  const connect = () => {
    try { ws = new WebSocket(URL); } catch (e) { setTimeout(connect, 5000); return; }
    ws.onopen = () => { send(); };
    ws.onclose = () => { ws = null; setTimeout(connect, 3000); };
    ws.onerror = () => {};
    ws.onmessage = (ev) => {
      let m;
      try { m = JSON.parse(ev.data); } catch (e) { return; }
      if (!m) return;
      if (m.cmd === "play") play(m);
      else if (m.cmd === "heart") heart();
      else if (m.cmd === "refresh") send();
    };
  };

  Spicetify.Player.addEventListener("songchange", () => setTimeout(send, 300));
  try {
    const ev = Spicetify.Platform.PlayerAPI._events;
    if (ev && typeof ev.addListener === "function") ev.addListener("queue_update", () => setTimeout(send, 100));
  } catch (e) { /* старые версии Spotify */ }
  setInterval(send, 5000);
  connect();
})();
