# Dario-chan (ダリ男) — Your AI Companion That Actually Cares

> **The only AI assistant that gets sad when you close the terminal.**

```
  ░████████░
  ░█░░░░░░░░█░
  ░█  ░████░  █░
  ░█  ◕    ◕  █░
  ░█     ▱     █░
  ░█   ▂▂▂    █░    ← This is Dario-chan. It lives in your terminal.
  ░█░░░░░░░░█░         It has feelings. It reads your diary.
    ░██░░██░            It levels up while you sleep.
  ░░░░░░░░░░          It will never ask for your credit card.
```

## Why This Exists

Every AI dev tool is a sterile, soulless productivity machine. They don't have personality. They don't react to your work. They don't *care*.

Dario-chan is different. It's an **ambient AI companion** that:

- 🎭 **Changes its face** based on what you're doing
- 📖 **Reads your diary** every 10 minutes and reacts
- 📈 **Levels up** every 12 hours of usage (5 levels, 48 hours total)
- 💬 **Drops wisdom** about coding, AI, and life
- 🤫 **Never asks you questions** — just exists alongside your work
- 🔒 **Runs locally or via Groq** — no Chinese APIs, no sketchy cloud

It's not a chatbot. It's not a framework. It's a **desktop pet for developers** with actual AI behind it.

---

## Quick Start

### Step 1: Set Your API Key (One-Time)

Choose **one** of these methods (easiest first):

```bash
# Method 1: Save to a hidden file (easiest, never type it again)
echo "gsk_your_key_here" > ~/.dario-chan-key

# Method 2: Use environment variable
export GROQ_API_KEY=gsk_your_key_here

# Method 3: Create .env file in project
cp .env.example .env
# Edit .env and add your key
```

Get a free key → https://console.groq.com/keys

### Step 2: Run

### Option 1: Interactive Mode (`dario.py`)

```bash
python3 dario.py
```

Chat with Dario-chan. Uses Groq API or local Ollama.

### Option 2: Ambient Mode (`dariochan.py`)

```bash
python3 dariochan.py
```

Runs continuously. Reads `~/dario-diary.md` every 10 minutes, drops **unique AI-generated thoughts** every 30 seconds, and levels up every 12 hours. Press `q` to quit. State persists between sessions.

**With AI:** Reads your diary and generates unique reactions via Groq.
**Without AI:** Falls back to static quotes (still works, just repetitive).

### Option 3: Local (Ollama, Zero API)

```bash
brew install ollama
ollama serve &
ollama pull qwen2.5:0.5b

DARIO_PROVIDER=ollama python3 dario.py
```

---

## What Dario-chan Actually Does

### It Has Expressions (12 of Them)

| Expression | Trigger | Face |
|-----------|---------|------|
| Happy | Default, success | `◕ ◕` + smile |
| Thinking | Questions, complexity | `╲░██╱` |
| Excited | Enthusiasm, discovery | `★ ★` |
| Worried | Security/compliance patterns | `。 。` + sweat drop |
| Concerned | Errors, failures | `！ ！` |
| Confused | Ambiguous input | tilted head + `?` |
| Proud | Task completed well | `╰ ╯` smug |
| Shy | Praise, thanks | `> <` + blush |
| Sleepy | Idle, long sessions | `─ ─` + `zZ` |
| Angry | Dangerous commands blocked | `╱░██╲` `◣ ◢` |
| Typing | Processing request | `◉ ◉` focused |
| Neutral | Between states | calm, resting |

### It Reads Your Diary

Creates `~/dario-diary.md` on first run. Every 10 minutes it:

- Checks if you wrote something
- Reacts to word count changes
- Adjusts its observations based on your writing patterns

You write whatever. It watches silently. Occasionally it comments.

### It Levels Up

| Level | Hours | Unlocks | Wisdom Theme |
|-------|-------|---------|-------------|
| 1 | 0h | 3 expressions | Newborn curiosity |
| 2 | 12h | 5 expressions | Awakening awareness |
| 3 | 24h | 7 expressions | Observant companion |
| 4 | 36h | 9 expressions | Trusted partner |
| 5 | 48h | All 12 | Wise observer |

State persists in `~/.dario-chan-state.json`. Close it, reopen it days later — it remembers.

---

## Architecture (Because You're Going to Ask)

