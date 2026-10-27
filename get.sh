#!/bin/bash
# Install or update the Email Agent without git or a GitHub account.
#   curl -fsSL https://raw.githubusercontent.com/Verma0118/email-agent/main/get.sh | bash
# Downloads the latest code into ~/email-agent, keeps your profile.json and personal/,
# then runs install.sh. Run the same command again any time to update.
set -euo pipefail
DIR="${EMAIL_AGENT_DIR:-$HOME/email-agent}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
KEEP="profile.json personal .jobs_repo"

if [ -d "$DIR/.git" ]; then
  echo "git checkout found, updating with git pull"; git -C "$DIR" pull -q
else
  curl -fsSL https://github.com/Verma0118/email-agent/archive/refs/heads/main.tar.gz | tar xz -C "$TMP"
  mkdir -p "$DIR"
  for keep in $KEEP; do [ -e "$DIR/$keep" ] && mv "$DIR/$keep" "$TMP/"; done
  find "$DIR" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  cp -R "$TMP/email-agent-main/." "$DIR/"
  for keep in $KEEP; do [ -e "$TMP/$keep" ] && mv "$TMP/$keep" "$DIR/"; done
  echo "downloaded latest into $DIR"
fi
"$DIR/install.sh" "$@" < /dev/tty
