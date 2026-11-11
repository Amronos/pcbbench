#!/usr/bin/env bash
# Leaves nothing from an earlier judge: its Sprocket server and subagents, KiCad servers, review folder, transcripts and /tmp files.
set -uo pipefail
keep="sshd|systemd|sd-pam|dbus-daemon"
for attempt in 1 2 3; do
	pids=$(ps -u ubuntu -o pid=,ppid=,comm= | awk -v self=$$ -v parent=$PPID -v keep="$keep" '$1 != self && $1 != parent && $2 != self && $3 !~ keep {print $1}')
	[ -z "$pids" ] && break
	kill $pids 2>/dev/null
	sleep 3
done
[ -n "${pids:-}" ] && kill -9 $pids 2>/dev/null
rm -rf ~/review ~/judge.out ~/judge.err ~/judge.exit ~/.sprocket/transcripts ~/.agent-browser ~/.config/kicad ~/.cache/kicad
find /tmp -mindepth 1 -maxdepth 1 -user ubuntu -exec rm -rf {} +
exit 0
