#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_DIR="$( cd "${SCRIPT_DIR}/.." && pwd )"
PY_DIR="${REPO_DIR}/ec-sbm"
export PYTHONPATH="${PY_DIR}${PYTHONPATH:+:${PYTHONPATH}}"

# Default values
TIMEOUT="3d"
N_THREADS=1
KEEP_STATE=0
SEED=1

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --input-edgelist) INPUT_EDGELIST="$2"; shift ;;
        --input-clustering) INPUT_CLUSTERING="$2"; shift ;;
        --output-dir) OUTPUT_DIR="$2"; shift ;;
        --timeout) TIMEOUT="$2"; shift ;;
        --n-threads) N_THREADS="$2"; shift ;;
        --keep-state) KEEP_STATE=1 ;;
        --seed) SEED="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

export OMP_NUM_THREADS="${N_THREADS}"
# Pin: set/dict iteration order affects byte output.
export PYTHONHASHSEED=0

if [ ! -f "${INPUT_EDGELIST}" ] || [ ! -f "${INPUT_CLUSTERING}" ]; then
    echo "Error: The input network or clustering file does not exist."
    exit 1
fi

source "${SCRIPT_DIR}/state.sh"

# ==========================================
# Top-level short-circuit
# ==========================================
FINAL_DONE="${OUTPUT_DIR}/done"
FINAL_PARAMS="${OUTPUT_DIR}/params.txt"
FINAL_IN="${INPUT_EDGELIST} ${INPUT_CLUSTERING} ${FINAL_PARAMS}"
FINAL_OUT="${OUTPUT_DIR}/edge.csv ${OUTPUT_DIR}/com.csv ${OUTPUT_DIR}/sources.json"
FINAL_LOG="${OUTPUT_DIR}/run.log"

mkdir -p "${OUTPUT_DIR}"

write_params_file "${FINAL_PARAMS}" \
    "seed=${SEED}" \
    "n_threads=${N_THREADS}"

log_invocation_header "${FINAL_LOG}" "${SEED}" "${KEEP_STATE}"

if is_step_done "${FINAL_DONE}" "${FINAL_OUT}"; then
    # Top-level done must not coexist with an inconsistent .state/.
    if [ -d "${OUTPUT_DIR}/.state" ] && ! is_state_tree_consistent "${OUTPUT_DIR}/.state"; then
        echo "Top-level done valid but .state/ is inconsistent; regenerating to restore cache."
        rm -rf "${OUTPUT_DIR}/.state" "${FINAL_DONE}"
    else
        echo "Skipping entire pipeline: valid top-level done-file found."
        if [ "${KEEP_STATE}" = "1" ]; then
            echo "Keeping intermediates under ${OUTPUT_DIR}/.state (--keep-state)."
        else
            rm -rf "${OUTPUT_DIR}/.state"
        fi
        echo "=== Pipeline execution completed successfully! ==="
        echo "Final Network: ${OUTPUT_DIR}/edge.csv"
        exit 0
    fi
fi

STATE_DIR="${OUTPUT_DIR}/.state"
STG_PROFILE_DIR="${STATE_DIR}/profile"
STG_GEN_CLUSTERED_DIR="${STATE_DIR}/gen_clustered"
STG_GEN_OUTLIER_EDGES_DIR="${STATE_DIR}/gen_outlier/edges"
STG_GEN_OUTLIER_DIR="${STATE_DIR}/gen_outlier"
STG_MATCH_DEGREE_EDGES_DIR="${STATE_DIR}/match_degree/edges"
STG_MATCH_DEGREE_DIR="${STATE_DIR}/match_degree"

mkdir -p "${STG_PROFILE_DIR}" "${STG_GEN_CLUSTERED_DIR}" \
         "${STG_GEN_OUTLIER_EDGES_DIR}" "${STG_GEN_OUTLIER_DIR}" \
         "${STG_MATCH_DEGREE_EDGES_DIR}" "${STG_MATCH_DEGREE_DIR}"

# ==========================================
# STAGE 1: Profile
# ==========================================
echo "=== Starting Stage 1: Profile ==="

