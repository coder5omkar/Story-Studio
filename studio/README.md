# Story Studio

Local, approval-gated web UI for the AI story pipeline. It exists so a 2–3 hour
render is never a gamble: you preview and approve every quality-critical decision
first, then batch generation runs on assets you have already seen.

Studio URL: <http://127.0.0.1:4780>

## Start

From the repository root:

```powershell
.\studio\start.cmd
```

Or run it directly:

```powershell
cd <repo>
$env:STUDIO_PORT = "4780"
.\.venv\Scripts\python.exe -m studio.server
```

The server binds to `127.0.0.1` only and rejects other `Host` headers (DNS
rebinding protection). Set `STUDIO_NO_BROWSER=1` to skip opening a browser and
`STUDIO_PORT` to change the port.

## Workflow

The rail starts with the **Story table**, then six production stages plus
settings, and the gate card lists what is still unapproved.

0. **Story table** — pick what to produce without inventing a premise:
   - **Suggest 5 genres** asks Claude for five distinct, channel-ready genre
     pillars. Each has a Hindi channel name, tagline, audience, repeatable story
     engines and example titles.
   - **Add your own genre** saves a custom pillar alongside the AI suggestions.
   - Select a genre and **Generate 3 story ideas**. Each idea is a full blueprint:
     Hindi hook, logline, 300–450-word premise, explicit ending, protagonist,
     obstacle, emotional arc, retention beats, chapter beats and thumbnail moment.
   - **Use this story** creates a project pre-filled with the blueprint and genre
     channel; **Use & write full story** also starts the first draft with the
     selected ideation model.
   - Multiple stories can be generated and produced from the same genre. The
     library is saved in `studio/.story_ideas.json` (gitignored), and idea status
     changes to *Project created* after selection.
   - Claude Haiku 5.5 is the default ideation model. It is also copied into the
     project's Story settings, so the full draft uses the same model unless you
     change it.
1. **Story** — pick a local Ollama model or an OpenAI-compatible provider, enter
   a premise, and optionally add story instructions (tone, genre, ending, themes
   to include or avoid). The prompt uses your topic and instructions plus only
   generic structure; no genre or finance requirements are hardcoded. Multi-chapter
   stories are outlined and written one chapter at a time. Incomplete or truncated
   drafts are blocked from approval.
   - **Model suggestions:** `deepseek-v4.1-flash` for fast, reliable Hindi drafts;
     `kimi-k3.1-pro` for more literary prose (use a larger output budget);
     `glm-5.3` or `qwen3.7-plus` as balanced alternatives.
   - If a genre or theme must be excluded, say so in **Story instructions**
     (for example: “No financial subplot, no EMI, no loans”). The model may
     otherwise choose a debt or money problem as a plot device on its own.
2. **Scene plan** — split the story into narration chunks and English image
   prompts. Review pacing, camera moves and prompts. "Fix English prompts"
   translates prompts that came back in Hindi. Approve the plan.
3. **Sample studio** — audition one scene before spending GPU hours:
   - **Voice:** Chatterbox sample with exaggeration / CFG / temperature sliders.
     The card shows **What the voice will read**: Indian amounts, percentages,
     ages and acronyms are converted to spoken Hindi words before synthesis.
     Use **Preview spoken text** to check the pronunciation without generating audio.
   - **Image:** SDXL, FaceID, IPAdapter or Z-Image sample with an optional seed.
   - **Music:** optional ACE-Step sample with prompt, BPM, key and duration.
     Turn off **Settings → Music & output → Use music bed** to skip the music
     sample and its approval gate.
   - **Subtitle / motion preview:** renders one scene through the real
     `assemble.py` path, including burned-in subtitles and optional music.
     Subtitles are toggled in the preview and final-render checkboxes; no
     separate subtitle file generation is required.
   Approve each sample.
