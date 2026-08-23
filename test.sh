#!/usr/bin/env bash

CONFIG_FILE=".local-config"
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Not configured." >&2
    echo "Run ./setup.sh first." >&2
    exit 2
fi
source "$CONFIG_FILE"

tar -cf - template.tex  weekly-report.sty |
docker run --rm -i \
    --network none \
    "$DOCKER_IMAGE" \
    sh -c '
        tar -xf - &&
        latexmk \
            -xelatex \
            -interaction=nonstopmode \
            -halt-on-error \
            template.tex
        cat template.pdf
    ' > template.pdf
