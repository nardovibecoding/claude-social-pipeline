"""claude-content-pipeline MCP server.

5 tools for Claude Code content workflow:
  content_capture    — save tweet-worthy moments while coding
  content_queue      — manage tweet draft queue
  session_checkpoint — save session state before /clear
  post_task_check    — check session for content-worthy material
  set_reminder       — timed terminal alerts (HH:MM or Nm/Nh)

# Copyright (c) 2026 Nardo (nardovibecoding)
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import subprocess
import sys
from pathlib import Path

# Ensure local lib is importable when run as a subprocess
sys.path.insert(0, str(Path(__file__).parent))

import lib as _lib
from patterns import check_patterns

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("mcp not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

mcp = FastMCP("content-pipeline")

# In-memory session actions (shared with lib.session_actions)
_session_actions = _lib.session_actions


# --- Tool 1: content_capture ---
@mcp.tool()
def content_capture(moment: str, category: str = "insight") -> dict:
    """Save a content-worthy moment to the running draft log. Call when something interesting happens worth tweeting about.

    Args:
        moment: what happened — the insight, discovery, result, or aha moment
        category: one of: insight, result, code, number, journey, mistake
    """
    return _lib.content_capture(moment, category)


# --- Tool 2: content_queue ---
@mcp.tool()
def content_queue(action: str = "list", tweet: str = "", priority: str = "normal") -> dict:
    """Manage tweet draft queue. Add drafts, list queue, get next to post.

    Args:
        action: "add" to add a draft, "list" to see queue, "next" to get highest priority, "posted" to mark top as done
        tweet: tweet text (required for "add")
        priority: "high", "normal", "low" (for "add")
    """
    return _lib.content_queue(action, tweet, priority)


# --- Tool 3: session_checkpoint ---
@mcp.tool()
def session_checkpoint(summary: str, key_decisions: list[str] = None, files_changed: list[str] = None) -> dict:
    """Save session state to checkpoint file. Call at context 20%/40%/60% or before /clear.

    Args:
        summary: what was accomplished this session (2-3 sentences)
        key_decisions: important decisions made (list of strings)
        files_changed: key files created or modified
    """
    return _lib.session_checkpoint(summary, key_decisions, files_changed)


# --- Tool 4: post_task_check ---
@mcp.tool()
def post_task_check() -> dict:
    """Check recent session actions against known improvement patterns. Call after completing a task."""
    actions = list(_session_actions)
    suggestions = check_patterns(actions)

    # Check if session produced content-worthy material
    content_worthy = False
    content_signals = []
    for a in actions:
        detail = a.get("detail", "")
        act = a.get("action", "")
        if act in ("new_hook", "new_mcp_tool", "new_skill", "architecture_change"):
            content_worthy = True
            content_signals.append(f"{act}: {detail}")

    if content_worthy:
        suggestions.append(
            f"Content-worthy session! Signals: {', '.join(content_signals[:5])}. "
            "Use content_capture to save moments."
        )

    return {
        "recent_actions": actions[-10:],
        "suggestions": suggestions,
        "content_worthy": content_worthy
    }


# --- Tool 5: set_reminder ---
@mcp.tool()
def set_reminder(time_spec: str, message: str) -> dict:
    """Set a timer reminder that alerts in the terminal.

    Args:
        time_spec: "16:55" for absolute local time (set TZ env var), or "30m"/"2h" for relative
        message: reminder text
    """
    import re as _re
    from datetime import datetime, timedelta
    import zoneinfo

    tz_name = os.environ.get("TZ", "UTC")
    try:
        tz = zoneinfo.ZoneInfo(tz_name)
    except Exception:
        tz = zoneinfo.ZoneInfo("UTC")
    now = datetime.now(tz)

    rel_match = _re.match(r"^(\d+)(m|h|min|hour)s?$", time_spec)
    abs_match = _re.match(r"^(\d{1,2}):(\d{2})$", time_spec)

    if rel_match:
        amount = int(rel_match.group(1))
        unit = rel_match.group(2)
        seconds = amount * 3600 if unit.startswith("h") else amount * 60
        target = now + timedelta(seconds=seconds)
    elif abs_match:
        hour, minute = int(abs_match.group(1)), int(abs_match.group(2))
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        seconds = int((target - now).total_seconds())
    else:
        return {"error": f"can't parse time: {time_spec}. Use HH:MM or Nm/Nh"}

    alert = f"⏰ Reminder: {message}"
    subprocess.Popen(
        ["bash", "-c", f"sleep {seconds} && echo -e '\\n\\n{alert}\\n'"],
        stdout=None, stderr=None
    )

    target_str = target.strftime(f"%H:%M {tz_name}")
    return {"set": True, "target": target_str, "seconds": seconds, "message": message}


# --- Tool 6: tweet_performance ---
@mcp.tool()
def tweet_performance(days: int = 7) -> dict:
    """Fetch engagement stats for tweets posted in the last N days.

    Reads tweets.jsonl log, pulls live stats via twikit for each tweet,
    and captures the best performer to running_log.md. Falls back to raw
    log data if twikit is unavailable or cookies are missing.

    Args:
        days: how many days back to look (default 7)
    """
    import json as _json
    from datetime import datetime, timedelta
    from pathlib import Path

    tweets_log = _lib.TWEETS_LOG
    if not tweets_log.exists():
        return {"error": "tweets.jsonl not found — no tweets logged yet"}

    cutoff = datetime.now() - timedelta(days=days)
    entries = []
    with open(tweets_log) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = _json.loads(line)
                posted_at = datetime.strptime(entry["posted_at"], "%Y-%m-%d %H:%M")
                if posted_at >= cutoff:
                    entries.append(entry)
            except (ValueError, KeyError):
                continue

    if not entries:
        return {"tweets": [], "days": days, "message": "no tweets in window"}

    # Try to pull live stats via twikit
    try:
        import asyncio
        import os
        from dotenv import load_dotenv

        _dotenv_path = os.environ.get("DOTENV_PATH", "")
        if _dotenv_path:
            load_dotenv(_dotenv_path)

        try:
            from twikit import Client as _TwikitClient
        except ImportError:
            raise RuntimeError("twikit not installed")

        cookies_path_str = os.environ.get("X_COOKIES_PATH", "")
        if not cookies_path_str:
            raise RuntimeError("X_COOKIES_PATH not set")
        cookies_path = Path(cookies_path_str)
        if not cookies_path.exists():
            raise RuntimeError("x_cookies.json missing")

        async def _fetch_stats(tweet_ids):
            client = _TwikitClient("en-US")
            client.load_cookies(str(cookies_path))
            results = []
            for tid in tweet_ids:
                try:
                    tweet = await client.get_tweet_by_id(tid)
                    score = (
                        getattr(tweet, "reply_count", 0) * 13.5
                        + getattr(tweet, "retweet_count", 0) * 20
                        + getattr(tweet, "bookmark_count", 0) * 10
                        + getattr(tweet, "favorite_count", 0) * 1
                    )
                    results.append({
                        "tweet_id": tid,
                        "text": tweet.text[:200],
                        "likes": getattr(tweet, "favorite_count", 0),
                        "retweets": getattr(tweet, "retweet_count", 0),
                        "replies": getattr(tweet, "reply_count", 0),
                        "bookmarks": getattr(tweet, "bookmark_count", 0),
                        "views": getattr(tweet, "view_count", 0),
                        "engagement_score": round(score, 1),
                    })
                except Exception:
                    pass
            return results

        tweet_ids = [e["tweet_id"] for e in entries]
        stats = asyncio.run(_fetch_stats(tweet_ids))

        # Auto-capture best performer
        if stats:
            best = max(stats, key=lambda x: x["engagement_score"])
            _lib.content_capture(
                moment=(
                    f"Best tweet ({days}d): score={best['engagement_score']} "
                    f"likes={best['likes']} RT={best['retweets']} "
                    f"replies={best['replies']} views={best['views']}\n"
                    f"{best['text']}"
                ),
                category="number",
            )

        return {"tweets": stats, "days": days, "source": "twikit"}

    except Exception as e:
        # Fall back to raw log data
        raw = [
            {
                "tweet_id": e["tweet_id"],
                "text": e["text"],
                "posted_at": e["posted_at"],
                "url": e.get("url", ""),
                "likes": None,
                "retweets": None,
                "replies": None,
                "bookmarks": None,
                "views": None,
                "engagement_score": None,
            }
            for e in entries
        ]
        return {"tweets": raw, "days": days, "source": "log_only", "reason": str(e)}


if __name__ == "__main__":
    mcp.run()
