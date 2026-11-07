# Story Studio

A local, approval-gated production studio for Hindi story videos.

Story Studio separates generation into reviewable stages so a long render is not
a gamble: write and approve the story, review the scene plan, audition the voice,
image, music and subtitle preview, then run batch production and approve the
final video.

![Minimalist style sample](studio/ui/style_samples/minimalist_thumb.jpg)

## Features

- **Story generation** with local Ollama models or an OpenAI-compatible provider
  (including OpenCode Go).
- **No forced genre**: the topic and optional story instructions are the creative
  brief. Only generic length, chapter and completeness rules are applied.
- **Multi-chapter generation**: an outline plus one chapter at a time, with
  per-chapter word targets and a retry for short chapters.
- **Completeness gates**: a story below 65% of the target length, or one that ends
  mid-sentence, cannot be approved.
- **Scene plan** with narration chunks, English image prompts, camera/mood and a
  **Restyle for current style** action.
- **Visual style library** with real sample renders: minimalist explainer, Indian
  flat-vector, cinematic photoreal, dark cinematic, anime, 3D animated, graphic
  novel, watercolor, vintage Indian poster and paper cutout.
- **Voice studio** with Chatterbox Multilingual and a spoken-text preview:
  Indian amounts, percentages, ordinals and acronyms are converted to Hindi
  words before synthesis.
- **Image samples** with SDXL, Z-Image Turbo, IPAdapter and FaceID.
- **Music samples** with ACE-Step.
- **Real subtitle/motion preview** rendered through the final `assemble.py` path.
- **Resumable batch production** with per-scene image/voice retry.
- **Final review** with approval and optional subtitle burn-in.
- **Local-first security**: binds to `127.0.0.1`; API keys are stored locally in
  `studio/.secrets.json` (gitignored) or supplied through environment variables.

## Visual styles

Open **Settings → Visuals → Style samples** to see a real render of every style.
Click a thumbnail to load that preset. Each preset sets a style prompt, recurring
character description, negative prompt and recommended engine.

| Style | Recommended engine |
|---|---|
| Minimalist explainer (stick figure) | Z-Image Turbo |
| Indian flat-vector | SDXL |
| Cinematic photoreal (realistic) | SDXL |
| Dark cinematic drama (realistic) | SDXL |
| Anime / hand-painted | Z-Image Turbo |
| 3D animated feature | SDXL |
| Graphic novel / comic | SDXL |
| Watercolor storybook | Z-Image Turbo |
| Vintage Indian poster | SDXL |
| Paper cutout collage | Z-Image Turbo |

For an existing project:

1. Select a preset in **Settings → Visuals** and click **Save settings**.
2. Open **Scene plan → Restyle for current style**.
3. Review and approve the rewritten prompts.
4. Generate an image sample with the recommended engine and approve it.
5. Batch production uses the same style and engine.

Style changes invalidate image, clip, production and final approvals. Old images
stay on disk until regenerated. **Custom** lets you paste your own style,
character and negative prompt.

## Requirements

This project is primarily set up for **Windows 10/11**.

- Python 3.11–3.13
- FFmpeg on `PATH`
- Ollama for local story generation, or an OpenCode Go / OpenAI-compatible API key
- ComfyUI for images and music
- Chatterbox Multilingual in a separate `tts_env` (or an environment where the
  server can invoke it)
- NVIDIA GPU recommended; SDXL, Z-Image Turbo and Chatterbox are GPU-heavy

### ComfyUI models

Start ComfyUI separately. The workflows in `pipeline/workflows` expect these
model names (edit the workflow JSON if your filenames differ):

| Purpose | Model file / folder |
|---|---|
| SDXL | `models/checkpoints/sd_xl_base_1.0.safetensors` |
| Z-Image Turbo | `diffusion_models/z_image_turbo_int8_convrot.safetensors` |
| Z-Image text encoder | `text_encoders/qwen_3_4b_fp8_mixed.safetensors` |
| Z-Image VAE | `vae/ae.safetensors` |
| ACE-Step music | `models/checkpoints/ace_step_1.5_turbo_aio.safetensors` |
| Optional FaceID/IPAdapter | IPAdapter, FaceID LoRA and CLIP vision files |

