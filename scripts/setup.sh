#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
    pwd -P
)"
REPOSITORY_VERSION="$(
    git -C "$REPO_DIR" describe --tags --always --dirty --match 'v[0-9]*' \
        2>/dev/null || echo "unknown"
)"

source "$REPO_DIR/scripts/admin-path-utils.sh"

CONFIG_FILE="$REPO_DIR/.local-config"
MANAGER_MANIFEST="$REPO_DIR/.manager-manifest.toml"
REPORT_BUILD_TARGET="/usr/local/bin/report-build"
REPORT_BUILD_SOURCE="$REPO_DIR/scripts/report-build"
WRITER_SKILL_NAME="wr-wr"
ADMIN_SKILL_NAME="admin-wr"

usage() {
    echo "Usage: $0 [--help]" >&2
    echo "       $0 <absolute-pdf-output-directory>" >&2
    echo "       $0 <docker-image>" >&2
    echo "       $0 <absolute-pdf-output-directory> <docker-image>" >&2
    echo "       $0 [setup-arguments] [--skills=<agents|claude|antigravity>[,...]] [--admin]" >&2
    echo "          [--admin-output=<absolute-directory>] [--replace-existing]" >&2
    echo "          [--admin-data=<absolute-directory>]" >&2
    echo "          [--auto-update[=stable|prerelease|off]]" >&2
    echo "Skill services codex, gemini, and copilot are aliases for agents." >&2
    echo "Output directories must start with '/' or '~/'." >&2
}

skill_link_for_service() {
    local service=$1
    local skill_name=$2

    case $service in
        agents)
            echo "${HOME:?HOME is not set}/.agents/skills/$skill_name"
            ;;
        antigravity)
            echo "${HOME:?HOME is not set}/.gemini/config/skills/$skill_name"
            ;;
        claude)
            echo "${HOME:?HOME is not set}/.claude/skills/$skill_name"
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

    preflight_directory_path "$(dirname -- "$target")" || return
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

preflight_directory_path() {
    local target=$1
    while [[ ! -d $target ]]; do
        if [[ -e $target || -L $target ]]; then
            echo "Directory path crosses a non-directory: $target" >&2
            return 1
        fi
        target="$(dirname -- "$target")"
    done
}

