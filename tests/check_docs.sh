#!/usr/bin/env bash
# Check shared Markdown with the current upstream mddt default branch.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for dependency in git uv; do
  if ! command -v "$dependency" >/dev/null 2>&1; then
    printf 'Documentation checks require %s on PATH.\n' "$dependency" >&2
    exit 2
  fi
done

mddt_dir="$(mktemp -d "${TMPDIR:-/tmp}/wr-mddt.XXXXXX")"
trap 'rm -rf -- "$mddt_dir"' EXIT

# Deliberately follow upstream without pinning a branch, tag, or commit.
git clone --quiet --depth 1 https://github.com/mirinae3145/mddt.git "$mddt_dir/upstream"
printf 'mddt commit: %s\n' "$(git -C "$mddt_dir/upstream" rev-parse HEAD)" >&2

cd "$repo_root"
uv run --no-project "$mddt_dir/upstream/skills/mddt/scripts/mddt.py" \
  --root "$repo_root" "$repo_root" "$@"
