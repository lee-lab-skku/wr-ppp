#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
    pwd -P
)"

TMP_ROOT="$(mktemp -d)"
TEST_DIR="$TMP_ROOT/template"

cleanup() {
    rm -rf -- "$TMP_ROOT"
}
trap cleanup EXIT

mkdir -p -- "$TEST_DIR"
cp -- "$REPO_DIR/template.tex" "$TEST_DIR/template.tex"

(
    cd -- "$TEST_DIR"
    "$REPO_DIR/scripts/report-build" --here --serial 1 template.tex
)

mv -f -- "$TEST_DIR/template.pdf" "$REPO_DIR/template.pdf"