preflight_manager_manifest() {
    preflight_directory_path "$(dirname -- "$MANAGER_MANIFEST")" || return
    if [[ -L "$MANAGER_MANIFEST" ]]; then
        if [[ -f "$MANAGER_MANIFEST" ]]; then
            return
        fi
        echo "Manager manifest link does not resolve to a regular file: $MANAGER_MANIFEST" >&2
        return 1
    fi

    if [[ -e "$MANAGER_MANIFEST" && ! -f "$MANAGER_MANIFEST" ]]; then
        echo "Manager manifest target must be a regular file: $MANAGER_MANIFEST" >&2
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

# The journal includes only changes made by this setup invocation.
CHANGED_TARGETS=()
CHANGED_SOURCES=()
CHANGED_BACKUPS=()
CHANGED_ELEVATED=()
CHANGE_COUNT=0
CONFIG_STAGE=""
SETUP_COMMITTED=0

setup_cleanup() {
    local status=$? index target source backup elevated
    if [[ $SETUP_COMMITTED -eq 0 ]]; then
        index=$CHANGE_COUNT
        while [[ $index -gt 0 ]]; do
            index=$((index - 1))
            target=${CHANGED_TARGETS[$index]}
            source=${CHANGED_SOURCES[$index]}
            backup=${CHANGED_BACKUPS[$index]}
            elevated=${CHANGED_ELEVATED[$index]}
            if [[ -L $target && $(readlink "$target") == "$source" ]]; then
                if ! run_install_command "$elevated" rm -- "$target"; then
                    echo "Rollback could not remove installed link: $target" >&2
                fi
            fi
            if [[ -n $backup && ( -e $backup || -L $backup ) ]]; then
                if [[ ! -e $target && ! -L $target ]] &&
                    run_install_command "$elevated" mv -- "$backup" "$target"; then
                    echo "Restored previous entry: $target" >&2
                else
                    echo "Rollback incomplete; previous entry remains at: $backup; inspect target: $target" >&2
                fi
            fi
        done
    fi
    if [[ -n $CONFIG_STAGE ]]; then
        rm -f -- "$CONFIG_STAGE" || echo "Could not remove temporary configuration: $CONFIG_STAGE" >&2
    fi
    return "$status"
}
trap setup_cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

install_link() {
    local source=$1 target=$2 description=$3 elevated=$4
    local backup_path=""

    if link_matches_source "$source" "$target"; then
        echo "Already linked: $description: $target"
        return
    fi
    run_install_command "$elevated" mkdir -p -- "$(dirname -- "$target")"
    if [[ -e $target || -L $target ]]; then
        if [[ -d $target && ! -L $target ]]; then
            echo "$description target is a directory and cannot be replaced: $target" >&2
            return 1
        elif [[ $REPLACE_EXISTING -ne 1 ]]; then
            echo "$description target appeared after the setup preflight: $target" >&2
            return 1
        fi
        backup_path="$(next_backup_path "$target")"
    fi
    CHANGED_TARGETS[$CHANGE_COUNT]=$target
    CHANGED_SOURCES[$CHANGE_COUNT]=$source
    CHANGED_BACKUPS[$CHANGE_COUNT]=$backup_path
    CHANGED_ELEVATED[$CHANGE_COUNT]=$elevated
    CHANGE_COUNT=$((CHANGE_COUNT + 1))
    if [[ -n $backup_path ]]; then
        run_install_command "$elevated" mv -- "$target" "$backup_path"
    fi
    run_install_command "$elevated" ln -s -- "$source" "$target"
    if [[ -n $backup_path ]]; then
        echo "WARNING: Replaced existing $description: $target" >&2
        echo "WARNING: Previous entry saved as: $backup_path" >&2
    fi
    echo "Linked: $description: $target -> $source"
}

normalize_output_directory() {
    local value=$1

    if [[ $value == '~/'* ]]; then
        value="${HOME:?HOME is not set}/${value#\~/}"
    elif [[ $value != /* ]]; then
        echo "Relative output directories are not allowed: $value" >&2
        return 1
    fi

    printf '%s\n' "$value"
}

create_manager_manifest() {
    if [[ -L "$MANAGER_MANIFEST" ]]; then
        if [[ ! -f "$MANAGER_MANIFEST" ]]; then
            echo "Manager manifest link no longer resolves to a regular file: $MANAGER_MANIFEST" >&2
            return 1
        fi
        echo "Preserved: manager manifest: $MANAGER_MANIFEST"
        return
    elif [[ -f "$MANAGER_MANIFEST" ]]; then
        echo "Preserved: manager manifest: $MANAGER_MANIFEST"
        return
    elif [[ -e "$MANAGER_MANIFEST" ]]; then
        echo "Manager manifest target appeared after setup preflight: $MANAGER_MANIFEST" >&2
        return 1
    fi

    (
        umask 077
        mkdir -p -- "$(dirname -- "$MANAGER_MANIFEST")"
        set -C
        cat > "$MANAGER_MANIFEST" <<'EOF'
# Administrator report discovery manifest.
# Set storage_root and add one [[members]] table per report author before use.
schema = 1
timezone = "Asia/Seoul"

# storage_root = "/absolute/path/to/report-storage"

# [[members]]
# id = "stable-id"
# display_name = "Display Name"
# order = 10
# required = true
# search_roots = ["path/relative/to/storage-root"]
EOF
    )
    # umask above requests 0600 at creation; NAS permissions may be server-managed.
    echo "Created: manager manifest: $MANAGER_MANIFEST"
}

SETUP_ARGS=()
SKILL_SERVICES=()
SKILLS_SET=0
ADMIN=0
ADMIN_OUTPUT_SET=0
ADMIN_OUTPUT_VALUE=""
ADMIN_DATA_SET=0
ADMIN_DATA_VALUE=""
REPLACE_EXISTING=0
AUTO_UPDATE_SET=0
AUTO_UPDATE_VALUE=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        --auto-update|--auto-update=*)
            if [[ $AUTO_UPDATE_SET -eq 1 ]]; then
                echo "Automatic update channel specified more than once." >&2
                exit 2
            fi
            AUTO_UPDATE_VALUE=stable
            if [[ $1 == *=* ]]; then
                AUTO_UPDATE_VALUE=${1#*=}
            fi
            case $AUTO_UPDATE_VALUE in
                stable|prerelease|off) ;;
                *) echo "Invalid automatic update channel: $AUTO_UPDATE_VALUE" >&2; exit 2 ;;
            esac
            AUTO_UPDATE_SET=1
            ;;
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
            echo "Use --skills=<agents|claude|antigravity>[,...]." >&2
            usage
            exit 2
            ;;
        --admin)
            if [[ $ADMIN -eq 1 ]]; then
                echo "--admin specified more than once." >&2
                usage
                exit 2
            fi
            ADMIN=1
            ;;
        --admin=*)
            echo "--admin does not take a value." >&2
            usage
            exit 2
            ;;
        --admin-output=*)
            if [[ $ADMIN_OUTPUT_SET -eq 1 ]]; then
                echo "Administrator output specified more than once." >&2
                usage
                exit 2
            fi
            ADMIN_OUTPUT_VALUE=${1#--admin-output=}
            if [[ -z $ADMIN_OUTPUT_VALUE ]]; then
                echo "Administrator output directory cannot be empty." >&2
                usage
                exit 2
            fi
            ADMIN_OUTPUT_SET=1
            ;;
        --admin-output)
            echo "Use --admin-output=<absolute-directory>." >&2
            usage
            exit 2
            ;;
        --admin-data=*)
            [[ $ADMIN_DATA_SET -eq 0 && -n ${1#*=} ]] || {
                echo "Administrator data directory must be nonempty and specified once." >&2
                exit 2
            }
            ADMIN_DATA_SET=1
            ADMIN_DATA_VALUE=${1#*=}
            ;;
        --admin-data)
            echo "Use --admin-data=<absolute-directory>." >&2
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
        -*)
            echo "Unknown option: $1" >&2
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

if [[ $ADMIN -eq 1 && $SKILLS_SET -eq 0 ]]; then
    echo "--admin requires --skills=<agents|claude|antigravity>[,...]." >&2
    usage
    exit 2
fi

if [[ $ADMIN -eq 0 && ( $ADMIN_OUTPUT_SET -eq 1 || $ADMIN_DATA_SET -eq 1 ) ]]; then
    echo "Administrator path options require --admin." >&2
    usage
    exit 2
fi

VALIDATED_SERVICES=()
for service in "${SKILL_SERVICES[@]}"; do
    case $service in
        codex|gemini|copilot)
            service=agents
            ;;
        agents|claude|antigravity)
            ;;
        *)
            echo "Unsupported skill service: $service" >&2
            usage
            exit 2
            ;;
    esac

    for existing_service in "${VALIDATED_SERVICES[@]}"; do
        if [[ $service == "$existing_service" ]]; then
            echo "Skill service specified more than once: $service" >&2
            usage
            exit 2
        fi
    done
    VALIDATED_SERVICES+=("$service")
done
SKILL_SERVICES=("${VALIDATED_SERVICES[@]}")

echo "Repository version: $REPOSITORY_VERSION"

PDF_OUTPUT_DIR=""
DOCKER_IMAGE=""
ADMIN_OUTPUT_DIR=""
ADMIN_DATA_DIR=""
AUTO_UPDATE_CHANNEL=off
if [[ -f "$CONFIG_FILE" ]]; then
    source "$CONFIG_FILE"
fi
PREVIOUS_AUTO_UPDATE_CHANNEL=$AUTO_UPDATE_CHANNEL
if [[ $AUTO_UPDATE_SET -eq 1 ]]; then
    AUTO_UPDATE_CHANNEL=$AUTO_UPDATE_VALUE
fi
case $AUTO_UPDATE_CHANNEL in
    stable|prerelease|off) ;;
    *) echo "Invalid saved automatic update channel; set --auto-update explicitly." >&2; exit 2 ;;
esac

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

OUTPUT_DIR="$(normalize_output_directory "$OUTPUT_DIR")"
if [[ $ADMIN_OUTPUT_SET -eq 1 ]]; then
    ADMIN_OUTPUT_DIR="$(normalize_admin_path "$ADMIN_OUTPUT_VALUE")"
fi

if [[ $ADMIN -eq 1 ]]; then
    # Omission selects the existing repository-local layout, including on reruns.
    ADMIN_DATA_DIR=""
    if [[ $ADMIN_DATA_SET -eq 1 ]]; then
        ADMIN_DATA_DIR="$(normalize_admin_path "$ADMIN_DATA_VALUE")"
        MANAGER_MANIFEST="${ADMIN_DATA_DIR%/}/manager-manifest.toml"
    fi
    ADMIN_HISTORY_TARGET="$REPO_DIR/.admin-wr/manifests"
    if [[ -n $ADMIN_DATA_DIR ]]; then
        ADMIN_HISTORY_TARGET="${ADMIN_DATA_DIR%/}/manifests"
    fi
fi

# Validate final saved values too, after explicit overrides and local reset.
if [[ -n $ADMIN_OUTPUT_DIR ]]; then
    ADMIN_OUTPUT_DIR="$(normalize_admin_path "$ADMIN_OUTPUT_DIR")"
fi
if [[ -n $ADMIN_DATA_DIR ]]; then
    ADMIN_DATA_DIR="$(normalize_admin_path "$ADMIN_DATA_DIR")"
fi

if [[ ! -x "$REPORT_BUILD_SOURCE" ]]; then
    echo "Build command source not found or not executable: $REPORT_BUILD_SOURCE" >&2
    exit 1
fi

REQUESTED_SKILLS=()
if [[ ${#SKILL_SERVICES[@]} -gt 0 ]]; then
    REQUESTED_SKILLS+=("$WRITER_SKILL_NAME")
    if [[ $ADMIN -eq 1 ]]; then
        REQUESTED_SKILLS+=("$ADMIN_SKILL_NAME")
    fi
fi

for skill_name in "${REQUESTED_SKILLS[@]}"; do
    skill_source="$REPO_DIR/skills/$skill_name"
    if [[ ! -f "$skill_source/SKILL.md" ]]; then
        echo "Skill source not found: $skill_source/SKILL.md" >&2
        exit 1
    fi
done

PREFLIGHT_FAILED=0
if ! preflight_link \
    "$REPORT_BUILD_SOURCE" \
    "$REPORT_BUILD_TARGET" \
    "report-build command"
then
    PREFLIGHT_FAILED=1
fi

for service in "${SKILL_SERVICES[@]}"; do
    for skill_name in "${REQUESTED_SKILLS[@]}"; do
        skill_source="$REPO_DIR/skills/$skill_name"
        skill_link="$(skill_link_for_service "$service" "$skill_name")"
        if ! preflight_link \
            "$skill_source" "$skill_link" "$service $skill_name skill"
        then
            PREFLIGHT_FAILED=1
        fi
    done
done

if [[ $ADMIN -eq 1 ]] && ! preflight_manager_manifest; then
    PREFLIGHT_FAILED=1
fi

if [[ $ADMIN -eq 1 ]] && ! preflight_directory_path "$ADMIN_HISTORY_TARGET"; then
    PREFLIGHT_FAILED=1
fi

if [[ $PREFLIGHT_FAILED -eq 1 ]]; then
    exit 1
fi

mkdir -p -- "$OUTPUT_DIR"

OUTPUT_DIR="$(
    cd -- "$OUTPUT_DIR"
    pwd -P
)"

if [[ $ADMIN -eq 1 ]]; then
    create_manager_manifest
fi

CONFIG_STAGE="$(umask 077; mktemp "$REPO_DIR/.local-config.tmp.XXXXXX")"
cat > "$CONFIG_STAGE" <<EOF
PDF_OUTPUT_DIR=$(printf '%q' "$OUTPUT_DIR")
DOCKER_IMAGE=$(printf '%q' "$DOCKER_IMAGE")
ADMIN_OUTPUT_DIR=$(printf '%q' "$ADMIN_OUTPUT_DIR")
ADMIN_DATA_DIR=$(printf '%q' "$ADMIN_DATA_DIR")
AUTO_UPDATE_CHANNEL=$(printf '%q' "$AUTO_UPDATE_CHANNEL")
EOF

install_link \
    "$REPORT_BUILD_SOURCE" \
    "$REPORT_BUILD_TARGET" \
    "report-build command" \
    1

for service in "${SKILL_SERVICES[@]}"; do
    for skill_name in "${REQUESTED_SKILLS[@]}"; do
        skill_source="$REPO_DIR/skills/$skill_name"
        skill_link="$(skill_link_for_service "$service" "$skill_name")"
        install_link \
            "$skill_source" "$skill_link" "$service $skill_name skill" 0
    done
done

if [[ $AUTO_UPDATE_CHANNEL != "$PREVIOUS_AUTO_UPDATE_CHANNEL" ]]; then
    rm -f -- "$REPO_DIR/.report-update/state"
fi
mv -f -- "$CONFIG_STAGE" "$CONFIG_FILE"
SETUP_COMMITTED=1
CONFIG_STAGE=""

echo
echo "Installed:    $REPORT_BUILD_TARGET"
echo "Style:        $REPO_DIR"
echo "Image:        $DOCKER_IMAGE"
echo "Auto update:  $AUTO_UPDATE_CHANNEL"
echo "PDF dir:      $OUTPUT_DIR"
if [[ $ADMIN -eq 1 ]]; then
    if [[ -n $ADMIN_OUTPUT_DIR ]]; then
        echo "Admin output: $ADMIN_OUTPUT_DIR"
    else
        echo "Admin output: not configured"
    fi
    echo "Admin config: $MANAGER_MANIFEST"
    echo "Admin history: $ADMIN_HISTORY_TARGET"
fi