IN_PROFILE="${INPUT_EDGELIST} ${INPUT_CLUSTERING}"
OUT_PROFILE="${STG_PROFILE_DIR}/node_id.csv ${STG_PROFILE_DIR}/cluster_id.csv ${STG_PROFILE_DIR}/assignment.csv ${STG_PROFILE_DIR}/degree.csv ${STG_PROFILE_DIR}/mincut.csv ${STG_PROFILE_DIR}/edge_counts.csv ${STG_PROFILE_DIR}/com.csv"

if ! is_step_done "${STG_PROFILE_DIR}/done" "${OUT_PROFILE}"; then
    run_stage "${STG_PROFILE_DIR}/time_and_err.log" \
        python "${PY_DIR}/profile.py" \
        --edgelist "${INPUT_EDGELIST}" \
        --clustering "${INPUT_CLUSTERING}" \
        --output-folder "${STG_PROFILE_DIR}"
    mark_done "${STG_PROFILE_DIR}/done" "Stage 1 (profile)" "${IN_PROFILE}" "${OUT_PROFILE}"
else
    note_stage_skipped "${STG_PROFILE_DIR}/time_and_err.log"
    echo "Skipping Stage 1: Valid state found."
fi

# ==========================================
# STAGE 2: Generate Clustered
# ==========================================
echo "=== Starting Stage 2: Generate Clustered ==="

STG_GEN_CLUSTERED_PARAMS="${STG_GEN_CLUSTERED_DIR}/params.txt"
write_params_file "${STG_GEN_CLUSTERED_PARAMS}" \
    "seed=${SEED}" \
    "n_threads=${N_THREADS}"

IN_GEN_CLUSTERED="${OUT_PROFILE} ${STG_GEN_CLUSTERED_PARAMS}"
OUT_GEN_CLUSTERED="${STG_GEN_CLUSTERED_DIR}/edge.csv"

if ! is_step_done "${STG_GEN_CLUSTERED_DIR}/done" "${OUT_GEN_CLUSTERED}"; then
    run_stage "${STG_GEN_CLUSTERED_DIR}/time_and_err.log" \
        python "${PY_DIR}/gen_clustered.py" \
        --node-id "${STG_PROFILE_DIR}/node_id.csv" \
        --cluster-id "${STG_PROFILE_DIR}/cluster_id.csv" \
        --assignment "${STG_PROFILE_DIR}/assignment.csv" \
        --degree "${STG_PROFILE_DIR}/degree.csv" \
        --mincut "${STG_PROFILE_DIR}/mincut.csv" \
        --edge-counts "${STG_PROFILE_DIR}/edge_counts.csv" \
        --output-folder "${STG_GEN_CLUSTERED_DIR}" \
        --seed "${SEED}"
    mark_done "${STG_GEN_CLUSTERED_DIR}/done" "Stage 2 (gen_clustered)" "${IN_GEN_CLUSTERED}" "${OUT_GEN_CLUSTERED}"
else
    note_stage_skipped "${STG_GEN_CLUSTERED_DIR}/time_and_err.log"
    echo "Skipping Stage 2: Valid state found."
fi


# ==========================================
# STAGE 3: Outlier Generation & Combine
# ==========================================
echo "=== Starting Stage 3: Outlier Generation & Combine ==="

# 3a. Generate Outliers
STG_GEN_OUTLIER_EDGES_PARAMS="${STG_GEN_OUTLIER_EDGES_DIR}/params.txt"
write_params_file "${STG_GEN_OUTLIER_EDGES_PARAMS}" \
    "seed=$((SEED + 1))"

IN_GEN_OUTLIER="${INPUT_EDGELIST} ${INPUT_CLUSTERING} ${STG_GEN_OUTLIER_EDGES_PARAMS}"
OUT_GEN_OUTLIER="${STG_GEN_OUTLIER_EDGES_DIR}/edge_outlier.csv"

if ! is_step_done "${STG_GEN_OUTLIER_EDGES_DIR}/done" "${OUT_GEN_OUTLIER}"; then
    run_stage "${STG_GEN_OUTLIER_EDGES_DIR}/time_and_err.log" \
        python "${PY_DIR}/gen_outlier.py" \
        --edgelist "${INPUT_EDGELIST}" \
        --clustering "${INPUT_CLUSTERING}" \
        --output-folder "${STG_GEN_OUTLIER_EDGES_DIR}" \
        --seed "$((SEED + 1))"
    mark_done "${STG_GEN_OUTLIER_EDGES_DIR}/done" "Stage 3a (gen_outlier)" "${IN_GEN_OUTLIER}" "${OUT_GEN_OUTLIER}"
