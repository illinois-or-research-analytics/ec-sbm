#!/usr/bin/env bash
# Standalone EC-SBM driver. Linear, no caching, no short-circuit.
#
# The algorithm lives in a single configurable module pair
# (gen_clustered.py + gen_outlier.py). This script wraps the common v1
# and v2 flag bundles behind --version, and also lets advanced users
# override any individual knob.
#
# Network-generation's pipeline wrapper (src/ec-sbm/v{1,2}/pipeline.sh) is
# the cached / stage-aware version used in that repo. This script is the
# minimal version for clone-and-run use.
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PKG_DIR="$( cd "${SCRIPT_DIR}/.." && pwd )/src"
export PYTHONPATH="${PKG_DIR}${PYTHONPATH:+:${PYTHONPATH}}"

# -------- defaults (pre-preset) --------
VERSION=""
INPUT_EDGELIST=""
INPUT_CLUSTERING=""
OUTPUT_DIR=""
SEED=1
N_THREADS=1
TIMEOUT="3d"
# Profile stage (shared).
OUTLIER_MODE="excluded"
DROP_OO_BOOL="false"
# Stage 2 (gen_clustered).
SBM_OVERLAY=""          # filled by preset unless overridden
# Stage 3a (gen_outlier).
SCOPE=""                # filled by preset unless overridden
GEN_OUTLIER_MODE=""     # filled by preset unless overridden
EDGE_CORRECTION=""      # filled by preset unless overridden
# Stage 4a (match_degree).
MATCH_DEGREE_ALGORITHM=""  # filled by preset unless overridden
# Stage 2 v3-only: PSO knobs.
PSO_GAMMA=""
PSO_M_POLICY=""
PSO_M_FLOOR=""
PSO_SEARCH_STRATEGY=""
PSO_SEARCH_MAX_ITERS=""
PSO_SEARCH_INITIAL_POINTS=""
PSO_SEARCH_SAMPLES_PER_T=""
PSO_SEARCH_DIFF_TOL=""
PSO_SEARCH_STEP_TOL=""
PSO_SEARCH_T_MIN=""
PSO_SEARCH_T_MAX=""
PSO_INITIAL_T=""

usage() {
    cat >&2 <<'EOF'
Usage: run_ecsbm.sh --version {v1|v2|v3} \
                    --input-edgelist <p> \
                    --input-clustering <p> \
                    --output-dir <p> \
                    [--seed N] [--n-threads N] [--timeout DUR]
                    [--outlier-mode {excluded|singleton|combined}]         # stage 1
                    [--drop-outlier-outlier-edges|--keep-outlier-outlier-edges]  # stage 1
                    [--sbm-overlay|--no-sbm-overlay]                        # stage 2 (v1/v2)
                    [--scope {outlier-incident|all}]                        # stage 3a
                    [--gen-outlier-mode {combined|singleton}]               # stage 3a
                    [--edge-correction {none|drop|rewire}]                  # stage 3a
                    [--match-degree-algorithm {greedy|true_greedy|random_greedy|rewire|hybrid}]  # stage 4a
                    [--pso-gamma F]                                          # stage 2 (v3)
                    [--pso-search-max-iters N]                               # stage 2 (v3)
                    [--pso-search-diff-tol F]                                # stage 2 (v3)
                    [--pso-search-step-tol F]                                # stage 2 (v3)
                    [--pso-search-t-min F]                                   # stage 2 (v3)
                    [--pso-search-t-max F]                                   # stage 2 (v3)
                    [--pso-initial-t F]                                      # stage 2 (v3)

--version sets a preset flag bundle:
  v1: --sbm-overlay --scope outlier-incident --gen-outlier-mode singleton
      --edge-correction none --match-degree-algorithm greedy
  v2: --no-sbm-overlay --scope all --gen-outlier-mode combined
      --edge-correction rewire --match-degree-algorithm true_greedy
  v3: per-cluster PSO core (uniform angular, T tuned to per-cluster ccoeff)
      then v2's residual SBM + match_degree. Stage 2 of v3 ignores
      --sbm-overlay; stages 3a/4a take v2's preset.

Stage 1 defaults to --outlier-mode excluded; all presets leave it
unchanged. Any explicit flag after --version overrides the preset.
EOF
}