4. **Production** — batch images / music / narration / assembly with resumable
   skips. Existing assets are not regenerated. Per-scene retry buttons regenerate
   one image or voice clip. Batch is blocked until every required gate is green.
   - **Scene review** sits above the scene table: step through every scene with
     the full image, a voice player, and the narration script. **Autoplay next**
     plays the voices in story order. Edit the script or English image prompt and
     click **Save scene**; then **Regenerate voice** or **Regenerate image** for
     that scene. Saving marks the scene plan draft but keeps the voice/image
     style approvals. Click **Approve plan** once the review is complete.
     Image regeneration uses a fresh seed each time, so it produces a real new
     variation; batch generation still uses deterministic per-scene seeds.
   - Assembling again reuses existing clips while their image, narration timing and
     scene prompt are unchanged, so a failed final mix does not re-render the video
     clips. If `audio/music.mp3` is missing, assembly automatically continues
     without music instead of failing.
5. **Final review** — assemble the full video, watch it, then approve. Choose
   whether subtitles are burned in and the output filename.
6. **Publish kit** — generate a ready-to-paste YouTube package from the story:
   five Hindi title options, a 1200–1800 character description with hook, moral,
   CTA, contact email, disclaimer and hashtags, 12–18 tags, thumbnail text and a
   thumbnail image prompt. Edit any field, pick a title, then **Generate
   thumbnail** to render a 1280×720 PNG in the project's current visual style
   with a Devanagari text overlay. Use the copy buttons to paste directly into
   YouTube Studio. Channel name, tagline, email, hashtags and CTA come from
   **Settings → Publish / YouTube**.
   - Thumbnail fonts: Nirmala UI on Windows, Noto Sans Devanagari on Linux, or
     set `THUMBNAIL_FONT` to a TTF/TTC file. Changing the image style or publish
     settings marks the publish kit stale so the thumbnail can be re-rendered.
   - Thumbnails are saved to
     `projects/<id>/studio/samples/thumbnail/thumbnail.png`.

### Visual styles

Choose a preset under **Settings → Visuals → Style preset**. Each preset sets a
style prompt, recurring-character description, negative prompt and recommended
engine:

- **Minimalist explainer (stick figure)** — Z-Image
- **Indian flat-vector (previous)** — SDXL
- **Cinematic photoreal (realistic)** — SDXL
- **Dark cinematic drama (realistic)** — SDXL
- **Anime / hand-painted** — Z-Image
- **3D animated feature** — SDXL
- **Graphic novel / comic** — SDXL
- **Watercolor storybook** — Z-Image
- **Vintage Indian poster** — SDXL
- **Paper cutout collage** — Z-Image
- **Custom** — edit the style, character and negative-prompt fields directly

The Settings page includes a **style sample gallery**. Each thumbnail is a real
render of the same test scene; click one to load that preset, then save. Use
**Open full sample** under a thumbnail to inspect it at full resolution.

Z-Image follows simplified 2D styles more faithfully; SDXL is better for
realistic, 3D and comic styles. To apply a style to an existing project:

1. Select the preset and click **Save settings**.
2. Open **Scene plan → Restyle for current style**.
3. Review and approve the rewritten prompts.
4. Generate an image sample with the recommended engine and approve it.
5. Batch production uses the same style and engine.

Changing the style invalidates existing image, clip, production and final
approvals. Old images stay on disk until regenerated. The style test is
per-project, so you can duplicate a project if you want to compare two looks.

Settings holds per-project defaults: LLM provider/model, ComfyUI URL, image
style/character/negative prompt, voice reference and prosody, music
prompt/volume, subtitle default, publish channel identity, and the API key for
an OpenAI-compatible provider.

## Providers

- **Local Ollama** (default): `http://127.0.0.1:11434`, any installed model.
- **OpenCode Go** (subscription): base URL
  `https://opencode.ai/inference/go/openai/v1`. Create a personal API key in
  Console → Account → Personal API keys (it starts with `oc_sk_`), paste it in
  Settings, then select **OpenCode Go** on the Story page. Model suggestions
  include `deepseek-v4.1-flash`, `kimi-k3`, `kimi-k3.1-pro`, `glm-5.3`,
  `qwen3.8-flash`, `qwen3.7-plus`, and `claude-haiku-5-5`.
- **OpenCode Console (pay-as-you-go)**: base URL
  `https://opencode.ai/inference/openai/v1`.
