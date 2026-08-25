#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <pdf-output-directory> <docker-image>" >&2
    exit 2
fi

REPO_DIR="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
    pwd -P
)"

OUTPUT_DIR="$1"
DOCKER_IMAGE="$2"

mkdir -p -- "$OUTPUT_DIR"

OUTPUT_DIR="$(
    cd -- "$OUTPUT_DIR"
    pwd -P
)"

CONFIG_FILE="$REPO_DIR/.local-config"

cat > "$CONFIG_FILE" <<EOF
PDF_OUTPUT_DIR=$(printf '%q' "$OUTPUT_DIR")
DOCKER_IMAGE=$(printf '%q' "$DOCKER_IMAGE")
EOF

chmod 0600 "$CONFIG_FILE"

TARGET="/usr/local/bin/report-build"

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

cat > "$tmp" <<EOF
#!/usr/bin/env bash
set -euo pipefail

STYLE_DIR=$(printf '%q' "$REPO_DIR")
CONFIG_FILE=\$STYLE_DIR/.local-config

if [[ ! -f "\$CONFIG_FILE" ]]; then
    echo "Configuration not found: \$CONFIG_FILE" >&2
    echo "Run setup.sh again." >&2
    exit 2
fi

source "\$CONFIG_FILE"

MAIN="\${1:-main.tex}"
SRC_DIR="\$PWD"

if [[ ! -f "\$SRC_DIR/\$MAIN" ]]; then
    echo "TeX source not found: \$SRC_DIR/\$MAIN" >&2
    exit 2
fi

REPORT_NAME="\$(basename "\$SRC_DIR")"
DEST="\$PDF_OUTPUT_DIR/\$REPORT_NAME.pdf"
TMP_PDF="\$(mktemp --suffix=.pdf)"

mkdir -p -- "\$PDF_OUTPUT_DIR"
PDF_COUNT="\$(find "\$PDF_OUTPUT_DIR" -maxdepth 1 -type f -name '*.pdf' -printf x | wc -c)"
REPORT_SERIAL_NUMBER="\$((PDF_COUNT + 1))"

cleanup() {
    rm -f -- "\$TMP_PDF"
}
trap cleanup EXIT

echo "source : \$SRC_DIR" >&2
echo "main   : \$MAIN" >&2
echo "style  : \$STYLE_DIR" >&2
echo "image  : \$DOCKER_IMAGE" >&2
echo "serial : #\$REPORT_SERIAL_NUMBER" >&2
echo "output : \$DEST" >&2

if tar -C "\$SRC_DIR" -cf - . |
    docker run --rm -i \
        --network none \
        --mount "type=bind,src=\$STYLE_DIR,dst=/style,readonly" \
        --tmpfs /work:rw,exec,nosuid,size=1g \
        -e 'TEXINPUTS=/style//:' \
        -e "MAIN=\$MAIN" \
        -e "REPORT_SERIAL_NUMBER=\$REPORT_SERIAL_NUMBER" \
        "\$DOCKER_IMAGE" \
        sh -c '
            set -eu

            mkdir -p /work/src
            tar -C /work/src -xf -
            cd /work/src

            latexmk \
                -xelatex \
                -usepretex \
                -pretex="\\def\\ReportSerialNumber{\$REPORT_SERIAL_NUMBER}" \
                -interaction=nonstopmode \
                -halt-on-error \
                "\$MAIN" >&2

            PDF="\${MAIN%.tex}.pdf"

            test -f "\$PDF"
            cat "\$PDF"
        ' > "\$TMP_PDF"
then
    mv -f -- "\$TMP_PDF" "\$DEST"
    trap - EXIT

    echo "written: \$DEST" >&2
else
    echo "LaTeX build failed." >&2
    exit 1
fi
EOF

chmod 0755 "$tmp"
sudo install -m 0755 "$tmp" "$TARGET"

echo
echo "Installed: $TARGET"
echo "Style:     $REPO_DIR"
echo "Image:     $DOCKER_IMAGE"
echo "PDF dir:   $OUTPUT_DIR"
