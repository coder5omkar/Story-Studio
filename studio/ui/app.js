const S = {
  projects: [],
  pid: null,
  data: null,
  page: "series",
  series: null,
  seriesBusy: false,
  seriesBusyMsg: "",
  seriesSettingsReady: false,
  seriesBibleReady: false,
  castDirty: false,
  ideas: null,
  selectedGenre: null,
  ideaBusy: false,
  ideaBusyMsg: "",
  ideaSettingsReady: false,
  jobId: null,
  job: null,
  poll: null,
  health: null,
  selectedScene: 1,
  reviewScene: null,
  reviewRenderedScene: null,
  reviewDirty: false,
  reviewPlayAfterLoad: false,
  storyDirty: false,
  topicDirty: false,
  instructionsDirty: false,
  sceneDirty: false,
  settingsDirty: false,
  voicePreviewText: "",
  toastTimer: null,
};

const PROVIDER_PRESETS = {
  "opencode-go": "https://opencode.ai/inference/go/openai/v1",
  "opencode": "https://opencode.ai/inference/openai/v1",
};

const PROVIDER_MODEL_HINTS = {
  "opencode-go": "deepseek-v4.1-flash",
  "opencode": "deepseek-v4.1-flash",
  "openai": "provider model ID",
};

const PROVIDER_DEFAULT_MODELS = {
  "opencode-go": "deepseek-v4.1-flash",
  "opencode": "deepseek-v4.1-flash",
  "ollama": "aya-expanse:8b",
};

const STYLE_PRESETS = {
  minimalist: {
    engine: "zimage",
    prefix:
      "minimalist 2D webcomic educational explainer illustration, flat clean vector lines, " +
      "solid flat colors, no shading, no gradients, simple shapes with detailed flat backgrounds, " +
      "clear daylight, wide 16:9 composition, Infographics Show and Kurzgesagt inspired, no text, no watermark",
    character:
      "the protagonist is a simple stick figure character with a large round white head, two dot eyes, " +
      "a small straight-line mouth, wearing a long-sleeve grey-blue shirt and dark blue jeans",
    negative:
      "low quality, blurry, text, watermark, logo, signature, photorealistic, 3D render, realistic human, " +
      "realistic skin texture, detailed face, detailed eyes, detailed mouth, nose, ears, beard, mustache, hair, " +
      "neck, tie, collar, buttons, suit, shirt cuffs, white shirt, smile, curved mouth, grin, eyebrows, teeth, " +
      "realistic hands, muscular body, realistic proportions, mannequin, statue, doll, shading, gradients, " +
      "soft shadows, complex clothing folds, deformed, extra fingers, bad anatomy",
  },
  "indian-flat": {
    engine: "sdxl",
    prefix:
      "flat vector illustration, clean bold outlines, warm muted palette, soft shading, cinematic composition, " +
      "Indian middle-class setting, detailed background, no text, no watermark",
    character:
      "Arjun, a 29-year-old Indian man with short black hair, a light mustache, average build, " +
      "wearing a white shirt, dark trousers, and a simple wristwatch",
    negative:
      "low quality, blurry, text, watermark, logo, signature, photorealistic, 3D render, " +
      "deformed, extra fingers, bad anatomy",
  },
  photoreal: {
    engine: "sdxl",
    prefix:
      "photorealistic cinematic film still, natural skin texture, detailed expressive faces, realistic clothing, " +
      "35mm lens, shallow depth of field, volumetric lighting, Indian middle-class setting, " +
      "muted cinematic color grade, no text, no watermark",
    character:
      "the protagonist is a realistic Indian man in his late thirties with short black hair, a light beard, " +
      "average build, wearing a simple shirt and trousers; keep the same face and outfit consistent across scenes",
    negative:
      "cartoon, anime, illustration, painting, drawing, 3D render, flat colors, low quality, blurry, " +
      "text, watermark, logo, signature, deformed, extra fingers, bad anatomy",
  },
  "cinematic-dark": {
    engine: "sdxl",
    prefix:
      "cinematic photorealistic film still, moody low-key lighting, deep shadows, tense atmosphere, 35mm lens, " +
      "shallow depth of field, Indian middle-class setting, desaturated color grade, no text, no watermark",
    character:
      "the protagonist is a realistic Indian man in his late thirties with short black hair, a light beard, " +
      "average build, wearing a simple shirt and trousers; keep the same face and outfit consistent across scenes",
    negative:
      "cartoon, anime, illustration, painting, drawing, 3D render, flat colors, low quality, blurry, " +
      "text, watermark, logo, signature, deformed, extra fingers, bad anatomy",
  },
  anime: {
    engine: "zimage",
    prefix:
      "hand-painted 2D anime film still, expressive characters, soft watercolor backgrounds, clean linework, " +
      "warm cinematic lighting, Indian middle-class setting, detailed background, no text, no watermark",
    character:
      "the protagonist is a young Indian man with short black hair, wearing a simple shirt and trousers, " +
      "drawn in a consistent anime style",
    negative:
      "photorealistic, 3D render, realistic skin texture, low quality, blurry, text, watermark, logo, " +
      "signature, deformed, extra fingers, bad anatomy",
  },
  "animated-3d": {
    engine: "sdxl",
    prefix:
      "stylized 3D animated feature film still, soft global illumination, rounded character design, " +
      "expressive faces, detailed environment, Indian middle-class setting, cinematic composition, " +
      "no text, no watermark",
    character:
      "the protagonist is a stylized 3D animated Indian man with short black hair, simple shirt and trousers, " +
      "consistent character design",
    negative:
      "photorealistic, flat vector, 2D illustration, line drawing, low quality, blurry, text, watermark, logo, " +
      "signature, deformed, extra fingers, bad anatomy",
  },
  "graphic-novel": {
    engine: "sdxl",
    prefix:
      "graphic novel illustration, bold ink outlines, dramatic comic panel composition, halftone texture, " +
      "limited color palette, Indian middle-class setting, detailed background, no text, no watermark",
    character:
      "the protagonist is an Indian man drawn in a consistent graphic novel style, short black hair, " +
      "simple shirt and trousers",
    negative:
      "photorealistic, 3D render, soft painting, watercolor, low quality, blurry, text, watermark, logo, " +
      "signature, deformed, extra fingers, bad anatomy",
  },
  watercolor: {
    engine: "zimage",
    prefix:
      "soft watercolor storybook illustration, delicate ink lines, visible paper texture, warm muted washes, " +
      "gentle lighting, Indian middle-class setting, detailed background, no text, no watermark",
    character:
      "the protagonist is an Indian man drawn in a consistent watercolor storybook style, short black hair, " +
      "simple clothes",
    negative:
      "photorealistic, 3D render, harsh shadows, high contrast, low quality, blurry, text, watermark, logo, " +
      "signature, deformed, extra fingers, bad anatomy",
  },
  "vintage-poster": {
    engine: "sdxl",
    prefix:
      "vintage Indian poster illustration, screen-print texture, muted retro palette, bold simplified shapes, " +
      "1970s Indian graphic design, Indian middle-class setting, no text, no watermark",
    character:
      "the protagonist is an Indian man in a consistent vintage poster style, simple shirt and trousers",
    negative:
      "photorealistic, 3D render, modern digital art, low quality, blurry, text, watermark, logo, signature, " +
      "deformed, extra fingers, bad anatomy",
  },
  "paper-cutout": {
    engine: "zimage",
    prefix:
      "layered paper cutout collage illustration, textured paper, bold simple shapes, soft drop shadows, " +
      "warm palette, Indian middle-class setting, no text, no watermark",
    character:
      "the protagonist is a paper-cutout Indian man with simple features, shirt and trousers",
    negative:
      "photorealistic, 3D render, smooth gradients, low quality, blurry, text, watermark, logo, signature, " +
      "deformed, extra fingers, bad anatomy",
  },
};

const $ = (id) => document.getElementById(id);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function statusClass(status) {
  const s = String(status || "empty").toLowerCase();
  return ["approved", "ready", "done", "draft", "running", "stale", "failed", "empty",
    "changes_requested"].includes(s) ? s : "empty";
}

function statusText(status) {
  return String(status || "empty").replaceAll("_", " ");
}

async function api(path, options = {}) {
  const opts = { ...options, headers: { ...(options.headers || {}) } };
  if (opts.body && typeof opts.body !== "string") {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(opts.body);
  }
  const res = await fetch(path, opts);
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!res.ok) {
    const detail = data?.detail ?? data;
    let message = typeof detail === "string" ? detail : detail?.message;
    if (!message) message = detail ? JSON.stringify(detail) : `HTTP ${res.status}`;
    const err = new Error(message);
    err.detail = detail;
    throw err;
  }
  return data;
}

function toast(message, type = "ok") {
  const el = $("toast");
  el.textContent = message;
  el.className = `toast ${type}`;
  clearTimeout(S.toastTimer);
  S.toastTimer = setTimeout(() => el.classList.add("hidden"), type === "error" ? 7000 : 3500);
}

