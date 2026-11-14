# Design review

opus-5.5 on high reasoning in the Sprocket CLI reviews each board once. A judge sees only an anonymous package of the board, made by `package.ts`:

- the KiCad project renamed to `board.*`, with its sheets and local libraries
- the BOM as `bom.csv`
- three renders and one image per layer, made on the box from the package with the run's KiCad version

The agent's README, notes, scripts and fab files are left out, and title-block company and comment fields are cleared. Names of harnesses and models are replaced or make `package.ts` stop. The rubric is in [prompt.md](prompt.md). [`start-judge.sh`](start-judge.sh) fills in the judge's model, which its subagents must use too. The judge lists findings on layout and routing, each `minor`, `major` or `fatal`, plus any other fatal faults. It gives no scores. `judge.ts` stores the review in `runs/<run-id>/review/<model>.json` and the finding counts under `review` in `metrics.json`. [`reasoning.ts`](reasoning.ts) writes the judge's final message and its subagents' reports to `runs/<run-id>/review/<model>.md`.

Each board gets its own box, so no judge can read another board. After each attempt, `judge.ts` copies the review and the Sprocket transcript to `bench/.state/judge/<run-id>/`, and [`clear-judge.sh`](clear-judge.sh) stops the judge's processes and deletes its files from the box.

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

`judge.ts` keeps only the run's KiCad on the box, at `/opt/kicad-run`. It doesn't start the judge when the review already exists, so it can be rerun after a failure.
