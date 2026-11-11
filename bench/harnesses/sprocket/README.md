# Sprocket harness

The runs used AMI `ami-0843bb9fd9c9b22da` (us-east-1, since deleted): Ubuntu 24.04 with Sprocket 0.5.0 and the KiCad connector v0.2.0 (KiCad 10.99.0-6344) installed. Its baked login was dead, so every box needed its own sign-in. To rebuild it, see "Rebuilding the AMI" below.

## Run

Launch a c7i.2xlarge from the AMI, copy the latest `bench/runs.ts`, `bench/prompt.md` and this folder to `~/pcbbench/bench/`, then run the driver inside `tmux` so it survives SSH drops:

```shell
cd ~/pcbbench/bench/harnesses/sprocket
~/.bun/bin/bun run.ts sprocket--opus-5.5 opus-5.5
```

The driver renders `bench/prompt.md`, runs `sprocket run` in the empty `~/pcbbench-run` with the `WALL_CLOCK_LIMIT_HOURS` timeout from `runs.ts`, and writes `~/pcbbench-results/<run-id>/`:

- `result.json`: thread id, Sprocket run id, model, timestamps and exit code. The ids are saved as soon as the run starts.
- `stdout.md`: the agent's final reply.
- `stderr.log`: the thread and run header, and tool-call names.
- `prompt.md`: the prompt as sent.

Token usage comes from the thread in the Sprocket web UI.

To check a fresh box first, run `bun run.ts smoke--<model> <model> smoke.md`, then empty `~/pcbbench-run`.

## Login

Each login is one WorkOS refresh-token chain. Every refresh replaces the token, and the old one stops working 30 s later. So one login can serve only one box, and an AMI or a copied credential works for at most one box.

Before a run, start `sprocket login --credential-store file` on every box at the same time, and have the account owner approve all the device codes in one sitting. Each code expires in about 5 minutes. If a box is still signed out when the driver starts, the driver runs that login itself.

## Rebuilding the AMI

1. Run `setup.sh` as `ubuntu` on a fresh Ubuntu 24.04 x86_64 box (100 GB gp3; KiCad needs about 10 GB).
2. `sprocket login --credential-store file` and approve the device code. The code expires in about 5 minutes.
3. Install KiCad from Settings → Connectors in the web UI. The install API needs a browser session, which the CLI login does not give. Start `SPROCKET_PORT=27731 sprocket serve` and tunnel `27731:127.0.0.1:27731`. If the owner's browser can't reach the tunnel, sign in from the app page:
   1. `POST /api/auth/desktop-login/start {"flow":"signIn"}`.
   2. Have the owner open the returned `authorizationUrl` and send back the failed `127.0.0.1:27731/.../callback?code=...` URL.
   3. Fetch that URL from the app page, then `POST /api/auth/desktop-login/result {"loginId": ...}`.

   Stay on the app page until this finishes. Leaving it cancels the pending sign-in.

4. Stop the server and run `sprocket logout`. Then `rm ~/.sprocket/installation.json` and `sudo truncate -s 0 /etc/machine-id` so each box gets its own Sprocket installation and machine id. Image the box.
