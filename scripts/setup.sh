#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
    pwd -P
)"

CONFIG_FILE="$REPO_DIR/.local-config"
SKILL_NAME="write-weekly-report"
SKILL_SOURCE="$REPO_DIR/skills/$SKILL_NAME"

usage() {
    echo "Usage: $0" >&2
    echo "       $0 <absolute-pdf-output-directory>" >&2
    echo "       $0 <docker-image>" >&2
    echo "       $0 <absolute-pdf-output-directory> <docker-image>" >&2
    echo "       $0 [setup-arguments] --skills=<codex|claude>[,...]" >&2
    echo "Output directories must start with '/' or '~/'." >&2
}

SETUP_ARGS=()
SKILL_SERVICES=()
SKILLS_SET=0
while [[ $# -gt 0 ]]; do
    case $1 in
        --skills=*)
            if [[ $SKILLS_SET -eq 1 ]]; then
                echo "Skills specified more than once." >&2
                usage
                exit 2
            fi

            skills_value=${1#--skills=}
            if [[ -z $skills_value || $skills_value == ,* ||
                $skills_value == *, || $skills_value == *,,* ]]
            then
                echo "Invalid skill service list: $skills_value" >&2
                usage
                exit 2
            fi

            IFS=',' read -r -a SKILL_SERVICES <<< "$skills_value"
            SKILLS_SET=1
            ;;
        --skills)
            echo "Use --skills=<codex|claude>[,...]." >&2
            usage
            exit 2
            ;;
        *)
            SETUP_ARGS+=("$1")
            ;;
    esac
    shift
done

set -- "${SETUP_ARGS[@]}"

if [[ $# -gt 2 ]]; then
    usage
    exit 2
fi

for service in "${SKILL_SERVICES[@]}"; do
    case $service in
        codex|claude)
            ;;
        *)
            echo "Unsupported skill service: $service" >&2
            usage
            exit 2
            ;;
    esac
done

PDF_OUTPUT_DIR=""
DOCKER_IMAGE=""
if [[ -f "$CONFIG_FILE" ]]; then
    source "$CONFIG_FILE"
fi

OUTPUT_DIR="$PDF_OUTPUT_DIR"

case $# in
    0)
        ;;
    1)
        if [[ $1 == /* || $1 == '~/'* ]]; then
            OUTPUT_DIR="$1"
        else
            DOCKER_IMAGE="$1"
        fi
        ;;
    2)
        OUTPUT_DIR="$1"
        DOCKER_IMAGE="$2"
        ;;
esac

if [[ -z "$OUTPUT_DIR" || -z "$DOCKER_IMAGE" ]]; then
    echo "Both output directory and Docker image must be configured." >&2
    echo "Provide both values once before omitting either argument." >&2
    usage
    exit 2
fi

if [[ $OUTPUT_DIR == '~/'* ]]; then
    OUTPUT_DIR="${HOME:?HOME is not set}/${OUTPUT_DIR#\~/}"
elif [[ $OUTPUT_DIR != /* ]]; then
    echo "Relative output directories are not allowed: $OUTPUT_DIR" >&2
    usage
    exit 2
fi

mkdir -p -- "$OUTPUT_DIR"

OUTPUT_DIR="$(
    cd -- "$OUTPUT_DIR"
    pwd -P
)"

cat > "$CONFIG_FILE" <<EOF
PDF_OUTPUT_DIR=$(printf '%q' "$OUTPUT_DIR")
DOCKER_IMAGE=$(printf '%q' "$DOCKER_IMAGE")
EOF

chmod 0600 "$CONFIG_FILE"

TARGET="/usr/local/bin/report-build"
REPORT_BUILD_SOURCE="$REPO_DIR/scripts/report-build"

if [[ -d "$TARGET" ]]; then
    echo "Install target is a directory: $TARGET" >&2
    exit 1
fi

sudo ln -sf "$REPORT_BUILD_SOURCE" "$TARGET"

install_skill_link() {
    local service=$1
    local skill_parent
    local skill_link
    local existing_source

    case $service in
        codex)
            skill_parent="${HOME:?HOME is not set}/.agents/skills"
            ;;
        claude)
            skill_parent="${HOME:?HOME is not set}/.claude/skills"
            ;;
    esac

    skill_link="$skill_parent/$SKILL_NAME"
    mkdir -p -- "$skill_parent"

    if [[ -L "$skill_link" ]]; then
        existing_source="$(cd -P -- "$skill_link" 2>/dev/null && pwd -P || true)"
        if [[ $existing_source == "$SKILL_SOURCE" ]]; then
            echo "Skill already linked for $service: $skill_link"
            return
        fi

        echo "Skill path already links elsewhere: $skill_link" >&2
        exit 1
    elif [[ -e "$skill_link" ]]; then
        echo "Skill path already exists and is not a link: $skill_link" >&2
        exit 1
    fi

    ln -s -- "$SKILL_SOURCE" "$skill_link"
    echo "Skill linked for $service: $skill_link -> $SKILL_SOURCE"
}

if [[ ${#SKILL_SERVICES[@]} -gt 0 ]]; then
    if [[ ! -f "$SKILL_SOURCE/SKILL.md" ]]; then
        echo "Skill source not found: $SKILL_SOURCE/SKILL.md" >&2
        exit 1
    fi

    for service in "${SKILL_SERVICES[@]}"; do
        install_skill_link "$service"
    done
fi

echo
echo "Installed: $TARGET"
echo "Style:     $REPO_DIR"
echo "Image:     $DOCKER_IMAGE"
echo "PDF dir:   $OUTPUT_DIR"
