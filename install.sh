#!/usr/bin/env bash
# Claude Social Pipeline — one-liner installer
# curl -fsSL https://raw.githubusercontent.com/nardovibecoding/claude-social-pipeline/main/install.sh | bash
set -euo pipefail

INSTALL_DIR="$HOME/claude-social-pipeline"
SETTINGS="$HOME/.claude/settings.json"

RED='\033[0;31m' GREEN='\033[0;32m' YELLOW='\033[1;33m' CYAN='\033[0;36m' BOLD='\033[1m' NC='\033[0m'

echo ""
echo -e "${CYAN}${BOLD}"
echo "  ╔═════════════════════════════════════════╗"
echo "  ║   Claude Social Pipeline Installer       ║"
echo "  ║   6 MCP tools + 2 skills for X/content   ║"
echo "  ╚═════════════════════════════════════════╝"
echo -e "${NC}"

# --- Check Python ---
if ! command -v python3 &>/dev/null; then
  echo -e "${RED}✗ Python 3 is required. Install it first.${NC}"
  exit 1
fi

# --- Clone or update ---
if [ -d "$INSTALL_DIR/.git" ]; then
  echo -e "${YELLOW}→ Updating existing install...${NC}"
  git -C "$INSTALL_DIR" pull --ff-only 2>/dev/null || true
else
  if [ -d "$INSTALL_DIR" ]; then
    echo -e "${RED}✗ $INSTALL_DIR exists but is not a git repo. Remove it first.${NC}"
    exit 1
  fi
  echo -e "${GREEN}→ Cloning repository...${NC}"
  git clone https://github.com/nardovibecoding/claude-social-pipeline.git "$INSTALL_DIR"
fi

# --- Install MCP dependencies ---
echo -e "${GREEN}→ Installing MCP server dependencies...${NC}"
pip3 install --quiet mcp 2>/dev/null || pip install --quiet mcp 2>/dev/null || echo -e "${YELLOW}  Warning: couldn't install mcp package. Install manually: pip install mcp${NC}"

# --- Patch settings.json ---
echo -e "${GREEN}→ Configuring MCP server...${NC}"
mkdir -p "$HOME/.claude"

python3 << 'PYEOF'
import json, os

INSTALL_DIR = os.path.expanduser("~/claude-social-pipeline")
SETTINGS = os.path.expanduser("~/.claude/settings.json")

if os.path.exists(SETTINGS):
    with open(SETTINGS) as f:
        settings = json.load(f)
else:
    settings = {}

# Add MCP server
mcp = settings.setdefault("mcpServers", {})
mcp["content-pipeline"] = {
    "command": "python3",
    "args": [f"{INSTALL_DIR}/mcp/server.py"]
}

with open(SETTINGS, "w") as f:
    json.dump(settings, f, indent=2)

print("  MCP server configured in ~/.claude/settings.json")
PYEOF

# --- Done ---
echo ""
echo -e "${GREEN}${BOLD}✓ Claude Social Pipeline installed!${NC}"
echo ""
echo -e "  ${BOLD}6 MCP tools${NC} for content capture, queuing, checkpointing."
echo -e "  ${BOLD}2 skills${NC} available in Claude Code:"
echo -e "    ${CYAN}/x-tweet${NC}            — draft + post tweets"
echo -e "    ${CYAN}/content-humanizer${NC}  — remove AI tone from text"
echo ""
echo -e "  ${YELLOW}Restart Claude Code if it's already running.${NC}"
echo ""