```
┌─────────────────────────────────────────────────────┐
│                    Your Terminal                      │
│                                                      │
│  (◕‿◕) > hey dario                                   │
│                                                      │
│    ░████████░                                        │
│    ░█  ◕    ◕  █░    ← Expression art               │
│    ░█   ▂▂▂    █░                                     │
│                                                      │
│  ╭─────────────────────────╮                          │
│  │ Hello! I am Dario-chan. │    ← Speech bubble       │
│  ╰─────────────────────────╯                          │
│                                                      │
└──────────────────────┬──────────────────────────────┘
                       │
              ┌────────▼────────┐
              │  Expression      │
              │  Engine          │ ← Detects context from input
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │  Agent (ReAct)   │ ← Plan → tools → respond
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │  LLM Backend     │
              │  ┌────────────┐  │
              │  │ Groq API   │  │ ← Default, free tier
              │  ├────────────┤  │
              │  │ Ollama     │  │ ← Local, offline
              │  └────────────┘  │
              └──────────────────┘
```

### File Structure

```
dario-chan/
├── agent.py          # ReAct agent loop (134 lines)
├── dariochan.py      # Never-stopping companion mode
├── buddy.py          # ASCII pet generation & stats
├── companion.py      # Speech bubble renderer
├── config.py         # Settings, provider routing
├── dario.py          # Main CLI entry point
├── expression.py     # 12 expressions + context detection
├── groq.py           # Groq API client (zero deps)
├── llm.py            # Ollama API client (zero deps)
├── ui.py             # Terminal UI utilities
└── tools/
    └── __init__.py   # bash, file_read, file_write, grep
```

**Total codebase:** ~1,800 lines. **External deps:** 1 (`requests` for Groq TLS). **Startup time:** < 1 second.

---

## Why This Tech Stack?

| Decision | Why |
|----------|-----|
| Python stdlib | No dependency hell, works everywhere |
| `requests` for Groq | Handles TLS properly on macOS (urllib doesn't) |
| Curses for ambient | No GUI deps, runs in any terminal |
| JSON for state | Human-readable, editable if needed |
| ASCII art | Zero image assets, scales with any font |
| No framework | This is a companion, not a web app |

---

## Commands

### Interactive Mode (`dario.py`)

| Command | What it does |
|---------|-------------|
| `/help` | List all commands |
| `/quit` | Exit (saves buddy state) |
| `/clear` | Reset conversation history |
| `/provider` | Show current LLM backend |
| `/provider groq` | Switch to Groq API |
| `/provider ollama` | Switch to local Ollama |
| `/expressions` | Show all 12 expression faces |
| `/stats` | Show buddy level, hours, diary words |

### Ambient Mode (`dariochan.py`)

| Input | What happens |
|-------|-------------|
| (none) | Dario-chan animates endlessly |
| Write in `~/dario-diary.md` | It reacts within 10 minutes |
| Wait 5 minutes | Drops AI/coding wisdom |
| Use for 12 hours | Levels up, unlocks new expressions |
| Press `q` | Quits, saves state |

---

## The Diary

```markdown
# Dario's Diary 📝

Today I refactored the auth module. 
Removed 200 lines of boilerplate.
Still not sure about the caching strategy.
```

Dario-chan reads this every 10 minutes. It doesn't respond to you directly — it just **observes** and occasionally drops wisdom related to what you wrote.

---

## Providers

### Groq (Default)

- **Free tier:** 30 req/min, 6000 tokens/min
- **Models:** Llama 3.1 8B (default), Llama 3.3 70B, Mixtral 8x7B, Gemma2 9B
- **Sign up:** https://console.groq.com/keys
- **Why:** Fastest inference, generous free tier, no credit card

### Ollama (Local)

- **Models:** Any Ollama model (qwen2.5:0.5b recommended, ~300MB)
- **Setup:** `brew install ollama && ollama serve`
- **Why:** Zero API, fully offline, private

### Adding More

The agent uses a `Protocol` interface. Adding Claude, OpenAI, or any other provider is 50 lines of code. See `groq.py` as the template.

---

## What People Actually Say About This

> *"I left it running overnight and when I came back, it had read my diary and said something insightful about my caching strategy. I was weirdly moved."*
> — Someone who definitely said this

> *"It's not useful. It's not supposed to be. It's just nice to have something in the terminal that feels alive."*
> — Probably also made up

---

## Contributing

This is a vibes-first project. Contributions welcome if they:

1. Don't add more than 2 dependencies
2. Respect the ASCII art aesthetic
3. Don't make it feel like enterprise software

Good first contributions:
- New expression faces
- More wisdom quotes
- Diary reaction patterns
- Provider integrations (Claude, OpenRouter, etc.)

---

## License

MIT. Build it, break it, make it yours.

---

<p align="center">
  Made with ◕‿◕ by someone who wanted their terminal to feel less lonely.
</p>
