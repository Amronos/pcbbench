# AGENTS.md

## Checks

- Use the Nix dev shell for every tool: `nix develop -c <command>`.
- `prek run -a` covers formatting, linting, and type checks. `bun run test` runs the tests.

## Effect

- `bench/` is written with Effect 4. Read `bench/node_modules/effect/AGENTS.md` and the `ai-docs` it links before writing Effect code. Prefer them over your memory of Effect 3.
- Entry points run their program with `BunRuntime.runMain` and parse arguments with `effect/cli`.
- Decode files, HTTP responses, and command output with `Schema` where they enter the program. Past that point, code works on the decoded types.
- Use `FileSystem`, `HttpClient` (`effect/http`), and `ChildProcess` (`effect/process`) for I/O, and `Schema.TaggedError` for errors.

## Benchmark data

- `runs/<run id>/output` is what each agent delivered. Never edit it.
- `bench/prompt.md`, `bench/judge/prompt.md`, and the harness `smoke.md` files are sent to models verbatim. Change them only on purpose, since that changes the benchmark.
