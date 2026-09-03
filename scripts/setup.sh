#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
    pwd -P
)"

CONFIG_FILE="$REPO_DIR/.local-config"
SKILL_NAME="wr-wr"
SKILL_SOURCE="$REPO_DIR/skills/$SKILL_NAME"
REPORT_BUILD_TARGET="/usr/local/bin/report-build"
REPORT_BUILD_SOURCE="$REPO_DIR/scripts/report-build"

usage() {
    echo "Usage: $0" >&2
    echo "       $0 <absolute-pdf-output-directory>" >&2
    echo "       $0 <docker-image>" >&2
    echo "       $0 <absolute-pdf-output-directory> <docker-image>" >&2
    echo "       $0 [setup-arguments] [--skills=<codex|claude>[,...]] [--replace-existing]" >&2
    echo "Output directories must start with '/' or '~/'." >&2
}

skill_link_for_service() {
    case $1 in
        codex)
            echo "${HOME:?HOME is not set}/.agents/skills/$SKILL_NAME"
            ;;
        claude)
            echo "${HOME:?HOME is not set}/.claude/skills/$SKILL_NAME"
            ;;
    esac
}

run_install_command() {
    local elevated=$1
    shift

    if [[ $elevated -eq 1 ]]; then
        sudo "$@"
    else
        "$@"
    fi
}

link_matches_source() {
    local source=$1
    local target=$2

    [[ -L "$target" && "$target" -ef "$source" ]]
}

preflight_link() {
    local source=$1
    local target=$2
    local description=$3

    if link_matches_source "$source" "$target"; then
        return
    fi

    if [[ -d "$target" && ! -L "$target" ]]; then
        echo "$description target is a directory and cannot be replaced: $target" >&2
        return 1
    fi

    if [[ -e "$target" || -L "$target" ]]; then
        if [[ $REPLACE_EXISTING -eq 1 ]]; then
            return
        fi

        echo "$description target already exists: $target" >&2
        echo "Use --replace-existing to back it up and install the link." >&2
        return 1
    fi
}

next_backup_path() {
    local target=$1
    local backup_path="${target}.backup"
    local suffix=1

    while [[ -e "$backup_path" || -L "$backup_path" ]]; do
        backup_path="${target}.backup.$suffix"
        suffix="$((suffix + 1))"
    done

    echo "$backup_path"
}

install_link() {
    local source=$1
    local target=$2
    local description=$3
    local elevated=$4
    local target_parent
    local backup_path

    if link_matches_source "$source" "$target"; then
        echo "Already linked: $description: $target"
        return
    fi

    target_parent="$(dirname -- "$target")"
    run_install_command "$elevated" mkdir -p -- "$target_parent"

    if [[ -e "$target" || -L "$target" ]]; then
        if [[ -d "$target" && ! -L "$target" ]]; then
            echo "$description target is a directory and cannot be replaced: $target" >&2
            return 1
        elif [[ $REPLACE_EXISTING -ne 1 ]]; then
            echo "$description target appeared after the setup preflight: $target" >&2
            return 1
        fi

        backup_path="$(next_backup_path "$target")"
        run_install_command "$elevated" mv -- "$target" "$backup_path"

        if run_install_command "$elevated" ln -s -- "$source" "$target"; then
            echo "WARNING: Replaced existing $description: $target" >&2
            echo "WARNING: Previous entry saved as: $backup_path" >&2
            return
        fi

        echo "Failed to link $description after backing up the existing target." >&2
        if [[ ! -e "$target" && ! -L "$target" ]] &&
            run_install_command "$elevated" mv -- "$backup_path" "$target"
        then
            echo "Restored previous entry: $target" >&2
        else
            echo "Previous entry remains at: $backup_path" >&2
        fi
        return 1
    fi

    run_install_command "$elevated" ln -s -- "$source" "$target"
    echo "Linked: $description: $target -> $source"
}

SETUP_ARGS=()
SKILL_SERVICES=()
SKILLS_SET=0
REPLACE_EXISTING=0
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
        --replace-existing)
            if [[ $REPLACE_EXISTING -eq 1 ]]; then
                echo "--replace-existing specified more than once." >&2
                usage
                exit 2
            fi
            REPLACE_EXISTING=1
            ;;
        --replace-existing=*)
            echo "--replace-existing does not take a value." >&2
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

if [[ ! -x "$REPORT_BUILD_SOURCE" ]]; then
    echo "Build command source not found or not executable: $REPORT_BUILD_SOURCE" >&2
    exit 1
fi

if [[ ${#SKILL_SERVICES[@]} -gt 0 && ! -f "$SKILL_SOURCE/SKILL.md" ]]; then
    echo "Skill source not found: $SKILL_SOURCE/SKILL.md" >&2
    exit 1
fi

PREFLIGHT_FAILED=0
if ! preflight_link \
    "$REPORT_BUILD_SOURCE" \
    "$REPORT_BUILD_TARGET" \
    "report-build command"
then
    PREFLIGHT_FAILED=1
fi

for service in "${SKILL_SERVICES[@]}"; do
    skill_link="$(skill_link_for_service "$service")"
    if ! preflight_link "$SKILL_SOURCE" "$skill_link" "$service skill"; then
        PREFLIGHT_FAILED=1
    fi
done

if [[ $PREFLIGHT_FAILED -eq 1 ]]; then
    exit 1
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

install_link \
    "$REPORT_BUILD_SOURCE" \
    "$REPORT_BUILD_TARGET" \
    "report-build command" \
    1

for service in "${SKILL_SERVICES[@]}"; do
    skill_link="$(skill_link_for_service "$service")"
    install_link "$SKILL_SOURCE" "$skill_link" "$service skill" 0
done

echo
echo "Installed: $REPORT_BUILD_TARGET"
echo "Style:     $REPO_DIR"
echo "Image:     $DOCKER_IMAGE"
echo "PDF dir:   $OUTPUT_DIR"