ComfyUI should be reachable at `http://127.0.0.1:8188` by default.

## Installation

### 1. Clone and create the studio environment

```powershell
git clone https://github.com/coder5omkar/Story-Studio.git
cd Story-Studio

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, call Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Start ComfyUI

```powershell
cd <ComfyUI>\ComfyUI_windows_portable
.\run_nvidia_gpu.bat
```

Make sure the models listed above are installed.

### 3. Start Ollama (optional if using OpenCode Go)

```powershell
ollama serve
ollama pull aya-expanse:8b
```

Other local models such as `qwen3:14b` or `llama3.1:8b` also work.

### 4. Install Chatterbox in `tts_env`

Create a separate environment so Chatterbox's dependencies do not conflict with
the studio:

```powershell
py -3.11 -m venv tts_env
.\tts_env\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Install the PyTorch build for your CUDA driver from
<https://pytorch.org/get-started/locally/>, then:

```powershell
pip install -r requirements-tts.txt
```

The current studio invokes `tts_env\Scripts\python.exe`. If your Chatterbox
environment has a different name, create a `tts_env` junction or edit
`TTS_PY` in `studio/ops.py`.

### 5. Add a Hindi voice reference (recommended)

Use a clean 5–15 second Hindi WAV with one speaker, for example:

```text
models/piper/hindi_ref.wav
```

Set the path in **Settings → Voice → Reference WAV**, or edit
`pipeline/config.json` → `tts.reference`. You can leave it empty to use the
model's default voice.

### 6. Configure the pipeline

Edit `pipeline/config.json` if needed:

```json
{
  "comfy_url": "http://127.0.0.1:8188",
  "ollama_url": "http://127.0.0.1:11434",
  "project_dir": "../projects/pilot_001",
  "tts": {
    "reference": "../models/piper/hindi_ref.wav"
  }
}
```

The studio writes its own absolute per-project config, so `project_dir` here is
mainly for direct CLI runs from the `pipeline` folder. The `tts.reference` path is
resolved from the `pipeline` folder when the studio runs TTS.

## Start Story Studio

From the repository root:

```powershell
.\studio\start.cmd
```

Or run it directly:

```powershell
.\.venv\Scripts\python.exe -m studio.server
```

Open:

**http://127.0.0.1:4780**

Useful environment variables:

```powershell
$env:STUDIO_PORT = "4780"
$env:STUDIO_NO_BROWSER = "1"
```

## OpenCode Go / OpenAI-compatible keys

In **Settings**:

1. Set **Provider** to **OpenCode Go**.
2. Base URL is pre-filled:
   `https://opencode.ai/inference/go/openai/v1`
3. Paste a personal key from OpenCode Console (starts with `oc_sk_`).
4. Click **Save API key**, then **Save settings**.
5. On the Story page, click **Refresh models** and select a Go model.

Pay-as-you-go uses:

```text
https://opencode.ai/inference/openai/v1
```

The studio sends the `x-opencode-session` header automatically and identifies
itself as `StoryStudio/1.0`. Keys are stored locally in
`studio/.secrets.json`, or read from `STUDIO_LLM_API_KEY`, `OPENCODE_API_KEY`
or `OPENAI_API_KEY`.

### Suggested story models

- **`deepseek-v4.1-flash`** — fast, reliable Hindi drafts; recommended starting
  point.
- **`kimi-k3.1-pro`** — more literary prose; reasoning-heavy, so use the chaptered
  flow and a generous output budget.
- **`glm-5.3`** or **`qwen3.7-plus`** — balanced alternatives.
- **`claude-haiku-5-5`** — clean prose; audition its Hindi style first.

## Workflow

1. **Story**
   - Create a project with a title, premise, minutes and chapters.
   - Add optional **Story instructions**: genre, tone, ending, themes to include
     or avoid. To exclude finance entirely, write:
     `No financial subplot, no EMI, no loans, no salary or savings details.`
   - Generate, edit and approve. Multi-chapter stories are outlined and written
     one chapter at a time.
   - Approval is blocked for incomplete stories (under 65% of target length or
     ending mid-sentence).