# -------- arg parse --------
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --version) VERSION="$2"; shift ;;
        --input-edgelist) INPUT_EDGELIST="$2"; shift ;;
        --input-clustering) INPUT_CLUSTERING="$2"; shift ;;
        --output-dir) OUTPUT_DIR="$2"; shift ;;
        --seed) SEED="$2"; shift ;;
        --n-threads) N_THREADS="$2"; shift ;;
        --timeout) TIMEOUT="$2"; shift ;;
        --outlier-mode) OUTLIER_MODE="$2"; shift ;;
        --drop-outlier-outlier-edges) DROP_OO_BOOL="true" ;;
        --keep-outlier-outlier-edges) DROP_OO_BOOL="false" ;;
        --sbm-overlay) SBM_OVERLAY="true" ;;
        --no-sbm-overlay) SBM_OVERLAY="false" ;;
        --scope) SCOPE="$2"; shift ;;
        --gen-outlier-mode) GEN_OUTLIER_MODE="$2"; shift ;;
        --edge-correction) EDGE_CORRECTION="$2"; shift ;;
        --match-degree-algorithm) MATCH_DEGREE_ALGORITHM="$2"; shift ;;
        --pso-gamma) PSO_GAMMA="$2"; shift ;;
        --pso-m-policy) PSO_M_POLICY="$2"; shift ;;
        --pso-m-floor) PSO_M_FLOOR="$2"; shift ;;
        --pso-search-strategy) PSO_SEARCH_STRATEGY="$2"; shift ;;
        --pso-search-max-iters) PSO_SEARCH_MAX_ITERS="$2"; shift ;;
        --pso-search-initial-points) PSO_SEARCH_INITIAL_POINTS="$2"; shift ;;
        --pso-search-samples-per-T) PSO_SEARCH_SAMPLES_PER_T="$2"; shift ;;
        --pso-search-diff-tol) PSO_SEARCH_DIFF_TOL="$2"; shift ;;
        --pso-search-step-tol) PSO_SEARCH_STEP_TOL="$2"; shift ;;
        --pso-search-t-min) PSO_SEARCH_T_MIN="$2"; shift ;;
        --pso-search-t-max) PSO_SEARCH_T_MAX="$2"; shift ;;
        --pso-initial-t) PSO_INITIAL_T="$2"; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown parameter: $1" >&2; usage; exit 1 ;;
    esac
    shift
done

# -------- arg check --------
if [[ -z "${VERSION}" || -z "${INPUT_EDGELIST}" || -z "${INPUT_CLUSTERING}" || -z "${OUTPUT_DIR}" ]]; then
    echo "Error: --version, --input-edgelist, --input-clustering, --output-dir are required." >&2
    usage; exit 1
fi
if [[ "${VERSION}" != "v1" && "${VERSION}" != "v2" && "${VERSION}" != "v3" ]]; then
    echo "Error: --version must be v1, v2, or v3 (got '${VERSION}')." >&2; exit 1
fi
if [[ ! -f "${INPUT_EDGELIST}" ]]; then
    echo "Error: input edgelist not found: ${INPUT_EDGELIST}" >&2; exit 1
fi
if [[ ! -f "${INPUT_CLUSTERING}" ]]; then
    echo "Error: input clustering not found: ${INPUT_CLUSTERING}" >&2; exit 1
fi

# -------- fill unset knobs from the version preset --------
if [[ "${VERSION}" == "v1" ]]; then
    : "${SBM_OVERLAY:=true}"
    : "${SCOPE:=outlier-incident}"
    : "${GEN_OUTLIER_MODE:=singleton}"
    : "${EDGE_CORRECTION:=none}"
    : "${MATCH_DEGREE_ALGORITHM:=greedy}"
