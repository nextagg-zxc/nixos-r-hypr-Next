// Read-only cover catalogue: liked songs, saved playlists (including folders), and updates.
(function preloadSpotifyCovers() {
  if (!(window.Spicetify && Spicetify.Platform?.LibraryAPI && Spicetify.Platform?.RootlistAPI && Spicetify.Platform?.PlaylistAPI)) {
    setTimeout(preloadSpotifyCovers, 1000);
    return;
  }
  if (window.__nextaggCoverPreload) return;
  const status = window.__nextaggCoverPreload = {state:"waiting", scanned_tracks:0, scanned_playlists:0, errors:[]};
  const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
  let socket, scanning = false;
  const send = (items = [], scope = "") => {
    if (socket?.readyState === 1) socket.send(JSON.stringify({type:"cover-library", items, scope, ...status}));
  };
  const artwork = t => {
    const images = t.album?.images || t.images || [];
    const image = images.find(x => x.label === "standard") || images[0];
    let url = String(image?.url || ""), localfile = "";
    if (url.startsWith("spotify:localfileimage:")) {
      try { localfile = decodeURIComponent(url.slice(23)); } catch (_) {}
      url = "";
    } else if (url.startsWith("spotify:image:")) url = "https://i.scdn.co/image/" + url.slice(14);
    return {uri:String(t.uri || ""), image:url, title:String(t.name || ""), localfile};
  };
  const scan = async () => {
    if (scanning || socket?.readyState !== 1) return;
    scanning = true;
    Object.assign(status,{state:"scanning",scanned_tracks:0,scanned_playlists:0,errors:[]});
    const seenTracks = new Set(), seenFolders = new Set(), seenPlaylists = new Set();
    const publish = (rows, scope) => {
      const items = [];
      for (const row of rows) {
        const item = artwork(row.track || row);
        if (!item.uri.startsWith("spotify:") || seenTracks.has(item.uri)) continue;
        seenTracks.add(item.uri);
        status.scanned_tracks++;
        items.push(item);
      }
      send(items, scope);
    };
    const pages = async (load, consume) => {
      let previous = "";
      for (let offset=0; offset<100000; offset+=100) {
        if (socket?.readyState !== 1) throw new Error("connection closed; retry on reconnect");
        const response = await load(offset);
        const rows = response.items || response.rows || [];
        const fingerprint = JSON.stringify(rows.map(x => (x.track || x).uri));
        if (rows.length && fingerprint === previous) throw new Error("pagination did not advance");
        previous = fingerprint;
        await consume(rows);
        if (rows.length < 100) return;
        await delay(100);
      }
      throw new Error("catalogue exceeds 100000 items");
    };
    const playlist = async uri => {
      if (seenPlaylists.has(uri)) return;
      seenPlaylists.add(uri);
      await pages(offset => Spicetify.Platform.PlaylistAPI.getContents(uri,{offset,limit:100}), rows => publish(rows,uri));
      status.scanned_playlists++;
    };
    const folder = async uri => {
      if (seenFolders.has(uri || "root")) return;
      seenFolders.add(uri || "root");
      await pages(offset => Spicetify.Platform.RootlistAPI.getContents({offset,limit:100,...(uri ? {folderUri:uri} : {})}), async rows => {
        for (const row of rows) {
          try {
            if (row.type === "folder") await folder(row.uri);
            else if (row.type === "playlist") await playlist(row.uri);
          } catch (error) { status.errors.push(String(error).slice(0,180)); }
        }
      });
    };
    try {
      send([],"liked");
      try { await pages(offset => Spicetify.Platform.LibraryAPI.getTracks({offset,limit:100}), rows => publish(rows,"liked")); }
      catch (error) { status.errors.push("Liked songs: " + String(error).slice(0,180)); }
      try { await folder(); }
      catch (error) { status.errors.push("Playlists: " + String(error).slice(0,180)); }
      status.state = status.errors.length ? "incomplete" : "complete";
      send([],"finished");
    } finally { scanning = false; }
  };
  const connect = () => {
    socket = new WebSocket("ws://127.0.0.1:47823");
    socket.onopen = () => scan();
    socket.onclose = () => setTimeout(connect,3000);
    socket.onerror = () => {};
  };
  setInterval(scan,30 * 60 * 1000);
  connect();
})();
