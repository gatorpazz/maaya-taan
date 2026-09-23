/* Maaya T'aan player. Hash routes: #/  #/lesson/L1-01/listen|phrases|dialogue|guide  #/review  #/about  #/contribute
   Two teaching languages (en, es); the Maya is shared. Progress stays on this device. */
const $ = (s, el = document) => el.querySelector(s);
const view = $("#view"), crumbs = $("#crumbs"), player = $("#player"), audio = $("#audio");

function load(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } }
function save(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} }
const fmt = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
function toast(msg) { const t = $("#toast"); t.textContent = msg; t.hidden = false; clearTimeout(t._h); t._h = setTimeout(() => (t.hidden = true), 2600); }
async function getJSON(url) { const r = await fetch(url, { cache: "no-store" }); if (!r.ok) throw new Error(`${url}: ${r.status}`); return r.json(); }

// ---------------------------------------------------------------- languages
const T = {
  en: {
    nav_about: "About", nav_record: "Record", your_turn: "Your turn", repeat_it: "Repeat it", play: "Play", pause: "Pause",
    lessons: "Lessons", lesson: "Lesson", next: "Next", done: "Done", new_phrases: "new phrases", start_with: "Start with lesson 1.",
    done_of: (a, b) => `${a} of ${b} done.`, more_soon: "More lessons are added as they're written.",
    hero_how: "Thirty minutes a day. Listen, then say the phrases out loud in the gaps. No reading needed, but the transcript is there when a sound is hard to catch.",
    synthetic: "The Maya voice is synthetic for now.", help_replace: "Native speakers can help replace it.",
    review_n: (n) => `${n} phrase${n > 1 ? "s" : ""} to review`, review_blurb: "A quick drill before your next lesson: hear the meaning, say the Maya, then check.",
    start_review: "Start review", say_in_maya: "Say it in Maya", check: "Check", got_it: "Got it", missed: "Missed it",
    review_done: "Review done", checked: (n) => `${n} phrase${n !== 1 ? "s" : ""} checked.`, back_to_lessons: "Back to lessons",
    tab_listen: "Listen", tab_phrases: "Phrases", tab_dialogue: "Dialogue", tab_guide: "Guide",
    show_maya: "Show Maya spelling", follow: "Follow along", finish_title: "Finish this lesson",
    finish_blurb: "Tick any phrase you blanked on. It will come back sooner.", mark_done: (n) => `Mark lesson ${n} done`,
    finished: (n, f) => `Lesson ${n} finished${f ? `, ${f} to review sooner` : ""}`,
    tap_phrase: "Tap a phrase or a piece of it to hear it from the lesson.", word_for_word: "Word for word", earlier: "From earlier lessons",
    opening: "Opening", closing: "Closing", pattern: "Pattern in this lesson",
    g_howto: "How to use a lesson", g_sounds: "The sounds", g_patterns: "Patterns so far",
    not_in_audio: "Not in this lesson's audio", load_fail: "Something didn't load", check_connection: "Check your connection and try again.",
    install_ios: "To install: tap <span class=\"share\" aria-label=\"Share\"></span> Share, then <strong>Add to Home Screen</strong>. It opens full screen like an app.",
    install_btn: "Install app", install_other: " or use it in the browser; on Android, Chrome's menu also has Add to Home screen.",
    review_crumb: "Review", about_crumb: "About", record_crumb: "Record",
  },
  es: {
    nav_about: "Acerca de", nav_record: "Grabar", your_turn: "Tu turno", repeat_it: "Repítelo", play: "Reproducir", pause: "Pausa",
    lessons: "Lecciones", lesson: "Lección", next: "Siguiente", done: "Hecha", new_phrases: "frases nuevas", start_with: "Empieza con la lección 1.",
    done_of: (a, b) => `${a} de ${b} hechas.`, more_soon: "Se van agregando lecciones conforme se escriben.",
    hero_how: "Treinta minutos al día. Escucha y di las frases en voz alta en las pausas. No hace falta leer, pero la transcripción está ahí cuando un sonido cuesta captar.",
    synthetic: "Por ahora la voz maya es sintética.", help_replace: "Los hablantes nativos pueden ayudar a reemplazarla.",
    review_n: (n) => `${n} frase${n > 1 ? "s" : ""} por repasar`, review_blurb: "Un repaso rápido antes de tu próxima lección: oye el significado, dilo en maya y comprueba.",
    start_review: "Empezar el repaso", say_in_maya: "Dilo en maya", check: "Comprobar", got_it: "La supe", missed: "Se me olvidó",
    review_done: "Repaso terminado", checked: (n) => `${n} frase${n !== 1 ? "s" : ""} repasada${n !== 1 ? "s" : ""}.`, back_to_lessons: "Volver a las lecciones",
    tab_listen: "Escuchar", tab_phrases: "Frases", tab_dialogue: "Diálogo", tab_guide: "Guía",
    show_maya: "Mostrar la escritura maya", follow: "Seguir el audio", finish_title: "Terminar esta lección",
    finish_blurb: "Marca las frases que se te olvidaron. Volverán antes.", mark_done: (n) => `Marcar la lección ${n} como hecha`,
    finished: (n, f) => `Lección ${n} terminada${f ? `, ${f} para repasar antes` : ""}`,
    tap_phrase: "Toca una frase, o una parte de ella, para oírla de la lección.", word_for_word: "Palabra por palabra", earlier: "De lecciones anteriores",
    opening: "Inicio", closing: "Cierre", pattern: "El patrón de esta lección",
    g_howto: "Cómo usar una lección", g_sounds: "Los sonidos", g_patterns: "Patrones hasta ahora",
    not_in_audio: "No está en el audio de esta lección", load_fail: "Algo no cargó", check_connection: "Revisa tu conexión e inténtalo de nuevo.",
    install_ios: "Para instalarla: toca <span class=\"share\" aria-label=\"Compartir\"></span> Compartir y luego <strong>Agregar a inicio</strong>. Se abre a pantalla completa, como una app.",
    install_btn: "Instalar la app", install_other: " o úsala en el navegador; en Android, el menú de Chrome también tiene Agregar a la pantalla de inicio.",
    review_crumb: "Repaso", about_crumb: "Acerca de", record_crumb: "Grabar",
  },
};
const COPY = {
  en: {
    about: (site) => `
      <h1>About ${esc(site.name)}</h1>
      <p>Maaya T'aan is Yucatec Maya, spoken by close to a million people across the Yucatán Peninsula. This is a free audio course for learning to speak it, built the way the Pimsleur courses work: you hear a short conversation, learn each phrase from the end forward, sound by sound, and then get asked for it again at growing intervals, in the lesson and across later lessons, always with a gap to answer out loud before you hear it.</p>
      <p>Every Maya phrase in the course is taken from human-written sources, never invented. The teaching voice is synthetic, and so is the Maya voice, which is the weakest part: it's the only text-to-speech model that exists for the language. <a href="#/contribute">Recordings from native speakers</a> would make the course much better.</p>
      <h2>How to use it</h2>
      <ul>
        <li>One lesson a day, about thirty minutes, ideally while walking or doing something with your hands.</li>
        <li>Say every answer out loud in a full voice. The gap is the lesson.</li>
        <li>Add this page to your phone's home screen to use it like an app. Lessons you've opened keep working offline.</li>
        <li>Your progress stays on this device. Nothing is sent anywhere.</li>
        <li>The course is taught in English or Spanish; switch at the top. The Maya is the same either way.</li>
      </ul>
      <h2>Sources</h2>
      <ul>
        <li>Phrases: the YUA-ES Communicative Contexts Corpus by Molina-Villegas and colleagues, CC BY 4.0, 14,332 everyday Yucatec Maya sentences with Spanish translations.</li>
        <li>Words: Yucatec Maya entries from Wiktionary via Kaikki, CC BY-SA 3.0.</li>
        <li>Spelling: the 2014 INALI writing norms for Maya, <em>U nu'ukbesajil u ts'íibta'al maayat'aan</em>.</li>
        <li>Maya voice: Meta's Massively Multilingual Speech text-to-speech model for Yucatec Maya, CC BY-NC 4.0. This course is free and non-commercial.</li>
        <li>Teaching voices: Kokoro, Apache 2.0.</li>
        <li>Method: Paul Pimsleur's graduated interval recall, described in his 1967 paper <em>A Memory Schedule</em>.</li>
      </ul>
      ${site.repo_url ? `<p>The course generator is open source: <a href="${esc(site.repo_url)}">${esc(site.repo_url.replace(/^https?:\/\//, ""))}</a>.</p>` : ""}
      ${site.contact_url ? `<p>Questions or corrections: <a href="${esc(site.contact_url)}">${esc(site.contact_label || site.contact_url)}</a>.</p>` : ""}`,
    contribute: (site) => `
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
      <p class="muted small">Tap to hear how the program says it now.</p>`,
  },
  es: {
    about: (site) => `
      <h1>Acerca de ${esc(site.name)}</h1>
      <p>Maaya T'aan es el maya yucateco, hablado por cerca de un millón de personas en la península de Yucatán. Este es un curso de audio gratuito para aprender a hablarlo, hecho como funcionan los cursos Pimsleur: oyes una conversación corta, aprendes cada frase desde el final hacia adelante, sonido por sonido, y luego te la vuelven a pedir a intervalos cada vez más largos, dentro de la lección y en las siguientes, siempre con una pausa para contestar en voz alta antes de oírla.</p>
      <p>Todas las frases en maya vienen de fuentes escritas por personas; ninguna es inventada. La voz que enseña es sintética, y también la voz maya, que es la parte más débil: es el único modelo de texto a voz que existe para la lengua. <a href="#/contribute">Las grabaciones de hablantes nativos</a> mejorarían mucho el curso.</p>
      <h2>Cómo usarlo</h2>
      <ul>
        <li>Una lección al día, de unos treinta minutos, de preferencia caminando o haciendo algo con las manos.</li>
        <li>Di cada respuesta en voz alta, con voz plena. La pausa es la lección.</li>
        <li>Agrega esta página a la pantalla de inicio de tu teléfono para usarla como app. Las lecciones que hayas abierto siguen funcionando sin conexión.</li>
        <li>Tu progreso se queda en este dispositivo. No se envía a ningún lado.</li>
        <li>El curso se enseña en español o en inglés; cámbialo arriba. El maya es el mismo.</li>
      </ul>
      <h2>Fuentes</h2>
      <ul>
        <li>Frases: el corpus YUA-ES de contextos comunicativos de Molina-Villegas y colegas, CC BY 4.0, 14,332 oraciones cotidianas en maya yucateco con traducción al español.</li>
        <li>Palabras: entradas de maya yucateco del Wikcionario vía Kaikki, CC BY-SA 3.0.</li>
        <li>Escritura: las normas de escritura para la lengua maya del INALI, 2014, <em>U nu'ukbesajil u ts'íibta'al maayat'aan</em>.</li>
        <li>Voz maya: el modelo de texto a voz para maya yucateco de Massively Multilingual Speech, de Meta, CC BY-NC 4.0. Este curso es gratuito y sin fines comerciales.</li>
        <li>Voces que enseñan: Kokoro, Apache 2.0.</li>
        <li>Método: el recuerdo a intervalos graduados de Paul Pimsleur, descrito en su artículo de 1967 <em>A Memory Schedule</em>.</li>
      </ul>
      ${site.repo_url ? `<p>El generador del curso es de código abierto: <a href="${esc(site.repo_url)}">${esc(site.repo_url.replace(/^https?:\/\//, ""))}</a>.</p>` : ""}
      ${site.contact_url ? `<p>Preguntas o correcciones: <a href="${esc(site.contact_url)}">${esc(site.contact_label_es || site.contact_label || site.contact_url)}</a>.</p>` : ""}`,
    contribute: (site) => `
      <h1>Presta tu voz</h1>
      <p>Si el maaya t'aan es tu lengua, puedes hacer que este curso suene como una persona y no como un programa. La voz sintética acierta las palabras casi siempre, pero aplana los tonos y se come las palabras cortas, y quien aprende merece algo mejor.</p>
      <div class="callout"><p>Lo que más ayuda: que un hablante nativo grabe las frases del curso con su teléfono, en un cuarto silencioso, diciendo cada una con naturalidad, dos veces. Quince minutos cubren una lección completa.</p></div>
      <h2>Cómo grabar</h2>
      <ul>
        <li>Usa la grabadora de voz de tu teléfono. Sostenlo a un palmo de la boca.</li>
        <li>Di el número de la frase, luego la frase a velocidad normal, y una vez más despacio.</li>
        <li>Una grabación por lección está bien. No te preocupes por los errores; solo repite la frase.</li>
        <li>Queremos tu manera de decir las cosas. Si una frase te suena mal, di cómo la dirías tú.</li>
      </ul>
      ${site.recordings_url || site.contact_url ? `<p>Envía las grabaciones aquí: <a href="${esc(site.recordings_url || site.contact_url)}">${esc(site.contact_label_es || site.contact_label || site.recordings_url || site.contact_url)}</a>. Dinos si quieres que te demos crédito y de dónde eres, porque el maya cambia de pueblo a pueblo.</p>` : `<p class="muted">Pronto habrá un lugar para enviar grabaciones.</p>`}
      <h2>Las frases</h2>
      <p class="muted small">Toca para oír cómo lo dice el programa ahora.</p>`,
  },
};

const state = {
  lang: load("lang", (navigator.language || "en").toLowerCase().startsWith("es") ? "es" : "en"),
  manifest: null, site: null, lesson: null, timeline: null, ref: null, guide: null, current: -1, stopAt: null,
  prefs: load("prefs", { showMaya: true, follow: true, rate: 1 }),
  progress: load("progress", { completed: [], items: {} }),
};
const t = (k, ...a) => { const v = T[state.lang][k] ?? T.en[k] ?? k; return typeof v === "function" ? v(...a) : v; };
function applyLang() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll("[data-t]").forEach((el) => { if (el.id !== "play" || audio.paused) el.textContent = t(el.dataset.t); });
  document.querySelectorAll(".lang").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === state.lang)));
}
document.querySelectorAll(".lang").forEach((b) => b.addEventListener("click", () => {
  if (b.dataset.lang === state.lang) return;
  state.lang = b.dataset.lang; save("lang", state.lang);
  state.lesson = null; state.guide = null; audio.pause(); applyLang(); route();
}));

// ---------------------------------------------------------------- progress (on this device)
// Same ladder as the course planner: after a phrase is met, it's due again after 1, 1, 3, 5, 10 lessons, then 25.
const GAPS = [1, 1, 3, 5, 10], STEADY = 25;
const nextDue = (st) => st.last + (st.rung < GAPS.length ? GAPS[st.rung] : STEADY);
function nextLesson() { const c = state.progress.completed; return c.length ? Math.max(...c) + 1 : 1; }
function dueItems() { const n = nextLesson(); return Object.entries(state.progress.items).filter(([, st]) => nextDue(st) <= n).map(([id]) => id); }
function completeLesson(number, failed) {
  const p = state.progress;
  const lesson = state.manifest.lessons.find((l) => l.number === number);
  for (const it of lesson.items) p.items[it.id] ??= { introduced: number, last: number, rung: 0, yua: it.yua, en: it.en, es: it.es };
  for (const id of failed) if (p.items[id]) { p.items[id].last = number; p.items[id].rung = 0; }
  if (!p.completed.includes(number)) p.completed.push(number);
  save("progress", p);
}
function reviewOutcome(id, ok) {
  const st = state.progress.items[id]; if (!st) return;
  st.last = nextLesson() - 1; st.rung = ok ? st.rung + 1 : 0; save("progress", state.progress);
}

// ---------------------------------------------------------------- routing
window.addEventListener("hashchange", route);
async function route() {
  const [, kind, id, tab = "listen"] = location.hash.replace(/^#\/?/, "/").split("/");
  try {
    if (!state.manifest) [state.manifest, state.site] = await Promise.all([getJSON("manifest.json"), getJSON("site.json")]);
    applyLang();
    if (kind === "lesson" && id) await showLesson(id, tab);
    else if (kind === "about") showAbout();
    else if (kind === "contribute") showContribute();
    else if (kind === "review") showReview();
    else showHome();
  } catch (e) {
    view.innerHTML = `<h1>${t("load_fail")}</h1><p>${esc(e.message)}</p><p class="muted">${t("check_connection")}</p>`;
  }
}
const lessonLang = (l) => (l.variants[state.lang] ? state.lang : "en");  // fall back to English audio if a lesson isn't in Spanish yet
const title = (l) => l.title[state.lang] || l.title.en;

// ---------------------------------------------------------------- home
function showHome() {
  crumbs.textContent = "";
  player.hidden = !state.lesson;
  const m = state.manifest, site = state.site;
  const next = nextLesson();
  const due = dueItems();
  const done = state.progress.completed.length;
  const tagline = state.lang === "es" ? site.tagline_es || site.tagline : site.tagline;
  view.innerHTML = `
    <div class="hero">
      <h1>${esc(site.name)}</h1>
      <p>${esc(tagline)}</p>
      <p class="install">${t("hero_how")}</p>
      ${installHint()}
    </div>
    ${due.length ? `<div class="review"><h2>${t("review_n", due.length)}</h2><p class="small muted">${t("review_blurb")}</p><a class="btn" href="#/review">${t("start_review")}</a></div>` : ""}
    <h2 style="margin-top:0.4rem">${t("lessons")}</h2>
    <p class="muted small">${done ? t("done_of", done, m.lessons.length) : t("start_with")} ${m.lessons.length < 30 ? t("more_soon") : ""}</p>
    <ul class="lessons">${m.lessons.map((l) => `
      <li><a class="lesson ${state.progress.completed.includes(l.number) ? "done" : ""} ${l.number === next ? "next" : ""}" href="#/lesson/${l.id}">
        <span class="n">${l.number}</span>
        <span><div class="t">${esc(title(l))}</div><div class="meta">${fmt(l.variants[lessonLang(l)].duration)} · ${l.new_items} ${t("new_phrases")}</div></span>
        <span class="state">${state.progress.completed.includes(l.number) ? t("done") : l.number === next ? t("next") : ""}</span>
      </a></li>`).join("")}
    </ul>
    <p class="muted small" style="margin-top:1.2rem">${t("synthetic")} <a href="#/contribute">${t("help_replace")}</a></p>`;
}

// ---------------------------------------------------------------- install
let installPrompt = null;
window.addEventListener("beforeinstallprompt", (e) => { e.preventDefault(); installPrompt = e; const b = $("#btn-install"); if (b) b.hidden = false; });
const isStandalone = () => window.matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;
const isIOS = () => /iPhone|iPad|iPod/.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
function installHint() {
  if (isStandalone()) return "";
  if (isIOS()) return `<p class="install-hint">${t("install_ios")}</p>`;
  return `<p class="install-hint"><button class="btn quiet" id="btn-install" ${installPrompt ? "" : "hidden"}>${t("install_btn")}</button><span class="muted small">${t("install_other")}</span></p>`;
}
document.addEventListener("click", async (e) => {
  if (e.target.id === "btn-install" && installPrompt) { installPrompt.prompt(); await installPrompt.userChoice; installPrompt = null; e.target.hidden = true; }
});

function showAbout() {
  crumbs.innerHTML = `<a href="#/">${t("lessons")}</a> / ${t("about_crumb")}`;
  view.innerHTML = `<div class="about">${COPY[state.lang].about(state.site)}</div>`;
}

function showContribute() {
  crumbs.innerHTML = `<a href="#/">${t("lessons")}</a> / ${t("record_crumb")}`;
  const phrases = state.manifest.lessons.flatMap((l) => l.items.map((it) => ({ ...it, lesson: l.id, lang: lessonLang(l) })));
  view.innerHTML = `<div class="about">${COPY[state.lang].contribute(state.site)}
    <ol class="phraselist">${phrases.map((p, i) => `<li><span class="muted small">${i + 1}</span><span class="y">${esc(p.yua)}</span><span class="e">${esc(p[state.lang] || p.en)}</span><button class="playbtn secondary" data-lesson="${p.lesson}" data-l="${p.lang}" data-play="${esc(p.yua)}">${t("play")}</button></li>`).join("")}</ol>
  </div>`;
  view.addEventListener("click", async (e) => {
    const b = e.target.closest("[data-play]"); if (!b) return;
    await withRef(b.dataset.lesson, b.dataset.l, () => playPhrase(b.dataset.play));
  });
}
async function withRef(lessonId, lang, fn) {
  const ref = await getJSON(`lessons/${lessonId}.${lang}.lesson.json`);
  const saved = state.ref; state.ref = ref; fn(); state.ref = saved;
}

// ---------------------------------------------------------------- review drill
function showReview() {
  crumbs.innerHTML = `<a href="#/">${t("lessons")}</a> / ${t("review_crumb")}`;
  const queue = dueItems().map((id) => ({ id, ...state.progress.items[id] }));
  let i = 0;
  const step = () => {
    if (i >= queue.length) { view.innerHTML = `<h1>${t("review_done")}</h1><p>${t("checked", queue.length)} <a href="#/">${t("back_to_lessons")}</a>.</p>`; return; }
    const q = queue[i];
    view.innerHTML = `<div class="drill">
      <div class="count">${i + 1} / ${queue.length}</div>
      <h1>${t("say_in_maya")}</h1>
      <p class="prompt">${esc(q[state.lang] || q.en)}</p>
      <div class="answer veiled" id="ans">${esc(q.yua)}</div>
      <div class="row"><button class="btn" id="reveal">${t("check")}</button></div>
      <div class="row" id="judge" hidden><button class="btn" id="ok">${t("got_it")}</button><button class="btn miss" id="miss">${t("missed")}</button></div>
    </div>`;
    $("#reveal").addEventListener("click", async () => {
      $("#ans").classList.remove("veiled"); $("#reveal").hidden = true; $("#judge").hidden = false;
      const lesson = state.manifest.lessons.find((l) => l.items.some((it) => it.id === q.id));
      if (lesson) await withRef(lesson.id, lessonLang(lesson), () => playPhrase(q.yua));
    });
    $("#ok").addEventListener("click", () => { reviewOutcome(q.id, true); i++; step(); });
    $("#miss").addEventListener("click", () => { reviewOutcome(q.id, false); i++; step(); });
  };
  step();
}

// ---------------------------------------------------------------- lesson
async function showLesson(id, tab) {
  const entry = state.manifest.lessons.find((l) => l.id === id);
  const lang = entry ? lessonLang(entry) : "en";
  if (!state.lesson || state.lesson !== id) {
    const [timeline, ref] = await Promise.all([getJSON(`lessons/${id}.${lang}.json`), getJSON(`lessons/${id}.${lang}.lesson.json`)]);
    state.lesson = id; state.timeline = timeline; state.ref = ref; state.current = -1;
    audio.src = `lessons/${timeline.audio}`; audio.playbackRate = state.prefs.rate;
    $("#t-dur").textContent = fmt(timeline.duration);
    $("#now-maya").textContent = ref.title; $("#now-maya").className = "now-maya"; $("#now-en").textContent = `${t("lesson")} ${ref.number}`;
  }
  if (!state.guide) state.guide = await getJSON(`guide.${state.lang}.json`).catch(() => getJSON("guide.en.json"));
  player.hidden = false;
  crumbs.innerHTML = `<a href="#/">${t("lessons")}</a> / ${t("lesson")} ${state.ref.number}`;
  const tabs = [["listen", t("tab_listen")], ["phrases", t("tab_phrases")], ["dialogue", t("tab_dialogue")], ["guide", t("tab_guide")]];
  view.innerHTML = `
    <h1>${esc(state.ref.title)}</h1>
    <div class="tabs" role="tablist">${tabs.map(([k, l]) => `<button class="tab" role="tab" aria-selected="${k === tab}" data-tab="${k}">${l}</button>`).join("")}</div>
    <section id="panel"></section>`;
  view.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => (location.hash = `#/lesson/${id}/${b.dataset.tab}`)));
  ({ listen: renderListen, phrases: renderPhrases, dialogue: renderDialogue, guide: renderGuide })[tab]?.($("#panel"));
}

function segLabel(seg) {
  if (seg.kind === "pause") return seg.turn === "response" ? t("your_turn") : seg.turn === "repeat" ? t("repeat_it") : "";
  return seg.text;
}

function renderListen(panel) {
  const tl = state.timeline.segments;
  panel.innerHTML = `
    <div class="opts">
      <label><input type="checkbox" id="opt-maya" ${state.prefs.showMaya ? "checked" : ""}> ${t("show_maya")}</label>
      <label><input type="checkbox" id="opt-follow" ${state.prefs.follow ? "checked" : ""}> ${t("follow")}</label>
    </div>
    <ol class="tx" id="tx">${tl.map((seg, i) => {
      if (seg.kind === "pause") return segLabel(seg) ? `<li class="seg pause ${seg.turn}" data-i="${i}">${segLabel(seg)} <span class="muted">${Math.round(seg.end - seg.start)} s</span></li>` : "";
      if (seg.kind === "narrator") return `<li class="seg narrator" data-i="${i}">${esc(seg.text)}</li>`;
      return `<li class="seg maya ${seg.slice_of ? "frag" : ""}" data-i="${i}"><span class="y ${state.prefs.showMaya ? "" : "hidden-maya"}">${esc(seg.text)}</span>${seg.meaning ? `<span class="e">${esc(seg.meaning)}</span>` : ""}</li>`;
    }).join("")}</ol>
    <div class="finish" id="finish">
      <h2 style="margin-top:0">${t("finish_title")}</h2>
      <p class="small muted">${t("finish_blurb")}</p>
      <div class="items">${[...state.ref.items, ...state.ref.review_items].map((it) => `
        <label><input type="checkbox" name="failed" value="${esc(it.id)}"><span><div class="fy">${esc(it.yua)}</div><div class="fe">${esc(it.meaning)}</div></span></label>`).join("")}</div>
      <button class="btn" id="btn-finish">${t("mark_done", state.ref.number)}</button>
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
      <div class="e">${esc(it.meaning)}</div>
      ${it.literal ? `<div class="lit">${t("word_for_word")}: ${esc(it.literal)}</div>` : ""}
      ${it.note ? `<div class="note">${esc(it.note)}</div>` : ""}
      ${it.syllables?.length > 1 ? `<div class="chunks">${it.syllables.map((c) => `<button class="chunk" data-play="${esc(c)}" data-full="${esc(it.yua)}">${esc(c)}${it.glosses?.[c] ? `<span class="g">${esc(it.glosses[c])}</span>` : ""}</button>`).join("")}</div>` : ""}
      ${Object.entries(it.glosses || {}).filter(([k]) => !it.syllables?.includes(k)).length ? `<div class="lit">${Object.entries(it.glosses).filter(([k]) => !it.syllables?.includes(k)).map(([k, v]) => `<span class="wg"><b>${esc(k)}</b> ${esc(v)}</span>`).join(" · ")}</div>` : ""}
      <button class="playbtn" data-play="${esc(it.yua)}">${t("play")}</button>
      ${it.transforms?.length ? it.transforms.map((tr) => `<button class="playbtn secondary" data-play="${esc(tr.yua)}">${esc(tr.yua)}</button>`).join(" ") : ""}
    </div>`;
  panel.innerHTML = `
    <p class="muted small">${t("tap_phrase")}</p>
    ${state.ref.items.map(block).join("")}
    ${state.ref.review_items.length ? `<h2>${t("earlier")}</h2>${state.ref.review_items.map(block).join("")}` : ""}`;
  panel.addEventListener("click", (e) => { const b = e.target.closest("[data-play]"); if (b) playPhrase(b.dataset.play, b.dataset.full); });
}

function renderDialogue(panel) {
  const dlg = (d, ttl) => `<h2>${ttl}</h2><p class="muted small">${esc(d.setting)}</p>
    <ul class="dlg">${d.lines.map((l) => `<li data-play="${esc(l.yua)}"><span class="who">${l.speaker}</span><span><div class="y">${esc(l.yua)}</div><div class="e">${esc(l.meaning)}</div></span></li>`).join("")}</ul>`;
  panel.innerHTML = dlg(state.ref.opening, t("opening")) + (state.ref.closing.id !== state.ref.opening.id ? dlg(state.ref.closing, t("closing")) : "") +
    (state.ref.grammar_note ? `<h2>${t("pattern")}</h2><p>${esc(state.ref.grammar_note)}</p>` : "");
  panel.addEventListener("click", (e) => { const b = e.target.closest("[data-play]"); if (b) playPhrase(b.dataset.play); });
}

function renderGuide(panel) {
  const g = state.guide;
  panel.innerHTML = `<div class="guide">
    <h2>${t("g_howto")}</h2>${g.howto.map((p) => `<p>${esc(p)}</p>`).join("")}
    <h2>${t("g_sounds")}</h2><table>${g.sounds.map((r) => `<tr><td>${esc(r.s)}</td><td>${esc(r.d)}<div class="ex muted">${esc(r.ex)}</div></td></tr>`).join("")}</table>
    <h2>${t("g_patterns")}</h2><table>${g.patterns.map((r) => `<tr><td>${esc(r.t)}</td><td>${esc(r.d)}</td></tr>`).join("")}</table>
    <p class="muted small">${esc(g.spelling)}</p></div>`;
}

// ---------------------------------------------------------------- playback
function seekTo(tm) { audio.currentTime = Math.max(0, tm); state.stopAt = null; }
const clipAudio = new Audio();
function findClip(text, full) {
  const entries = Object.entries(state.ref.clips || {}).map(([k, url]) => { const [tx, rate, slice] = k.split("|"); return { t: tx, rate: +rate, slice, url }; })
    .filter((c) => c.t.toLowerCase() === text.toLowerCase());
  if (!entries.length) return null;
  const score = (c) => (full ? (c.slice.toLowerCase() === full.toLowerCase() ? 0 : 2) : (c.slice ? 2 : 0)) + (c.rate === 1 ? 0 : 1) + (full && c.rate < 1 ? -0.5 : 0);
  return entries.sort((a, b) => score(a) - score(b))[0];
}
function playPhrase(text, full) {
  const clip = findClip(text, full);
  if (clip) { audio.pause(); clipAudio.src = `lessons/${clip.url}`; clipAudio.play(); return; }
  const tl = state.timeline?.segments || [];
  const want = text.toLowerCase();
  const seg = tl.find((s) => s.kind === "maya" && s.text.toLowerCase() === want && s.rate === 1) || tl.find((s) => s.kind === "maya" && s.text.toLowerCase() === want);
  if (!seg) { toast(t("not_in_audio")); return; }
  audio.currentTime = seg.start; state.stopAt = seg.end; audio.play();
}
$("#play").addEventListener("click", () => { clipAudio.pause(); audio.paused ? audio.play() : audio.pause(); });
$("#back").addEventListener("click", () => seekTo(audio.currentTime - 5));
$("#fwd").addEventListener("click", () => seekTo(audio.currentTime + 5));
$("#rate").addEventListener("click", () => { const r = [1, 0.85, 0.7, 1.15][([1, 0.85, 0.7, 1.15].indexOf(state.prefs.rate) + 1) % 4]; state.prefs.rate = r; save("prefs", state.prefs); audio.playbackRate = r; $("#rate").textContent = `${r}×`; });
$("#rate").textContent = `${state.prefs.rate}×`;
audio.addEventListener("play", () => ($("#play").textContent = t("pause")));
audio.addEventListener("pause", () => ($("#play").textContent = t("play")));
$("#seek").addEventListener("input", (e) => { if (state.timeline) seekTo((e.target.value / 1000) * state.timeline.duration); });
audio.addEventListener("ended", () => { state.stopAt = null; });

function tick() {
  requestAnimationFrame(tick);
  if (!state.timeline || audio.paused) return;
  const tm = audio.currentTime;
  if (state.stopAt != null && tm >= state.stopAt - 0.08) { audio.pause(); state.stopAt = null; return; }
  $("#seek").value = Math.round((tm / state.timeline.duration) * 1000);
  $("#t-cur").textContent = fmt(tm);
  const tl = state.timeline.segments;
  let i = state.current;
  if (i < 0 || tm < tl[i].start || tm >= tl[i].end) {
    i = tl.findIndex((s) => tm >= s.start && tm < s.end);
    if (i !== state.current) { state.current = i; highlight(); }
  }
  const seg = tl[i];
  if (seg && seg.kind === "pause" && seg.turn) $("#turn-fill").style.width = `${Math.min(100, ((tm - seg.start) / (seg.end - seg.start)) * 100)}%`;
}
requestAnimationFrame(tick);

function highlight(initial = false) {
  const tl = state.timeline?.segments; if (!tl) return;
  const seg = tl[state.current];
  const nowM = $("#now-maya"), nowE = $("#now-en"), turn = $("#turn");
  if (seg) {
    if (seg.kind === "maya") { nowM.textContent = state.prefs.showMaya ? seg.text : "· · ·"; nowM.className = "now-maya"; nowE.textContent = seg.meaning || ""; turn.hidden = true; }
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
  const btn = $("#btn-finish"); btn.textContent = t("done"); btn.classList.add("done"); btn.disabled = true;
  toast(t("finished", state.ref.number, failed.length));
  setTimeout(() => (location.hash = "#/"), 900);
}

// ---------------------------------------------------------------- boot
if ("serviceWorker" in navigator && location.protocol === "https:") navigator.serviceWorker.register("sw.js").catch(() => {});
route();
