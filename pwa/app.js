/* Maaya T'aan player. Hash routes: #/  #/lesson/L1-01/listen|phrases|dialogue|guide */
const $ = (s, el = document) => el.querySelector(s);
const view = $("#view"), crumbs = $("#crumbs"), player = $("#player"), audio = $("#audio");
const state = { manifest: null, site: null, lesson: null, timeline: null, ref: null, guide: null, current: -1, stopAt: null,
  prefs: load("prefs", { showMaya: true, follow: true, rate: 1 }),
  progress: load("progress", { completed: [], items: {} }) };

// ---------------------------------------------------------------- progress (on this device)
// Same ladder as the course planner: after a phrase is met, it's due again after 1, 1, 3, 5, 10 lessons, then 25.
const GAPS = [1, 1, 3, 5, 10], STEADY = 25;
const nextDue = (st) => st.last + (st.rung < GAPS.length ? GAPS[st.rung] : STEADY);
function nextLesson() { const c = state.progress.completed; return c.length ? Math.max(...c) + 1 : 1; }
function dueItems() {
  const n = nextLesson();
  return Object.entries(state.progress.items).filter(([, st]) => nextDue(st) <= n).map(([id]) => id);
}
function completeLesson(number, failed) {
  const p = state.progress;
  const lesson = state.manifest.lessons.find((l) => l.number === number);
  for (const it of lesson.items) p.items[it.id] ??= { introduced: number, last: number, rung: 0, yua: it.yua, en: it.en };
  for (const id of failed) if (p.items[id]) { p.items[id].last = number; p.items[id].rung = 0; }
  if (!p.completed.includes(number)) p.completed.push(number);
  save("progress", p);
}
function reviewOutcome(id, ok) {
  const st = state.progress.items[id]; if (!st) return;
  st.last = nextLesson() - 1; st.rung = ok ? st.rung + 1 : 0; save("progress", state.progress);
}

function load(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } }
function save(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} }
const fmt = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
function toast(msg) { const t = $("#toast"); t.textContent = msg; t.hidden = false; clearTimeout(t._h); t._h = setTimeout(() => (t.hidden = true), 2600); }

async function getJSON(url) { const r = await fetch(url, { cache: "no-store" }); if (!r.ok) throw new Error(`${url}: ${r.status}`); return r.json(); }

