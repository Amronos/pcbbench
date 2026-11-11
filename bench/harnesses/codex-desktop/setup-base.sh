#!/usr/bin/env bash
# Prepares the EC2 Mac for codex-desktop runs. Run on the Mac as ec2-user:
#   ssh mac "EC2_USER_PASSWORD=... bash -s" < setup-base.sh
# The GUI-only steps (Computer Use install, TCC grants, first KiCad launch) follow in README.md.
set -euo pipefail
: "${EC2_USER_PASSWORD:?}"

CHATGPT_DMG_URL=https://persistent.oaistatic.com/codex-app-prod/ChatGPT.dmg
KICAD_NIGHTLIES=https://downloads.kicad.org/kicad/macos/explore/nightlies
KICAD_DMG_URL="${KICAD_DMG_URL:-$(curl -fsSL "$KICAD_NIGHTLIES" | grep -oE "$KICAD_NIGHTLIES/download/kicad-unified-universal-[^\"]+\.dmg" | head -1)}"

sudo dscl . -passwd /Users/ec2-user "$EC2_USER_PASSWORD"

sudo launchctl enable system/com.apple.screensharing
sudo launchctl bootstrap system /System/Library/LaunchDaemons/com.apple.screensharing.plist 2>/dev/null || true

# Auto-login so the root-volume reset reboots straight into a GUI session.
sudo defaults write /Library/Preferences/com.apple.loginwindow autoLoginUser ec2-user
EC2_USER_PASSWORD="$EC2_USER_PASSWORD" perl -e '
	my @k = (0x7D,0x89,0x52,0x23,0xD2,0xBC,0xDD,0xEA,0xA3,0xB9,0x1F);
	my @p = map ord, split //, $ENV{EC2_USER_PASSWORD};
	push @p, 0;
	push @p, 0 while @p % 12;
	print map { chr($p[$_] ^ $k[$_ % @k]) } 0..$#p;
' | sudo tee /etc/kcpassword >/dev/null
sudo chmod 600 /etc/kcpassword

sudo pmset -a sleep 0 displaysleep 0 disksleep 0 powernap 0 autorestart 1
defaults -currentHost write com.apple.screensaver idleTime -int 0
sudo sysadminctl -screenLock off -password "$EC2_USER_PASSWORD" || true

for k in AutomaticCheckEnabled AutomaticDownload AutomaticallyInstallMacOSUpdates CriticalUpdateInstall ConfigDataInstall; do
	sudo defaults write /Library/Preferences/com.apple.SoftwareUpdate "$k" -bool false
done
sudo defaults write /Library/Preferences/com.apple.commerce AutoUpdate -bool false

install_dmg() { # url, then the paths inside the volume to copy into /Applications
	local url=$1 dmg mnt
	shift
	dmg=$(mktemp -d)/image.dmg
	curl -fsSL -o "$dmg" "$url"
	mnt=$(mktemp -d)
	hdiutil attach -nobrowse -readonly -mountpoint "$mnt" "$dmg" >/dev/null
	for p in "$@"; do sudo ditto "$mnt/$p" "/Applications/$p"; done
	hdiutil detach "$mnt" >/dev/null
	rm -f "$dmg"
}
install_dmg "$CHATGPT_DMG_URL" ChatGPT.app
install_dmg "$KICAD_DMG_URL" KiCad
echo "$KICAD_DMG_URL" | sudo tee /Applications/KiCad/SOURCE_DMG_URL >/dev/null

sudo mkdir -p /etc/codex
sudo tee /etc/codex/requirements.toml >/dev/null <<'EOF'
[features]
in_app_updates = false
EOF

mkdir -p ~/.codex ~/pcbbench-run
/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex --version
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli version
