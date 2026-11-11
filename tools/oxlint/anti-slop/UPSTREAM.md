# Upstream

- Source: https://github.com/dmmulroy/anti-slop, `src/` at commit `13909c9`.
- Copied from Sprocket's vendored copy (`tools/oxlint/anti-slop` at Sprocket `70fd91fd`). Its local changes on top of that commit:
  - Effect rules only count a broad catch's last argument as the handler, and resolve the tagged subject through scope.
  - `shared/dictionary-types.ts` and `shared/type-alias-resolution.ts` resolve interfaces through lexical type bindings.
  - `require-readable-spacing-cli.test.ts` runs the installed Oxlint binary through Node instead of `pnpm exec`.
  - Formatted with single quotes and tabs.
- Installed plugins: `index.ts` (generic) and `effect/index.ts` (Effect).