// ---------------------------------------------------------------- routing
window.addEventListener("hashchange", route);
async function route() {
  const [, kind, id, tab = "listen"] = location.hash.replace(/^#\/?/, "/").split("/");
  try {
    if (!state.manifest) [state.manifest, state.site] = await Promise.all([getJSON("manifest.json"), getJSON("site.json")]);
    if (kind === "lesson" && id) await showLesson(id, tab);
    else if (kind === "about") showAbout();
    else if (kind === "contribute") showContribute();
    else if (kind === "review") showReview();
    else showHome();
  } catch (e) {
    view.innerHTML = `<h1>Something didn't load</h1><p>${esc(e.message)}</p><p class="muted">Check your connection and try again.</p>`;
  }
}

// ---------------------------------------------------------------- home
function showHome() {
  crumbs.textContent = "";
  player.hidden = !state.lesson;
  const m = state.manifest, site = state.site;
  const next = nextLesson();
  const due = dueItems();
  const done = state.progress.completed.length;
  view.innerHTML = `
    <div class="hero">
      <h1>${esc(site.name)}</h1>
      <p>${esc(site.tagline)}</p>
      <p class="install">Thirty minutes a day. Listen, then say the phrases out loud in the gaps. No reading needed, but the transcript is there when a sound is hard to catch.</p>
      ${installHint()}
    </div>
    ${due.length ? `<div class="review"><h2>${due.length} phrase${due.length > 1 ? "s" : ""} to review</h2><p class="small muted">A quick drill before your next lesson: hear the meaning, say the Maya, then check.</p><a class="btn" href="#/review">Start review</a></div>` : ""}
    <h2 style="margin-top:0.4rem">Lessons</h2>
    <p class="muted small">${done ? `${done} of ${m.lessons.length} done.` : "Start with lesson 1."} ${m.lessons.length < 30 ? "More lessons are added as they're written." : ""}</p>
    <ul class="lessons">${m.lessons.map((l) => `
      <li><a class="lesson ${state.progress.completed.includes(l.number) ? "done" : ""} ${l.number === next ? "next" : ""}" href="#/lesson/${l.id}">
        <span class="n">${l.number}</span>
        <span><div class="t">${esc(l.title)}</div><div class="meta">${fmt(l.duration)} · ${l.new_items} new phrases</div></span>
        <span class="state">${state.progress.completed.includes(l.number) ? "Done" : l.number === next ? "Next" : ""}</span>
      </a></li>`).join("")}
    </ul>
    <p class="muted small" style="margin-top:1.2rem">The Maya voice is synthetic for now. <a href="#/contribute">Native speakers can help replace it.</a></p>`;
}

// ---------------------------------------------------------------- install
let installPrompt = null;
window.addEventListener("beforeinstallprompt", (e) => { e.preventDefault(); installPrompt = e; const b = $("#btn-install"); if (b) b.hidden = false; });
const isStandalone = () => window.matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;
const isIOS = () => /iPhone|iPad|iPod/.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
function installHint() {
  if (isStandalone()) return "";
  if (isIOS()) return `<p class="install-hint">To install: tap <span class="share" aria-label="Share"></span> Share, then <strong>Add to Home Screen</strong>. It opens full screen like an app.</p>`;
  return `<p class="install-hint"><button class="btn quiet" id="btn-install" ${installPrompt ? "" : "hidden"}>Install app</button><span class="muted small"> or use it in the browser; on Android, Chrome's menu also has Add to Home screen.</span></p>`;
}
document.addEventListener("click", async (e) => {
  if (e.target.id === "btn-install" && installPrompt) { installPrompt.prompt(); await installPrompt.userChoice; installPrompt = null; e.target.hidden = true; }
});

function showAbout() {
  crumbs.innerHTML = `<a href="#/">Lessons</a> / About`;
  const site = state.site;
  view.innerHTML = `<div class="about">
    <h1>About ${esc(site.name)}</h1>
    <p>Maaya T'aan is Yucatec Maya, spoken by close to a million people across the Yucatán Peninsula. This is a free audio course for learning to speak it, built the way the Pimsleur courses work: you hear a short conversation, learn each phrase from the end forward, sound by sound, and then get asked for it again at growing intervals, in the lesson and across later lessons, always with a gap to answer out loud before you hear it.</p>
    <p>Every Maya phrase in the course is taken from human-written sources, never invented. The teaching voice in English is synthetic, and so is the Maya voice, which is the weakest part: it's the only text-to-speech model that exists for the language. <a href="#/contribute">Recordings from native speakers</a> would make the course much better.</p>
    <h2>How to use it</h2>
    <ul>
      <li>One lesson a day, about thirty minutes, ideally while walking or doing something with your hands.</li>
      <li>Say every answer out loud in a full voice. The gap is the lesson.</li>
      <li>Add this page to your phone's home screen to use it like an app. Lessons you've opened keep working offline.</li>
      <li>Your progress stays on this device. Nothing is sent anywhere.</li>
    </ul>
    <h2>Sources</h2>
    <ul>
      <li>Phrases: the YUA-ES Communicative Contexts Corpus by Molina-Villegas and colleagues, CC BY 4.0, 14,332 everyday Yucatec Maya sentences with Spanish translations.</li>
      <li>Words: Yucatec Maya entries from Wiktionary via Kaikki, CC BY-SA 3.0.</li>
      <li>Spelling: the 2014 INALI writing norms for Maya, <em>U nu'ukbesajil u ts'íibta'al maayat'aan</em>.</li>
      <li>Maya voice: Meta's Massively Multilingual Speech text-to-speech model for Yucatec Maya, CC BY-NC 4.0. This course is free and non-commercial.</li>
      <li>English voice: Kokoro, Apache 2.0.</li>
      <li>Method: Paul Pimsleur's graduated interval recall, described in his 1967 paper <em>A Memory Schedule</em>.</li>
    </ul>
    ${site.repo_url ? `<p>The course generator is open source: <a href="${esc(site.repo_url)}">${esc(site.repo_url.replace(/^https?:\/\//, ""))}</a>.</p>` : ""}
    ${site.contact_url ? `<p>Questions or corrections: <a href="${esc(site.contact_url)}">${esc(site.contact_label || site.contact_url)}</a>.</p>` : ""}
  </div>`;
}

function showContribute() {
  crumbs.innerHTML = `<a href="#/">Lessons</a> / Record`;
  const site = state.site;
  const phrases = state.manifest.lessons.flatMap((l) => l.items.map((it) => ({ ...it, lesson: l.id })));
  view.innerHTML = `<div class="about">
    <h1>Lend your voice</h1>
    <p>If Maaya T'aan is your language, you can make this course sound like a person instead of a program. The synthetic voice gets the words right most of the time, but it flattens the tones and swallows short words, and learners deserve better.</p>
    <div class="callout"><p>What helps most: a native speaker recording the course phrases on a phone, in a quiet room, saying each one naturally, twice. Fifteen minutes covers a whole lesson.</p></div>
    <h2>How to record</h2>
    <ul>
      <li>Use your phone's voice recorder. Hold it about a hand's width from your mouth.</li>
      <li>Say the phrase's number, then the phrase at a normal speed, then once more slowly.</li>
      <li>One recording per lesson is fine. Don't worry about mistakes; just repeat the phrase.</li>
      <li>Your own way of saying things is what we want. If a phrase sounds wrong to you, say how you'd say it.</li>
    </ul>
    ${site.recordings_url || site.contact_url ? `<p>Send recordings here: <a href="${esc(site.recordings_url || site.contact_url)}">${esc(site.contact_label || site.recordings_url || site.contact_url)}</a>. Say if you'd like to be credited, and where you're from, since Maya varies from town to town.</p>` : `<p class="muted">A place to send recordings is coming soon.</p>`}
    <h2>The phrases</h2>
    <p class="muted small">Tap to hear how the program says it now.</p>
    <ol class="phraselist">${phrases.map((p, i) => `<li><span class="muted small">${i + 1}</span><span class="y">${esc(p.yua)}</span><span class="e">${esc(p.en)}</span><button class="playbtn secondary" data-lesson="${p.lesson}" data-play="${esc(p.yua)}">Play</button></li>`).join("")}</ol>
  </div>`;
  view.addEventListener("click", async (e) => {
    const b = e.target.closest("[data-play]"); if (!b) return;
    const ref = await getJSON(`lessons/${b.dataset.lesson}.lesson.json`);
    const saved = state.ref; state.ref = ref; playPhrase(b.dataset.play); state.ref = saved;
  });
}

// ---------------------------------------------------------------- review drill
function showReview() {
  crumbs.innerHTML = `<a href="#/">Lessons</a> / Review`;
  const queue = dueItems().map((id) => ({ id, ...state.progress.items[id] }));
  let i = 0;
  const step = () => {
    if (i >= queue.length) { view.innerHTML = `<h1>Review done</h1><p>${queue.length} phrase${queue.length !== 1 ? "s" : ""} checked. <a href="#/">Back to lessons</a>.</p>`; return; }
    const q = queue[i];
    view.innerHTML = `<div class="drill">
      <div class="count">${i + 1} of ${queue.length}</div>
      <h1>Say it in Maya</h1>
      <p class="prompt">${esc(q.en)}</p>
      <div class="answer veiled" id="ans">${esc(q.yua)}</div>
      <div class="row"><button class="btn" id="reveal">Check</button></div>
      <div class="row" id="judge" hidden><button class="btn" id="ok">Got it</button><button class="btn miss" id="miss">Missed it</button></div>
    </div>`;
    $("#reveal").addEventListener("click", async () => {
      $("#ans").classList.remove("veiled"); $("#reveal").hidden = true; $("#judge").hidden = false;
      const lesson = state.manifest.lessons.find((l) => l.items.some((it) => it.id === q.id));
      if (lesson) { const ref = await getJSON(`lessons/${lesson.id}.lesson.json`); const saved = state.ref; state.ref = ref; playPhrase(q.yua); state.ref = saved; }
    });
    $("#ok").addEventListener("click", () => { reviewOutcome(q.id, true); i++; step(); });
    $("#miss").addEventListener("click", () => { reviewOutcome(q.id, false); i++; step(); });
  };
  step();
}

// ---------------------------------------------------------------- lesson
async function showLesson(id, tab) {
  if (!state.lesson || state.lesson !== id) {
    const [timeline, ref] = await Promise.all([getJSON(`lessons/${id}.json`), getJSON(`lessons/${id}.lesson.json`)]);
    state.lesson = id; state.timeline = timeline; state.ref = ref; state.current = -1;
    audio.src = `lessons/${timeline.audio}`; audio.playbackRate = state.prefs.rate;
    $("#t-dur").textContent = fmt(timeline.duration);
    $("#now-maya").textContent = ref.title; $("#now-maya").className = "now-maya"; $("#now-en").textContent = "Lesson " + ref.number;
  }
  if (!state.guide) state.guide = await getJSON("guide.json");
  player.hidden = false;
  crumbs.innerHTML = `<a href="#/">Lessons</a> / Lesson ${state.ref.number}`;
  const tabs = [["listen", "Listen"], ["phrases", "Phrases"], ["dialogue", "Dialogue"], ["guide", "Guide"]];
  view.innerHTML = `
    <h1>${esc(state.ref.title)}</h1>
    <div class="tabs" role="tablist">${tabs.map(([k, l]) => `<button class="tab" role="tab" aria-selected="${k === tab}" data-tab="${k}">${l}</button>`).join("")}</div>
    <section id="panel"></section>`;
  view.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => (location.hash = `#/lesson/${id}/${b.dataset.tab}`)));
  ({ listen: renderListen, phrases: renderPhrases, dialogue: renderDialogue, guide: renderGuide })[tab]?.($("#panel"));
}

function segLabel(seg) {
  if (seg.kind === "pause") return seg.turn === "response" ? "Your turn" : seg.turn === "repeat" ? "Repeat it" : "";
  return seg.text;
}

function renderListen(panel) {
  const tl = state.timeline.segments;
  panel.innerHTML = `
    <div class="opts">
      <label><input type="checkbox" id="opt-maya" ${state.prefs.showMaya ? "checked" : ""}> Show Maya spelling</label>
      <label><input type="checkbox" id="opt-follow" ${state.prefs.follow ? "checked" : ""}> Follow along</label>
    </div>
    <ol class="tx" id="tx">${tl.map((seg, i) => {
      if (seg.kind === "pause") return segLabel(seg) ? `<li class="seg pause ${seg.turn}" data-i="${i}">${segLabel(seg)} <span class="muted">${Math.round(seg.end - seg.start)} s</span></li>` : "";
      if (seg.kind === "narrator") return `<li class="seg narrator" data-i="${i}">${esc(seg.text)}</li>`;
      return `<li class="seg maya ${seg.slice_of ? "frag" : ""}" data-i="${i}"><span class="y ${state.prefs.showMaya ? "" : "hidden-maya"}">${esc(seg.text)}</span>${seg.en ? `<span class="e">${esc(seg.en)}</span>` : ""}</li>`;
    }).join("")}</ol>
    <div class="finish" id="finish">
      <h2 style="margin-top:0">Finish this lesson</h2>
      <p class="small muted">Tick any phrase you blanked on. It will come back sooner.</p>
      <div class="items">${[...state.ref.items, ...state.ref.review_items].map((it) => `
        <label><input type="checkbox" name="failed" value="${esc(it.id)}"><span><div class="fy">${esc(it.yua)}</div><div class="fe">${esc(it.en)}</div></span></label>`).join("")}</div>
      <button class="btn" id="btn-finish">Mark lesson ${state.ref.number} done</button>
    </div>`;
  $("#opt-maya").addEventListener("change", (e) => { state.prefs.showMaya = e.target.checked; save("prefs", state.prefs); panel.querySelectorAll(".seg.maya .y").forEach((y) => y.classList.toggle("hidden-maya", !e.target.checked)); });
  $("#opt-follow").addEventListener("change", (e) => { state.prefs.follow = e.target.checked; save("prefs", state.prefs); });
  $("#tx").addEventListener("click", (e) => { const li = e.target.closest(".seg"); if (li) { seekTo(tl[+li.dataset.i].start); audio.play(); } });
  $("#btn-finish").addEventListener("click", finishLesson);
  highlight(true);
}

function renderPhrases(panel) {
  const block = (it) => `
    <div class="phrase">
      <div class="y">${esc(it.yua)}</div>
      <div class="e">${esc(it.en)}</div>
      ${it.literal ? `<div class="lit">Word for word: ${esc(it.literal)}</div>` : ""}
      ${it.note ? `<div class="note">${esc(it.note)}</div>` : ""}
      ${it.syllables?.length > 1 ? `<div class="chunks">${it.syllables.map((c) => `<button class="chunk" data-play="${esc(c)}" data-full="${esc(it.yua)}">${esc(c)}${it.glosses?.[c] ? `<span class="g">${esc(it.glosses[c])}</span>` : ""}</button>`).join("")}</div>` : ""}
      <button class="playbtn" data-play="${esc(it.yua)}">Play</button>
      ${it.transforms?.length ? it.transforms.map((t) => `<button class="playbtn secondary" data-play="${esc(t.yua)}">${esc(t.yua)}</button>`).join(" ") : ""}
    </div>`;
  panel.innerHTML = `
    <p class="muted small">Tap a phrase or a piece of it to hear it from the lesson.</p>
    ${state.ref.items.map(block).join("")}
    ${state.ref.review_items.length ? `<h2>From earlier lessons</h2>${state.ref.review_items.map(block).join("")}` : ""}`;
  panel.addEventListener("click", (e) => { const b = e.target.closest("[data-play]"); if (b) playPhrase(b.dataset.play, b.dataset.full); });
}

function renderDialogue(panel) {
  const dlg = (d, title) => `<h2>${title}</h2><p class="muted small">${esc(d.setting_en)}</p>
    <ul class="dlg">${d.lines.map((l) => `<li data-play="${esc(l.yua)}"><span class="who">${l.speaker}</span><span><div class="y">${esc(l.yua)}</div><div class="e">${esc(l.en)}</div></span></li>`).join("")}</ul>`;
  panel.innerHTML = dlg(state.ref.opening, "Opening") + (state.ref.closing.id !== state.ref.opening.id ? dlg(state.ref.closing, "Closing") : "") +
    (state.ref.grammar_note ? `<h2>Pattern in this lesson</h2><p>${esc(state.ref.grammar_note)}</p>` : "");
  panel.addEventListener("click", (e) => { const b = e.target.closest("[data-play]"); if (b) playPhrase(b.dataset.play); });
}

function renderGuide(panel) {
  const g = state.guide;
  panel.innerHTML = `<div class="guide">
    <h2>How to use a lesson</h2>${g.howto.map((p) => `<p>${esc(p)}</p>`).join("")}
    <h2>The sounds</h2><table>${g.sounds.map((r) => `<tr><td>${esc(r.s)}</td><td>${esc(r.d)}<div class="ex muted">${esc(r.ex)}</div></td></tr>`).join("")}</table>
    <h2>Patterns so far</h2><table>${g.patterns.map((r) => `<tr><td>${esc(r.t)}</td><td>${esc(r.d)}</td></tr>`).join("")}</table>
    <p class="muted small">${esc(g.spelling)}</p></div>`;
}

// ---------------------------------------------------------------- playback
function seekTo(t) { audio.currentTime = Math.max(0, t); state.stopAt = null; }
const clipAudio = new Audio();
function findClip(text, full) {
  // keys are "text|rate|slice_of"; a fragment of a phrase prefers its slice, a phrase prefers full speed
  const entries = Object.entries(state.ref.clips || {}).map(([k, url]) => { const [t, rate, slice] = k.split("|"); return { t, rate: +rate, slice, url }; })
    .filter((c) => c.t.toLowerCase() === text.toLowerCase());
  if (!entries.length) return null;
  const score = (c) => (full ? (c.slice.toLowerCase() === full.toLowerCase() ? 0 : 2) : (c.slice ? 2 : 0)) + (c.rate === 1 ? 0 : 1) + (full && c.rate < 1 ? -0.5 : 0);
  return entries.sort((a, b) => score(a) - score(b))[0];
}
function playPhrase(text, full) {
  const clip = findClip(text, full);
  if (clip) { audio.pause(); clipAudio.src = `lessons/${clip.url}`; clipAudio.play(); return; }
  // fallback: seek inside the lesson
  const tl = state.timeline.segments;
  const want = text.toLowerCase();
  const seg = tl.find((s) => s.kind === "maya" && s.text.toLowerCase() === want && s.rate === 1) || tl.find((s) => s.kind === "maya" && s.text.toLowerCase() === want);
  if (!seg) { toast("Not in this lesson's audio"); return; }
  audio.currentTime = seg.start; state.stopAt = seg.end; audio.play();
}
$("#play").addEventListener("click", () => { clipAudio.pause(); audio.paused ? audio.play() : audio.pause(); });
$("#back").addEventListener("click", () => seekTo(audio.currentTime - 5));
$("#fwd").addEventListener("click", () => seekTo(audio.currentTime + 5));
$("#rate").addEventListener("click", () => { const r = [1, 0.85, 0.7, 1.15][([1, 0.85, 0.7, 1.15].indexOf(state.prefs.rate) + 1) % 4]; state.prefs.rate = r; save("prefs", state.prefs); audio.playbackRate = r; $("#rate").textContent = `${r}×`; });
$("#rate").textContent = `${state.prefs.rate}×`;
audio.addEventListener("play", () => ($("#play").textContent = "Pause"));
audio.addEventListener("pause", () => ($("#play").textContent = "Play"));
$("#seek").addEventListener("input", (e) => { if (state.timeline) seekTo((e.target.value / 1000) * state.timeline.duration); });
audio.addEventListener("ended", () => { state.stopAt = null; });

function tick() {
  requestAnimationFrame(tick);
  if (!state.timeline || audio.paused) return;
  const t = audio.currentTime;
  if (state.stopAt != null && t >= state.stopAt - 0.08) { audio.pause(); state.stopAt = null; return; }
  $("#seek").value = Math.round((t / state.timeline.duration) * 1000);
  $("#t-cur").textContent = fmt(t);
  const tl = state.timeline.segments;
  let i = state.current;
  if (i < 0 || t < tl[i].start || t >= tl[i].end) {
    i = tl.findIndex((s) => t >= s.start && t < s.end);
    if (i !== state.current) { state.current = i; highlight(); }
  }
  const seg = tl[i];
  if (seg && seg.kind === "pause" && seg.turn) $("#turn-fill").style.width = `${Math.min(100, ((t - seg.start) / (seg.end - seg.start)) * 100)}%`;
}
requestAnimationFrame(tick);

function highlight(initial = false) {
  const tl = state.timeline?.segments; if (!tl) return;
  const seg = tl[state.current];
  const nowM = $("#now-maya"), nowE = $("#now-en"), turn = $("#turn");
  if (seg) {
    if (seg.kind === "maya") { nowM.textContent = state.prefs.showMaya ? seg.text : "· · ·"; nowM.className = "now-maya"; nowE.textContent = seg.en || ""; turn.hidden = true; }
    else if (seg.kind === "narrator") { nowM.textContent = seg.text; nowM.className = "now-maya narr"; nowE.textContent = ""; turn.hidden = true; }
    else if (seg.turn) { turn.hidden = false; $(".turn-label").textContent = segLabel(seg); $("#turn-fill").style.width = "0"; }
  }
  const tx = $("#tx"); if (!tx) return;
  tx.querySelectorAll(".seg.current").forEach((el) => el.classList.remove("current"));
  const li = tx.querySelector(`.seg[data-i="${state.current}"]`);
  if (li) { li.classList.add("current"); if (state.prefs.follow && !initial) li.scrollIntoView({ block: "center", behavior: "smooth" }); }
}

// ---------------------------------------------------------------- finish
function finishLesson() {
  const failed = [...document.querySelectorAll('input[name="failed"]:checked')].map((i) => i.value);
  completeLesson(state.ref.number, failed);
  const btn = $("#btn-finish"); btn.textContent = "Done"; btn.classList.add("done"); btn.disabled = true;
  toast(`Lesson ${state.ref.number} finished${failed.length ? `, ${failed.length} to review sooner` : ""}`);
  setTimeout(() => (location.hash = "#/"), 900);
}

// ---------------------------------------------------------------- boot
if ("serviceWorker" in navigator && location.protocol === "https:") navigator.serviceWorker.register("sw.js").catch(() => {});
route();
