# Design review

Two models review each board: gpt-6.1-sol and opus-5.5, each on high reasoning in the Sprocket CLI. fable-5.2 wasn't used. A judge sees only an anonymous package of the board, made by `package.ts`:

- the KiCad project renamed to `board.*`, with its sheets and local libraries
- the BOM as `bom.csv`
- the run's renders, and one image per layer, both exported with the run's KiCad version

The agent's README, notes, scripts and fab files are left out. Names of harnesses and models are replaced or make `package.ts` stop. The rubric is in [prompt.md](prompt.md). Judges answer three yes or no questions and give five integer scores from 0 to 10 against shared bands, from "ship it as is" down to "would stop the board working or being built". `judge.ts` stores each review in `runs/<run-id>/review/<model>.json` and their votes and mean scores under `review` in `metrics.json`. [`reasoning.ts`](reasoning.ts) writes each judge's final message and its subagents' reports to `runs/<run-id>/review/<model>.md`.

Each board gets its own box, so no judge can read another board. The judges of a board run one at a time, in random order. After each judge, `judge.ts` copies the review and the Sprocket transcript to `bench/.state/judge/<run-id>/`, and [`clear-judge.sh`](clear-judge.sh) stops the judge's processes and deletes its files from the box.

## The box image

Ubuntu 24.04 x86_64 with 100 GB gp3, prepared as `ubuntu`:

1. Run [`../harnesses/sprocket/setup.sh`](../harnesses/sprocket/setup.sh), then `sudo apt-get install -y librsvg2-bin`.
2. Copy `~/.sprocket/connectors/kicad` and `~/.sprocket/tools/python` from a machine where the KiCad connector is installed. The connector's scripts use that machine's home folder, so link it with `sudo ln -s /home/ubuntu /home/<user>`. Sprocket finds the connector from these files.
3. Put each run's KiCad in `/opt/kicad-versions/<version>`, named as in `info.json`: the extracted nightly AppImages, Backplane's fork from a box where [`../harnesses/backplane/install-kicad.ts`](../harnesses/backplane/install-kicad.ts) ran, and a link to the connector's `kicad` folder for 10.99.0-6344. New AppImages extract `squashfs-root` as a link to `AppDir`.
4. Delete `~/.sprocket/installation.json`, run `sudo truncate -s 0 /etc/machine-id` and image the box.

## Run

Launch one box per board and sign each in with `sprocket login --credential-store file`. The Sprocket harness README explains why each box needs its own login. Then, from `bench/`:

```shell
bun judge/judge.ts <run-id> <box address>
```

`judge.ts` keeps only the run's KiCad on the box, at `/opt/kicad-run`. It skips judges whose review already exists, so it can be rerun after a failure.
