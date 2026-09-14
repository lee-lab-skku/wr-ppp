#!/usr/bin/env bash
# Shared administrator path contract; source without changing caller options.
normalize_admin_path() {
    local value=$1
    if [[ $value == '~/'* ]]; then
        value="${HOME:?HOME is not set}/${value#\~/}"
    fi
    if [[ $value != /* || $value == *$'\t'* || $value == *$'\n'* ||
        $value == *$'\r'* || $value == */../* || $value == */.. ||
        $value == */./* || $value == */. ]]; then
        echo "Invalid administrator path: $value" >&2
        return 1
    fi
    printf '%s\n' "$value"
}
