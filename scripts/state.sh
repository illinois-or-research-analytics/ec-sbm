# State-tracking helpers: cache-aware stage execution via sha256 done-files.

# Usage: is_step_done "done_file" "output1 output2..."
is_step_done() {
    local done_file="$1"
    read -r -a outputs <<< "$2"

    if [ ! -f "${done_file}" ]; then
        return 1
    fi

    for target_file in "${outputs[@]}"; do
        if [ ! -f "${target_file}" ] || [ ! -s "${target_file}" ]; then
            return 1
        fi
    done

    if ! sha256sum --status -c "${done_file}" 2>/dev/null; then
        echo "State change detected. Recomputing..."
        return 1
    fi

    return 0
}

# Write a per-stage params.txt fingerprint; participates in the stage's IN hash.
# Format: one `key=value` per line, sorted. Values verbatim (no bool coercion).
# Usage: write_params_file "path/to/params.txt" "key1=val1" "key2=val2" ...
write_params_file() {
    local out_file="$1"
    shift
    if [ "$#" -eq 0 ]; then
        echo "Error [write_params_file]: at least one key=value required." >&2
        exit 2
    fi
    mkdir -p "$(dirname "${out_file}")"
    local tmp="${out_file}.tmp.$$"
    printf '%s\n' "$@" | LC_ALL=C sort > "${tmp}"
    mv "${tmp}" "${out_file}"
}


# Record a stage as done. Atomic: tmp+rename so readers never see partial state.
# Only declared inputs/outputs are hashed; incidental side-files are ignored.
# Usage: mark_done "done_file" "stage_name" "input1..." "output1..."
mark_done() {
    local done_file="$1"
    local stage_name="$2"
    read -r -a inputs <<< "$3"
    read -r -a outputs <<< "$4"

    for target_file in "${outputs[@]}"; do
        if [ ! -f "${target_file}" ]; then
            echo "Error [${stage_name}]: Output file ${target_file} was not created."
            exit 1
        fi
        if [ ! -s "${target_file}" ]; then
            echo "Error [${stage_name}]: Output file ${target_file} is completely empty (0 bytes)."
            exit 1
        fi

        local line_count=$(wc -l < "${target_file}")
        echo "Success [${stage_name}]: Verified ${target_file} ($((line_count - 1)) lines)."
    done

    local tmp_done="${done_file}.tmp.$$"
    if ! sha256sum "${inputs[@]}" "${outputs[@]}" > "${tmp_done}"; then
        echo "Error [${stage_name}]: sha256sum failed while recording I/O hashes."
        rm -f "${tmp_done}"
        exit 1
    fi
    mv "${tmp_done}" "${done_file}"
    echo "Success [${stage_name}]: I/O hashes recorded atomically. Marked as done."
}

# Verify every `done` file under .state/ still matches on disk.
# Used by --keep-state reruns so a broken inner cache can't masquerade as valid.
# Usage: is_state_tree_consistent "state_dir"
is_state_tree_consistent() {
    local state_dir="$1"
    [ -d "${state_dir}" ] || return 1
    local found_any=0
    while IFS= read -r -d '' done_file; do
        found_any=1
        if ! sha256sum --status -c "${done_file}" 2>/dev/null; then
            return 1
        fi
    done < <(find "${state_dir}" -type f -name done -print0)
    [ "${found_any}" = "1" ]
}

# Run a stage under timeout + /usr/bin/time -v, appending to time_and_err.log.
# Exit code captured outside `time` so timeouts/SIGKILLs still get recorded.
# Usage: run_stage "time_and_err.log" <command and args...>
run_stage() {
    local log="$1"; shift
    mkdir -p "$(dirname "${log}")"
    echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) | pid=$$ | host=$(hostname) | EXECUTED ===" >> "${log}"
    { timeout "${TIMEOUT}" /usr/bin/time -v "$@"; } 2>> "${log}"
    local rc=$?
    echo "=== exit=${rc} ===" >> "${log}"
    return ${rc}
}

# Record a cache-hit skip using the same header shape as run_stage.
# Usage: note_stage_skipped "time_and_err.log"
note_stage_skipped() {
    local log="$1"
    mkdir -p "$(dirname "${log}")"
    echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) | pid=$$ | host=$(hostname) | SKIPPED (cache hit) ===" >> "${log}"
}

# Append a pipeline-invocation header to run.log. Called unconditionally
# at pipeline start so even top-level cache hits leave a trace.
# Usage: log_invocation_header "run.log" "seed" "keep_state"
log_invocation_header() {
    local final_log="$1"
    local seed="$2"
    local keep_state="$3"
    mkdir -p "$(dirname "${final_log}")"
    echo "=== Invocation $(date -u +%Y-%m-%dT%H:%M:%SZ) | seed=${seed} | keep_state=${keep_state} | pid=$$ | host=$(hostname) ===" >> "${final_log}"
}

# Append a per-stage log to dest_log with a "[label] " prefix.
# Missing source logs are silently skipped (idempotent).
# Usage: append_stage_log "dest_log" "stage_label" "source_log"
append_stage_log() {
    local dest_log="$1"
    local stage_label="$2"
    local source_log="$3"

    [ -f "${source_log}" ] || return 0

    mkdir -p "$(dirname "${dest_log}")"
    {
        echo "=== [${stage_label}] ${source_log} ==="
        sed -e "s|^|[${stage_label}] |" "${source_log}"
        echo ""
    } >> "${dest_log}"
}