2. **Scene plan**
   - Generate narration chunks and English image prompts.
   - Use **Fix English prompts** for Hindi/short prompts.
   - Use **Restyle for current style** after changing the visual preset.
   - Review and approve.
3. **Sample studio**
   - **Voice:** audition Chatterbox with exaggeration/CFG/temperature. Click
     **Preview spoken text** to see exactly how amounts and acronyms will be read.
   - **Image:** generate one scene with the selected style/engine.
   - **Music:** audition an ACE-Step bed.
   - **Subtitle/motion preview:** render one scene through the real final assembly
     path, with optional subtitles and music.
   - Approve every sample required by the gates.
4. **Production**
   - Batch images, music, narration and assembly. Completed assets are skipped.
   - Retry individual scenes without rerunning everything.
5. **Final review**
   - Watch the assembled video, approve it, and download `final.mp4`.

## Voice normalization

`pipeline/hindi_text.py` converts narration before TTS:

```text
₹38,000   -> अड़तीस हज़ार रुपये
₹14,500   -> चौदह हज़ार पाँच सौ रुपये
11.5%     -> ग्यारह दशमलव पाँच प्रतिशत
₹1.5 लाख  -> डेढ़ लाख रुपये
EMI       -> ईएमआई
CIBIL     -> सिबिल
```

The voice QA checks for remaining digits, currency symbols, percentages and
English words. Synth output is peak-normalized with short fades to avoid clipping.
If a number still sounds wrong, use **Preview spoken text**, edit the narration,
or extend `pipeline/hindi_text.py`.

## Project data

Each project is self-contained under `projects/<id>/`:

```text
projects/<id>/
  project.json
  story.md
  scenes.json
  images/
  audio/
  video/
  studio/
    state.json
    config.json
    samples/
    versions/
```

`projects/`, `models/`, `tts_env/` and `studio/.secrets.json` are gitignored.
The repository does not include model weights, generated projects, or local
environments.

## Repository layout

```text
pipeline/                 # story, scenes, images, music, TTS, assembly
  workflows/              # ComfyUI workflow JSON
  hindi_text.py           # Hindi number/currency normalization
studio/                   # FastAPI backend + vanilla HTML/CSS/JS UI
  ui/                     # UI and style sample gallery
  start.cmd               # Windows launcher
requirements.txt          # studio/pipeline Python dependencies
requirements-tts.txt      # Chatterbox environment dependencies
```

## Direct pipeline CLI

You can still run the pipeline without the studio:

```powershell
cd pipeline
$env:PYTHONIOENCODING = "utf-8"

..\.venv\Scripts\python.exe story.py --topic "A story about..." --minutes 5 --chapters 5
..\.venv\Scripts\python.exe scenes.py
..\.venv\Scripts\python.exe images.py --engine sdxl
..\.venv\Scripts\python.exe music.py
..\tts_env\Scripts\python.exe tts.py
..\.venv\Scripts\python.exe assemble.py
```

## Troubleshooting

- **ComfyUI offline** — start it and check
  `http://127.0.0.1:8188/system_stats`.
- **Missing images/music** — verify the ComfyUI model filenames match the
  workflow JSON, or edit the workflow files.
- **Chatterbox not found** — create `tts_env` and install
  `requirements-tts.txt`, including a CUDA PyTorch build.
- **A figure sounds wrong** — click **Preview spoken text** in Sample studio and
  check the normalized Hindi. Add exceptions to `pipeline/hindi_text.py`.
- **Story is too short or ends mid-sentence** — regenerate; the new gates block
  approval. Use more chapters or a model with a larger output budget.
- **OpenCode 401/403** — verify the key belongs to a Go-enabled workspace and
  that the model/region is allowed.
- **A gate is blocked** — approve the required story, scene, voice, image, music
  and preview-clip stages in order.
- **Port already in use** — set `STUDIO_PORT` before starting.

## Credits

Built on the local AI media stack: OpenMontage conventions, ComfyUI, SDXL,
Z-Image Turbo, ACE-Step, Chatterbox Multilingual, Ollama and FFmpeg.

No license file is included yet. Add one before redistributing model outputs or
commercial use.
