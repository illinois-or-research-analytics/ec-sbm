#!/usr/bin/env bash
# Standalone EC-SBM (v1 or v2) driver. Linear, no caching, no short-circuit.
#
# Network-generation's pipeline wrapper (src/ec-sbm/v{1,2}/pipeline.sh) is the
# cached / stage-aware version used in that repo. This script is the minimal
# version for clone-and-run use.
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PKG_DIR="$( cd "${SCRIPT_DIR}/.." && pwd )/ec-sbm"
# common/ first so gen_clustered_core resolves; package root second so the flat
# vendored helpers (profile_common, pipeline_common, ...) resolve.
export PYTHONPATH="${PKG_DIR}/common:${PKG_DIR}${PYTHONPATH:+:${PYTHONPATH}}"

# -------- defaults --------
VERSION=""
INPUT_EDGELIST=""
INPUT_CLUSTERING=""
OUTPUT_DIR=""
SEED=1
N_THREADS=1
TIMEOUT="3d"
OUTLIER_MODE="excluded"
DROP_OO_BOOL="false"
GEN_OUTLIER_MODE="combined"
EDGE_CORRECTION="rewire"
MATCH_DEGREE_ALGORITHM="hybrid"

usage() {
    cat >&2 <<'EOF'
Usage: run_ecsbm.sh --version {v1|v2} \
                    --input-edgelist <p> \
                    --input-clustering <p> \
                    --output-dir <p> \
                    [--seed N] [--n-threads N] [--timeout DUR]
                    [--outlier-mode {excluded|singleton|combined}]          # v2
                    [--drop-outlier-outlier-edges|--keep-outlier-outlier-edges]  # v2
                    [--gen-outlier-mode {combined|singleton}]               # v2
                    [--edge-correction {drop|rewire}]                        # v2
                    [--match-degree-algorithm {greedy|true_greedy|random_greedy|rewire|hybrid}]  # v2

v1 ignores all v2-only flags; --outlier-mode must be 'excluded' for v1.
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
        --gen-outlier-mode) GEN_OUTLIER_MODE="$2"; shift ;;
        --edge-correction) EDGE_CORRECTION="$2"; shift ;;
        --match-degree-algorithm) MATCH_DEGREE_ALGORITHM="$2"; shift ;;
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
if [[ "${VERSION}" != "v1" && "${VERSION}" != "v2" ]]; then
    echo "Error: --version must be v1 or v2 (got '${VERSION}')." >&2; exit 1
fi
if [[ ! -f "${INPUT_EDGELIST}" ]]; then
    echo "Error: input edgelist not found: ${INPUT_EDGELIST}" >&2; exit 1
fi
if [[ ! -f "${INPUT_CLUSTERING}" ]]; then
    echo "Error: input clustering not found: ${INPUT_CLUSTERING}" >&2; exit 1
fi

# v1 constraints.
if [[ "${VERSION}" == "v1" ]]; then
    if [[ "${OUTLIER_MODE}" != "excluded" ]]; then
        echo "Error: v1 only supports --outlier-mode excluded (got '${OUTLIER_MODE}')." >&2
        exit 1
    fi
    MATCH_DEGREE_ALGORITHM="greedy"
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

# ---- Stage 1: profile ----
run_stage "profile" \
    python "${PKG_DIR}/common/profile.py" \
    --edgelist "${INPUT_EDGELIST}" \
    --clustering "${INPUT_CLUSTERING}" \
    --output-folder "${STG_PROFILE}" \
    --outlier-mode "${OUTLIER_MODE}" \
    $( [[ "${DROP_OO_BOOL}" == "true" ]] && echo "--drop-outlier-outlier-edges" || echo "--keep-outlier-outlier-edges" )

# ---- Stage 2: gen_clustered ----
run_stage "gen_clustered (${VERSION})" \
    python "${PKG_DIR}/${VERSION}/gen_clustered.py" \
    --node-id "${STG_PROFILE}/node_id.csv" \
    --cluster-id "${STG_PROFILE}/cluster_id.csv" \
    --assignment "${STG_PROFILE}/assignment.csv" \
    --degree "${STG_PROFILE}/degree.csv" \
    --mincut "${STG_PROFILE}/mincut.csv" \
    --edge-counts "${STG_PROFILE}/edge_counts.csv" \
    --output-folder "${STG_GEN_CLUSTERED}" \
    --seed "${SEED}"

# ---- Stage 3a: gen_outlier ----
if [[ "${VERSION}" == "v1" ]]; then
    run_stage "gen_outlier (v1)" \
        python "${PKG_DIR}/v1/gen_outlier.py" \
        --edgelist "${INPUT_EDGELIST}" \
        --clustering "${INPUT_CLUSTERING}" \
        --output-folder "${STG_GEN_OUTLIER_EDGES}" \
        --seed "$((SEED + 1))"
else
    run_stage "gen_outlier (v2)" \
        python "${PKG_DIR}/v2/gen_outlier.py" \
        --orig-edgelist "${INPUT_EDGELIST}" \
        --orig-clustering "${INPUT_CLUSTERING}" \
        --exist-edgelist "${STG_GEN_CLUSTERED}/edge.csv" \
        --outlier-mode "${GEN_OUTLIER_MODE}" \
        --edge-correction "${EDGE_CORRECTION}" \
        --output-folder "${STG_GEN_OUTLIER_EDGES}" \
        --seed "$((SEED + 1))"
fi

# ---- Stage 3b: combine (clustered + outlier) ----
run_stage "combine clustered+outlier" \
    python "${PKG_DIR}/combine_edgelists.py" \
    --edgelist-1 "${STG_GEN_CLUSTERED}/edge.csv" \
    --name-1 "clustered" \
    --edgelist-2 "${STG_GEN_OUTLIER_EDGES}/edge_outlier.csv" \
    --name-2 "outlier" \
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
    --name-2 "match_degree" \
    --output-folder "${STG_MATCH_DEGREE}" \
    --output-filename "edge.csv"

# ---- promote final artifacts ----
cp "${STG_MATCH_DEGREE}/edge.csv"     "${OUTPUT_DIR}/edge.csv"
cp "${STG_MATCH_DEGREE}/sources.json" "${OUTPUT_DIR}/sources.json"
cp "${STG_PROFILE}/com.csv"           "${OUTPUT_DIR}/com.csv"

echo "=== Done. Final network: ${OUTPUT_DIR}/edge.csv ==="
