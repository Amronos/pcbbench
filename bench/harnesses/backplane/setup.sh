#!/usr/bin/env bash
# Prepares a fresh Ubuntu 24.04 x86_64 box for Backplane runs. Run it as the login user from a copy of the repo's bench/ folder:
#   bash bench/harnesses/backplane/setup.sh
# It leaves no hub running and no key anywhere; run.ts brings both per run.
set -euo pipefail
BACKPLANE_VERSION=v0.15.0
CLAUDE_CODE_VERSION=2.1.321
CODEX_VERSION=0.167.0
PREFIX="$HOME/.local/share/backplane"
HERE=$(cd "$(dirname "$0")" && pwd)
export PATH="$HOME/.local/bin:$HOME/.bun/bin:$PATH"

sudo apt-get update -q
sudo DEBIAN_FRONTEND=noninteractive apt-get install -yq curl ca-certificates git jq ripgrep unzip zip python3 python3-pip python3-venv build-essential \
	libnss3 libatk1.0-0t64 libatk-bridge2.0-0t64 libcups2t64 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
	libpango-1.0-0 libcairo2 libasound2t64 libgl1 libegl1 libglu1-mesa libgtk-3-0t64
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo DEBIAN_FRONTEND=noninteractive apt-get install -yq nodejs

command -v bun >/dev/null || curl -fsSL https://bun.sh/install | bash
command -v claude >/dev/null || curl -fsSL https://claude.ai/install.sh | bash -s "$CLAUDE_CODE_VERSION"
sudo npm install -g "@openai/codex@$CODEX_VERSION"

# The hub alone (no desktop app). Its installer starts a guard on a throwaway home; stop it so nothing runs in the image.
curl -fsSL "https://github.com/BackplaneWorks/Backplane/releases/download/$BACKPLANE_VERSION/install.sh" |
	BACKPLANE_NO_DESKTOP_APP=1 BACKPLANE_HOME=/tmp/bp-install sh -s -- --quiet
backplane hub stop --home /tmp/bp-install
rm -rf /tmp/bp-install "$HOME/.config/backplane"

# The wire dictionaries the hub's CBOR replies are compressed with, from the same release's source.
curl -fsSL "https://raw.githubusercontent.com/BackplaneWorks/Backplane/$BACKPLANE_VERSION/native/host/src/wire_dict.rs" |
	python3 -c 'import json,re,sys; s=sys.stdin.read(); print(json.dumps({k.lower(): json.loads(re.search(r"pub const %s: &\[&str\] = &(\[.*?\]);" % k, s, re.S).group(1)) for k in ("KEYS", "WORDS")}))' \
		> "$PREFIX/pcbbench-wire-dict.json"

[ -n "$(ls -A "$PREFIX/kicad" 2>/dev/null)" ] || bun "$HERE/install-kicad.ts"

claude --version
codex --version
bun --version
"$PREFIX"/kicad/*/bin/kicad-cli version
