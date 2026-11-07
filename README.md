<a name="readme-top"></a>

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:00D9FF,100:7C3AED&height=140&section=header&reversal=false" width="100%" alt="" />

<!-- Animated Title -->
<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=32&duration=2800&pause=2000&color=00D9FF&center=true&vCenter=true&width=600&lines=Hey+Jarvis...;%F0%9F%8E%99%EF%B8%8F+I%27m+listening.;Your+AI+assistant%2C+locally+owned." alt="Typing SVG" />

<br/>

# 🤖 Jarvis Lite

**A fast, privacy-first AI voice assistant and computer control agent for Windows.**
Wake word → Listen → Think → Speak. No cloud microphone stream. Audio never leaves your machine.

<br/>

[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)
[![Stars](https://img.shields.io/github/stars/YOUR_USERNAME/jarvis-lite?style=for-the-badge&color=FFD700&logo=github)](https://github.com/YOUR_USERNAME/jarvis-lite/stargazers)
[![Issues](https://img.shields.io/github/issues/YOUR_USERNAME/jarvis-lite?style=for-the-badge&color=FF6B6B)](https://github.com/YOUR_USERNAME/jarvis-lite/issues)

![Groq](https://img.shields.io/badge/Groq-F55036?style=flat-square)
![Ollama](https://img.shields.io/badge/Ollama-000000?style=flat-square&logo=ollama&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![ONNX Runtime](https://img.shields.io/badge/ONNX_Runtime-005CED?style=flat-square&logo=onnx&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat-square&logo=opencv&logoColor=white)
![YOLO](https://img.shields.io/badge/YOLO-00FFFF?style=flat-square&logoColor=black)
![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=flat-square&logo=playwright&logoColor=white)

<br/>

<a href="#-installation"><b>Get Started</b></a> &nbsp;·&nbsp;
<a href="#-configuration">Configuration</a> &nbsp;·&nbsp;
<a href="#-voice-commands">Voice Commands</a> &nbsp;·&nbsp;
<a href="https://github.com/YOUR_USERNAME/jarvis-lite/issues">Report a Bug</a>

<br/>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%"/>

</div>

<br/>

## ✨ What Makes Jarvis Lite Different

> [!NOTE]
> Most voice assistants send your continuous microphone audio stream to external cloud servers. Jarvis Lite does not.
> Wake word detection, speech-to-text recognition, webcam computer vision, and speech synthesis all run directly on your own CPU. When using the default Groq cloud brain, only the transcribed text of your specific queries is sent; when configured with Ollama, the entire pipeline operates 100% offline.

<br/>

<div align="center">

| Feature | Jarvis Lite | Traditional Assistants |
|:--------|:-----------:|:----------------------:|
| Microphone audio stream stays local | ✅ | ❌ |
| Works fully offline | ✅ (Ollama mode) | ❌ |
| Sees through your webcam (YOLO) | ✅ | ❌ |
| Real-time Web UI dashboard included | ✅ | ❌ |
| Controls your Windows desktop & windows | ✅ | ❌ |
| Fully open & customizable | ✅ | ❌ |
| Free & subscription-free | ✅ | ❌ |

</div>

<br/>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%"/>

<br/>

## 📋 Table of Contents

<details open>
<summary><b>Jump to a section</b></summary>
<br/>

- [🧩 Architecture](#-architecture)
- [🚀 Features](#-features)
- [💻 Requirements](#-requirements)
- [📦 Installation](#-installation)
- [📥 Model Downloads](#-model-downloads)
- [🔧 Configuration](#-configuration)
- [⚡ Running Jarvis](#-running-jarvis)
- [🌐 Web UI Dashboard](#-web-ui-dashboard)
- [🎤 Voice Commands](#-voice-commands)
- [🤖 Agent Mode](#-agent-mode)
- [👀 Vision Mode](#-vision-mode)
- [🔊 TTS Engines](#-tts-engines)
- [🧰 Troubleshooting](#-troubleshooting)
- [📁 Project Structure](#-project-structure)
- [🧭 Roadmap](#-roadmap)
- [📄 License](#-license)

</details>

<br/>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%"/>

<br/>

## 🧩 Architecture

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│                                 JARVIS LITE                                  │
│                                                                              │
│  ┌────────────┐   ┌────────────┐   ┌─────────────────────────────────────┐   │
│  │    MIC     │──▶│    STT     │──▶│               ROUTER                │   │
│  │sounddevice │   │ Moonshine  │   │  ┌───────────────┬───────────────┐  │   │
│  └────────────┘   └────────────┘   │  │    Skills     │     Brain     │  │   │
│                                    │  │   (offline)   │ (Groq/Ollama) │  │   │
│  ┌────────────┐                    │  ├───────────────┼───────────────┤  │   │
│  │ WAKE WORD  │                    │  │    Vision     │     Agent     │  │   │
│  │openWakeWord│                    │  │    (YOLO)     │   (planner)   │  │   │
│  └────────────┘                    │  └───────────────┴───────────────┘  │   │
│                                    └──────────────────┬──────────────────┘   │
│                                                       │                      │
│  ┌────────────┐   ┌────────────┐                      ▼                      │
│  │  SPEAKER   │◀──│    TTS     │◀──────────[ Local WebSocket Hub ]           │
│  │sounddevice │   │ Paradee /  │                      │                      │
│  └────────────┘   │  Piper /   │                      ▼                      │
│                   │   Kokoro   │            [ Browser Dashboard ]            │
│                   └────────────┘            http://localhost:8765            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Wake:** `openWakeWord` monitors the local audio buffer for the wake phrase *"Hey Jarvis"*.
2. **Listen:** `moonshine-voice` transcribes incoming speech locally on the CPU with sub-word partial streaming.
3. **Route:** The router evaluates regex skills (media, window management, timers, notes, memory). If no direct skill matches, it engages the restricted Agent planner or Conversational Brain.
4. **Speak:** Audio is streamed to `paradee`, `piper`, or `kokoro` and played via `sounddevice`.
5. **Dashboard:** The internal FastAPI WebSocket server pushes audio levels, transcripts, state transitions, and tool actions to the web interface in real time.

<div align="right"><a href="#readme-top">⬆ Back to top</a></div>

<br/>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%"/>

<br/>

## 🚀 Features

<details open>
<summary><b>🗣️ Voice Interaction & Audio</b></summary>
<br/>

- **Wake word** — Say *"Hey Jarvis"* to wake; Jarvis plays a chime and begins listening.
- **Always-on mode** — Set `wake.enabled: false` to keep listening continuously without a wake phrase.
- **Interrupt mid-speech** — Say the wake word or make noise while Jarvis is speaking to cut it off immediately.
- **Follow-up window** — Jarvis remains attentive for several seconds after replying so you can chain commands naturally.
- **Multi-step chaining** — Chain multiple intents in one breath: *"Open Notepad and type meeting notes and then snap Notepad to the right"*.

</details>

<details>
<summary><b>🧠 Intelligence (Brain)</b></summary>
<br/>

- **Groq (Default)** — Ultra-fast cloud LLM inference using models like `llama-3.3-70b-versatile` with sub-500 ms time-to-first-token.
- **Ollama (100% Offline)** — Seamlessly plug in local models (e.g. `qwen2.5:0.5b`, `llama3.2`) for completely private, air-gapped conversations.
- **Conversation Memory** — Configurable context window (default: 4 turns) stored strictly in memory during your session.
- **Streaming Audio Synthesis** — Chunks tokens from the model into natural sentence boundaries and speaks before generation finishes.

</details>

<details>
<summary><b>🛠️ Built-in Skills (Instant & Offline)</b></summary>
<br/>

| Category | Examples |
|:---|:---|
| **Apps & Web** | *"Open Chrome"*, *"Search YouTube for lo-fi beats"*, *"Go to GitHub"* |
| **Window Control** | *"Snap Notepad to the left"*, *"Maximize Edge"*, *"Close Calculator"* |
| **Keyboard** | *"Copy"*, *"Paste"*, *"Select all"*, *"New tab"*, *"Scroll down a lot"* |
| **Typing & Dictation** | *"Type hello world"*, *"Write a short thank you email in Notepad"* |
| **Media Control** | *"Play"*, *"Pause"*, *"Next track"*, *"Volume up"*, *"Mute"* |
| **System Info** | *"Take a screenshot"*, *"Battery level"*, *"CPU usage"*, *"System status"* |
| **Notes** | *"Note this down: buy milk"*, *"Read my notes"*, *"Show my notes"*, *"Delete last note"* |
| **Long-Term Memory** | *"Remember that my flight is at 3pm"*, *"When is my flight?"*, *"Forget my flight"* |
| **Timers & Reminders** | *"Set a timer for 10 minutes"*, *"Remind me at 4pm to take medicine"*, *"Snooze"* |
| **Alarms** | *"Wake me up at 7am tomorrow"*, *"Cancel my alarm"* |
| **Vision** | *"What do you see?"*, *"Is there a person?"*, *"How many cups are on the desk?"* |
| **Basics** | *"What time is it?"*, *"What's today's date?"*, *"Goodbye"* |

</details>

<details>
<summary><b>👁️ Vision (Webcam Object Detection)</b></summary>
<br/>

- Runs **YOLO** on CPU via ONNX Runtime — detects 80 standard COCO object categories in real time.
- Zero frame delay: keeps only the latest camera frame in memory to prevent processing queues.
- Query with natural questions: *"What do you see?"*, *"Can you see a cup?"*, *"How many people are here?"*.
- Camera stays idle when not in use; detections are evaluated on demand.

</details>

<details>
<summary><b>🤖 Restricted Agent Mode</b></summary>
<br/>

- Plans multi-step desktop tasks using structured LLM reasoning.
- **Dry-run validation** — Inspects and builds the execution plan before triggering actions.
- **Confirmation gate** — Destructive or irreversible steps (e.g. closing windows with unsaved changes) pause and verbally request approval (*"Should I close Notepad? Say yes or no."*).
- **Strict allowlist** — Only whitelisted, locally verified tools can execute.
- **Dynamic app catalog** — Safe discovery of installed Windows applications from Start Menu and AppsFolder without running arbitrary shell scripts.

</details>

<details>
<summary><b>🖥️ Real-Time Glassmorphism Web UI</b></summary>
<br/>

- Built-in local web dashboard served at `http://localhost:8765`.
- Visual reactive audio orb that pulses to your microphone volume.
- Live streaming partial and final transcription feed.
- Visual feedback on Jarvis's internal states (`sleeping`, `listening`, `thinking`, `speaking`).
- Real-time tool execution status badges.

</details>

<div align="right"><a href="#readme-top">⬆ Back to top</a></div>

<br/>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%"/>

<br/>

## 💻 Requirements

| Requirement | Minimum | Recommended |
|:---|:---|:---|
| **OS** | Windows 10 (64-bit) | Windows 11 (64-bit) |
| **Python** | 3.12 | 3.12 |
| **RAM** | 4 GB | 8 GB+ |
| **CPU** | Modern x64 dual-core | 4+ cores (AVX2 supported) |
| **Microphone** | Any input microphone | Dedicated USB headset or array mic |
| **Webcam** | *(Optional)* USB or built-in webcam | 720p / 1080p webcam |
| **Groq API Key** | Required for default Groq mode | Free account from [console.groq.com](https://console.groq.com) |
| **Ollama** | Required only for offline mode | [ollama.com](https://ollama.com) |

> [!NOTE]
> **No discrete GPU required.** Every component is optimized to run efficiently on CPU.

<div align="right"><a href="#readme-top">⬆ Back to top</a></div>

<br/>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%"/>

<br/>

## 📦 Installation

### Step 1 — Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/jarvis-lite.git
cd jarvis-lite
```

### Step 2 — Create & Activate Virtual Environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

> [!TIP]
> Ensure you see `(.venv)` in your terminal prompt.

### Step 3 — Install Dependencies

```powershell
pip install -r requirements.txt
```

> [!NOTE]
> ⏳ Packages including `onnxruntime`, `opencv-python`, and speech tools may take a couple of minutes to download and cache.

### Step 4 — Set Your Groq API Key

If using the default Groq brain, obtain a free key from [console.groq.com](https://console.groq.com).

**Option A (Recommended — `.env` file):** Copy `.env.example` to `.env` in the root directory:

```powershell
copy .env.example .env
```

Open `.env` in any text editor and fill in your key:

```env
GROQ_API_KEY=gsk_your_actual_key_here
```

**Option B (Windows User Environment Variable):**

```powershell
[System.Environment]::SetEnvironmentVariable("GROQ_API_KEY", "gsk_your_key_here", "User")
```

*(Restart your terminal after setting the environment variable).*

> [!TIP]
> Prefer 100% offline with Ollama? Skip this step and see the [Configuration](#-configuration) section below.

### Step 5 — (Optional) Install Playwright for Browser Agent CLI

If you wish to test the standalone public web browser agent (`test_browser_agent.py`):

```powershell
playwright install chromium
```

<div align="right"><a href="#readme-top">⬆ Back to top</a></div>

<br/>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%"/>

<br/>

## 📥 Model Downloads

Jarvis Lite organizes downloaded models under the `models/` directory.

### 1. 🗣️ Speech-to-Text — Moonshine (Automatic)

The Moonshine base model downloads automatically via Hugging Face on the first launch. No manual action needed.

### 2. 🎙️ Wake Word — openWakeWord (Automatic)

The *"Hey Jarvis"* wake word model downloads automatically on initial boot.

### 3. 🔊 Text-to-Speech (Choose One Engine)

<details open>
<summary><b>Option A: Paradee</b> — Default, Fastest & Smallest</summary>
<br/>

Paradee is a tiny, distilled voice model bundled directly through Python dependencies.
No manual download required. It is configured as default in `config.yaml`.

</details>

<details>
<summary><b>Option B: Piper</b> — Good Quality, Fast</summary>
<br/>

Download the ONNX model into `models/piper/`.

</details>

<details>
<summary><b>Option C: Kokoro-82M</b> — Highest Audio Quality</summary>
<br/>

Download the ONNX model into `models/kokoro/`.

</details>

### 4. 👁️ Vision — YOLO Object Detection (Optional)

Required if `vision.enabled: true` in `config.yaml`:

- Download `yolo26n.onnx` (or export YOLOv8/11 nano to ONNX with 640x640 input shape).
- Place it in: `models/yolo/yolo26n.onnx`

### Directory Overview

```text
models/
├── kokoro/
│   ├── kokoro-v1.0.int8.onnx
│   └── voices-v1.0.bin
├── piper/
│   ├── en_US-lessac-medium.onnx
│   └── en_US-lessac-medium.onnx.json
└── yolo/
    └── yolo26n.onnx
```

<div align="right"><a href="#readme-top">⬆ Back to top</a></div>

<br/>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%"/>

<br/>

## 🔧 Configuration

All user settings are defined in `config.yaml` at the repository root:

```yaml
# ── Audio ─────────────────────────────────────────────────────────────
audio:
  sample_rate: 16000       # Required for speech models
  input_device: null       # null = default microphone; set to integer index to override
  output_device: null      # null = default speaker

# ── TTS Engine ────────────────────────────────────────────────────────
tts:
  engine: paradee          # paradee | piper | kokoro

# ── Brain (LLM) ───────────────────────────────────────────────────────
brain:
  engine: groq             # groq | ollama
  history_turns: 4         # Dialog history turns remembered
  groq:
    model: llama-3.3-70b-versatile
    max_reply_tokens: 120
    temperature: 0.4
  ollama:
    model: qwen2.5:0.5b    # Any locally pulled Ollama model
    keep_alive: 30m

# ── Wake Word ─────────────────────────────────────────────────────────
wake:
  enabled: true            # false = always listening without wake word
  threshold: 0.5           # Lower = more sensitive, higher = fewer false wakes
  threshold_while_busy: 0.7 # Stricter threshold while Jarvis is talking to prevent self-trigger
  listen_seconds: 8        # Listening timeout after wake chime
  follow_up_seconds: 6     # Listening window maintained after answering

# ── Vision ────────────────────────────────────────────────────────────
vision:
  enabled: true            # false = webcam remains off
  camera_index: 0          # 0 = primary webcam

# ── Assistant Identity ────────────────────────────────────────────────
assistant:
  name: Jarvis
  user_name: YourName      # ← Set your preferred name
```

### Running 100% Offline with Ollama

1. Download and run [Ollama](https://ollama.com).
2. Pull a lightweight model:

   ```bash
   ollama pull qwen2.5:0.5b
   ```

3. In `config.yaml`, change `brain.engine` to:

   ```yaml
   brain:
     engine: ollama
   ```

<div align="right"><a href="#readme-top">⬆ Back to top</a></div>

<br/>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%"/>

<br/>

## ⚡ Running Jarvis

With your virtual environment active:

```powershell
python -m jarvis.main
```

Or simply double-click `run.bat` (or launch `run.ps1`).

**Expected Startup Log:**

```text
Loading voice...
Loading ears...
  Moonshine model: moonshine/base
Starting camera and vision...
Loading brain (the first time can take a while)...
UI: http://localhost:8765
Ready! Say 'Hey Jarvis' (wait for the chime), then ask something.
Say 'goodbye' or press Ctrl+C to quit.
```

> [!TIP]
> **To Stop:** Say *"Goodbye"* or press `Ctrl + C` in the console.

<div align="right"><a href="#readme-top">⬆ Back to top</a></div>

<br/>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%"/>

<br/>

## 🌐 Web UI Dashboard

Jarvis Lite features an integrated, real-time web dashboard.

While Jarvis is running, open: **[http://localhost:8765](http://localhost:8765)**

```text
┌─────────────────────────────────────────────────────────────────────────┐
│  JARVIS                    [● CONNECTED]                       12:45 PM │
│                                                                         │
│                              ╭─────────╮                                │
│                              │  ◉   ◉  │                                │
│                              │    ▽    │                                │
│                              ╰─────────╯                                │
│                          (Reactive Audio Orb)                           │
│                                                                         │
│               User: "What open windows do I have right now?"            │
│               Jarvis: "You have Chrome, VS Code, and Spotify open."     │
│                                                                         │
│  [STATUS: LISTENING]                           [TOOL: WINDOW.LIST_OPEN] │
└─────────────────────────────────────────────────────────────────────────┘
```

- **Reactive Orb:** Canvas-rendered visualizer that pulses and reacts to microphone sound levels.
- **Live Transcription:** Shows partial streaming transcriptions as you speak, switching to final text automatically.
- **Streaming Output:** Displays speech chunk-by-chunk in sync with the audio synthesizer.
- **Zero External Network Dependencies:** Served locally with no CDNs or tracking scripts.

<div align="right"><a href="#readme-top">⬆ Back to top</a></div>

<br/>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%"/>

<br/>

## 🎤 Voice Commands

> [!TIP]
> Start your request with **"Hey Jarvis"** (unless always-on mode is active).

<details open>
<summary><b>🌍 Apps & Web Navigation</b></summary>
<br/>

- `"Open Chrome"`
- `"Launch Notepad"`
- `"Open File Explorer"`
- `"Go to GitHub"`
- `"Search YouTube for lo-fi beats"`
- `"Search Google for python dataclass tutorial"`

</details>

<details>
<summary><b>🪟 Window Management</b></summary>
<br/>

- `"Snap Chrome to the left and Notepad to the right"`
- `"Maximize Edge"`
- `"Minimize everything"` / `"Show desktop"`
- `"Switch to Visual Studio Code"`
- `"Close Calculator"`
- `"What windows do I have open?"`

</details>

<details>
<summary><b>⌨️ Typing & Keyboard Shortcuts</b></summary>
<br/>

- `"Type hello world"`
- `"Type this into Notepad: meeting at 3pm"`
- `"Write a short poem in Notepad"`
- `"Copy"` &nbsp;|&nbsp; `"Paste"` &nbsp;|&nbsp; `"Select all"` &nbsp;|&nbsp; `"Save"`
- `"New tab"` &nbsp;|&nbsp; `"Close tab"` &nbsp;|&nbsp; `"Reopen tab"`
- `"Scroll down"` &nbsp;|&nbsp; `"Scroll up a lot"`

</details>

<details>
<summary><b>📝 Notes & Memory</b></summary>
<br/>

- `"Note this down: buy milk and coffee beans"`
- `"Read my notes"`
- `"Show my notes"`
- `"Delete the last note"`
- `"Remember that my locker code is 4821"`
- `"What is my locker code?"`
- `"Forget my locker code"`

</details>

<details>
<summary><b>⏰ Timers, Alarms & Reminders</b></summary>
<br/>

- `"Set a timer for 15 minutes"`
- `"How much time is left on my timer?"`
- `"Cancel my timer"`
- `"Remind me in 45 minutes to stretch"`
- `"Wake me up at 7am tomorrow"`
- `"Snooze for 10 minutes"`

</details>

<details>
<summary><b>🎵 System & Media</b></summary>
<br/>

- `"Take a screenshot"`
- `"How is my battery doing?"`
- `"CPU usage"` / `"System status"`
- `"Volume up"` &nbsp;|&nbsp; `"Volume down"` &nbsp;|&nbsp; `"Mute"`
- `"Play"` &nbsp;|&nbsp; `"Pause"` &nbsp;|&nbsp; `"Next track"`

</details>

<details>
<summary><b>👁️ Vision (Webcam)</b></summary>
<br/>

- `"What do you see?"`
- `"Is there a person?"`
- `"How many bottles do you see?"`
- `"Can you see a phone?"`

</details>

<details>
<summary><b>🔗 Multi-Step Action Chaining</b></summary>
<br/>

- `"Open Notepad and type hello world"`
- `"Open Chrome and go to YouTube and search for jazz"`
- `"Take a screenshot and then show desktop"`

</details>

<div align="right"><a href="#readme-top">⬆ Back to top</a></div>

<br/>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%"/>

<br/>

## 🤖 Agent Mode

Agent mode empowers Jarvis to handle complex requests by breaking them down into steps, validating them against a strict tool catalog, and gating risky operations behind explicit user confirmation.

**Enable in `config.yaml`:**

```yaml
agent:
  enabled: true
  voice_enabled: true
  max_steps: 6
  execution:
    allow_low_risk: true
```

### How Confirmation Gating Works

1. **You say:** *"Close Photoshop and open Figma"*.
2. Jarvis creates a plan and evaluates the risk level of each tool call.
3. For reversible or safe steps (`app.open`), it proceeds immediately.
4. For destructive steps (`window.close`), Jarvis pauses and asks verbally:

   > *"Do you want me to close Photoshop? Say yes or no."*

5. If you say **"Yes"**, the step executes. If you say **"No"** or remain silent, the action is cancelled.

<div align="right"><a href="#readme-top">⬆ Back to top</a></div>

<br/>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%"/>

<br/>

## 👀 Vision Mode

Jarvis can observe your surroundings using your webcam and a local YOLO model (80 COCO classes).

```yaml
vision:
  enabled: true
  camera_index: 0
  confidence: 0.25
  sure_confidence: 0.45
```

**Detectable Objects Include:** `person`, `bicycle`, `car`, `laptop`, `mouse`, `keyboard`, `cell phone`, `cup`, `bottle`, `chair`, `couch`, `book`, `clock`, `tv`...

**Dialogue Examples:**

```text
User:   "Hey Jarvis, what do you see?"
Jarvis: "I can see a person, a laptop, and a cup."

User:   "Hey Jarvis, how many people are here?"
Jarvis: "I can see 2 people."

User:   "Hey Jarvis, is there a phone?"
Jarvis: "Yes, I can see a cell phone."
```

<div align="right"><a href="#readme-top">⬆ Back to top</a></div>

<br/>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%"/>

<br/>

## 🔊 TTS Engines

| Engine | Latency | Voice Quality | Footprint | Setup |
|:---|:---|:---|:---|:---|
| **Paradee** *(Default)* | ⚡ Ultra-fast (<100ms) | Good | ~50 MB | Automatic via pip |
| **Piper** | ⚡ Fast (~150ms) | Natural | ~65 MB | Download ONNX to `models/piper/` |
| **Kokoro-82M** | 🐢 Moderate (~350ms) | 🏆 Studio Quality | ~310 MB | Download ONNX to `models/kokoro/` |

> [!TIP]
> Switch engines seamlessly in `config.yaml` under `tts.engine`.

<div align="right"><a href="#readme-top">⬆ Back to top</a></div>

<br/>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%"/>

<br/>

## 🧰 Troubleshooting

- ❌ **"GROQ_API_KEY is not set"**
- ❌ **"Could not open the webcam"**
- ❌ **Microphone not capturing speech**
- ❌ **False wake word activations**

<div align="right"><a href="#readme-top">⬆ Back to top</a></div>

<br/>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%"/>

<br/>

## 📁 Project Structure

<details open>
<summary><b>Expand repository tree</b></summary>
<br/>

```text
jarvis-lite/
│
├── config.yaml                  # Master settings configuration
├── requirements.txt             # Pinned dependency lockfile
├── requirements.in              # Top-level dependencies specification
├── pytest.ini                   # Pytest configuration
├── run.bat                      # Windows one-click batch launcher
├── run.ps1                      # Windows PowerShell launcher
├── .env.example                 # Environment variables template
├── LICENSE                      # MIT License
│
├── jarvis/                      # Core package
│   ├── main.py                  # Entry point and voice loop
│   ├── config.py                # Config loader, validation, and data paths
│   ├── router.py                # Regex intent routing and multi-step execution
│   ├── reply.py                 # Structured action reply model
│   ├── mic.py                   # Microphone input stream (sounddevice)
│   ├── audio.py                 # Speaker output stream and interruption
│   ├── wake.py                  # openWakeWord integration
│   ├── scheduler.py             # Timers, alarms, and reminders engine
│   ├── store.py                 # Thread-safe JSON persistence
│   ├── sounds.py                # Chime synthesizers
│   ├── textutil.py              # String formatting and second-person converters
│   ├── timeparse.py             # Natural language time parsing engine
│   ├── ui_server.py             # Local FastAPI WebSocket server
│   ├── logger.py                # Rotating structured file logging
│   │
│   ├── brain/                   # LLM inference backends
│   │   ├── groq_brain.py        # Groq streaming client
│   │   ├── ollama_brain.py      # Ollama local client
│   │   └── chunker.py           # Streaming token-to-sentence segmenter
│   │
│   ├── stt/                     # Speech-to-text
│   │   └── moonshine_engine.py  # Local Moonshine ONNX STT
│   │
│   ├── tts/                     # Text-to-speech engines
│   │   ├── paradee_engine.py    # Lightweight fast TTS
│   │   ├── piper_engine.py      # Piper ONNX TTS
│   │   ├── kokoro_engine.py     # Kokoro-82M neural TTS
│   │   └── text.py              # Text normalizer and number expander
│   │
│   ├── vision/                  # Computer vision
│   │   ├── camera.py            # Non-blocking OpenCV capture thread
│   │   ├── detector.py          # YOLO ONNX object detector
│   │   ├── describe.py          # Detection-to-natural-language formulation
│   │   └── rules.py             # Vision question pattern matching
│   │
│   ├── agent/                   # Restricted autonomous agent
│   │   ├── voice_agent.py       # Spoken confirmation wrapper
│   │   ├── planner.py           # Structured dry-run planner
│   │   ├── executor.py          # Allowlisted tool execution engine
│   │   ├── tools.py             # Catalog of allowed tools and schemas
│   │   ├── confirmation.py      # Timed approval gates
│   │   ├── contracts.py         # Plan and Step data models
│   │   └── app_catalog.py       # Safe Windows application discovery
│   │
│   ├── browser/                 # Grounded public web navigation (Playwright)
│   │   ├── session.py           # Isolated browser session & SSRF protection
│   │   └── agent.py             # Grounded web planner
│   │
│   └── skills/                  # Local offline capability modules
│       ├── registry.py          # Skill registry & context state
│       ├── apps_skills.py       # Application launch & tab reuse logic
│       ├── windows_skills.py    # Window snapping, focus, and layout
│       ├── keys_skills.py       # Typing, shortcuts, and media controls
│       ├── system_skills.py     # System stats, battery, and screenshots
│       ├── notes_skills.py      # Local note capture and reading
│       ├── memory_skills.py     # Keyword-based persistent knowledge store
│       ├── reminder_skills.py   # Timers, alarms, and snoozing
│       ├── winapi.py            # Windows ctypes & Win32 API bindings
│       └── windowtools.py       # Window handle inspection utilities
│
├── ui/                          # Real-time web UI
│   └── index.html               # Particle visualizer & WebSocket frontend
│
└── tests/                       # Automated test suite
    ├── conftest.py              # Pytest isolation fixtures
    ├── test_config.py           # Config and environment validation tests
    ├── test_router.py           # Normalization and command splitting tests
    ├── test_scheduler.py        # Timer and reminder queue tests
    ├── test_store.py            # JSON persistence and recovery tests
    └── test_timeparse.py        # Natural time parsing tests
```

</details>

<div align="right"><a href="#readme-top">⬆ Back to top</a></div>

<br/>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%"/>

<br/>

## 🧭 Roadmap

- [ ] Multi-turn autonomous tool chaining
- [ ] Fully local Vision-Language Model (VLM) for deep screen understanding
- [ ] System tray icon and background Windows service mode
- [ ] Local calendar and email client integration
- [ ] Multi-language speech recognition support

<div align="right"><a href="#readme-top">⬆ Back to top</a></div>

<br/>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%"/>

<br/>

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

<br/>

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:7C3AED,100:00D9FF&height=100&section=footer&reversal=false" width="100%" alt="" />

</div>