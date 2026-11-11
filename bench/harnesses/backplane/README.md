# Backplane harness

The runs used AMI `ami-0679e466e7854c8b3` (us-east-1, since deleted): Ubuntu 24.04 with Backplane v0.15.0 (hub only, no desktop app), Claude Code 2.1.321, codex 0.167.0, bun 1.4.4, Node 22 and Backplane KiCad 10.99.0-bp.4 in `~/.local/share/backplane/kicad`. It held no key, no repo copy and no CLI login. `setup.sh` rebuilds it on a fresh box (c7i.2xlarge, 100 GB gp3).

## Run

Launch a box from the AMI, then copy the repo's `bench/` folder and the run's API key. `run.ts` imports `bench/runs.ts`.

```shell
rsync -a --exclude node_modules --exclude .state bench/ ubuntu@<ip>:pcbbench/bench/
ssh ubuntu@<ip> 'umask 077; cat > ~/.pcbbench-key' < <file with the run's API key>
ssh ubuntu@<ip> 'tmux new -d "~/.bun/bin/bun ~/pcbbench/bench/harnesses/backplane/run.ts --run-id <run-id> --model <model> --key-file ~/.pcbbench-key"'
```

The driver deletes the key file once read. It starts a hub on an empty `~/pcbbench-hub`, turns Backplane's ordering and price estimates off, opens `~/pcbbench-run` as the project, sends the rendered `bench/prompt.md` (or `--prompt <file>` for smoke tests) to one thread at `REASONING_EFFORT` and waits until every thread has been idle for 3 minutes, or until `WALL_CLOCK_LIMIT_HOURS`. Then it stops the hub. The driver answers the agent's questions with "decide yourself" and accepts every approval.

Collect `~/pcbbench-run` and `~/pcbbench-logs/<run-id>/`:

- `events.jsonl`, `hub.log`: the hub's event log and output.
- `driver.log`: the driver's log of threads, turns and asks.
- `summary.json`: thread states, status (`done`, `timeout` or `error`) and timings.
- `claude-projects/` or `codex-sessions/`: the CLI session logs. These show the model each API call used.
- `model-overrides.log`: every model or effort flag the wrappers rewrote.

`TurnUsage` in `events.jsonl` names the model Backplane asked for, not the one the wrapper ran. A subthread the agent started on `claude-haiku-4-5` is labeled `claude-haiku-4-5` there, while its session log shows the run's model.

## What the driver changes in Backplane

- Wrappers for `claude` and `codex` in the hub's PATH rewrite `--model`/`-m` and `--effort`/`model_reasoning_effort` to the run's model and effort. `delegate_task` accepts any model name, and titles and summaries run at low effort.
- The `codex` wrapper closes stdin for `codex exec` turns. Backplane keeps a turn's stdin open, and `codex exec` waits for EOF, so turns never start without this.
- A `kicad-cli` wrapper in PATH. Backplane builds the agent prompt's KiCad block only from PATH, and its `--version` check reads a Backplane build as stock KiCad.
- `BACKPLANE_MODELS` lists only the run's model in the prompt.
- Codex native subagents are turned off, as Backplane does for Claude's.
- Claude runs the run's model with 1M context and a 128k output cap. Codex gets a model catalog entry for the run's model copied from `gpt-6.1-sol`. Without these, both CLIs treat the model names as unknown and fall back to generic limits.