function fmtMinutes(seconds) {
  if (!seconds) return "—";
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

function providerBase(provider) {
  if (provider === "ollama") {
    return $("setOllamaUrl")?.value.trim() || "http://127.0.0.1:11434";
  }
  return PROVIDER_PRESETS[provider] || $("setApiBase")?.value.trim() || "";
}

function applyProviderPreset(provider) {
  const preset = PROVIDER_PRESETS[provider];
  if (preset) $("setApiBase").value = preset;
}

const STYLE_LABELS = {
  minimalist: "Minimalist explainer",
  "indian-flat": "Indian flat-vector",
  photoreal: "Cinematic photoreal",
  "cinematic-dark": "Dark cinematic drama",
  anime: "Anime / hand-painted",
  "animated-3d": "3D animated feature",
  "graphic-novel": "Graphic novel / comic",
  watercolor: "Watercolor storybook",
  "vintage-poster": "Vintage Indian poster",
  "paper-cutout": "Paper cutout collage",
};

function renderStyleGallery() {
  const el = $("styleGallery");
  if (!el) return;
  el.innerHTML = Object.entries(STYLE_LABELS).map(([key, label]) => `
    <div class="style-card">
      <button type="button" class="style-card-select" data-style="${key}" title="Select ${esc(label)}">
        <img src="/ui/style_samples/${key}_thumb.jpg" alt="${esc(label)} sample">
        <span class="style-card-label">${esc(label)}</span>
      </button>
      <a class="style-card-full" href="/ui/style_samples/${key}.png" target="_blank" rel="noopener">Open full sample</a>
    </div>
  `).join("");
}

function markSelectedStyle(key) {
  $$("#styleGallery [data-style]").forEach((button) => {
    const card = button.closest(".style-card");
    if (card) card.classList.toggle("selected", button.dataset.style === key);
  });
}

function stylePresetFor(prefix, character, negative) {
  const p = String(prefix || "").trim();
  for (const [key, preset] of Object.entries(STYLE_PRESETS)) {
    if (p === preset.prefix) return key;
  }
  const text = `${p} ${character || ""} ${negative || ""}`.toLowerCase();
  if (text.includes("minimalist") || text.includes("webcomic")) return "minimalist";
  return "custom";
}

function stage(path) {
  let node = S.data?.state?.stages || {};
  for (const part of path.split(".")) node = node?.[part] || {};
  return node;
}

function stageStatus(path) {
  return stage(path).status || "empty";
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

async function boot() {
  bind();
  renderStyleGallery();
  const hashPage = location.hash.replace(/^#/, "");
  if (["series", "ideas", "story", "scenes", "samples", "production", "final", "publish", "settings"].includes(hashPage)) {
    S.page = hashPage;
  }
  await loadHealth();
  await loadSeries();
  await loadIdeas();
  await loadProjects();
  await loadIdeaModels();
  await loadSeriesModels();
  showPage(S.page);
  setInterval(loadHealth, 15000);
}

async function loadHealth() {
  try {
    S.health = await api("/api/health");
    const items = [
      ["Ollama", S.health.ollama],
      ["ComfyUI", S.health.comfy],
      ["FFmpeg", S.health.ffmpeg],
      ["TTS", S.health.tts_env],
    ];
    $("services").innerHTML = items.map(([name, ok]) =>
      `<span class="service ${ok ? "ok" : "down"}" title="${name}: ${ok ? "online" : "offline"}"><span class="dot"></span><span>${name}</span></span>`
    ).join("");
  } catch (e) {
    $("services").innerHTML = `<span class="service down"><span class="dot"></span><span>server offline</span></span>`;
  }
}

async function loadProjects() {
  try {
    S.projects = await api("/api/projects");
  } catch (e) {
    S.projects = [];
    toast(e.message, "error");
  }
  const sel = $("projectSelect");
  if (!S.projects.length) {
    sel.innerHTML = `<option value="">No projects yet</option>`;
    S.pid = null;
    S.data = null;
    renderEmpty();
    return;
  }
  sel.innerHTML = S.projects.map((p) =>
    `<option value="${esc(p.id)}">${esc(p.title)}</option>`
  ).join("");
  const wanted = S.pid && S.projects.some((p) => p.id === S.pid) ? S.pid : S.projects[0].id;
  sel.value = wanted;
  if (wanted !== S.pid || !S.data) await selectProject(wanted);
}

async function selectProject(pid) {
  S.pid = pid;
  S.storyDirty = false;
  S.topicDirty = false;
  S.instructionsDirty = false;
  S.sceneDirty = false;
  S.settingsDirty = false;
  S.selectedScene = 1;
  S.reviewScene = null;
  S.reviewRenderedScene = null;
  S.reviewDirty = false;
  S.reviewPlayAfterLoad = false;
  S.voicePreviewText = "";
  $("voiceText").value = "";
  await loadProject();
}

async function loadProject() {
  if (!S.pid) return;
  try {
    S.data = await api(`/api/projects/${S.pid}`);
  } catch (e) {
    toast(e.message, "error");
    return;
  }
  if (S.data.active_job) {
    S.jobId = S.data.active_job.id;
    S.job = S.data.active_job;
    startPolling();
  }
  renderAll();
  if (!S.modelsLoaded) {
    S.modelsLoaded = true;
    loadModels();
  }
}

function renderEmpty() {
  $("projectTitle").textContent = "No project selected";
  $("projectMeta").textContent = "Create a project to begin.";
  ["story", "scenes", "samples", "production", "final"].forEach((p) => {
    const badge = $(`badge-${p}`);
    if (badge) { badge.textContent = "empty"; badge.className = "stage-badge empty"; }
  });
  $("gateList").innerHTML = "";
  $("sceneList").innerHTML = `<div class="empty-state"><strong>No project</strong>Create a project to start the approval-gated workflow.</div>`;
}

// ---------------------------------------------------------------------------
// Global render
// ---------------------------------------------------------------------------

function renderAll() {
  if (!S.data) {
    renderEmpty();
    renderSeries();
    renderIdeas();
    showPage(S.page);
    return;
  }
  renderTop();
  renderRail();
  renderStory();
  renderScenes();
  renderSamples();
  renderProduction();
  renderFinal();
  renderPublish();
  renderSeries();
  renderIdeas();
  renderSettings();
  showPage(S.page);
}

function renderTop() {
  const p = S.data.project;
  const st = S.data.state;
  const seriesTitle = st.settings?.series_title || "";
  const episodeNumber = st.settings?.episode_number || "";
  const seriesLine = seriesTitle
    ? `${esc(seriesTitle)}${episodeNumber ? ` · EP ${esc(String(episodeNumber))}` : ""}<br>`
    : "";
  $("projectTitle").textContent = p.title || p.id;
  $("projectMeta").innerHTML =
    `<span class="mono">${esc(p.id)}</span> · ${esc(st.created_at || "")}<br>` +
    seriesLine +
    `${S.data.scenes.length} scenes · ${S.data.scene_status.filter((s) => s.image).length} images · ` +
    `${S.data.scene_status.filter((s) => s.audio).length} voice clips`;
}

function renderRail() {
  const map = {
    story: stageStatus("story"),
    scenes: stageStatus("scenes"),
    samples: aggregateSampleStatus(),
    production: stageStatus("production"),
    final: stageStatus("final"),
    publish: stageStatus("publish"),
  };
  for (const [page, status] of Object.entries(map)) {
    const badge = $(`badge-${page}`);
    if (!badge) continue;
    badge.textContent = statusText(status);
    badge.className = `stage-badge ${statusClass(status)}`;
  }

  const musicEnabled = S.data.state.settings.music.enabled !== false;
  const gates = [
    ["Story approved", stageStatus("story") === "approved"],
    ["Scene plan approved", stageStatus("scenes") === "approved"],
    ["Voice sample approved", stage("samples.voice").approved],
    ["Image sample approved", stage("samples.image").approved],
    ...(musicEnabled
      ? [["Music sample approved", stage("samples.music").approved]]
      : [["Music disabled (optional)", true]]),
    ["Preview clip approved", stage("samples.clip").approved],
  ];
  $("gateList").innerHTML = gates.map(([label, on]) =>
    `<div class="gate ${on ? "on" : ""}"><span class="gate-check">${on ? "✓" : ""}</span><span>${esc(label)}</span></div>`
  ).join("");
}

function aggregateSampleStatus() {
  const kinds = ["voice", "image", "music", "clip"].map((k) => stageStatus(`samples.${k}`));
  if (kinds.every((k) => k === "approved")) return "approved";
  if (kinds.some((k) => ["draft", "ready", "running"].includes(k))) return "draft";
  if (kinds.some((k) => k === "stale")) return "stale";
  return "empty";
}

function showPage(page) {
  S.page = page;
  $$(".page").forEach((el) => el.classList.toggle("active", el.id === `page-${page}`));
  $$(".stage-link").forEach((el) => el.classList.toggle("active", el.dataset.page === page));
  if (location.hash !== `#${page}`) history.replaceState(null, "", `#${page}`);
}

// ---------------------------------------------------------------------------
// Series room
// ---------------------------------------------------------------------------

async function loadSeries() {
  try {
    S.series = await api("/api/series");
  } catch (e) {
    console.warn(e);
    if (!S.series) S.series = null;
  }
  S.seriesBibleReady = false;
  S.castDirty = false;
  renderSeries();
}

function initSeriesSettings() {
  if (S.seriesSettingsReady || !S.series) return;
  const settings = S.series.settings || {};
  if (settings.provider) $("seriesProvider").value = settings.provider;
  if (!$("seriesProvider").value) $("seriesProvider").value = "opencode-go";
  if (settings.model) $("seriesModel").value = settings.model;
  S.seriesSettingsReady = true;
}

function seriesLlmPayload() {
  const provider = $("seriesProvider").value;
  return {
    provider,
    model: $("seriesModel").value.trim(),
    api_base: providerBase(provider),
    temperature: 0.9,
  };
}

function seriesModelReady() {
  if (!$("seriesModel").value.trim()) {
    toast("Choose a series model first", "error");
    return false;
  }
  const provider = $("seriesProvider").value;
  if (provider !== "ollama" && S.health && S.health.secrets === false) {
    toast("No API key saved. Add your OpenCode key in Settings.", "error");
    return false;
  }
  return true;
}

function setSeriesBusy(message) {
  S.seriesBusy = !!message;
  S.seriesBusyMsg = message || "";
  renderSeries();
}

function fillSeriesBible() {
  if (!S.series) return;
  const bible = S.series.series || {};
  const fields = {
    seriesTitle: "title",
    seriesTitleHi: "title_hi",
    seriesTagline: "tagline",
    seriesPremise: "premise",
    seriesWorld: "world",
    seriesTone: "tone",
    seriesVisualStyle: "visual_style",
    seriesNarrator: "narrator",
    seriesNarratorVoice: "narrator_voice_reference",
    seriesIntro: "intro",
    seriesOutro: "outro",
    seriesContinuity: "continuity_rules",
    seriesStorySoFar: "story_so_far",
  };
  for (const [id, key] of Object.entries(fields)) {
    const el = $(id);
    if (el && document.activeElement !== el) el.value = bible[key] || "";
  }
  $("seriesPillars").value = (bible.pillars || []).join(", ");
  S.seriesBibleReady = true;
}

function collectCast() {
  return $$("#castGrid .cast-card").map((card) => {
    const get = (field) => card.querySelector(`[data-cast="${field}"]`)?.value ?? "";
    return {
      id: card.dataset.castId,
      name: get("name").trim(),
      name_hi: get("name_hi").trim(),
      age: Number(get("age") || 0),
      role: get("role").trim(),
      pillar: get("pillar").trim(),
      appearance: get("appearance").trim(),
      wardrobe: get("wardrobe").trim(),
      signature_prop: get("signature_prop").trim(),
      voice_reference: get("voice_reference").trim(),
      speaking_style: get("speaking_style").trim(),
      relationships: get("relationships").trim(),
      face_reference: get("face_reference").trim(),
    };
  });
}

function renderCast(force = false) {
  if (!S.series) return;
  if (S.castDirty && !force) return;
  const cast = S.series.cast || [];
  $("castGrid").innerHTML = cast.map((person) => `
    <details class="cast-card" data-cast-id="${esc(person.id)}">
      <summary>
        <span class="cast-name">${esc(person.name || "New character")}</span>
        <span class="cast-meta">${esc(String(person.age || ""))} · ${esc(person.role || "")} · ${esc(person.pillar || "")}</span>
      </summary>
      <div class="row wrap">
        <label>Name <input data-cast="name" type="text" value="${esc(person.name || "")}"></label>
        <label>Hindi name <input data-cast="name_hi" type="text" value="${esc(person.name_hi || "")}"></label>
      </div>
      <div class="row wrap">
        <label>Age <input data-cast="age" type="number" value="${esc(String(person.age || ""))}"></label>
        <label>Role <input data-cast="role" type="text" value="${esc(person.role || "")}"></label>
        <label>Pillar <input data-cast="pillar" type="text" value="${esc(person.pillar || "")}"></label>
      </div>
      <label>Appearance prompt <textarea data-cast="appearance" rows="3">${esc(person.appearance || "")}</textarea></label>
      <div class="row wrap">
        <label>Wardrobe <input data-cast="wardrobe" type="text" value="${esc(person.wardrobe || "")}"></label>
        <label>Signature prop <input data-cast="signature_prop" type="text" value="${esc(person.signature_prop || "")}"></label>
      </div>
      <div class="row wrap">
        <label>Voice reference <input data-cast="voice_reference" type="text" value="${esc(person.voice_reference || "")}" placeholder="Chatterbox reference WAV"></label>
        <label>Face reference (Phase 2) <input data-cast="face_reference" type="text" value="${esc(person.face_reference || "")}" placeholder="ComfyUI input filename"></label>
      </div>
      <label>Speaking style <input data-cast="speaking_style" type="text" value="${esc(person.speaking_style || "")}"></label>
      <label>Relationships <input data-cast="relationships" type="text" value="${esc(person.relationships || "")}"></label>
    </details>
  `).join("");
}

function episodeCard(episode) {
  const isProject = !!episode.project_id;
  const support = (episode.supporting_cast || []).join(", ");
  return `<article class="idea-card">
    <div class="idea-head">
      <div>
        <h4 class="idea-title">${isProject ? `EP ${episode.episode_number} · ` : ""}${esc(episode.title)}</h4>
        <div class="idea-title-en">${esc(episode.title_en || "")}</div>
      </div>
      <div class="idea-badges">
        <span class="review-chip">${esc(episode.pillar || "")}</span>
        <span class="review-chip">${episode.minutes || 10} min</span>
        <span class="idea-status ${isProject ? "project" : ""}">${isProject ? `Episode ${episode.episode_number}` : "Idea"}</span>
      </div>
    </div>
    <p class="idea-logline"><b>Lead:</b> ${esc(episode.protagonist_name || "")} · ${esc(episode.logline || "")}</p>
    ${episode.hook ? `<div class="idea-hook"><b>Hook:</b> ${esc(episode.hook)}</div>` : ""}
    <details>
      <summary>Read full episode blueprint</summary>
      <div class="idea-details">
        <h4>Full plot</h4>
        ${ideaParagraphs(episode.premise)}
        ${episode.ending ? `<h4>Ending / resolution</h4>${ideaParagraphs(episode.ending)}` : ""}
        ${episode.lesson ? `<h4>Practical lesson</h4><p>${esc(episode.lesson)}</p>` : ""}
        ${support ? `<h4>Supporting cast</h4><p>${esc(support)}</p>` : ""}
        ${episode.continuity_impact ? `<h4>Continuity impact</h4><p>${esc(episode.continuity_impact)}</p>` : ""}
        ${episode.next_hook ? `<h4>Next episode tease</h4><p>${esc(episode.next_hook)}</p>` : ""}
        ${episode.why_it_works ? `<h4>Why it works</h4><p>${esc(episode.why_it_works)}</p>` : ""}
        ${episode.thumbnail_moment ? `<h4>Thumbnail moment</h4><p>${esc(episode.thumbnail_moment)}</p>` : ""}
      </div>
    </details>
    <div class="idea-actions">
      ${isProject
        ? `<button class="btn primary" type="button" data-open-episode="${esc(episode.project_id)}">Open project</button>`
        : `<button class="btn primary" type="button" data-use-episode="${esc(episode.id)}" data-generate="0">Use episode</button>
           <button class="btn" type="button" data-use-episode="${esc(episode.id)}" data-generate="1">Use &amp; write full story</button>`}
    </div>
  </article>`;
}

function renderSeries() {
  if (!S.series) {
    $("seriesHeading").textContent = "Simplify Life";
    $("seriesSub").textContent = "Loading series…";
    $("episodeList").innerHTML = `<div class="idea-empty">Series library is loading.</div>`;
    return;
  }
  initSeriesSettings();
  const bible = S.series.series || {};
  const cast = S.series.cast || [];
  const episodes = S.series.episodes || [];
  const used = episodes.filter((episode) => episode.project_id);
  const ideas = episodes.filter((episode) => !episode.project_id);
  const next = S.series.next_episode_number || (used.length + 1);

  $("seriesHeading").textContent = bible.title || "Simplify Life";
  $("seriesSub").textContent = [bible.tagline, (bible.pillars || []).join(" · ")].filter(Boolean).join(" · ");
  const badge = $("badge-series");
  if (badge) badge.textContent = `EP ${next}`;
  $("seriesStatus").textContent = S.seriesBusy ? (S.seriesBusyMsg || "Working…") : "";
  $("seriesBibleStatus").textContent = "Series memory drives every episode.";
  $("castSummary").textContent = `${cast.length} characters · ${(bible.pillars || []).length} pillars`;
  $("episodeSummary").textContent = `${used.length} episodes · ${ideas.length} ideas · next EP ${next}`;
  $("saveSeries").disabled = S.seriesBusy;
  $("addCastMember").disabled = S.seriesBusy;
  $("generateEpisodes").disabled = S.seriesBusy;

  if (!S.seriesBibleReady) fillSeriesBible();
  renderCast();
  $("episodeList").innerHTML = episodes.length
    ? episodes.map(episodeCard).join("")
    : `<div class="idea-empty">
        <b>No episodes yet.</b><br>
        Pick a pillar (or leave it on Auto) and click <b>Generate 3 episodes</b>. Claude will use the series bible, cast and continuity memory.
      </div>`;
}

async function loadSeriesModels() {
  const provider = $("seriesProvider").value || "opencode-go";
  const base = providerBase(provider);
  try {
    const res = await api(`/api/models?provider=${encodeURIComponent(provider)}&base_url=${encodeURIComponent(base)}`);
    const shown = (res.models || []).length ? res.models : (res.suggestions || []);
    $("seriesModelOptions").innerHTML = shown.map((model) => `<option value="${esc(model)}"></option>`).join("");
    if (res.ok) {
      const keyNote = provider !== "ollama" && S.health && S.health.secrets === false
        ? " · no API key saved"
        : "";
      $("seriesModelHint").textContent = `${shown.length} models · Claude Haiku 5.5 recommended${keyNote}`;
    } else {
      $("seriesModelHint").textContent = `${res.error || "Could not load models"} · Claude Haiku 5.5 still works with a valid key.`;
    }
  } catch (e) {
    $("seriesModelHint").textContent = e.message;
  }
}

async function saveSeries() {
  if (!S.series) return;
  const title = $("seriesTitle").value.trim();
  if (!title) return toast("Series title is required", "error");
  const cast = collectCast();
  if (cast.some((person) => !person.name)) return toast("Every character needs a name", "error");
  setSeriesBusy("Saving series bible and cast…");
  try {
    const res = await api("/api/series", {
      method: "PUT",
      body: {
        ...seriesLlmPayload(),
        series: {
          title,
          title_hi: $("seriesTitleHi").value.trim(),
          tagline: $("seriesTagline").value.trim(),
          premise: $("seriesPremise").value.trim(),
          world: $("seriesWorld").value.trim(),
          tone: $("seriesTone").value.trim(),
          pillars: $("seriesPillars").value.trim(),
          visual_style: $("seriesVisualStyle").value.trim(),
          narrator: $("seriesNarrator").value.trim(),
          narrator_voice_reference: $("seriesNarratorVoice").value.trim(),
          intro: $("seriesIntro").value.trim(),
          outro: $("seriesOutro").value.trim(),
          continuity_rules: $("seriesContinuity").value,
          story_so_far: $("seriesStorySoFar").value,
        },
        cast,
      },
    });
    S.series = res;
    S.seriesBibleReady = false;
    S.castDirty = false;
    renderSeries();
    toast("Series bible and cast saved");
  } catch (e) {
    toast(e.message, "error");
  } finally {
    setSeriesBusy("");
  }
}

function addCastMember() {
  if (!S.series) return;
  S.series.cast = S.series.cast || [];
  S.series.cast.push({
    id: `cast-${Date.now()}`,
    name: "New character",
    name_hi: "",
    age: 30,
    role: "",
    pillar: "Relationships",
    appearance: "",
    wardrobe: "",
    signature_prop: "",
    voice_reference: "",
    speaking_style: "",
    relationships: "",
    face_reference: "",
  });
  S.castDirty = true;
  renderCast(true);
  toast("Character added. Fill the fields and save.");
}

async function generateEpisodes() {
  if (S.seriesBusy || !seriesModelReady()) return;
  if (S.castDirty) return toast("Save the cast first so the episode uses your changes.", "error");
  const pillar = $("episodePillar").value;
  const minutes = Number($("episodeMinutes").value || 10);
  const chapters = Number($("episodeChapters").value || 5);
  setSeriesBusy("Claude is writing 3 continuity-aware episodes…");
  try {
    const res = await api("/api/series/episodes/generate", {
      method: "POST",
      body: { ...seriesLlmPayload(), pillar, minutes, chapters },
    });
    S.series = res.library;
    S.seriesBibleReady = true;
    toast(`${res.episodes.length} episodes ready`);
    setTimeout(() => $("episodeList").scrollIntoView({ behavior: "smooth", block: "start" }), 60);
  } catch (e) {
    toast(e.message, "error");
  } finally {
    setSeriesBusy("");
  }
}

async function openEpisodeProject(pid) {
  S.pid = pid;
  S.data = null;
  await loadProjects();
  showPage("story");
}

async function useEpisode(episodeId, generate) {
  if (S.seriesBusy || !seriesModelReady()) return;
  setSeriesBusy(generate ? "Creating the episode and writing the first draft…" : "Creating the episode project…");
  try {
    const res = await api(`/api/series/episodes/${episodeId}/project`, {
      method: "POST",
      body: { generate, ...seriesLlmPayload() },
    });
    S.pid = res.project_id;
    S.data = null;
    await loadProjects();
    showPage("story");
    if (res.job) startJob({ job: res.job });
    toast(res.existing
      ? "Opening the existing episode project"
      : generate
        ? `Episode project created. Writing the full draft…`
        : "Episode project created. Review the blueprint, then generate the story.");
    await loadSeries();
  } catch (e) {
    toast(e.message, "error");
  } finally {
    setSeriesBusy("");
  }
}

// ---------------------------------------------------------------------------
// Story table / idea lab
// ---------------------------------------------------------------------------

async function loadIdeas() {
  try {
    S.ideas = await api("/api/ideas");
  } catch (e) {
    console.warn(e);
    if (!S.ideas) S.ideas = { genres: [], ideas: [], settings: {} };
  }
  const genres = S.ideas?.genres || [];
  if (!S.selectedGenre) {
    const newest = [...(S.ideas?.ideas || [])].sort((a, b) =>
      String(b.created_at || "").localeCompare(String(a.created_at || ""))
    )[0];
    S.selectedGenre = newest?.genre_id || genres[0]?.id || null;
  }
  if (!genres.some((genre) => genre.id === S.selectedGenre)) {
    S.selectedGenre = genres[0]?.id || null;
  }
  renderIdeas();
}

function initIdeaSettings() {
  if (S.ideaSettingsReady) return;
  const settings = S.ideas?.settings || {};
  if (settings.provider) $("ideaProvider").value = settings.provider;
  if (!$("ideaProvider").value) $("ideaProvider").value = "opencode-go";
  if (settings.model) $("ideaModel").value = settings.model;
  S.ideaSettingsReady = true;
}

function ideaLlmPayload() {
  const provider = $("ideaProvider").value;
  return {
    provider,
    model: $("ideaModel").value.trim(),
    api_base: providerBase(provider),
    temperature: 0.9,
  };
}

function ideaModelReady() {
  if (!$("ideaModel").value.trim()) {
    toast("Choose an ideation model first", "error");
    return false;
  }
  const provider = $("ideaProvider").value;
  if (provider !== "ollama" && S.health && S.health.secrets === false) {
    toast("No API key saved. Add your OpenCode key in Settings.", "error");
    return false;
  }
  return true;
}

function setIdeaBusy(message) {
  S.ideaBusy = !!message;
  S.ideaBusyMsg = message || "";
  renderIdeas();
}

function ideaParagraphs(text) {
  return String(text || "")
    .split(/\n{2,}/)
    .map((part) => `<p>${esc(part).replace(/\n/g, "<br>")}</p>`)
    .join("");
}

function renderIdeas() {
  initIdeaSettings();
  const data = S.ideas || { genres: [], ideas: [], settings: {} };
  const genres = data.genres || [];
  const ideas = data.ideas || [];
  if (!S.selectedGenre || !genres.some((genre) => genre.id === S.selectedGenre)) {
    S.selectedGenre = genres[0]?.id || null;
  }
  const selected = genres.find((genre) => genre.id === S.selectedGenre) || null;
  const selectedIdeas = selected
    ? ideas.filter((idea) => idea.genre_id === selected.id)
    : [];

  $("suggestGenres").disabled = S.ideaBusy;
  $("addGenre").disabled = S.ideaBusy;
  $("generateIdeas").disabled = S.ideaBusy || !selected;
  $("ideasStatus").textContent = S.ideaBusy ? (S.ideaBusyMsg || "Working…") : "";
  $("genreSummary").textContent = genres.length
    ? `${genres.length} channels · ${ideas.length} story ideas · ${ideas.filter((idea) => !idea.project_id).length} ready to pick`
    : "No genres yet.";

  $("genreGrid").innerHTML = genres.length    ? genres.map((genre) => {
        return `<button type="button" class="genre-card ${genre.id === S.selectedGenre ? "selected" : ""}" data-genre-id="${esc(genre.id)}">
          <span class="genre-card-top">
            <span class="genre-name">${esc(genre.name)}</span>
            <span class="genre-source ${genre.source === "user" ? "" : "llm"}">${genre.source === "user" ? "YOURS" : "AI"}</span>
          </span>
          <span class="genre-hi">${esc(genre.name_hi || genre.name)}</span>
          <span class="genre-desc">${esc(genre.description || genre.why_it_works || "Story channel pillar")}</span>
          <span class="genre-meta">${esc(genre.channel_name || "Channel TBD")} · ${genre.idea_count || 0} idea${(genre.idea_count || 0) === 1 ? "" : "s"}</span>
        </button>`;
      }).join("")
    : `<p class="hint">Click <b>Suggest 5 genres</b> to let Claude design five separate channel pillars.</p>`;

  if (!selected) {
    $("selectedGenreName").textContent = "Choose a genre";
    $("selectedGenreMeta").textContent = "Select a genre above to see its story bank.";
    $("genreBrief").innerHTML = "";
    $("ideaList").innerHTML = `<div class="empty-state"><strong>No genre selected</strong>Suggest five genres, then generate three story ideas for the one you want to build.</div>`;
    return;
  }

  const meta = [selected.name_hi, selected.channel_name, selected.audience].filter(Boolean).join(" · ");
  $("selectedGenreName").textContent = selected.name;
  $("selectedGenreMeta").textContent = meta || "Story bank";
  $("genreBrief").innerHTML = `
    <div class="brief-item"><b>Story engines</b>${esc((selected.themes || []).join(" · ") || selected.description || "—")}</div>
    <div class="brief-item"><b>Why listeners stay</b>${esc(selected.why_it_works || selected.description || "—")}</div>
    <div class="brief-item"><b>Audience</b>${esc(selected.audience || "—")}</div>`;

  if (!selectedIdeas.length) {
    $("ideaList").innerHTML = `<div class="idea-empty">
      <b>No story ideas for this genre yet.</b><br>
      Set the target length above and click <b>Generate 3 story ideas</b>. Claude will write three full blueprints with hooks, twists and chapter cliffhangers.
    </div>`;
    return;
  }

  $("ideaList").innerHTML = selectedIdeas.map((idea) => {
    const projectId = String(idea.project_id || "");
    const breaks = (idea.chapter_breaks || []);
    const beats = (idea.retention_beats || []);
    return `<article class="idea-card">
      <div class="idea-head">
        <div>
          <h4 class="idea-title">${esc(idea.title)}</h4>
          <div class="idea-title-en">${esc(idea.title_en || "")}</div>
        </div>
        <div class="idea-badges">
          <span class="review-chip">${idea.minutes || 10} min</span>
          <span class="review-chip">${idea.chapters || 5} chapters</span>
          <span class="idea-status ${projectId ? "project" : ""}">${projectId ? "Project created" : "Idea"}</span>
        </div>
      </div>
      <p class="idea-logline">${esc(idea.logline || "")}</p>
      ${idea.hook ? `<div class="idea-hook"><b>Hook:</b> ${esc(idea.hook)}</div>` : ""}
      <details>
        <summary>Read full plot blueprint</summary>
        <div class="idea-details">
          <h4>Premise</h4>
          ${ideaParagraphs(idea.premise)}
          ${idea.ending ? `<h4>Ending / resolution</h4>${ideaParagraphs(idea.ending)}` : ""}
          ${idea.protagonist ? `<h4>Protagonist</h4><p>${esc(idea.protagonist)}</p>` : ""}
          ${idea.antagonist ? `<h4>Antagonist / obstacle</h4><p>${esc(idea.antagonist)}</p>` : ""}
          ${idea.emotional_arc ? `<h4>Emotional arc</h4><p>${esc(idea.emotional_arc)}</p>` : ""}
          ${beats.length ? `<h4>Retention beats</h4><ul>${beats.map((beat) => `<li>${esc(beat)}</li>`).join("")}</ul>` : ""}
          ${breaks.length ? `<h4>Chapter cliffhangers</h4><ol>${breaks.map((brk) => `<li>${esc(brk)}</li>`).join("")}</ol>` : ""}
          ${idea.why_it_hooks ? `<h4>Why it hooks</h4><p>${esc(idea.why_it_hooks)}</p>` : ""}
          ${idea.thumbnail_moment ? `<h4>Thumbnail moment</h4><p>${esc(idea.thumbnail_moment)}</p>` : ""}
        </div>
      </details>
      <div class="idea-actions">
        ${projectId
          ? `<button class="btn primary" type="button" data-open-project="${esc(projectId)}">Open project</button>`
          : `<button class="btn primary" type="button" data-use-idea="${esc(idea.id)}" data-generate="0">Use this story</button>
             <button class="btn" type="button" data-use-idea="${esc(idea.id)}" data-generate="1">Use &amp; write full story</button>`}
      </div>
    </article>`;
  }).join("");
}

async function loadIdeaModels() {
  const provider = $("ideaProvider").value || "opencode-go";
  const base = providerBase(provider);
  $("ideaModelHint").textContent = "Loading models...";
  try {
    const res = await api(`/api/models?provider=${encodeURIComponent(provider)}&base_url=${encodeURIComponent(base)}`);
    const shown = (res.models || []).length ? res.models : (res.suggestions || []);
    $("ideaModelOptions").innerHTML = shown.map((model) => `<option value="${esc(model)}"></option>`).join("");
    if (res.ok) {
      const keyNote = provider !== "ollama" && S.health && S.health.secrets === false
        ? " · no API key saved"
        : "";
      $("ideaModelHint").textContent = `${shown.length} models · Claude Haiku 5.5 recommended${keyNote}`;
    } else {
      $("ideaModelHint").textContent = `${res.error || "Could not load models"} · Claude Haiku 5.5 still works if your key is valid.`;
    }
  } catch (e) {
    $("ideaModelHint").textContent = e.message;
  }
}

async function suggestGenres() {
  if (S.ideaBusy || !ideaModelReady()) return;
  if ((S.ideas?.ideas || []).length) {
    const ok = window.confirm(
      "Suggest five new genre channels? Genres that already have story ideas are kept; unused AI genres are replaced."
    );
    if (!ok) return;
  }
  setIdeaBusy("Claude is designing 5 channel-ready genres…");
  try {
    const data = await api("/api/ideas/genres/suggest", {
      method: "POST",
      body: ideaLlmPayload(),
    });
    S.ideas = data;
    if (!data.genres.some((genre) => genre.id === S.selectedGenre)) {
      S.selectedGenre = data.genres[0]?.id || null;
    }
    toast("Five genre channels are ready");
  } catch (e) {
    toast(e.message, "error");
  } finally {
    setIdeaBusy("");
  }
}

async function addGenre() {
  if (S.ideaBusy) return;
  const name = $("newGenreName").value.trim();
  if (!name) return toast("Genre name is required", "error");
  setIdeaBusy("Saving your genre…");
  try {
    const data = await api("/api/ideas/genres", {
      method: "POST",
      body: {
        name,
        name_hi: $("newGenreNameHi").value.trim(),
        description: $("newGenreDesc").value.trim(),
        why_it_works: $("newGenreWhy").value.trim(),
        audience: $("newGenreAudience").value.trim(),
        tone: $("newGenreTone").value.trim(),
        channel_name: $("newGenreChannel").value.trim(),
        channel_tagline: $("newGenreTagline").value.trim(),
        themes: $("newGenreThemes").value.trim(),
      },
    });
    S.ideas = data;
    const created = data.genres.find(
      (genre) => genre.source === "user" && genre.name.toLowerCase() === name.toLowerCase()
    );
    if (created) S.selectedGenre = created.id;
    ["newGenreName", "newGenreNameHi", "newGenreDesc", "newGenreWhy", "newGenreAudience", "newGenreTone",
     "newGenreChannel", "newGenreTagline", "newGenreThemes"].forEach((id) => { $(id).value = ""; });
    toast("Genre saved");
  } catch (e) {
    toast(e.message, "error");
  } finally {
    setIdeaBusy("");
  }
}

async function generateGenreIdeas() {
  if (S.ideaBusy || !S.selectedGenre || !ideaModelReady()) return;
  const minutes = Number($("ideaMinutes").value || 10);
  const chapters = Number($("ideaChapters").value || 5);
  setIdeaBusy("Claude is writing 3 plot blueprints…");
  try {
    const res = await api(`/api/ideas/genres/${S.selectedGenre}/ideas`, {
      method: "POST",
      body: { ...ideaLlmPayload(), minutes, chapters },
    });
    S.ideas = res.library;
    toast(`${res.ideas.length} story ideas ready`);
    setTimeout(() => $("genreWorkspace").scrollIntoView({ behavior: "smooth", block: "start" }), 60);
  } catch (e) {
    toast(e.message, "error");
  } finally {
    setIdeaBusy("");
  }
}

async function openIdeaProject(pid) {
  S.pid = pid;
  S.data = null;
  await loadProjects();
  showPage("story");
}

async function useIdea(ideaId, generate) {
  if (S.ideaBusy || !ideaModelReady()) return;
  setIdeaBusy(generate ? "Creating the project and starting the first draft…" : "Creating the project…");
  try {
    const res = await api(`/api/ideas/${ideaId}/project`, {
      method: "POST",
      body: { generate, ...ideaLlmPayload() },
    });
    S.pid = res.project_id;
    S.data = null;
    await loadProjects();
    showPage("story");
    if (res.job) startJob({ job: res.job });
    toast(res.existing
      ? "Opening the existing project"
      : generate
        ? "Project created. Writing the full story with Claude Haiku 5.5…"
        : "Project created. Review the blueprint, then generate the story.");
    await loadIdeas();
  } catch (e) {
    toast(e.message, "error");
  } finally {
    setIdeaBusy("");
  }
}

// ---------------------------------------------------------------------------
// Story
// ---------------------------------------------------------------------------

function renderStory() {
  const st = stage("story");
  $("storyStatus").textContent = statusText(st.status);
  $("storyStatus").className = `status ${statusClass(st.status)}`;

  const text = S.data.story || "";
  if (!S.storyDirty && document.activeElement !== $("storyText")) {
    $("storyText").value = text;
  }
  $("storyWords").textContent = `${text.trim() ? text.trim().split(/\s+/).length : 0} words`;
  renderChecks("storyChecks", S.data.story_validation, "storyScore");

  if (document.activeElement !== $("storyModel")) $("storyModel").value = S.data.state.settings.llm.model || "";
  if (!S.topicDirty && document.activeElement !== $("storyTopic")) {
    $("storyTopic").value = S.data.state.settings.story_topic || "";
  }
  if (!S.instructionsDirty && document.activeElement !== $("storyInstructions")) {
    $("storyInstructions").value = S.data.state.settings.story_instructions || "";
  }
  if (document.activeElement !== $("storyMinutes")) $("storyMinutes").value = S.data.state.settings.story_minutes || 5;
  if (document.activeElement !== $("storyChapters")) $("storyChapters").value = S.data.state.settings.story_chapters || 5;
  const provider = S.data.state.settings.llm.provider || "ollama";
  if (document.activeElement !== $("llmProvider")) $("llmProvider").value = provider;
  const temp = Number(S.data.state.settings.llm.temperature ?? 0.85);
  if (document.activeElement !== $("storyTemp")) {
    $("storyTemp").value = temp;
    $("storyTempVal").textContent = temp.toFixed(2);
  }
  $("storyModel").placeholder = provider === "ollama"
    ? "aya-expanse:8b"
    : (PROVIDER_MODEL_HINTS[provider] || "model ID");
  updateStoryPlanHint();
}

function renderChecks(targetId, validation, scoreId = null) {
  const el = $(targetId);
  if (!validation) {
    el.innerHTML = `<div class="check"><span class="check-icon">–</span><div>No checks yet.</div></div>`;
    if (scoreId) $(scoreId).textContent = "";
    return;
  }
  if (scoreId) $(scoreId).textContent = `Score ${validation.score}/100`;
  const icons = { pass: "✓", warn: "!", fail: "✕" };
  el.innerHTML = (validation.checks || []).map((c) =>
    `<div class="check ${c.status}"><span class="check-icon">${icons[c.status] || "·"}</span>` +
    `<div><div class="check-label-text">${esc(c.label)}</div><div class="check-detail">${esc(c.detail)}</div></div></div>`
  ).join("");
}

async function generateStory() {
  const topic = $("storyTopic").value.trim();
  if (!topic) return toast("Enter a topic first", "error");
  const provider = $("llmProvider").value;
  if (provider !== "ollama" && !$("storyModel").value.trim()) {
    return toast("Choose a model for this provider", "error");
  }
  S.storyDirty = false;
  try {
    const res = await api(`/api/projects/${S.pid}/story/generate`, {
      method: "POST",
      body: {
        topic,
        minutes: Number($("storyMinutes").value || 5),
        chapters: Number($("storyChapters").value || 5),
        instructions: $("storyInstructions").value.trim(),
        provider,
        model: $("storyModel").value.trim(),
        api_base: providerBase(provider),
        temperature: Number($("storyTemp").value || 0.85),
      },
    });
    startJob(res);
    S.topicDirty = false;
    S.instructionsDirty = false;
    toast("Story generation started");
  } catch (e) { toast(e.message, "error"); }
}

async function saveStory() {
  try {
    const res = await api(`/api/projects/${S.pid}/story`, {
      method: "PUT",
      body: { text: $("storyText").value },
    });
    S.storyDirty = false;
    toast("Story draft saved");
    await loadProject();
    renderChecks("storyChecks", res.validation, "storyScore");
  } catch (e) { toast(e.message, "error"); }
}

async function approveStory() {
  try {
    await api(`/api/projects/${S.pid}/story/approve`, { method: "POST" });
    toast("Story approved");
    await loadProject();
  } catch (e) {
    if (e.detail?.validation) renderChecks("storyChecks", e.detail.validation, "storyScore");
    toast(e.message, "error");
  }
}

async function requestStoryChanges() {
  const notes = window.prompt("What needs to change?", "");
  if (notes === null) return;
  try {
    await api(`/api/projects/${S.pid}/story/request-changes`, {
      method: "POST", body: { notes },
    });
    toast("Changes requested");
    await loadProject();
  } catch (e) { toast(e.message, "error"); }
}

// ---------------------------------------------------------------------------
// Scenes
// ---------------------------------------------------------------------------

function renderScenes() {
  const scenes = S.data.scenes || [];
  const status = S.data.scene_status || [];
  const totalWords = scenes.reduce((n, s) => n + String(s.narration || "").split(/\s+/).filter(Boolean).length, 0);
  const est = totalWords / 2.4;
  $("sceneStats").innerHTML = [
    ["Scenes", scenes.length],
    ["Words", totalWords],
    ["Est. runtime", fmtMinutes(est)],
    ["Images", status.filter((s) => s.image).length],
    ["Voice clips", status.filter((s) => s.audio).length],
  ].map(([label, value]) => `<div class="stat"><div class="stat-value">${value}</div><div class="stat-label">${label}</div></div>`).join("");
  renderChecks("sceneChecks", S.data.scenes_validation);
  renderSceneList();
}

function renderSceneList() {
  const filter = ($("sceneFilter")?.value || "").toLowerCase();
  const scenes = (S.data.scenes || []).filter((s) =>
    !filter || `${s.id} ${s.narration} ${s.image_prompt} ${s.mood}`.toLowerCase().includes(filter)
  );
  $("sceneFilterCount").textContent = filter ? `${scenes.length} matching` : "";
  if (!scenes.length) {
    $("sceneList").innerHTML = `<div class="empty-state"><strong>No scene plan yet</strong>Generate the scene plan from the approved story, or add a scene manually.</div>`;
    return;
  }
  const status = Object.fromEntries((S.data.scene_status || []).map((s) => [s.id, s]));
  const cameras = ["slow push in", "slow pull back", "slow pan left", "slow pan right"];
  $("sceneList").innerHTML = scenes.map((scene) => {
    const st = status[scene.id] || {};
    return `<article class="scene-card" data-id="${scene.id}">
      <div class="scene-top">
        <span class="scene-id">SCENE ${String(scene.id).padStart(2, "0")}</span>
        <span class="scene-assets">
          <span class="${st.image ? "yes" : ""}">${st.image ? "🖼 image" : "no image"}</span>
          <span class="${st.audio ? "yes" : ""}">${st.audio ? "🔊 voice" : "no voice"}</span>
          ${st.duration ? `<span>${st.duration.toFixed(1)}s</span>` : ""}
        </span>
      </div>
      <label>Narration <textarea data-field="narration" rows="3">${esc(scene.narration)}</textarea></label>
      <label>English image prompt <textarea data-field="image_prompt" rows="2">${esc(scene.image_prompt)}</textarea></label>
      <div class="row wrap">
        <label>Camera
          <select data-field="camera">${cameras.map((c) => `<option value="${c}" ${scene.camera === c ? "selected" : ""}>${c}</option>`).join("")}</select>
        </label>
        <label>Mood <input data-field="mood" type="text" value="${esc(scene.mood)}"></label>
        <div class="scene-tools"><button class="btn ghost small" data-use-scene="${scene.id}">Use in Sample Studio →</button></div>
      </div>
    </article>`;
  }).join("");
}

function collectScenes() {
  const byId = Object.fromEntries((S.data.scenes || []).map((s) => [s.id, s]));
  $$(".scene-card").forEach((card) => {
    const get = (field) => card.querySelector(`[data-field="${field}"]`)?.value ?? "";
    const id = Number(card.dataset.id);
    byId[id] = {
      ...(byId[id] || {}),
      id,
      chapter: byId[id]?.chapter ?? 0,
      narration: get("narration"),
      image_prompt: get("image_prompt"),
      camera: get("camera"),
      mood: get("mood"),
    };
  });
  return (S.data.scenes || []).map((s) => byId[s.id]).filter(Boolean);
}

async function generateScenes() {
  if (!S.data.story) return toast("Generate or write the story first", "error");
  const provider = $("llmProvider").value;
  S.sceneDirty = false;
  try {
    const res = await api(`/api/projects/${S.pid}/scenes/generate`, {
      method: "POST",
      body: {
        target_words: Number($("sceneTargetWords").value || 24),
        batch_size: Number($("sceneBatch").value || 12),
        provider,
        model: $("storyModel").value.trim(),
        api_base: providerBase(provider),
      },
    });
    startJob(res);
    toast("Scene generation started");
  } catch (e) { toast(e.message, "error"); }
}

async function repairPrompts() {
  if (!S.data.scenes?.length) return toast("Generate the scene plan first", "error");
  const provider = $("llmProvider").value;
  try {
    const res = await api(`/api/projects/${S.pid}/scenes/repair-prompts`, {
      method: "POST",
      body: {
        provider,
        model: $("storyModel").value.trim(),
        api_base: providerBase(provider),
      },
    });
    startJob(res);
    toast("Repairing image prompts");
  } catch (e) { toast(e.message, "error"); }
}

async function restylePrompts() {
  if (!S.data.scenes?.length) return toast("Generate the scene plan first", "error");
  const provider = $("llmProvider").value;
  try {
    const res = await api(`/api/projects/${S.pid}/scenes/restyle-prompts`, {
      method: "POST",
      body: {
        provider,
        model: $("storyModel").value.trim(),
        api_base: providerBase(provider),
      },
    });
    startJob(res);
    toast("Rewriting scene prompts for the current style");
  } catch (e) { toast(e.message, "error"); }
}

async function saveScenes() {
  try {
    const scenes = collectScenes();
    const res = await api(`/api/projects/${S.pid}/scenes`, {
      method: "PUT", body: { scenes },
    });
    S.sceneDirty = false;
    toast("Scene plan saved");
    await loadProject();
    renderChecks("sceneChecks", res.validation);
  } catch (e) { toast(e.message, "error"); }
}

async function approveScenes() {
  try {
    await api(`/api/projects/${S.pid}/scenes/approve`, { method: "POST" });
    toast("Scene plan approved");
    await loadProject();
  } catch (e) {
    if (e.detail?.validation) renderChecks("sceneChecks", e.detail.validation);
    toast(e.message, "error");
  }
}

function addScene() {
  const scenes = collectScenes();
  scenes.push({
    id: (scenes.at(-1)?.id || 0) + 1,
    chapter: 0,
    narration: "",
    image_prompt: "Indian middle-class setting, cinematic flat vector illustration, emotional storytelling scene",
    camera: "slow push in",
    mood: "emotional",
  });
  S.data.scenes = scenes;
  S.sceneDirty = true;
  renderSceneList();
}

function useScene(id) {
  if (S.sceneDirty) {
    S.data.scenes = collectScenes();
    S.sceneDirty = false;
  }
  S.selectedScene = Number(id);
  const scene = (S.data.scenes || []).find((s) => s.id === S.selectedScene);
  showPage("samples");
  populateSceneSelects();
  for (const select of ["voiceScene", "imageScene", "clipScene"]) {
    $(select).value = String(S.selectedScene);
  }
  if (scene) $("voiceText").value = scene.narration || "";
  renderSampleMedia();
  toast(`Scene ${id} selected in Sample Studio`);
}

// ---------------------------------------------------------------------------
// Samples
// ---------------------------------------------------------------------------

function populateSceneSelects() {
  const scenes = S.data.scenes || [];
  const options = scenes.map((s) =>
    `<option value="${s.id}">Scene ${String(s.id).padStart(2, "0")} · ${esc(String(s.narration || "").slice(0, 48))}${String(s.narration || "").length > 48 ? "…" : ""}</option>`
  ).join("");
  for (const id of ["voiceScene", "imageScene", "clipScene"]) {
    const select = $(id);
    const current = Number(select.value || S.selectedScene);
    select.innerHTML = options || `<option value="1">No scenes yet</option>`;
    if (scenes.some((s) => s.id === current)) select.value = String(current);
    else if (scenes.length) select.value = String(scenes[0].id);
  }
}

function syncSampleScene() {
  populateSceneSelects();
  const id = Number($("voiceScene").value || S.selectedScene || 1);
  S.selectedScene = id;
  $("imageScene").value = String(id);
  $("clipScene").value = String(id);
  renderSampleMedia();
}

function renderSamples() {
  const settings = S.data.state.settings;
  const voice = stage("samples.voice");
  const image = stage("samples.image");
  const music = stage("samples.music");
  const clip = stage("samples.clip");

  populateSceneSelects();
  const sceneId = Number($("voiceScene").value || S.selectedScene || 1);
  const scene = (S.data.scenes || []).find((s) => s.id === sceneId);
  if (scene && !$("voiceText").value.trim()) $("voiceText").value = scene.narration || "";

  if (document.activeElement !== $("voiceExag")) $("voiceExag").value = settings.tts.exaggeration ?? 0.5;
  if (document.activeElement !== $("voiceCfg")) $("voiceCfg").value = settings.tts.cfg_weight ?? 0.3;
  if (document.activeElement !== $("voiceTemp")) $("voiceTemp").value = settings.tts.temperature ?? 0.8;
  if (document.activeElement !== $("voiceRef")) $("voiceRef").value = settings.tts.reference || "";
  if (document.activeElement !== $("musicPrompt")) $("musicPrompt").value = settings.music.prompt || "";
  if (document.activeElement !== $("musicDuration")) $("musicDuration").value = settings.music.duration ?? 60;
  if (document.activeElement !== $("musicBpm")) $("musicBpm").value = settings.music.bpm ?? 78;
  if (document.activeElement !== $("musicKey")) $("musicKey").value = settings.music.key || "C minor";
  if (document.activeElement !== $("imageEngine")) $("imageEngine").value = settings.image.engine || "sdxl";

  setSampleStatus("sampleVoiceStatus", voice.status);
  setSampleStatus("sampleImageStatus", image.status);
  setSampleStatus("sampleMusicStatus", music.status);
  setSampleStatus("sampleClipStatus", clip.status);
  const musicEnabled = settings.music.enabled !== false;
  $("musicDisabledHint").classList.toggle("hidden", musicEnabled);
  if (!musicEnabled && !music.status) setSampleStatus("sampleMusicStatus", "disabled");
  renderChecks("voiceChecks", voice.validation);
  const normalizedText = voice.normalized_text || S.voicePreviewText;
  if (normalizedText) {
    $("voiceNormalized").textContent = normalizedText;
    $("voiceNormalizedWrap").classList.remove("hidden");
  } else {
    $("voiceNormalized").textContent = "";
    $("voiceNormalizedWrap").classList.add("hidden");
  }
  renderChecks("imageChecks", image.validation);
  renderChecks("musicChecks", music.validation);
  renderChecks("clipChecks", clip.validation);
  renderSampleMedia();
  updateRangeLabels();
}

function setSampleStatus(id, status) {
  const el = $(id);
  el.textContent = statusText(status);
  el.className = `status ${statusClass(status)}`;
}

function renderSampleMedia() {
  const voice = S.data.samples?.voice;
  const image = S.data.samples?.image;
  const music = S.data.samples?.music;
  const clip = S.data.samples?.clip;

  const statusById = Object.fromEntries((S.data.scene_status || []).map((s) => [s.id, s]));
  const sceneFile = (sceneId, dir, ext) =>
    `/api/projects/${S.pid}/media/${dir}/scene_${String(sceneId).padStart(3, "0")}.${ext}`;
  const voiceSceneId = Number($("voiceScene")?.value || 1);
  const imageSceneId = Number($("imageScene")?.value || 1);
  const voiceSt = statusById[voiceSceneId] || {};
  const imageSt = statusById[imageSceneId] || {};

  // Imported projects have approved stages but no saved sample file: fall back
  // to the real project assets for the currently selected scene.
  toggleMedia("voiceAudio", voice?.url || (voiceSt.audio ? sceneFile(voiceSceneId, "audio", "wav") : ""));
  toggleMedia("musicAudio", music?.url || S.data.project_audio?.music || "");
  toggleMedia("clipVideo", clip?.url);

  const img = $("imagePreview");
  const imageUrl = image?.url || (imageSt.image ? sceneFile(imageSceneId, "images", "png") : "");
  if (imageUrl) {
    if (img.getAttribute("src") !== imageUrl) img.src = imageUrl;
    img.classList.remove("hidden");
  } else {
    img.removeAttribute("src");
    img.classList.add("hidden");
  }
}

function toggleMedia(id, url) {
  const el = $(id);
  if (url) {
    // Avoid resetting playback when an unrelated re-render happens.
    if (el.getAttribute("src") !== url) el.src = url;
    el.classList.remove("hidden");
  } else {
    if (el.hasAttribute("src")) {
      el.pause?.();
      el.removeAttribute("src");
      el.load?.();
    }
    el.classList.add("hidden");
  }
}

function showNormalizedText(text) {
  $("voiceNormalized").textContent = text;
  $("voiceNormalizedWrap").classList.remove("hidden");
  $("voiceNormalizedWrap").open = true;
}

async function previewVoiceText() {
  const text = $("voiceText").value.trim();
  if (!text) return toast("Voice text is empty", "error");
  try {
    const res = await api(`/api/projects/${S.pid}/tts/normalize`, {
      method: "POST", body: { text },
    });
    S.voicePreviewText = res.text;
    showNormalizedText(res.text);
    toast("Spoken text updated");
  } catch (e) { toast(e.message, "error"); }
}

async function generateVoice() {
  const text = $("voiceText").value.trim();
  if (!text) return toast("Voice text is empty", "error");
  try {
    const res = await api(`/api/projects/${S.pid}/samples/voice`, {
      method: "POST",
      body: {
        text,
        scene_id: Number($("voiceScene").value || S.selectedScene),
        overrides: {
          exaggeration: Number($("voiceExag").value),
          cfg_weight: Number($("voiceCfg").value),
          temperature: Number($("voiceTemp").value),
          reference: $("voiceRef").value.trim(),
        },
      },
    });
    startJob(res);
    toast("Voice sample started");
  } catch (e) { toast(e.message, "error"); }
}

async function generateImage() {
  try {
    const res = await api(`/api/projects/${S.pid}/samples/image`, {
      method: "POST",
      body: {
        scene_id: Number($("imageScene").value || S.selectedScene),
        engine: $("imageEngine").value,
        seed: Number($("imageSeed").value || 0),
      },
    });
    startJob(res);
    toast("Image sample started");
  } catch (e) { toast(e.message, "error"); }
}

async function generateMusic() {
  try {
    const res = await api(`/api/projects/${S.pid}/samples/music`, {
      method: "POST",
      body: {
        prompt: $("musicPrompt").value.trim(),
        duration: Number($("musicDuration").value || 60),
        bpm: Number($("musicBpm").value || 78),
        key: $("musicKey").value.trim() || "C minor",
      },
    });
    startJob(res);
    toast("Music sample started");
  } catch (e) { toast(e.message, "error"); }
}

async function generateClip() {
  try {
    const res = await api(`/api/projects/${S.pid}/samples/clip`, {
      method: "POST",
      body: {
        scene_id: Number($("clipScene").value || S.selectedScene),
        subtitles: $("clipSubtitles").checked,
        with_music: $("clipMusic").checked,
      },
    });
    startJob(res);
    toast("Preview clip started");
  } catch (e) { toast(e.message, "error"); }
}

async function approveSample(kind) {
  try {
    await api(`/api/projects/${S.pid}/samples/${kind}/approve`, { method: "POST" });
    toast(`${kind} sample approved`);
    await loadProject();
  } catch (e) {
    if (e.detail?.validation) {
      const map = { voice: "voiceChecks", image: "imageChecks", music: "musicChecks", clip: "clipChecks" };
      renderChecks(map[kind], e.detail.validation);
    }
    toast(e.message, "error");
  }
}

async function rejectSample(kind) {
  const notes = window.prompt(`Why reject the ${kind} sample?`, "");
  if (notes === null) return;
  try {
    await api(`/api/projects/${S.pid}/samples/${kind}/reject`, {
      method: "POST", body: { notes },
    });
    toast(`${kind} sample rejected`);
    await loadProject();
  } catch (e) { toast(e.message, "error"); }
}

function updateRangeLabels() {
  $("voiceExagVal").textContent = Number($("voiceExag").value).toFixed(2);
  $("voiceCfgVal").textContent = Number($("voiceCfg").value).toFixed(2);
  $("voiceTempVal").textContent = Number($("voiceTemp").value).toFixed(2);
  $("storyTempVal").textContent = Number($("storyTemp").value).toFixed(2);
}

function updateStoryPlanHint() {
  const minutes = Number($("storyMinutes").value || 5);
  const chapters = Math.max(1, Number($("storyChapters").value || 5));
  const target = Math.round(minutes * 130);
  const perChapter = Math.round(target / chapters);
  const el = $("storyPlanHint");
  if (!el) return;
  if (!minutes) {
    el.textContent = "";
    return;
  }
  el.textContent =
    `~${target} words total, ~${perChapter} words per chapter.` +
    (perChapter > 2600 ? " Add more chapters so local models do not truncate." : "");
  el.style.color = perChapter > 2600 ? "var(--amber)" : "";
}

// ---------------------------------------------------------------------------
// Production
// ---------------------------------------------------------------------------

function renderProduction() {
  const gates = S.data.gates?.gates || {};
  const musicEnabled = S.data.state.settings.music.enabled !== false;
  const labels = {
    story: "Story approved",
    scenes: "Scene plan approved",
    voice: "Voice sample approved",
    image: "Image sample approved",
    music: musicEnabled ? "Music sample approved" : "Music disabled (optional)",
    clip: "Preview clip approved",
  };
  $("productionGates").innerHTML =
    `<div class="card-head"><h3>Approval gates</h3><span class="hint">${S.data.gates?.ok ? "Ready for batch" : "Approve every gate before batch generation"}</span></div>` +
    `<div class="gate-list">${Object.entries(labels).map(([key, label]) =>
      `<div class="gate ${gates[key] ? "on" : ""}"><span class="gate-check">${gates[key] ? "✓" : ""}</span><span>${label}</span></div>`
    ).join("")}</div>`;
  $("startProduction").disabled = !S.data.gates?.ok || !!S.data.active_job;
  $("prodMusic").disabled = !musicEnabled;
  if (!musicEnabled) $("prodMusic").checked = false;

  const status = S.data.scene_status || [];
  const currentReview = currentReviewScene();
  $("sceneAssetSummary").textContent =
    `${status.filter((s) => s.image).length}/${status.length} images · ${status.filter((s) => s.audio).length}/${status.length} voice`;
  $("sceneStatusTable").querySelector("tbody").innerHTML = status.map((s) =>
    `<tr class="review-row ${s.id === currentReview?.id ? "selected" : ""}" data-review="${s.id}">
      <td class="mono">${String(s.id).padStart(2, "0")}</td>
      <td>${s.words}</td>
      <td class="${s.image ? "ok" : "no"}">${s.image ? "ready" : "missing"}</td>
      <td class="${s.audio ? "ok" : "no"}">${s.audio ? "ready" : "missing"}</td>
      <td>${s.duration ? `${s.duration.toFixed(1)}s` : "—"}</td>
      <td>
        <button class="btn ghost small" data-review="${s.id}">Review</button>
        <button class="btn ghost small" data-retry="image" data-scene="${s.id}" title="Regenerate image">↻ Image</button>
        <button class="btn ghost small" data-retry="voice" data-scene="${s.id}" title="Regenerate voice">↻ Voice</button>
      </td>
    </tr>`
  ).join("") || `<tr><td colspan="6">No scenes yet.</td></tr>`;

  renderSceneReview();
  renderJobPanel();
}

function renderJobPanel() {
  const job = S.job;
  const pct = job ? Number(job.progress || 0) : 0;
  $("prodBar").style.width = `${pct}%`;
  $("prodPct").textContent = job ? `${job.kind} · ${pct}% · ${job.status}` : "idle";
  $("prodLog").textContent = job?.logs?.length ? job.logs.join("\n") : (job ? job.message : "No job running.");
}

// ---------------------------------------------------------------------------
// Scene review
// ---------------------------------------------------------------------------

function currentReviewScene() {
  const scenes = S.data?.scenes || [];
  if (!scenes.length) return null;
  if (!S.reviewScene || !scenes.some((s) => s.id === S.reviewScene)) {
    S.reviewScene = scenes[0].id;
  }
  return scenes.find((s) => s.id === S.reviewScene) || scenes[0];
}

function reviewStatusFor(id) {
  return (S.data?.scene_status || []).find((s) => s.id === id) || {};
}

function renderSceneReview() {
  const scenes = S.data?.scenes || [];
  const scene = currentReviewScene();
  const busy = !!S.data?.active_job;
  const plan = stageStatus("scenes");

  if (!scene) {
    $("reviewSceneLabel").textContent = "No scenes";
    $("reviewStatusChips").innerHTML = "";
    $("reviewImage").classList.add("hidden");
    $("reviewImageEmpty").classList.remove("hidden");
    $("reviewImageLink").removeAttribute("href");
    $("reviewAudioRow").classList.add("hidden");
    $("reviewAudioEmpty").classList.remove("hidden");
    $("reviewNarration").value = "";
    $("reviewPrompt").value = "";
    $("reviewDirty").classList.add("hidden");
    $("reviewPlanState").textContent = "Generate a scene plan first.";
    $("reviewPrev").disabled = $("reviewNext").disabled = true;
    $("reviewSave").disabled = $("reviewApprove").disabled = true;
    $("reviewRegenVoice").disabled = $("reviewRegenImage").disabled = true;
    $("reviewJump").value = 1;
    S.reviewRenderedScene = null;
    S.reviewDirty = false;
    return;
  }

  const keepEdits = S.reviewDirty && S.reviewRenderedScene === scene.id;
  const st = reviewStatusFor(scene.id);
  const chapter = scene.chapter ? ` · Chapter ${scene.chapter}` : "";
  $("reviewSceneLabel").textContent = `Scene ${scene.id} / ${scenes.length}${chapter}`;
  $("reviewStatusChips").innerHTML = `
    <span class="review-chip ${st.image ? "on" : "off"}">${st.image ? "image ready" : "no image"}</span>
    <span class="review-chip ${st.audio ? "on" : "off"}">${st.audio ? "voice ready" : "no voice"}</span>
    <span class="review-chip">${st.words || 0} words</span>
    ${st.duration ? `<span class="review-chip">${st.duration.toFixed(1)}s</span>` : ""}`;

  const image = $("reviewImage");
  const imageLink = $("reviewImageLink");
  if (st.image_url) {
    if (image.getAttribute("src") !== st.image_url) image.src = st.image_url;
    image.alt = `Scene ${scene.id} image`;
    image.classList.remove("hidden");
    $("reviewImageEmpty").classList.add("hidden");
    imageLink.href = st.image_url;
    imageLink.style.pointerEvents = "";
    $("reviewImageName").textContent = `scene_${String(scene.id).padStart(3, "0")}.png`;
  } else {
    image.removeAttribute("src");
    image.classList.add("hidden");
    $("reviewImageEmpty").classList.remove("hidden");
    imageLink.removeAttribute("href");
    imageLink.style.pointerEvents = "none";
    $("reviewImageName").textContent = "";
  }

  const audio = $("reviewAudio");
  if (st.audio_url) {
    $("reviewAudioRow").classList.remove("hidden");
    $("reviewAudioEmpty").classList.add("hidden");
    if (audio.dataset.url !== st.audio_url) {
      audio.dataset.url = st.audio_url;
      audio.src = st.audio_url;
      audio.load();
    }
  } else {
    audio.pause();
    audio.removeAttribute("src");
    delete audio.dataset.url;
    audio.load();
    $("reviewAudioRow").classList.add("hidden");
    $("reviewAudioEmpty").classList.remove("hidden");
  }

  if (!keepEdits) {
    $("reviewNarration").value = scene.narration || "";
    $("reviewPrompt").value = scene.image_prompt || "";
    $("reviewDirty").classList.add("hidden");
    S.reviewDirty = false;
  } else {
    $("reviewDirty").classList.remove("hidden");
  }
  S.reviewRenderedScene = scene.id;

  $("reviewJump").max = Math.max(...scenes.map((s) => s.id));
  $("reviewJump").value = scene.id;
  $("reviewPrev").disabled = scenes[0].id === scene.id;
  $("reviewNext").disabled = scenes.at(-1).id === scene.id;
  $("reviewSave").disabled = busy;
  $("reviewRegenVoice").disabled = busy;
  $("reviewRegenImage").disabled = busy;
  $("reviewApprove").disabled = busy || plan === "approved" || S.reviewDirty;

  $("reviewPlanState").textContent = plan === "approved"
    ? "Scene plan is approved. Review the assets, then assemble."
    : `Scene plan is ${statusText(plan).toLowerCase()}. Click Approve plan once the script is final.`;

  if (S.reviewPlayAfterLoad && st.audio_url) {
    S.reviewPlayAfterLoad = false;
    audio.play().catch(() => {});
  }
}

function updateReviewDirty() {
  const scene = currentReviewScene();
  if (!scene) return false;
  const dirty =
    $("reviewNarration").value !== (scene.narration || "") ||
    $("reviewPrompt").value !== (scene.image_prompt || "");
  S.reviewDirty = dirty;
  $("reviewDirty").classList.toggle("hidden", !dirty);
  const plan = stageStatus("scenes");
  $("reviewApprove").disabled = !!S.data?.active_job || plan === "approved" || dirty;
  return dirty;
}

function pickReviewScene(id, { force = false } = {}) {
  if (S.reviewDirty && !force && !window.confirm("Discard unsaved changes in this scene?")) {
    return false;
  }
  S.reviewScene = Number(id);
  S.reviewDirty = false;
  renderSceneReview();
  $$("#sceneStatusTable tr[data-review]").forEach((row) => {
    row.classList.toggle("selected", Number(row.dataset.review) === S.reviewScene);
  });
  return true;
}

function stepReview(delta) {
  const scenes = S.data?.scenes || [];
  const index = scenes.findIndex((s) => s.id === S.reviewScene);
  const next = scenes[index + delta];
  if (next) pickReviewScene(next.id);
}

function jumpReviewScene() {
  const scenes = S.data?.scenes || [];
  if (!scenes.length) return;
  const raw = Number($("reviewJump").value);
  const target = scenes.find((s) => s.id === raw) || scenes[Math.max(0, Math.min(scenes.length - 1, raw - 1))];
  if (target) pickReviewScene(target.id);
}

function playReviewAudio() {
  const audio = $("reviewAudio");
  if (audio.getAttribute("src")) audio.play().catch(() => {});
}

async function saveSceneReview({ silent = false } = {}) {
  const scene = currentReviewScene();
  if (!scene) return false;
  const narration = $("reviewNarration").value.trim();
  const imagePrompt = $("reviewPrompt").value.trim();
  if (!narration) {
    toast("Script cannot be empty", "error");
    return false;
  }
  if (!imagePrompt) {
    toast("Image prompt cannot be empty", "error");
    return false;
  }
  if (!updateReviewDirty()) {
    if (!silent) toast("No changes to save");
    return true;
  }
  const narrationChanged = narration !== (scene.narration || "");
  try {
    await api(`/api/projects/${S.pid}/scenes/${scene.id}`, {
      method: "PUT",
      body: { narration, image_prompt: imagePrompt },
    });
    S.reviewDirty = false;
    await loadProject();
    if (!silent) {
      toast(narrationChanged
        ? `Scene ${scene.id} saved — regenerate its voice to hear the new script`
        : `Scene ${scene.id} saved`);
    }
    return true;
  } catch (e) {
    toast(e.message, "error");
    return false;
  }
}

async function approveScenePlan() {
  if (S.reviewDirty) return toast("Save this scene before approving the plan", "error");
  try {
    await api(`/api/projects/${S.pid}/scenes/approve`, { method: "POST" });
    toast("Scene plan approved");
    await loadProject();
  } catch (e) {
    const failed = e.detail?.validation?.checks?.filter((c) => c.status === "fail") || [];
    toast(failed.length
      ? `Cannot approve: ${failed.map((c) => c.label).join(", ")}`
      : e.message, "error");
  }
}

async function regenerateReview(kind) {
  const scene = currentReviewScene();
  if (!scene) return;
  if (S.reviewDirty && !(await saveSceneReview({ silent: true }))) return;
  try {
    const res = await api(`/api/projects/${S.pid}/production/retry`, {
      method: "POST",
      body: { scene_id: scene.id, kind },
    });
    if (kind === "voice") S.reviewPlayAfterLoad = true;
    startJob(res);
    toast(kind === "voice"
      ? `Voice regeneration started for scene ${scene.id}`
      : `New image variation started for scene ${scene.id}`);
  } catch (e) {
    toast(e.message, "error");
  }
}

async function startProduction() {
  if (S.reviewDirty) {
    toast("Save or discard your scene changes before starting production", "error");
    showPage("production");
    return;
  }
  const stages = [];
  const musicEnabled = S.data.state.settings.music.enabled !== false;
  if ($("prodImages").checked) stages.push("images");
  if ($("prodMusic").checked && musicEnabled) stages.push("music");
  if ($("prodTts").checked) stages.push("tts");
  if ($("prodAssemble").checked) stages.push("assemble");
  if (!stages.length) return toast("Select at least one stage", "error");
  try {
    const res = await api(`/api/projects/${S.pid}/production/start`, {
      method: "POST",
      body: { stages, subtitles: $("prodSubtitles").checked },
    });
    startJob(res);
    toast("Batch production started");
  } catch (e) { toast(e.message, "error"); }
}

async function retryScene(sceneId, kind) {
  if (S.reviewDirty) {
    if (sceneId === S.reviewScene) {
      if (!(await saveSceneReview({ silent: true }))) return;
    } else {
      toast("Save or discard the current scene changes before regenerating another scene", "error");
      return;
    }
  }
  try {
    const res = await api(`/api/projects/${S.pid}/production/retry`, {
      method: "POST",
      body: { scene_id: sceneId, kind },
    });
    startJob(res);
    toast(`Scene ${sceneId} ${kind} retry started`);
  } catch (e) { toast(e.message, "error"); }
}

// ---------------------------------------------------------------------------
// Final
// ---------------------------------------------------------------------------

function renderFinal() {
  const node = stage("final");
  $("finalStatus").textContent = statusText(node.status);
  $("finalStatus").className = `status ${statusClass(node.status)}`;
  renderChecks("finalChecks", node.validation);

  let url = null;
  if (node.path) {
    const version = encodeURIComponent(node.updated_at || Date.now());
    url = `/api/projects/${S.pid}/media/${node.path}?v=${version}`;
  }
  if (!url && S.data.outputs?.["final.mp4"]?.url) url = S.data.outputs["final.mp4"].url;
  const video = $("finalVideo");
  if (url) {
    if (video.getAttribute("src") !== url) video.src = url;
    video.classList.remove("hidden");
    $("finalEmpty").classList.add("hidden");
  } else {
    if (video.hasAttribute("src")) {
      video.pause();
      video.removeAttribute("src");
      video.load();
    }
    video.classList.add("hidden");
    $("finalEmpty").classList.remove("hidden");
  }
  $("finalLinks").innerHTML = url ? `<a class="btn" href="${url}" download>Download final.mp4</a>` : "";
  if (document.activeElement !== $("finalSubtitles")) {
    $("finalSubtitles").checked = !!S.data.state.settings.subtitles;
  }
  $("renderFinal").disabled =
    !S.data.gates?.ok || stageStatus("production") !== "done" || !!S.data.active_job;
  $("approveFinal").disabled = !node.path || !!S.data.active_job;
}

async function renderFinalVideo() {
  try {
    const res = await api(`/api/projects/${S.pid}/final/render`, {
      method: "POST",
      body: {
        subtitles: $("finalSubtitles").checked,
        out_name: $("finalName").value.trim() || "final.mp4",
      },
    });
    startJob(res);
    toast("Final render started");
  } catch (e) { toast(e.message, "error"); }
}

async function approveFinal() {
  try {
    await api(`/api/projects/${S.pid}/final/approve`, { method: "POST" });
    toast("Final render approved");
    await loadProject();
  } catch (e) { toast(e.message, "error"); }
}

// ---------------------------------------------------------------------------
// Publish kit
// ---------------------------------------------------------------------------

function renderPublish() {
  const p = S.data.publish || {};
  const status = p.status || "empty";
  $("publishStatus").textContent = statusText(status);
  $("publishStatus").className = `status ${statusClass(status)}`;

  const options = Array.isArray(p.title_options) ? p.title_options : [];
  const selected = p.title || options[0] || "";
  $("publishTitleOptions").innerHTML = options.length
    ? options.map((t) =>
        `<button type="button" class="title-option ${t === selected ? "selected" : ""}" data-title="${esc(t)}">${esc(t)}</button>`
      ).join("")
    : `<p class="hint">Generate a publish kit to see title options.</p>`;

  if (document.activeElement !== $("publishTitle")) $("publishTitle").value = selected;
  if (document.activeElement !== $("publishDescription")) $("publishDescription").value = p.description || "";
  if (document.activeElement !== $("publishTags")) $("publishTags").value = p.tags || "";
  if (document.activeElement !== $("publishThumbText")) $("publishThumbText").value = p.thumbnail_text || "";

  const thumbUrl = p.thumbnail_url || "";
  const img = $("publishThumbPreview");
  if (thumbUrl) {
    if (img.getAttribute("src") !== thumbUrl) img.src = thumbUrl;
    img.classList.remove("hidden");
  } else {
    img.removeAttribute("src");
    img.classList.add("hidden");
  }
  const download = $("publishThumbDownload");
  if (thumbUrl) {
    download.href = thumbUrl;
    download.classList.remove("hidden");
  } else {
    download.removeAttribute("href");
    download.classList.add("hidden");
  }

  const thumbStatus = p.thumbnail_status || "empty";
  $("publishThumbStatus").textContent = statusText(thumbStatus);
  $("publishThumbStatus").className = `status ${statusClass(thumbStatus)}`;
  $("generatePublish").disabled = !S.data.story || !!S.data.active_job;
  $("generateThumbnail").disabled = !p.thumbnail_prompt || !!S.data.active_job;
  renderPublishLog();
}

function renderPublishLog() {
  const el = $("publishLog");
  if (!el) return;
  el.textContent = S.job?.logs?.length
    ? S.job.logs.join("\n")
    : (S.job ? S.job.message : "No job running.");
}

function markPublishTitle(title) {
  $$("#publishTitleOptions [data-title]").forEach((button) => {
    button.classList.toggle("selected", button.dataset.title === title);
  });
}

async function generatePublish() {
  if (!S.data?.story) return toast("Generate the story first", "error");
  const provider = $("llmProvider").value;
  try {
    const res = await api(`/api/projects/${S.pid}/publish/generate`, {
      method: "POST",
      body: {
        provider,
        model: $("storyModel").value.trim(),
        api_base: providerBase(provider),
      },
    });
    startJob(res);
    toast("Generating titles, description and tags");
  } catch (e) { toast(e.message, "error"); }
}

async function generatePublishThumbnail() {
  const p = S.data.publish || {};
  if (!p.thumbnail_prompt) return toast("Generate the publish kit first", "error");
  try {
    const res = await api(`/api/projects/${S.pid}/publish/thumbnail`, {
      method: "POST",
      body: { engine: S.data.state.settings.image.engine || "zimage" },
    });
    startJob(res);
    toast("Generating thumbnail");
  } catch (e) { toast(e.message, "error"); }
}

async function savePublish() {
  try {
    await api(`/api/projects/${S.pid}/publish`, {
      method: "PUT",
      body: {
        title: $("publishTitle").value.trim(),
        description: $("publishDescription").value,
        tags: $("publishTags").value,
        thumbnail_text: $("publishThumbText").value.trim(),
      },
    });
    toast("Publish kit saved");
    await loadProject();
  } catch (e) { toast(e.message, "error"); }
}

async function copyPublishText(text, label) {
  const value = String(text || "").trim();
  if (!value) return toast(`Nothing to copy for ${label}`, "error");
  try {
    await navigator.clipboard.writeText(value);
    toast(`${label} copied`);
  } catch {
    const area = document.createElement("textarea");
    area.value = value;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    area.remove();
    toast(`${label} copied`);
  }
}

function copyPublishAll() {
  const title = $("publishTitle").value.trim();
  const description = $("publishDescription").value.trim();
  const tags = $("publishTags").value.trim();
  const text = `${title}\n\n${description}\n\nTags:\n${tags}`;
  copyPublishText(text, "Publish kit");
}

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

function renderSettings() {
  if (S.settingsDirty) return;
  const s = S.data.state.settings;
  $("setLlmProvider").value = s.llm.provider || "ollama";
  $("setLlmModel").value = s.llm.model || "";
  $("setOllamaUrl").value = s.llm.ollama_url || s.ollama_url || "";
  $("setApiBase").value = s.llm.api_base || "https://opencode.ai/inference/go/openai/v1";
  $("setApiKey").value = "";
  $("apiKeyStatus").textContent = s.llm.has_api_key ? "API key saved locally" : "No API key saved";
  $("setComfyUrl").value = s.comfy_url || "";
  $("setImageEngine").value = s.image.engine || "sdxl";
  $("setStylePrefix").value = s.image.style_prefix || "";
  $("setCharacter").value = s.image.character || "";
  $("setNegativePrompt").value = s.image.negative_prompt || "";
  $("setImageStylePreset").value = stylePresetFor(
    s.image.style_prefix, s.image.character, s.image.negative_prompt
  );
  markSelectedStyle($("setImageStylePreset").value);
  $("setWidth").value = s.image.width || 1344;
  $("setHeight").value = s.image.height || 768;
  $("setSteps").value = s.image.steps || 28;
  $("setCfg").value = s.image.cfg || 7;
  $("setTtsLang").value = s.tts.language_id || "hi";
  $("setTtsReference").value = s.tts.reference || "";
  $("setTtsExag").value = s.tts.exaggeration ?? 0.5;
  $("setTtsCfg").value = s.tts.cfg_weight ?? 0.3;
  $("setTtsTemp").value = s.tts.temperature ?? 0.8;
  $("setMusicPrompt").value = s.music.prompt || "";
  $("setMusicDuration").value = s.music.duration || 300;
  $("setMusicBpm").value = s.music.bpm || 78;
  $("setMusicKey").value = s.music.key || "C minor";
  $("setMusicVolume").value = s.music.volume ?? 0.1;
  $("setMusicEnabled").checked = s.music.enabled !== false;
  $("setSubtitles").checked = !!s.subtitles;
  const publish = s.publish || {};
  $("setChannelName").value = publish.channel_name || "";
  $("setChannelTagline").value = publish.channel_tagline || "";
  $("setContactEmail").value = publish.contact_email || "";
  $("setHashtags").value = publish.hashtags || "";
  $("setCta").value = publish.cta || "";
}

function collectSettings() {
  const old = S.data.state.settings;
  return {
    llm: {
      provider: $("setLlmProvider").value,
      model: $("setLlmModel").value.trim(),
      ollama_url: $("setOllamaUrl").value.trim(),
      api_base: $("setApiBase").value.trim(),
      temperature: old.llm.temperature ?? 0.85,
      num_predict: old.llm.num_predict ?? 4096,
    },
    image: {
      engine: $("setImageEngine").value,
      style_prefix: $("setStylePrefix").value.trim(),
      character: $("setCharacter").value.trim(),
      negative_prompt: $("setNegativePrompt").value.trim(),
      width: Number($("setWidth").value || 1344),
      height: Number($("setHeight").value || 768),
      steps: Number($("setSteps").value || 28),
      cfg: Number($("setCfg").value || 7),
      sampler: old.image.sampler || "res_multistep",
      scheduler: old.image.scheduler || "simple",
    },
    tts: {
      ...old.tts,
      language_id: $("setTtsLang").value.trim() || "hi",
      reference: $("setTtsReference").value.trim(),
      exaggeration: Number($("setTtsExag").value || 0.5),
      cfg_weight: Number($("setTtsCfg").value || 0.3),
      temperature: Number($("setTtsTemp").value || 0.8),
    },
    music: {
      prompt: $("setMusicPrompt").value.trim(),
      duration: Number($("setMusicDuration").value || 300),
      bpm: Number($("setMusicBpm").value || 78),
      key: $("setMusicKey").value.trim() || "C minor",
      volume: Number($("setMusicVolume").value || 0.1),
      enabled: $("setMusicEnabled").checked,
    },
    comfy_url: $("setComfyUrl").value.trim(),
    ollama_url: $("setOllamaUrl").value.trim(),
    subtitles: $("setSubtitles").checked,
    publish: {
      channel_name: $("setChannelName").value.trim(),
      channel_tagline: $("setChannelTagline").value.trim(),
      contact_email: $("setContactEmail").value.trim(),
      hashtags: $("setHashtags").value.trim(),
      cta: $("setCta").value.trim(),
    },
    video: old.video || { width: 1920, height: 1080, fps: 30 },
    story_chapters: old.story_chapters || 5,
    story_minutes: old.story_minutes || 5,
    story_topic: old.story_topic || "",
  };
}

async function saveSettings() {
  try {
    await api(`/api/projects/${S.pid}/settings`, {
      method: "PATCH", body: { settings: collectSettings() },
    });
    S.settingsDirty = false;
    toast("Settings saved");
    await loadProject();
  } catch (e) { toast(e.message, "error"); }
}

async function saveApiKey() {
  try {
    const res = await api(`/api/projects/${S.pid}/settings/api-key`, {
      method: "POST", body: { key: $("setApiKey").value.trim() },
    });
    $("setApiKey").value = "";
    $("apiKeyStatus").textContent = res.has_api_key ? "API key saved locally" : "No API key saved";
    toast("API key updated");
    await loadModels();
  } catch (e) { toast(e.message, "error"); }
}

async function loadModels() {
  const provider = $("llmProvider").value;
  const base = providerBase(provider);
  $("modelHint").textContent = "Loading models...";
  try {
    const res = await api(`/api/models?provider=${encodeURIComponent(provider)}&base_url=${encodeURIComponent(base)}`);
    const listed = res.models || [];
    const suggestions = res.suggestions || [];
    const shown = listed.length ? listed : suggestions;
    $("modelOptions").innerHTML = shown.map((m) => `<option value="${esc(m)}"></option>`).join("");
    if (res.ok) {
      const keyNote = provider !== "ollama" && !S.data?.state?.settings?.llm?.has_api_key
        ? " · save a key in Settings to generate"
        : "";
      $("modelHint").textContent = `${listed.length} models available · ${res.base_url || base}${keyNote}`;
    } else {
      const keyHint = provider === "ollama" ? "" : " — save an OpenCode API key in Settings.";
      const suggestHint = suggestions.length
        ? ` Suggested: ${suggestions.slice(0, 5).join(", ")}.`
        : "";
      $("modelHint").textContent = `${res.error}${keyHint}${suggestHint}`;
    }
  } catch (e) {
    $("modelHint").textContent = e.message;
  }
}

// ---------------------------------------------------------------------------
// Jobs
// ---------------------------------------------------------------------------

function startJob(res) {
  if (!res?.job) return;
  S.jobId = res.job.id;
  S.job = { ...res.job, logs: [] };
  startPolling();
}

function startPolling() {
  clearInterval(S.poll);
  S.poll = setInterval(pollJob, 1000);
  pollJob();
}

async function pollJob() {
  if (!S.jobId) return;
  try {
    const job = await api(`/api/jobs/${S.jobId}`);
    S.job = job;
    renderJobPill();
    renderJobPanel();
    renderPublishLog();
    if (job.status === "done" || job.status === "failed") {
      clearInterval(S.poll);
      S.poll = null;
      $("jobPill").classList.add("hidden");
      if (job.status === "failed") toast(job.error || "Job failed", "error");
      else toast("Job complete", "ok");
      await loadProject();
      S.job = job;
      renderJobPanel();
      renderPublishLog();
    }
  } catch (e) {
    // A transient poll failure should not kill the UI.
    console.warn(e);
  }
}

function renderJobPill() {
  const job = S.job;
  const pill = $("jobPill");
  if (!job || !["queued", "running"].includes(job.status)) {
    pill.classList.add("hidden");
    return;
  }
  pill.classList.remove("hidden");
  $("jobPillText").textContent = job.message || job.kind;
  $("jobPillPct").textContent = `${job.progress || 0}%`;
}

// ---------------------------------------------------------------------------
// New project modal
// ---------------------------------------------------------------------------

function openModal() { $("modal").classList.remove("hidden"); }
function closeModal() { $("modal").classList.add("hidden"); }

async function createProject() {
  const title = $("newTitle").value.trim();
  if (!title) return toast("Title is required", "error");
  try {
    const res = await api("/api/projects", {
      method: "POST",
      body: {
        title,
        topic: $("newTopic").value.trim(),
        minutes: Number($("newMinutes").value || 5),
        chapters: Number($("newChapters").value || 5),
      },
    });
    closeModal();
    await loadProjects();
    S.pid = res.id;
    await selectProject(res.id);
    showPage("story");
    toast("Project created");
  } catch (e) { toast(e.message, "error"); }
}

// ---------------------------------------------------------------------------
// Events
// ---------------------------------------------------------------------------

function bind() {
  $("projectSelect").addEventListener("change", (e) => selectProject(e.target.value));
  $("settingsBtn").addEventListener("click", () => showPage("settings"));
  $("newProjectBtn").addEventListener("click", openModal);
  $("closeModal").addEventListener("click", closeModal);
  $("createProject").addEventListener("click", createProject);
  $("modal").addEventListener("click", (e) => { if (e.target.id === "modal") closeModal(); });

  $$(".stage-link").forEach((el) => el.addEventListener("click", () => showPage(el.dataset.page)));
  window.addEventListener("hashchange", () => {
    const page = location.hash.replace(/^#/, "");
    if (["series", "ideas", "story", "scenes", "samples", "production", "final", "publish", "settings"].includes(page) && page !== S.page) {
      showPage(page);
    }
  });

  $("saveSeries").addEventListener("click", saveSeries);
  $("addCastMember").addEventListener("click", addCastMember);
  $("generateEpisodes").addEventListener("click", generateEpisodes);
  $("seriesRefreshModels").addEventListener("click", loadSeriesModels);
  $("seriesProvider").addEventListener("change", () => {
    if (["opencode-go", "opencode"].includes($("seriesProvider").value)) {
      $("seriesModel").value = "claude-haiku-5-5";
    }
    loadSeriesModels();
  });
  $("castGrid").addEventListener("input", () => { S.castDirty = true; });
  $("episodeList").addEventListener("click", (e) => {
    const use = e.target.closest("[data-use-episode]");
    if (use) {
      useEpisode(use.dataset.useEpisode, use.dataset.generate === "1");
      return;
    }
    const open = e.target.closest("[data-open-episode]");
    if (open) openEpisodeProject(open.dataset.openEpisode);
  });

  $("suggestGenres").addEventListener("click", suggestGenres);
  $("addGenre").addEventListener("click", addGenre);
  $("generateIdeas").addEventListener("click", generateGenreIdeas);
  $("ideaRefreshModels").addEventListener("click", loadIdeaModels);
  $("ideaProvider").addEventListener("change", () => {
    if (["opencode-go", "opencode"].includes($("ideaProvider").value)) {
      $("ideaModel").value = "claude-haiku-5-5";
    }
    loadIdeaModels();
  });
  $("genreGrid").addEventListener("click", (e) => {
    const card = e.target.closest("[data-genre-id]");
    if (!card) return;
    S.selectedGenre = card.dataset.genreId;
    renderIdeas();
  });
  $("ideaList").addEventListener("click", (e) => {
    const use = e.target.closest("[data-use-idea]");
    if (use) {
      useIdea(use.dataset.useIdea, use.dataset.generate === "1");
      return;
    }
    const open = e.target.closest("[data-open-project]");
    if (open) openIdeaProject(open.dataset.openProject);
  });

  $("generateStory").addEventListener("click", generateStory);
  $("saveStory").addEventListener("click", saveStory);
  $("approveStory").addEventListener("click", approveStory);
  $("requestStoryChanges").addEventListener("click", requestStoryChanges);
  $("storyText").addEventListener("input", () => {
    S.storyDirty = true;
    const words = $("storyText").value.trim() ? $("storyText").value.trim().split(/\s+/).length : 0;
    $("storyWords").textContent = `${words} words`;
  });
  $("storyTemp").addEventListener("input", updateRangeLabels);
  $("storyTopic").addEventListener("input", () => { S.topicDirty = true; });
  $("storyInstructions").addEventListener("input", () => { S.instructionsDirty = true; });
  ["storyMinutes", "storyChapters"].forEach((id) =>
    $(id).addEventListener("input", updateStoryPlanHint)
  );
  $("llmProvider").addEventListener("change", () => {
    const provider = $("llmProvider").value;
    $("setLlmProvider").value = provider;
    applyProviderPreset(provider);
    if (PROVIDER_DEFAULT_MODELS[provider]) {
      $("storyModel").value = PROVIDER_DEFAULT_MODELS[provider];
      $("setLlmModel").value = PROVIDER_DEFAULT_MODELS[provider];
    }
    $("storyModel").placeholder = provider === "ollama"
      ? "aya-expanse:8b"
      : (PROVIDER_MODEL_HINTS[provider] || "model ID");
    loadModels();
  });
  $("refreshModels").addEventListener("click", loadModels);

  $("generateScenes").addEventListener("click", generateScenes);
  $("repairPrompts").addEventListener("click", repairPrompts);
  $("restylePrompts").addEventListener("click", restylePrompts);
  $("saveScenes").addEventListener("click", saveScenes);
  $("approveScenes").addEventListener("click", approveScenes);
  $("addScene").addEventListener("click", addScene);
  $("sceneFilter").addEventListener("input", () => {
    if (S.sceneDirty) S.data.scenes = collectScenes();
    renderSceneList();
  });
  $("sceneList").addEventListener("input", () => { S.sceneDirty = true; });
  $("sceneList").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-use-scene]");
    if (btn) useScene(btn.dataset.useScene);
  });

  $("voiceScene").addEventListener("change", () => {
    S.selectedScene = Number($("voiceScene").value || 1);
    const scene = (S.data.scenes || []).find((s) => s.id === S.selectedScene);
    if (scene) $("voiceText").value = scene.narration || "";
    syncSampleScene();
  });
  $("imageScene").addEventListener("change", () => {
    S.selectedScene = Number($("imageScene").value || 1);
    syncSampleScene();
  });
  $("clipScene").addEventListener("change", () => {
    S.selectedScene = Number($("clipScene").value || 1);
    syncSampleScene();
  });
  ["voiceExag", "voiceCfg", "voiceTemp"].forEach((id) => $(id).addEventListener("input", updateRangeLabels));
  $("genVoice").addEventListener("click", generateVoice);
  $("previewVoiceText").addEventListener("click", previewVoiceText);
  $("genImage").addEventListener("click", generateImage);
  $("genMusic").addEventListener("click", generateMusic);
  $("genClip").addEventListener("click", generateClip);
  $("approveVoice").addEventListener("click", () => approveSample("voice"));
  $("approveImage").addEventListener("click", () => approveSample("image"));
  $("approveMusic").addEventListener("click", () => approveSample("music"));
  $("approveClip").addEventListener("click", () => approveSample("clip"));
  $("rejectVoice").addEventListener("click", () => rejectSample("voice"));
  $("rejectImage").addEventListener("click", () => rejectSample("image"));
  $("rejectMusic").addEventListener("click", () => rejectSample("music"));
  $("rejectClip").addEventListener("click", () => rejectSample("clip"));

  $("startProduction").addEventListener("click", startProduction);
  $("sceneStatusTable").addEventListener("click", (e) => {
    const retry = e.target.closest("[data-retry]");
    if (retry) {
      retryScene(Number(retry.dataset.scene), retry.dataset.retry);
      return;
    }
    const pick = e.target.closest("[data-review]");
    if (pick) pickReviewScene(Number(pick.dataset.review));
  });
  $("reviewPrev").addEventListener("click", () => stepReview(-1));
  $("reviewNext").addEventListener("click", () => stepReview(1));
  $("reviewJump").addEventListener("change", jumpReviewScene);
  $("reviewSave").addEventListener("click", () => saveSceneReview());
  $("reviewApprove").addEventListener("click", approveScenePlan);
  $("reviewRegenVoice").addEventListener("click", () => regenerateReview("voice"));
  $("reviewRegenImage").addEventListener("click", () => regenerateReview("image"));
  $("reviewNarration").addEventListener("input", updateReviewDirty);
  $("reviewPrompt").addEventListener("input", updateReviewDirty);
  $("reviewAudio").addEventListener("ended", () => {
    if (!$("reviewAutoplay").checked) return;
    if (S.reviewDirty) {
      toast("Save this scene before moving to the next one", "error");
      return;
    }
    const scenes = S.data?.scenes || [];
    const index = scenes.findIndex((s) => s.id === S.reviewScene);
    const next = scenes[index + 1];
    if (next && pickReviewScene(next.id, { force: true })) playReviewAudio();
  });

  $("renderFinal").addEventListener("click", renderFinalVideo);
  $("approveFinal").addEventListener("click", approveFinal);

  $("generatePublish").addEventListener("click", generatePublish);
  $("savePublish").addEventListener("click", savePublish);
  $("generateThumbnail").addEventListener("click", generatePublishThumbnail);
  $("copyTitle").addEventListener("click", () => copyPublishText($("publishTitle").value, "Title"));
  $("copyDescription").addEventListener("click", () => copyPublishText($("publishDescription").value, "Description"));
  $("copyTags").addEventListener("click", () => copyPublishText($("publishTags").value, "Tags"));
  $("copyPublishAll").addEventListener("click", copyPublishAll);
  $("publishTitleOptions").addEventListener("click", (event) => {
    const button = event.target.closest("[data-title]");
    if (!button) return;
    $("publishTitle").value = button.dataset.title;
    markPublishTitle(button.dataset.title);
  });

  $("saveSettings").addEventListener("click", saveSettings);
  $("saveApiKey").addEventListener("click", saveApiKey);
  $("setLlmProvider").addEventListener("change", () => {
    const provider = $("setLlmProvider").value;
    $("llmProvider").value = provider;
    applyProviderPreset(provider);
    if (PROVIDER_DEFAULT_MODELS[provider]) {
      $("setLlmModel").value = PROVIDER_DEFAULT_MODELS[provider];
      $("storyModel").value = PROVIDER_DEFAULT_MODELS[provider];
    }
    S.settingsDirty = true;
  });
  $("setImageStylePreset").addEventListener("change", () => {
    const key = $("setImageStylePreset").value;
    const preset = STYLE_PRESETS[key];
    if (preset) {
      $("setStylePrefix").value = preset.prefix;
      $("setCharacter").value = preset.character;
      $("setNegativePrompt").value = preset.negative;
      $("setImageEngine").value = preset.engine;
      toast(`Style preset loaded · recommended engine: ${preset.engine}`);
    }
    markSelectedStyle(key);
    S.settingsDirty = true;
  });
  $("styleGallery").addEventListener("click", (event) => {
    const button = event.target.closest("[data-style]");
    if (!button) return;
    const select = $("setImageStylePreset");
    select.value = button.dataset.style;
    select.dispatchEvent(new Event("change"));
  });
  ["setStylePrefix", "setCharacter", "setNegativePrompt"].forEach((id) =>
    $(id).addEventListener("input", () => {
      $("setImageStylePreset").value = "custom";
      markSelectedStyle("custom");
      S.settingsDirty = true;
    })
  );
  $("page-settings").addEventListener("input", () => { S.settingsDirty = true; });
  $("page-settings").addEventListener("change", () => { S.settingsDirty = true; });
}

boot();