else
    note_stage_skipped "${STG_GEN_OUTLIER_EDGES_DIR}/time_and_err.log"
    echo "Skipping Stage 3a: Valid state found."
fi

# 3b. Combine Clustered + Outliers (pure concat; no params.txt).
IN_GEN_OUTLIER_COMBINE="${STG_GEN_CLUSTERED_DIR}/edge.csv ${STG_GEN_OUTLIER_EDGES_DIR}/edge_outlier.csv"
OUT_GEN_OUTLIER_COMBINE="${STG_GEN_OUTLIER_DIR}/edge.csv ${STG_GEN_OUTLIER_DIR}/sources.json"

if ! is_step_done "${STG_GEN_OUTLIER_DIR}/done" "${OUT_GEN_OUTLIER_COMBINE}"; then
    run_stage "${STG_GEN_OUTLIER_DIR}/time_and_err.log" \
        python "${PY_DIR}/combine_edgelists.py" \
        --edgelist-1 "${STG_GEN_CLUSTERED_DIR}/edge.csv" \
        --name-1 "clustered" \
        --edgelist-2 "${STG_GEN_OUTLIER_EDGES_DIR}/edge_outlier.csv" \
        --name-2 "outlier" \
        --output-folder "${STG_GEN_OUTLIER_DIR}" \
        --output-filename "edge.csv"
    mark_done "${STG_GEN_OUTLIER_DIR}/done" "Stage 3b (gen_outlier/combine)" "${IN_GEN_OUTLIER_COMBINE}" "${OUT_GEN_OUTLIER_COMBINE}"
else
    note_stage_skipped "${STG_GEN_OUTLIER_DIR}/time_and_err.log"
    echo "Skipping Stage 3b: Valid state found."
fi

# ==========================================
# STAGE 4: Degree Matching & Final Combine
# ==========================================
echo "=== Starting Stage 4: Degree Matching & Final Combine ==="

# 4a. Match Degrees
STG_MATCH_DEGREE_EDGES_PARAMS="${STG_MATCH_DEGREE_EDGES_DIR}/params.txt"
write_params_file "${STG_MATCH_DEGREE_EDGES_PARAMS}" \
    "seed=$((SEED + 2))"

IN_MATCH_DEGREE="${STG_GEN_OUTLIER_DIR}/edge.csv ${INPUT_EDGELIST} ${INPUT_CLUSTERING} ${STG_MATCH_DEGREE_EDGES_PARAMS}"
OUT_MATCH_DEGREE="${STG_MATCH_DEGREE_EDGES_DIR}/degree_matching_edge.csv"

if ! is_step_done "${STG_MATCH_DEGREE_EDGES_DIR}/done" "${OUT_MATCH_DEGREE}"; then
    run_stage "${STG_MATCH_DEGREE_EDGES_DIR}/time_and_err.log" \
        python "${PY_DIR}/match_degree.py" \
        --input-edgelist "${STG_GEN_OUTLIER_DIR}/edge.csv" \
        --ref-edgelist "${INPUT_EDGELIST}" \
        --ref-clustering "${INPUT_CLUSTERING}" \
        --output-folder "${STG_MATCH_DEGREE_EDGES_DIR}" \
        --seed "$((SEED + 2))"
    mark_done "${STG_MATCH_DEGREE_EDGES_DIR}/done" "Stage 4a (match_degree)" "${IN_MATCH_DEGREE}" "${OUT_MATCH_DEGREE}"
else
    note_stage_skipped "${STG_MATCH_DEGREE_EDGES_DIR}/time_and_err.log"
    echo "Skipping Stage 4a: Valid state found."
fi

# 4b. Final Combination (com.csv is a Stage-1 passthrough; moved separately).
IN_MATCH_DEGREE_COMBINE="${STG_GEN_OUTLIER_DIR}/edge.csv ${STG_GEN_OUTLIER_DIR}/sources.json ${STG_MATCH_DEGREE_EDGES_DIR}/degree_matching_edge.csv"
OUT_MATCH_DEGREE_COMBINE="${OUTPUT_DIR}/edge.csv ${OUTPUT_DIR}/sources.json"

