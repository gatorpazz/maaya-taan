// Serves site/ as static assets, adding HTTP byte-range support for audio.
// Cloudflare's static asset handler answers Range requests with the whole
// file, which breaks <audio> seeking and is refused outright by iOS Safari.
// Audio is cached at the edge on first request; the Cache API honours Range
// on cached objects, and misses are sliced by hand.
const AUDIO = /\.mp3$/;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (!AUDIO.test(url.pathname) || (request.method !== "GET" && request.method !== "HEAD")) {
      return env.ASSETS.fetch(request);
    }
    const cache = caches.default;
    const hit = await cache.match(request);
    if (hit) return withHeaders(hit);

    const full = await env.ASSETS.fetch(new Request(url.toString(), { method: "GET" }));
    if (!full.ok) return full;
    const buf = await full.arrayBuffer();
    const stored = new Response(buf, {
      headers: {
        "Content-Type": "audio/mpeg",
        "Content-Length": String(buf.byteLength),
        "Accept-Ranges": "bytes",
        "Cache-Control": "public, max-age=604800",
      },
    });
    ctx.waitUntil(cache.put(new Request(url.toString(), { method: "GET" }), stored.clone()));
    const range = request.headers.get("Range");
    if (request.method === "HEAD") return new Response(null, { status: 200, headers: stored.headers });
    if (!range) return stored;
    return slice(buf, range);
  },
};

function withHeaders(res) {
  const h = new Headers(res.headers);
  h.set("Accept-Ranges", "bytes");
  return new Response(res.body, { status: res.status, headers: h });
}

function slice(buf, range) {
  const size = buf.byteLength;
  const m = /^bytes=(\d*)-(\d*)$/.exec(range);
  if (!m) return new Response(null, { status: 416, headers: { "Content-Range": `bytes */${size}` } });
  let start = m[1] ? parseInt(m[1], 10) : Math.max(0, size - parseInt(m[2], 10));
  let end = m[1] && m[2] ? Math.min(parseInt(m[2], 10), size - 1) : size - 1;
  if (start > end || start >= size) return new Response(null, { status: 416, headers: { "Content-Range": `bytes */${size}` } });
  return new Response(buf.slice(start, end + 1), {
    status: 206,
    headers: {
      "Content-Type": "audio/mpeg",
      "Content-Range": `bytes ${start}-${end}/${size}`,
      "Content-Length": String(end - start + 1),
      "Accept-Ranges": "bytes",
      "Cache-Control": "public, max-age=604800",
    },
  });
}
