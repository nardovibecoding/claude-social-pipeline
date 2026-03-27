<div align="center">
  <h1>claude-social-pipeline</h1>

  <p><strong>Capture insights while coding. Draft tweets without leaving the terminal.</strong></p>

  [![MCP Tools](https://img.shields.io/badge/MCP%20TOOLS-6-0057FF?style=for-the-badge)](https://github.com/nardovibecoding/claude-social-pipeline)
  [![Skills](https://img.shields.io/badge/SKILLS-2-FF6B00?style=for-the-badge)](https://github.com/nardovibecoding/claude-social-pipeline)
  [![Platform](https://img.shields.io/badge/PLATFORM-macOS%20%7C%20Linux-lightgrey?style=for-the-badge)](https://github.com/nardovibecoding/claude-social-pipeline)
  [![License](https://img.shields.io/badge/LICENSE-AGPL--3.0-red?style=for-the-badge)](LICENSE)
</div>

---

```bash
claude plugins install nardovibecoding/claude-social-pipeline
```

---

## What It Does

The best content comes from real work. This plugin makes it frictionless to capture insights as they happen, humanize drafts before publishing, and post from the terminal — without breaking flow.

**The pipeline:**

```
coding session
     │
     ├── interesting thing happens
     │       └── content_capture("discovered X")
     │                   └── ~/.claude/content_drafts/running_log.md
     │
     ├── session getting long
     │       └── session_checkpoint("built Y")
     │                   └── ~/.claude/content_drafts/checkpoint_ts.md
     │
     ├── task complete
     │       └── post_task_check()
     │                   └── "content-worthy: use content_capture"
     │
     └── ready to post
             └── /tweet suggest
                         └── git log → privacy filter → draft
                                     └── humanizer → approve → X API
```

---

## MCP Tools

Six tools Claude calls automatically during your session — no slash commands needed.

| Tool | What it does |
|------|-------------|
| `content_capture` | Save a tweet-worthy moment mid-session. Appends to `running_log.md` with timestamp and context. |
| `content_queue` | Manage tweet drafts — add, list, get next, mark posted. Priority-sorted queue. |
| `session_checkpoint` | Snapshot session state (summary, decisions, files changed) before `/clear` or context limit. |
| `post_task_check` | After finishing a task — scan session for content-worthy material and improvement patterns. |
| `set_reminder` | Terminal alert with no background service: `"30m"`, `"2h"`, or `"16:55"` (HKT). |
| `tweet_performance` | Pull engagement stats for recent tweets — likes, retweets, replies, views, engagement score. Auto-captures best performer to content log. |

---

## Skills

### `/tweet` — x-tweet

Draft, humanize, and post tweets. Runs every post through a multi-step pipeline before anything reaches the API.

**Pipeline:** git log → privacy filter → voice rules → content-humanizer → anti-pattern scan → manual approval → X API v2

**Modes:**

| Command | What it does |
|---------|-------------|
| `/tweet [topic]` | Draft from a topic, approve, post |
| `/tweet suggest` | Read git log, surface privacy-safe angles |
| `/tweet hot` | Search X for trending topics in your space |
| `/tweet draft` | Save to queue without posting |
| `/tweet queue` | View and pick from saved drafts |
| `/tweet thread` | Generate a 3–5 tweet thread |

**Never auto-posts.** Every tweet requires explicit approval before the X API is called.

**Env vars required:**
```env
X_API_KEY=your_key
X_API_SECRET=your_secret
X_ACCESS_TOKEN=your_token
X_ACCESS_TOKEN_SECRET=your_token_secret
```

---

### `content-humanizer`

Detects and removes AI writing patterns. Not a word-swap tool — it rebuilds voice from the ground up using a two-pass approach.

**Triggers:** `"sounds like AI"`, `"make it human"`, `"add personality"`, `"too generic"`, `"fix AI writing"`

**How it works:**

1. `humanizer_scorer.py` runs a 12-point checklist: filler words, hedge phrases, em-dash overuse, passive constructions, hollow intensifiers, and more
2. Produces a score (0–100) and a list of specific tells
3. Rewriter addresses each tell with concrete changes — not paraphrasing

**Before / After:**

```
BEFORE (AI score: 31/100)
"It's worth noting that this approach leverages cutting-edge techniques
to significantly enhance performance. The implementation showcases a
robust solution that addresses the core challenges effectively."

AFTER (AI score: 89/100)
"This drops response time by 40%. The trick: cache the embedding lookup
instead of recomputing on every request. Obvious in hindsight."
```

**Attribution:** Content humanizer skill originally by [Alireza Rezvani](https://github.com/AliiRezaa) — MIT licensed. Scorer script and voice techniques added for this distribution.

---

## Install

### Plugin (recommended)

```bash
claude plugins install nardovibecoding/claude-social-pipeline
```

### Manual

```bash
git clone https://github.com/nardovibecoding/claude-social-pipeline.git

# MCP server
pip install mcp
```

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "social-pipeline": {
      "command": "python",
      "args": ["/path/to/claude-social-pipeline/mcp/server.py"]
    }
  }
}
```

Copy skills:

```bash
cp -r claude-social-pipeline/skills/x-tweet ~/.claude/skills/
cp -r claude-social-pipeline/skills/content-humanizer ~/.claude/skills/
```

---

## Configuration

No config required for basic usage (content capture, checkpoints, humanizer).

For `x-tweet` posting, set in `.env`:

```env
X_API_KEY=your_key
X_API_SECRET=your_secret
X_ACCESS_TOKEN=your_token
X_ACCESS_TOKEN_SECRET=your_token_secret
```

For Telegram post alerts (optional):

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## Project Structure

```
claude-social-pipeline/
├── mcp/
│   ├── server.py              # MCP server — 6 content tools
│   ├── lib.py                 # Pure Python content functions
│   ├── patterns.py            # post_task_check patterns
│   └── pyproject.toml
├── skills/
│   ├── x-tweet/
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   ├── post_tweet.py          # X API v2 posting
│   │   │   └── tweet_stats.py         # Performance metrics
│   │   └── references/
│   │       ├── voice-rules.md
│   │       ├── templates.md
│   │       ├── anti-patterns.md
│   │       ├── hashtag-strategy.md
│   │       ├── content-calendar.md
│   │       └── engagement-data.md
│   └── content-humanizer/
│       ├── SKILL.md
│       ├── scripts/
│       │   └── humanizer_scorer.py
│       └── references/
│           ├── ai-tells-checklist.md
│           └── voice-techniques.md
├── README.md
└── LICENSE
```

Content drafts are written to `~/.claude/content_drafts/`:

```
~/.claude/content_drafts/
├── running_log.md       # All content_capture() moments
├── queue.md             # Tweet draft queue (priority-sorted)
└── checkpoint_*.md      # Session checkpoints
```

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=nardovibecoding/claude-social-pipeline&type=Date)](https://star-history.com/#nardovibecoding/claude-social-pipeline&Date)

---

## License

AGPL-3.0 — see [LICENSE](LICENSE).

`content-humanizer` skill includes work originally by [Alireza Rezvani](https://github.com/AliiRezaa) (MIT). See `skills/content-humanizer/SKILL.md` for full attribution.