if ! is_step_done "${STG_MATCH_DEGREE_DIR}/done" "${OUT_MATCH_DEGREE_COMBINE}"; then
    run_stage "${STG_MATCH_DEGREE_DIR}/time_and_err.log" \
        python "${PY_DIR}/combine_edgelists.py" \
        --edgelist-1 "${STG_GEN_OUTLIER_DIR}/edge.csv" \
        --json-1 "${STG_GEN_OUTLIER_DIR}/sources.json" \
        --edgelist-2 "${STG_MATCH_DEGREE_EDGES_DIR}/degree_matching_edge.csv" \
        --name-2 "match_degree" \
        --output-folder "${STG_MATCH_DEGREE_DIR}" \
        --output-filename "edge.csv"
    # Copy (not move) so stage done-files stay valid on rerun.
    cp "${STG_MATCH_DEGREE_DIR}/edge.csv" "${OUTPUT_DIR}/edge.csv"
    cp "${STG_MATCH_DEGREE_DIR}/sources.json" "${OUTPUT_DIR}/sources.json"
    mark_done "${STG_MATCH_DEGREE_DIR}/done" "Stage 4b (match_degree/combine)" "${IN_MATCH_DEGREE_COMBINE}" "${OUT_MATCH_DEGREE_COMBINE}"
else
    note_stage_skipped "${STG_MATCH_DEGREE_DIR}/time_and_err.log"
    echo "Skipping Stage 4b: Valid state found."
fi

# Promote com.csv from Stage 1 (copy, not move — preserves stage-1 hash).
cp "${STG_PROFILE_DIR}/com.csv" "${OUTPUT_DIR}/com.csv"

# ==========================================
# Consolidate per-stage logs into top-level run.log (append-only).
# ==========================================
append_stage_log "${FINAL_LOG}" "Stage 1 (profile)" "${STG_PROFILE_DIR}/time_and_err.log"
append_stage_log "${FINAL_LOG}" "Stage 1 (profile)" "${STG_PROFILE_DIR}/run.log"
append_stage_log "${FINAL_LOG}" "Stage 2 (gen_clustered)" "${STG_GEN_CLUSTERED_DIR}/time_and_err.log"
append_stage_log "${FINAL_LOG}" "Stage 2 (gen_clustered)" "${STG_GEN_CLUSTERED_DIR}/run.log"
append_stage_log "${FINAL_LOG}" "Stage 3a (gen_outlier)" "${STG_GEN_OUTLIER_EDGES_DIR}/time_and_err.log"
append_stage_log "${FINAL_LOG}" "Stage 3a (gen_outlier)" "${STG_GEN_OUTLIER_EDGES_DIR}/run.log"
append_stage_log "${FINAL_LOG}" "Stage 3b (gen_outlier/combine)" "${STG_GEN_OUTLIER_DIR}/time_and_err.log"
append_stage_log "${FINAL_LOG}" "Stage 3b (gen_outlier/combine)" "${STG_GEN_OUTLIER_DIR}/run.log"
append_stage_log "${FINAL_LOG}" "Stage 4a (match_degree)" "${STG_MATCH_DEGREE_EDGES_DIR}/time_and_err.log"
append_stage_log "${FINAL_LOG}" "Stage 4a (match_degree)" "${STG_MATCH_DEGREE_EDGES_DIR}/run.log"
append_stage_log "${FINAL_LOG}" "Stage 4b (match_degree/combine)" "${STG_MATCH_DEGREE_DIR}/time_and_err.log"
append_stage_log "${FINAL_LOG}" "Stage 4b (match_degree/combine)" "${STG_MATCH_DEGREE_DIR}/run.log"

# ==========================================
# Record top-level done and clean up
# ==========================================
mark_done "${FINAL_DONE}" "Pipeline" "${FINAL_IN}" "${FINAL_OUT}"

if [ "${KEEP_STATE}" = "1" ]; then
    echo "Keeping intermediates under ${STATE_DIR} (--keep-state)."
else
    rm -rf "${STATE_DIR}"
fi

echo "=== Pipeline execution completed successfully! ==="
echo "Final Network: ${OUTPUT_DIR}/edge.csv"