elif [[ "${VERSION}" == "v2" ]]; then
    : "${SBM_OVERLAY:=false}"
    : "${SCOPE:=all}"
    : "${GEN_OUTLIER_MODE:=combined}"
    : "${EDGE_CORRECTION:=rewire}"
    : "${MATCH_DEGREE_ALGORITHM:=true_greedy}"
else  # v3 (PSO clustered + v2-style residual + match_degree)
    : "${SBM_OVERLAY:=false}"  # stage 2 of v3 ignores this; kept for params.txt
    : "${SCOPE:=all}"
    : "${GEN_OUTLIER_MODE:=combined}"
    : "${EDGE_CORRECTION:=rewire}"
    : "${MATCH_DEGREE_ALGORITHM:=true_greedy}"
    : "${PSO_GAMMA:=2.0}"
    : "${PSO_M_POLICY:=auto}"
    : "${PSO_M_FLOOR:=1}"
    : "${PSO_SEARCH_STRATEGY:=secant}"
    : "${PSO_SEARCH_MAX_ITERS:=30}"
    : "${PSO_SEARCH_INITIAL_POINTS:=5}"
    : "${PSO_SEARCH_SAMPLES_PER_T:=3}"
    : "${PSO_SEARCH_DIFF_TOL:=0.01}"
    : "${PSO_SEARCH_STEP_TOL:=0.0001}"
    : "${PSO_SEARCH_T_MIN:=0.01}"
    : "${PSO_SEARCH_T_MAX:=0.99}"
    : "${PSO_INITIAL_T:=0.5}"
fi

export OMP_NUM_THREADS="${N_THREADS}"
# Pin: set/dict iteration order affects byte output.
export PYTHONHASHSEED=0

mkdir -p "${OUTPUT_DIR}"
OUTPUT_DIR="$( cd "${OUTPUT_DIR}" && pwd )"

STAGE_DIR="${OUTPUT_DIR}/stage"
STG_PROFILE="${STAGE_DIR}/profile"
STG_GEN_CLUSTERED="${STAGE_DIR}/gen_clustered"
STG_GEN_OUTLIER_EDGES="${STAGE_DIR}/gen_outlier/edges"
STG_GEN_OUTLIER="${STAGE_DIR}/gen_outlier"
STG_MATCH_DEGREE_EDGES="${STAGE_DIR}/match_degree/edges"
STG_MATCH_DEGREE="${STAGE_DIR}/match_degree"
mkdir -p "${STG_PROFILE}" "${STG_GEN_CLUSTERED}" \
         "${STG_GEN_OUTLIER_EDGES}" "${STG_GEN_OUTLIER}" \
         "${STG_MATCH_DEGREE_EDGES}" "${STG_MATCH_DEGREE}"

FINAL_LOG="${OUTPUT_DIR}/run.log"
: > "${FINAL_LOG}"
echo "=== EC-SBM ${VERSION} | seed=${SEED} | $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" >> "${FINAL_LOG}"

run_stage() {
    local label="$1"; shift
    echo "=== Stage: ${label} ==="
    echo "--- Stage: ${label} ---" >> "${FINAL_LOG}"
    timeout "${TIMEOUT}" "$@" 2>&1 | tee -a "${FINAL_LOG}"
    local rc="${PIPESTATUS[0]}"
    if [[ "${rc}" -ne 0 ]]; then
        echo "Stage '${label}' failed with exit code ${rc}." >&2
        exit "${rc}"
    fi
}

if [[ "${DROP_OO_BOOL}" == "true" ]]; then
    PROFILE_DROP_OO_FLAG=(--drop-outlier-outlier-edges)
else
    PROFILE_DROP_OO_FLAG=(--keep-outlier-outlier-edges)
fi

if [[ "${SBM_OVERLAY}" == "true" ]]; then
    SBM_OVERLAY_FLAG=(--sbm-overlay)
else
    SBM_OVERLAY_FLAG=(--no-sbm-overlay)
fi

