#!/usr/bin/env bash
# Recompute reference cluster stats for B0 (10K-100K) nets so cluster_*
# metrics show up in comparison.csv. Then re-run compare_pair.py for every
# (config, net, seed) in B0 to overwrite the stale comparison.csv.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUBMODULE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPO_ROOT="$(cd "${SUBMODULE_ROOT}/../.." && pwd)"
cd "$REPO_ROOT"
NWBENCH_BIN="/home/vltanh/miniconda3/envs/nwbench/bin"
export PATH="${NWBENCH_BIN}:${PATH}"

LOG="${SUBMODULE_ROOT}/examples/bench_stack/recompute_b0.log"
: > "$LOG"

B0_NETS=(
  sp_infectious wiki_rfa dblp_cite anybeat chicago_road foldoc inploid google
  marvel_universe fly_hemibrain internet_as word_assoc cora lkml_reply linux
  topology email_enron pgp_strong facebook_wall slashdot_threads
  python_dependency marker_cafe epinions_trust slashdot_zoo twitter_15m prosper
)
CLUST="leiden-cpm-0.0001"
GEN="ec-sbm-v2"
CONFIGS=(cptg stack rewire_stack)
SEEDS=(1 2 3 4 5)
N_PARALLEL="${N_PARALLEL:-14}"

flock_log() {
  {
    flock 8
    echo "[$(date +'%F %T')] $*" >> "$LOG"
  } 8>>"${LOG}.lock"
}
export -f flock_log
export LOG REPO_ROOT GEN CLUST

# Stage A: nuke + recompute reference cluster stats for B0 nets.
echo "[$(date +'%F %T')] === Stage A: re-build B0 ref cluster stats ===" | tee -a "$LOG"
for net in "${B0_NETS[@]}"; do
  rm -rf "data/reference_clusterings/stats/${CLUST}/${net}"
done

recompute_refclust() {
  local net="$1"
  local edge="data/empirical_networks/networks/${net}/${net}.csv"
  local com="data/reference_clusterings/clusterings/${CLUST}/${net}/com.csv"
  local out="data/reference_clusterings/stats/${CLUST}/${net}"
  [[ -f "$edge" && -f "$com" ]] || { flock_log "MISS $net"; return; }
  mkdir -p "$out"
  flock_log "START refclust $net"
  local t0=$(date +%s)
  python "${REPO_ROOT}/network_evaluation/network_stats/compute_cluster_stats.py" \
    --network "$edge" --community "$com" --outdir "$out" >>"${out}/run.log" 2>&1
  local rc=$?; local t1=$(date +%s)
  flock_log "END   refclust $net rc=${rc} $((t1-t0))s"
}
export -f recompute_refclust
printf '%s\n' "${B0_NETS[@]}" | xargs -n 1 -P "$N_PARALLEL" -I {} bash -c 'recompute_refclust "$1"' _ {}

# Stage B: re-run compare_pair.py for every (config, net, seed) in B0.
echo "[$(date +'%F %T')] === Stage B: re-run comparisons ===" | tee -a "$LOG"
recompare_one() {
  IFS='|' read -r cfg net seed <<<"$1"
  local synth_dir="data/synthetic_networks/stats/${GEN}/${CLUST}/${net}/${cfg}_s${seed}"
  local synth_n="${synth_dir}/network"
  local synth_c="${synth_dir}/cluster"
  local ref_n="data/empirical_networks/stats/${net}"
  local ref_c="data/reference_clusterings/stats/${CLUST}/${net}"
  if [[ ! -d "$synth_n" || ! -d "$synth_c" || ! -d "$ref_c" ]]; then
    flock_log "SKIP recompare ${cfg}|${net}|${seed} (missing dirs)"
    return
  fi
  flock_log "START recompare ${cfg}|${net}|${seed}"
  python "${REPO_ROOT}/network_evaluation/compare/compare_pair.py" \
    --cluster-1-folder "$synth_c" --cluster-2-folder "$ref_c" \
    --network-1-folder "$synth_n" --network-2-folder "$ref_n" \
    --output-file "${synth_dir}/comparison.csv" \
    --is-compare-sequence >>"${synth_dir}/recompare.log" 2>&1
  local rc=$?
  flock_log "END   recompare ${cfg}|${net}|${seed} rc=${rc}"
}
export -f recompare_one
JOBS=()
for cfg in "${CONFIGS[@]}"; do
  for net in "${B0_NETS[@]}"; do
    for seed in "${SEEDS[@]}"; do
      JOBS+=("${cfg}|${net}|${seed}")
    done
  done
done
echo "[$(date +'%F %T')] dispatching ${#JOBS[@]} recompare jobs (P=${N_PARALLEL})" | tee -a "$LOG"
printf '%s\n' "${JOBS[@]}" | xargs -n 1 -P "$N_PARALLEL" -I {} bash -c 'recompare_one "$1"' _ {}
echo "[$(date +'%F %T')] === ALL DONE ===" | tee -a "$LOG"
