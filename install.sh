#!/bin/bash
# Installs the Email Agent for Claude Code:
#   - links this folder to ~/.claude/skills/email-agent (skipped if it already lives there)
#   - links the reviewer agent into ~/.claude/agents/
#   - adds an `email-agent` terminal command in ~/.local/bin
#   - optionally sets up the job-search pipeline (ai-job-search) in ~/ai-job-search
# Flags: --jobs (set up job search without asking), --no-jobs (skip it)
set -euo pipefail
REPO="$(cd "$(dirname "$0")" && pwd)"
SKILLS="$HOME/.claude/skills"; AGENTS="$HOME/.claude/agents"; BIN="$HOME/.local/bin"
JOBS_DIR="${JOBS_DIR:-$HOME/ai-job-search}"
mkdir -p "$SKILLS" "$AGENTS" "$BIN"

link() {  # link SRC DEST, refusing to clobber a real file or folder
  if [ -e "$2" ] && [ ! -L "$2" ]; then
    if cmp -s "$1" "$2"; then rm "$2"; else echo "refusing: $2 exists and is not a link"; exit 1; fi
  fi
  ln -sfn "$1" "$2"; echo "linked $2"
}
[ "$REPO" = "$SKILLS/email-agent" ] || link "$REPO" "$SKILLS/email-agent"
link "$REPO/agents/email-reviewer.md" "$AGENTS/email-reviewer.md"
chmod +x "$REPO/tools/"*.py "$REPO/tools/"*.sh "$REPO/tests/"*.sh "$REPO/tests/"*.py "$REPO/"*.sh

cat > "$BIN/email-agent" <<'SH'
#!/bin/bash
exec claude "/email-agent $*"
SH
chmod +x "$BIN/email-agent"
echo "installed command: $BIN/email-agent"

# --- Job search (optional) -------------------------------------------------
want_jobs=""
case "${1:-}" in --jobs) want_jobs=y;; --no-jobs) want_jobs=n;; esac
if [ -z "$want_jobs" ]; then
  if [ -d "$JOBS_DIR/.git" ]; then want_jobs=y
  else
    read -r -p "Set up the job search pipeline too (find jobs, tailor CV, cover letters)? [y/N] " want_jobs || want_jobs=n
  fi
fi
if [[ "$want_jobs" =~ ^[Yy] ]]; then
  if [ -d "$JOBS_DIR/.git" ]; then
    echo "job search repo found at $JOBS_DIR (update it from inside the agent: say 'check job search updates')"
  else
    command -v git >/dev/null || { echo "job search needs git. Install Xcode tools: xcode-select --install, then rerun"; exit 1; }
    git clone -q https://github.com/MadsLorentzen/ai-job-search.git "$JOBS_DIR"
    # Local clone only: your profile data stays on this computer. Keep `origin` as upstream for updates.
    git -C "$JOBS_DIR" remote rename origin upstream
    echo "cloned job search into $JOBS_DIR"
  fi
  [ -d "$JOBS_DIR/.venv" ] || python3 -m venv "$JOBS_DIR/.venv"
  "$JOBS_DIR/.venv/bin/pip" install -q pypdf && echo "python env ready"
  if ! command -v bun >/dev/null && [ ! -x "$HOME/.bun/bin/bun" ]; then
    echo "installing bun (runs the job board search tools)"
    curl -fsSL https://bun.sh/install | bash >/dev/null
  fi
  (cd "$JOBS_DIR" && PATH="$HOME/.bun/bin:$PATH" python3 tools/install_portal_clis.py >/dev/null) && echo "job board tools ready"
  command -v lualatex >/dev/null || [ -x "$HOME/Library/TinyTeX/bin/universal-darwin/lualatex" ] \
    || echo "note: no LaTeX found. Needed only to turn CVs into PDFs. The agent can walk you through installing TinyTeX."
  printf '%s\n' "$JOBS_DIR" > "$REPO/.jobs_repo"   # read by onboarding to fill paths.jobs_repo
fi

command -v claude >/dev/null || echo "WARNING: Claude Code not found. Install it first: https://claude.com/claude-code"
case ":$PATH:" in *":$BIN:"*) ;; *) echo "WARNING: add $BIN to your PATH:  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc && source ~/.zshrc";; esac
python3 "$REPO/tests/run_tests.py" >/dev/null 2>&1 && echo "self-test: pass" || echo "self-test: FAILED (run: python3 tests/run_tests.py)"
echo "done. Type: email-agent"