# ---- Stage 1: profile ----
run_stage "profile" \
    python "${PKG_DIR}/profile.py" \
    --edgelist "${INPUT_EDGELIST}" \
    --clustering "${INPUT_CLUSTERING}" \
    --output-folder "${STG_PROFILE}" \
    --outlier-mode "${OUTLIER_MODE}" \
    "${PROFILE_DROP_OO_FLAG[@]}"

# ---- Stage 2: gen_clustered ----
if [[ "${VERSION}" == "v3" ]]; then
    run_stage "gen_clustered_v3 (per-cluster PSO, T-search)" \
        python "${PKG_DIR}/gen_clustered_v3.py" \
        --node-id "${STG_PROFILE}/node_id.csv" \
        --cluster-id "${STG_PROFILE}/cluster_id.csv" \
        --assignment "${STG_PROFILE}/assignment.csv" \
        --degree "${STG_PROFILE}/degree.csv" \
        --mincut "${STG_PROFILE}/mincut.csv" \
        --edge-counts "${STG_PROFILE}/edge_counts.csv" \
        --orig-edgelist "${INPUT_EDGELIST}" \
        --orig-clustering "${INPUT_CLUSTERING}" \
        --output-folder "${STG_GEN_CLUSTERED}" \
        --seed "${SEED}" \
        --pso-gamma "${PSO_GAMMA}" \
        --pso-m-policy "${PSO_M_POLICY}" \
        --pso-m-floor "${PSO_M_FLOOR}" \
        --pso-search-strategy "${PSO_SEARCH_STRATEGY}" \
        --pso-search-max-iters "${PSO_SEARCH_MAX_ITERS}" \
        --pso-search-initial-points "${PSO_SEARCH_INITIAL_POINTS}" \
        --pso-search-samples-per-T "${PSO_SEARCH_SAMPLES_PER_T}" \
        --pso-search-diff-tol "${PSO_SEARCH_DIFF_TOL}" \
        --pso-search-step-tol "${PSO_SEARCH_STEP_TOL}" \
        --pso-search-t-min "${PSO_SEARCH_T_MIN}" \
        --pso-search-t-max "${PSO_SEARCH_T_MAX}" \
        --pso-initial-t "${PSO_INITIAL_T}"
else
    run_stage "gen_clustered (sbm_overlay=${SBM_OVERLAY})" \
        python "${PKG_DIR}/gen_clustered.py" \
        --node-id "${STG_PROFILE}/node_id.csv" \
        --cluster-id "${STG_PROFILE}/cluster_id.csv" \
        --assignment "${STG_PROFILE}/assignment.csv" \
        --degree "${STG_PROFILE}/degree.csv" \
        --mincut "${STG_PROFILE}/mincut.csv" \
        --edge-counts "${STG_PROFILE}/edge_counts.csv" \
        --output-folder "${STG_GEN_CLUSTERED}" \
        --seed "${SEED}" \
        "${SBM_OVERLAY_FLAG[@]}"
fi

# ---- Stage 3a: gen_outlier ----
# Under scope=all we subtract stage-2 output from the residual budget.
# Under scope=outlier-incident v1 doesn't consult --exist-edgelist.
GEN_OUTLIER_EXIST_FLAG=()
if [[ "${SCOPE}" == "all" ]]; then
    GEN_OUTLIER_EXIST_FLAG=(--exist-edgelist "${STG_GEN_CLUSTERED}/edge.csv")
fi
run_stage "gen_outlier (scope=${SCOPE}, outlier_mode=${GEN_OUTLIER_MODE}, edge_correction=${EDGE_CORRECTION})" \
    python "${PKG_DIR}/gen_outlier.py" \
    --orig-edgelist "${INPUT_EDGELIST}" \
    --orig-clustering "${INPUT_CLUSTERING}" \
    "${GEN_OUTLIER_EXIST_FLAG[@]}" \
    --scope "${SCOPE}" \
    --outlier-mode "${GEN_OUTLIER_MODE}" \
    --edge-correction "${EDGE_CORRECTION}" \
    --output-folder "${STG_GEN_OUTLIER_EDGES}" \
    --seed "$((SEED + 1))"

