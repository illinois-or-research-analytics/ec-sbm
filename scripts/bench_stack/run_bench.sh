#!/usr/bin/env bash
# Bench: ec-sbm-v2 with two matcher configs against
# leiden-cpm-0.0001 reference clustering, on nets in 10K-100K and
# 100K-200K node bands.
#
# config A "cptg":         --degree-matcher cluster_preserving_true_greedy        (current v2 default)
# config B "stack":        --degree-matcher cluster_preserving_true_greedy,true_greedy
# config C "rewire_stack": --degree-matcher cluster_preserving_rewire,cluster_preserving_true_greedy,true_greedy
#
# Question: does the plain-TG cleanup step recover stuck stubs without
# regressing other stats? If so, does the answer change with bucket size?
# Also: does prepending CP-rewire (which gives the bp-budget more room
# to manoeuvre via 2-opt swaps before plain TG cleanup) improve any
# stat further?
#
# Resume-safe (skip if comparison.csv exists). 5 seeds per cell.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUBMODULE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPO_ROOT="$(cd "${SUBMODULE_ROOT}/../.." && pwd)"
cd "$REPO_ROOT"

NWBENCH_BIN="/home/vltanh/miniconda3/envs/nwbench/bin"
if [[ ! -x "${NWBENCH_BIN}/python" ]]; then
  echo "FATAL: nwbench python not at ${NWBENCH_BIN}/python" >&2
  exit 1
fi
export PATH="${NWBENCH_BIN}:${PATH}"

OUT_DIR="${SUBMODULE_ROOT}/examples/bench_stack"
mkdir -p "$OUT_DIR"
LOG="${OUT_DIR}/bench.log"
SUMMARY="${OUT_DIR}/summary.csv"
WORKER="${SCRIPT_DIR}/worker.sh"

export REPO_ROOT LOG SUMMARY

N_PARALLEL="${N_PARALLEL:-14}"

# Bucket B0: 10K-100K nodes (sorted by node count ascending).
B0_NETS=(
  "sp_infectious"      # 10972 nodes
  "wiki_rfa"           # 11381
  "dblp_cite"          # 12590
  "anybeat"            # 12645
  "chicago_road"       # 12979
  "foldoc"             # 13356
  "inploid"            # 14629
  "google"             # 15763
  "marvel_universe"    # 19251
  "fly_hemibrain"      # 21739
  "internet_as"        # 22963
  "word_assoc"         # 23132
  "cora"               # 23166
  "lkml_reply"         # 26885
  "linux"              # 30834
  "topology"           # 34761
  "email_enron"        # 36692
  "pgp_strong"         # 39796
  "facebook_wall"      # 45813
  "slashdot_threads"   # 51083
  "python_dependency"  # 58739
  "marker_cafe"        # 69413
  "epinions_trust"     # 75879
  "slashdot_zoo"       # 79116
  "twitter_15m"        # 85712
  "prosper"            # 89269
)

# Bucket B1: 100K-200K nodes (matches the prior bench's network list).
B1_NETS=(
  "douban"
  "wordnet"
  "wiki_users"
  "wiki_link_dyn"
  "lastfm_aminer"
  "wikiconflict"
  "livemocha"
)

CONFIGS=(cptg stack rewire_stack)
SEEDS=(1 2 3 4 5)

touch "$LOG"
if [[ ! -s "$SUMMARY" ]]; then
  echo "config,net,seed,run_id,status,wall_s" > "$SUMMARY"
fi
chmod +x "$WORKER"

run_bucket() {
  local label="$1"; shift
  local nets=("$@")
  echo "[$(date +'%F %T')] ===== Bucket $label : ${#nets[@]} nets =====" >> "$LOG"
  jobs=()
  for net in "${nets[@]}"; do
    for cfg in "${CONFIGS[@]}"; do
      for seed in "${SEEDS[@]}"; do
        jobs+=("${cfg}|${net}|${seed}")
      done
    done
  done
  echo "[$(date +'%F %T')] dispatching ${#jobs[@]} jobs to xargs -P ${N_PARALLEL}" >> "$LOG"
  printf '%s\n' "${jobs[@]}" | xargs -n 1 -P "$N_PARALLEL" -I {} bash "$WORKER" "{}"
  echo "[$(date +'%F %T')] bucket $label done" >> "$LOG"
}

echo "[$(date +'%F %T')] driver start; N_PARALLEL=${N_PARALLEL}" >> "$LOG"
run_bucket "B0_10K_100K" "${B0_NETS[@]}"
run_bucket "B1_100K_200K" "${B1_NETS[@]}"
echo "[$(date +'%F %T')] ALL DONE" >> "$LOG"
