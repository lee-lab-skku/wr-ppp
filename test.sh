#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
    pwd -P
)"
CONFIG_FILE="$REPO_DIR/.local-config"
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Not configured." >&2
    echo "Run ./setup.sh first." >&2
    exit 2
fi
source "$CONFIG_FILE"
source "$REPO_DIR/report-metadata.sh"

resolve_report_date
REPORT_SERIAL_NUMBER=1

tar -C "$REPO_DIR" -cf - template.tex weekly-report.sty |
docker run --rm -i \
    --network none \
    -e "REPORT_SERIAL_NUMBER=$REPORT_SERIAL_NUMBER" \
    -e "REPORT_DATE=$REPORT_DATE" \
    -e "REPORT_WEEK_LABEL=$REPORT_WEEK_LABEL" \
    "$DOCKER_IMAGE" \
    sh -c '
        tar -xf - &&
        latexmk \
            -xelatex \
            -usepretex \
            -pretex="\def\ReportSerialNumber{$REPORT_SERIAL_NUMBER}\def\ReportDate{$REPORT_DATE}\def\ReportWeekLabel{$REPORT_WEEK_LABEL}" \
            -interaction=nonstopmode \
            -halt-on-error \
            template.tex >&2
        cat template.pdf
    ' > "$REPO_DIR/template.pdf"