# ---- Stage 3b: combine (clustered + outlier) ----
run_stage "combine clustered+outlier" \
    python "${PKG_DIR}/combine_edgelists.py" \
    --edgelist-1 "${STG_GEN_CLUSTERED}/edge.csv" \
    --json-1 "${STG_GEN_CLUSTERED}/sources.json" \
    --edgelist-2 "${STG_GEN_OUTLIER_EDGES}/edge_outlier.csv" \
    --json-2 "${STG_GEN_OUTLIER_EDGES}/sources.json" \
    --output-folder "${STG_GEN_OUTLIER}" \
    --output-filename "edge.csv"

# ---- Stage 4a: match_degree ----
run_stage "match_degree (${MATCH_DEGREE_ALGORITHM})" \
    python "${PKG_DIR}/match_degree.py" \
    --input-edgelist "${STG_GEN_OUTLIER}/edge.csv" \
    --ref-edgelist "${INPUT_EDGELIST}" \
    --match-degree-algorithm "${MATCH_DEGREE_ALGORITHM}" \
    --output-folder "${STG_MATCH_DEGREE_EDGES}" \
    --seed "$((SEED + 2))"

# ---- Stage 4b: combine (stage3 + match_degree) ----
run_stage "combine stage3+match_degree" \
    python "${PKG_DIR}/combine_edgelists.py" \
    --edgelist-1 "${STG_GEN_OUTLIER}/edge.csv" \
    --json-1 "${STG_GEN_OUTLIER}/sources.json" \
    --edgelist-2 "${STG_MATCH_DEGREE_EDGES}/degree_matching_edge.csv" \
    --json-2 "${STG_MATCH_DEGREE_EDGES}/sources.json" \
    --output-folder "${STG_MATCH_DEGREE}" \
    --output-filename "edge.csv"

# ---- promote final artifacts ----
cp "${STG_MATCH_DEGREE}/edge.csv"     "${OUTPUT_DIR}/edge.csv"
cp "${STG_MATCH_DEGREE}/sources.json" "${OUTPUT_DIR}/sources.json"
cp "${STG_PROFILE}/com.csv"           "${OUTPUT_DIR}/com.csv"

# ---- top-level params.txt (one key=value per line, sorted) ----
{
    printf '%s\n' \
        "drop_outlier_outlier_edges=${DROP_OO_BOOL}" \
        "edge_correction=${EDGE_CORRECTION}" \
        "gen_outlier_mode=${GEN_OUTLIER_MODE}" \
        "match_degree_algorithm=${MATCH_DEGREE_ALGORITHM}" \
        "n_threads=${N_THREADS}" \
        "outlier_mode=${OUTLIER_MODE}" \
        "sbm_overlay=${SBM_OVERLAY}" \
        "scope=${SCOPE}" \
        "seed=${SEED}" \
        "version=${VERSION}"
    if [[ "${VERSION}" == "v3" ]]; then
        printf '%s\n' \
            "pso_gamma=${PSO_GAMMA}" \
            "pso_initial_t=${PSO_INITIAL_T}" \
            "pso_m_floor=${PSO_M_FLOOR}" \
            "pso_m_policy=${PSO_M_POLICY}" \
            "pso_search_diff_tol=${PSO_SEARCH_DIFF_TOL}" \
            "pso_search_initial_points=${PSO_SEARCH_INITIAL_POINTS}" \
            "pso_search_max_iters=${PSO_SEARCH_MAX_ITERS}" \
            "pso_search_samples_per_T=${PSO_SEARCH_SAMPLES_PER_T}" \
            "pso_search_step_tol=${PSO_SEARCH_STEP_TOL}" \
            "pso_search_strategy=${PSO_SEARCH_STRATEGY}" \
            "pso_search_t_max=${PSO_SEARCH_T_MAX}" \
            "pso_search_t_min=${PSO_SEARCH_T_MIN}"
    fi
} > "${OUTPUT_DIR}/params.txt"

echo "=== Done. Final network: ${OUTPUT_DIR}/edge.csv ==="
