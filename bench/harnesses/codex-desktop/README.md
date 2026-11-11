# Codex desktop harness

Both Mac runs use one EC2 Mac: instance `i-0667c1457d80ee354` (mac2-m2.metal, host `h-017cb5de3df2b3cf9`, `54.234.19.231`) in us-east-1. Its base image is AMI `ami-0a11b952507c9bb48`, with:

- macOS 26.7, auto-login as `ec2-user`, no sleep, screen lock or automatic updates.
- The ChatGPT desktop app 26.1103.60933 in Codex mode (codex-cli 0.167.0-alpha.3.2). In-app updates are off through `/etc/codex/requirements.toml`.
- Computer Use granted Accessibility and Screen Recording, with access to any app.
- KiCad nightly 10.99.0 from `kicad-unified-universal-20261109-0413-0ef63a79e8.dmg`, with the first-run wizard done. The Linux runs' connector KiCad is `8c85ac1452` from a day earlier.
- No ChatGPT account and no stored API key. With the model provider from `config.toml` and the run's API key in its environment, the app skips sign-in.

The display is 1024x768, the most the EC2 Mac virtual display offers.

## Run

From `bench/`, in `tmux`, for each run id in turn (`codex-desktop--gpt-6.1-sol`, then `codex-desktop-texttocad--gpt-6.1-sol`):

```shell
bun harnesses/codex-desktop/run.ts reset
bun harnesses/codex-desktop/run.ts start <run-id>
```

`reset` replaces the root volume with the base AMI. The instance reboots, and the command returns once the GUI session is up, after about 30 minutes. `start` refuses a Mac that still has a work folder or chat from an earlier run.

`start` then:

1. Writes `config.toml` with the run's model and effort.
2. For the text-to-cad run, installs it with `install.sh --only codex --no-telemetry` and runs `cad doctor`. The installer adds the plugin to `config.toml`, so it runs after step 1.
3. Puts the run's API key in the GUI session's launchd environment, in memory only, and opens the app.
4. Opens `codex://new?prompt=…&path=~/pcbbench-run` with `prompt.md` filled in, then clicks send over VNC.
5. Polls the thread's rollout over SSH every minute and prints token usage. The run ends at the turn's `task_complete` or `turn_aborted`. At `WALL_CLOCK_LIMIT_HOURS` it kills the app.
6. Copies `~/pcbbench-run` and `~/.codex/sessions` to `~/pcbbench-results/<run-id>/`.

The results folder also holds `prompt.md`, `result.json` (versions, rollout path, timestamps, outcome), `texttocad-install.log`, and the `filled.png`, `started.png` and `finished.png` screenshots. If the driver dies, `run.ts wait <run-id>` picks the run up again, and `run.ts collect <run-id>` copies the files on demand.

To check the machine, run `start codex-desktop-texttocad--gpt-6.1-sol--smoke harnesses/codex-desktop/smoke.md` with the run's API key saved under that id, then `reset`.

## During a run

Nobody answers prompts on the Mac, so an unexpected dialog stalls the run until the time limit. The work folder sits outside the macOS-protected Documents, Desktop and Downloads folders, and KiCad already has access to Documents.

Avoid VNC during a run. Each connection shows a "Your screen is being controlled" banner, and any input moves the mouse that Computer Use is driving. A screenshot alone leaves the mouse where it is:

```shell
ssh -i ~/.ssh/pcbbench.pem -N -L 15900:localhost:5900 ec2-user@54.234.19.231 &
uv run harnesses/codex-desktop/vnc.py shot now.png
```

VNC uses Apple Remote Desktop authentication as `ec2-user`. The password is in `~/.config/pcbbench/mac-ec2-user-password`. The security group only allows SSH from the bench machine's IP.

## Rebuilding the AMI

1. Run `setup-base.sh` on the Mac as `ec2-user`.
2. Start the app as `start` does, with a throwaway key, and send a prompt that uses Computer Use. Grant what it asks for:
   - Accessibility for Codex Computer Use, by toggling it on in System Settings.
   - Screen & System Audio Recording, by dragging `~/.codex/computer-use/Codex Computer Use.app` into the list, then Quit & Reopen.
   - Bypassing the system private window picker.
3. In the app, set Settings → Computer use → Any App, and hide the full-access banner with "Don't show again".
4. Open KiCad once. Pick the built-in libraries, untick both update checks, turn data collection off, and allow access to Documents.
5. Quit both apps. Delete the chats from `~/.codex/sessions`, `session_index.jsonl`, the `threads` and `thread_read_receipts` tables of `state_5.sqlite`, the tables of `thread_history_1.sqlite`, and the `local_thread_catalog*` tables of `sqlite/codex.db`. Remove the run's API key from the GUI session's launchd environment.
6. `aws ec2 create-image --instance-id i-0667c1457d80ee354`, then update `BASE_AMI` in `run.ts`.

Don't run ARD `kickstart -activate`, because it makes Screen Sharing view-only.