- **Other OpenAI-compatible**: set a base URL and API key in Settings. OpenAI,
  OpenRouter, and local OpenAI-compatible servers also work.

OpenCode Go needs a stable `x-opencode-session` header. The studio sends this
automatically, using one session ID per project, and identifies itself as
`StoryStudio/1.0`. The models endpoint is queried at
`https://opencode.ai/inference/go/v1/models`; if the key is missing or invalid,
the UI still shows a curated list of model IDs you can type manually.

The API key is stored in `studio/.secrets.json`, or supplied through
`STUDIO_LLM_API_KEY`, `OPENCODE_API_KEY`, or `OPENAI_API_KEY`. It is local-only;
the studio binds to `127.0.0.1`.

### OpenCode Go quick setup

1. In [Console](https://opencode.ai/console), subscribe to **Go** and create a
   personal API key (`oc_sk_...`).
2. In Story Studio, open **Settings**.
3. Set **Provider** to **OpenCode Go**, then click **Save settings**.
4. Paste the key into **API key** and click **Save API key**.
5. Go to **Story**, choose **OpenCode Go**, click **Refresh models**, and select
   a model such as `deepseek-v4.1-flash`.
6. Generate a short story first to confirm the provider before a long run.

A 401/403 usually means the key is from the wrong workspace, the workspace is
not subscribed to Go, or the selected model/region is not enabled. Go workspace
privacy settings may restrict some models and regions.

## Quality checks

Each stage has automated checks that inform approval. A failing check blocks
approval; warnings are visible but do not block.

- **Story:** length vs target, chapter headings, Devanagari ratio, complete
  ending, concrete details, repetition.
- **Scenes:** scene IDs, missing narration, English prompt quality, camera
  vocabulary, words per scene, estimated runtime.
- **Audio:** duration, mean volume, clipping, plus spoken-text checks (digits,
  currency/percent symbols, English words left in the narration).
- **Image:** resolution, aspect ratio, exposure, file size.
- **Video:** streams, resolution, duration, file size.

## Project data

Every project is self-contained under `projects/<id>/`:

```
projects/<id>/
  project.json
  story.md
  scenes.json
  images/scene_001.png ...
  audio/scene_001.wav, timings.json, music.mp3
  video/final.mp4
  studio/
    state.json          # stage status, approvals, checks, history
    config.json         # per-project pipeline config used by PIPELINE_CONFIG
    samples/            # voice, image, music, clip previews
    versions/           # saved story/scene revisions
```

Projects created before Studio are imported automatically with sensible stage
approvals, so you can open and continue an existing project.

## Requirements

- FFmpeg on PATH
- Ollama running for story/scene generation
- ComfyUI running at `http://127.0.0.1:8188` for image and music samples
- Chatterbox in `tts_env`
- Studio dependencies in `.venv`

The header shows live status for Ollama, ComfyUI, FFmpeg and the TTS env.

## Troubleshooting

- **ComfyUI offline:** start `D:\ComfyUI\ComfyUI_windows_portable\run_nvidia_gpu.bat`.
- **Image/music sample fails:** the studio surfaces the pipeline process output in
  the live job log. Check ComfyUI first.
- **Prompts come back in Hindi:** click **Fix English prompts** on the scene plan,
  or edit the prompt directly before approving.
- **A figure or amount sounds wrong:** in Sample studio, click **Preview spoken
  text**. Amounts such as `₹38,000`, `11.5%`, `₹1.5 लाख`, `EMI` and `CIBIL` are
  converted to Hindi words before synthesis. If a word still sounds wrong, edit
  the scene narration or extend `pipeline/hindi_text.py`.
- **“The model returned only reasoning” or an empty response:** reasoning models
  such as `deepseek-v4.1-flash` can spend the whole output budget on hidden
  reasoning. The studio now gives them at least 8192 tokens and retries once
  with a larger budget. If it still happens, switch to another model or run the
  request again.
- **A batch failed midway:** fix the cause and start production again. Completed
  images and voice clips are skipped; use the retry buttons for individual scenes.
- **Port already in use:** set `STUDIO_PORT` before starting.
