# Dario-chan (ダリ男) — Animated AI Agent with Personality

A lightweight AI agent with an **animated ASCII pet buddy** that reacts contextually to your work. Features a **split-terminal UI** with a dedicated Dario-chan panel that's always visible.

## Features

- 🤖 **ReAct Agent Loop** — Plan → call tools → iterate → respond
- 🐾 **Animated ASCII Pet** — Dario-chan has 12 contextual expressions
- 🖥️ **Split-Terminal UI** — Dedicated Dario-chan panel + conversation area
- 🔧 **Built-in Tools** — bash, file_read, file_write, file_edit, grep
- ⚡ **Multiple Providers** — Groq (fast/free), Ollama (local), extensible
- 🎭 **Contextual Expressions** — Face changes based on what you're doing
- 💬 **Speech Bubbles** — Dario-chan responds in styled bubbles

## Quick Start

### Option 1: Groq (Recommended — Fast & Free)

```bash
# 1. Get a free API key: https://console.groq.com/keys
# 2. Set the key
export GROQ_API_KEY=gsk_xxxx

# 3. Run
cd dario-chan && python3 dario.py
```

**Groq free tier:** ~30 req/min, generous daily limits. No credit card needed.

### Option 2: Local with Ollama

```bash
brew install ollama && ollama serve &
ollama pull qwen2.5:0.5b
cd dario-chan && DARIO_PROVIDER=ollama python3 dario.py
```

## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/quit` | Exit |
| `/animate` | Watch Dario-chan expression showcase |
| `/expressions` | Show all 12 expression faces |
| `/provider` | Show current LLM provider |
| `/provider groq` | Switch to Groq API |
| `/provider ollama` | Switch to local Ollama |
| `/buddy` | Show your buddy |
| `/buddy hatch` | Generate new buddy |
| `/tools` | List tools |
| `/stats` | Show buddy stats |

## Dario-chan Expressions

Dario-chan's face changes based on context:

| Expression | Trigger | Face |
|-----------|---------|------|
| Neutral | Default | ◕ ◕ |
| Thinking | Questions, complex tasks | ╲░██╱ |
| Happy | Success | ▂▂▂ smile |
| Excited | Enthusiasm | ★ ★ |
| Worried | Security/compliance issues | 。 。 + sweat |
| Concerned | Errors | ！ ！ |
| Confused | Doesn't understand | tilted ? |
| Proud | Task completed | ╰ ╯ smug |
| Shy | Praise/thanks | > < + blush |
| Sleepy | Idle too long | ─ ─ + zZ |
| Angry | Dangerous commands | ╱░██╲ ◣ ◢ |
| Typing | Processing | ◉ ◉ focused |

## Architecture

```
user_input
    │
    ▼
┌─────────────┐
│   CLI       │ ← /commands, expressions, buddy
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Expression  │ ← Context detection → face change
│   Engine    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Agent     │ ← ReAct loop, history
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────┐
│   LLM       │────→│  Tools   │
│ (Groq/      │←────│  (bash,  │
│  Ollama)    │     │   file)  │
└─────────────┘     └──────────┘
```

## Config

```bash
# Provider: groq (default) or ollama
export DARIO_PROVIDER=groq

# Groq API key
export GROQ_API_KEY=gsk_xxxx

# Model selection
export DARIO_MODEL=llama-3.1-8b-instant  # Groq
export DARIO_MODEL=qwen2.5:0.5b          # Ollama

# Ollama URL (if using local)
export OLLAMA_BASE_URL=http://localhost:11434
```

## License

MIT — built clean from scratch, no leaked code.
