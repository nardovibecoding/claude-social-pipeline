"""Improvement pattern database for post_task_check."""

# Pattern: (condition_fn, suggestion)
PATTERNS = [
    {
        "name": "no_commit_after_edits",
        "check": lambda actions: (
            any(a["action"] == "file_edit" for a in actions[-10:])
            and not any(a["action"] == "git_commit" for a in actions[-5:])
            and sum(1 for a in actions[-10:] if a["action"] == "file_edit") >= 3
        ),
        "suggestion": "3+ file edits without a commit. Consider committing before moving on."
    },
    {
        "name": "content_worthy_no_capture",
        "check": lambda actions: (
            any(a["action"] in ("new_hook", "new_mcp_tool", "new_skill", "architecture_change") for a in actions)
            and not any(a["action"] == "content_capture" for a in actions)
        ),
        "suggestion": "Session produced something novel but nothing saved to content drafts. Use content_capture."
    },
    {
        "name": "unpublished_project",
        "check": lambda actions: (
            any(a["action"] == "file_edit" and "server.py" in a.get("detail", "") for a in actions)
            and not any(a["action"] == "git_push" for a in actions[-10:])
            and not any(a["action"] == "github_publish" for a in actions)
        ),
        "suggestion": "New project code written but not pushed. Consider gh repo create + README."
    },
    {
        "name": "long_session_no_checkpoint",
        "check": lambda actions: (
            len(actions) > 30
            and not any(a["action"] == "memory_save" for a in actions[-20:])
        ),
        "suggestion": "Long session with no memory saves. Consider saving important findings."
    },
    {
        "name": "queue_not_checked",
        "check": lambda actions: (
            len(actions) > 15
            and not any(a["action"] == "content_queue" for a in actions)
        ),
        "suggestion": "Long session without checking tweet queue. Any drafts worth posting?"
    },
]


def check_patterns(actions: list) -> list[str]:
    """Run all patterns against session actions, return matching suggestions."""
    if not actions:
        return []

    suggestions = []
    for pattern in PATTERNS:
        try:
            if pattern["check"](actions):
                suggestions.append(pattern["suggestion"])
        except (IndexError, KeyError, TypeError):
            continue

    return suggestions
