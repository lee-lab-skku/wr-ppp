#!/usr/bin/env bash

# Resolve a report date, its reporting-week label, and its Monday-to-Sunday
# reporting period on the host.
# Arguments: optional date in YYYY-MM-DD format.
resolve_report_date() {
    local requested_date="${1:-}"
    local date_implementation
    local normalized_date
    local weekday
    local thursday
    local thursday_offset
    local thursday_adjustment
    local thursday_day
    local week_number
    local monday_offset
    local sunday_offset
    local monday_adjustment
    local sunday_adjustment

    if date -d "2000-01-01" +%F >/dev/null 2>&1; then
        date_implementation="gnu"
    elif date -j -f "%Y-%m-%d" "2000-01-01" +%F >/dev/null 2>&1; then
        date_implementation="bsd"
    else
        echo "Unsupported date implementation." >&2
        return 1
    fi

    if [[ -z "$requested_date" ]]; then
        REPORT_DATE="$(date +%F)"
    else
        if [[ ! $requested_date =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
            echo "Invalid report date (expected YYYY-MM-DD): $requested_date" >&2
            return 2
        fi

        if [[ $date_implementation == "gnu" ]]; then
            normalized_date="$(date -d "$requested_date 12:00:00" +%F 2>/dev/null)" ||
                normalized_date=""
        else
            normalized_date="$(
                date -j -f "%Y-%m-%d %H:%M:%S" \
                    "$requested_date 12:00:00" +%F 2>/dev/null
            )" || normalized_date=""
        fi

        if [[ -z $normalized_date ||
            $normalized_date != "$requested_date" ]]
        then
            echo "Invalid report date: $requested_date" >&2
            return 2
        fi
        REPORT_DATE="$normalized_date"
    fi

    if [[ $date_implementation == "gnu" ]]; then
        weekday="$(date -d "$REPORT_DATE 12:00:00" +%u)"
        thursday_offset="$((4 - weekday))"
        thursday="$(
            date -d "$thursday_offset days $REPORT_DATE 12:00:00" +%F
        )"
        monday_offset="$((1 - weekday))"
        sunday_offset="$((7 - weekday))"
        REPORT_WEEK_START="$(
            date -d "$monday_offset days $REPORT_DATE 12:00:00" +%F
        )"
        REPORT_WEEK_END="$(
            date -d "$sunday_offset days $REPORT_DATE 12:00:00" +%F
        )"
    else
        weekday="$(
            date -j -f "%Y-%m-%d %H:%M:%S" \
                "$REPORT_DATE 12:00:00" +%u
        )"
        thursday_offset="$((4 - weekday))"
        if [[ $thursday_offset -ge 0 ]]; then
            thursday_adjustment="+${thursday_offset}d"
        else
            thursday_adjustment="${thursday_offset}d"
        fi
        thursday="$(
            date -j -v"$thursday_adjustment" \
                -f "%Y-%m-%d %H:%M:%S" "$REPORT_DATE 12:00:00" +%F
        )"
        monday_offset="$((1 - weekday))"
        sunday_offset="$((7 - weekday))"
        if [[ $monday_offset -ge 0 ]]; then
            monday_adjustment="+${monday_offset}d"
        else
            monday_adjustment="${monday_offset}d"
        fi
        if [[ $sunday_offset -ge 0 ]]; then
            sunday_adjustment="+${sunday_offset}d"
        else
            sunday_adjustment="${sunday_offset}d"
        fi
        REPORT_WEEK_START="$(
            date -j -v"$monday_adjustment" \
                -f "%Y-%m-%d %H:%M:%S" "$REPORT_DATE 12:00:00" +%F
        )"
        REPORT_WEEK_END="$(
            date -j -v"$sunday_adjustment" \
                -f "%Y-%m-%d %H:%M:%S" "$REPORT_DATE 12:00:00" +%F
        )"
    fi

    thursday_day="${thursday##*-}"
    week_number="$(((10#$thursday_day - 1) / 7 + 1))"
    REPORT_WEEK_LABEL="${thursday:0:7}-W$week_number"
}
