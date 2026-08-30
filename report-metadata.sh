#!/usr/bin/env bash

# Resolve a report date and its reporting-week label on the host.
# Arguments: optional date in YYYY-MM-DD format.
resolve_report_date() {
    local requested_date="${1:-}"
    local normalized_date
    local weekday
    local thursday
    local thursday_day
    local week_number

    if [[ -z "$requested_date" ]]; then
        REPORT_DATE="$(date +%F)"
    else
        if [[ ! $requested_date =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
            echo "Invalid report date (expected YYYY-MM-DD): $requested_date" >&2
            return 2
        fi
        if ! normalized_date="$(date -d "$requested_date" +%F 2>/dev/null)" ||
            [[ $normalized_date != "$requested_date" ]]
        then
            echo "Invalid report date: $requested_date" >&2
            return 2
        fi
        REPORT_DATE="$normalized_date"
    fi

    weekday="$(date -d "$REPORT_DATE" +%u)"
    thursday="$(date -d "$REPORT_DATE $((4 - weekday)) days" +%F)"
    thursday_day="${thursday##*-}"
    week_number="$(((10#$thursday_day - 1) / 7 + 1))"
    REPORT_WEEK_LABEL="${thursday:0:7}-W$week_number"
}
