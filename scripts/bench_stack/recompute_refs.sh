#!/usr/bin/env bash
# Pre-compute reference network stats and reference cluster stats for
# every (net, leiden-cpm-0.0001) pair the stack bench will exercise.
# Races would otherwise occur when many parallel workers hit the same
# empty ref dir from `ensure_reference_stats` in run_generator.sh.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUBMODULE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPO_ROOT="$(cd "${SUBMODULE_ROOT}/../.." && pwd)"
cd "$REPO_ROOT"

NWBENCH_BIN="/home/vltanh/miniconda3/envs/nwbench/bin"
export PATH="${NWBENCH_BIN}:${PATH}"

LOG="${SUBMODULE_ROOT}/examples/bench_stack/recompute_refs.log"
mkdir -p "$(dirname "$LOG")"
: > "$LOG"

# Union of B0 (10K-100K) and B1 (100K-200K).
NETS=(
  sp_infectious wiki_rfa dblp_cite anybeat chicago_road foldoc inploid google
  marvel_universe fly_hemibrain internet_as word_assoc cora lkml_reply linux
  topology email_enron pgp_strong facebook_wall slashdot_threads
  python_dependency marker_cafe epinions_trust slashdot_zoo twitter_15m prosper
  douban wordnet wiki_users wiki_link_dyn lastfm_aminer wikiconflict livemocha
)
CLUST="leiden-cpm-0.0001"
N_PARALLEL="${N_PARALLEL:-14}"

flock_log() {
  {
    flock 8
    echo "[$(date +'%F %T')] $*" >> "$LOG"
  } 8>>"${LOG}.lock"
}
export -f flock_log
export LOG REPO_ROOT CLUST

compute_ref_network() {
  local net="$1"
  local edge="data/empirical_networks/networks/${net}/${net}.csv"
  local out="data/empirical_networks/stats/${net}"
  [[ -f "$edge" ]] || { flock_log "MISS edge $net"; return; }
  if [[ -f "${out}/done" ]]; then flock_log "SKIP refnet $net (cached)"; return; fi
  mkdir -p "$out"
  flock_log "START refnet $net"
  local t0=$(date +%s)
  python "${REPO_ROOT}/network_evaluation/network_stats/compute_network_stats.py" \
    --network "$edge" --outdir "$out" >>"${out}/run.log" 2>&1
  local rc=$?; local t1=$(date +%s)
  flock_log "END   refnet $net rc=${rc} $((t1-t0))s"
}
export -f compute_ref_network

compute_ref_cluster() {
  local net="$1"
  local edge="data/empirical_networks/networks/${net}/${net}.csv"
  local com="data/reference_clusterings/clusterings/${CLUST}/${net}/com.csv"
  local out="data/reference_clusterings/stats/${CLUST}/${net}"
  [[ -f "$edge" && -f "$com" ]] || { flock_log "MISS $net/$CLUST"; return; }
  if [[ -f "${out}/done" ]]; then flock_log "SKIP refclust $net (cached)"; return; fi
  mkdir -p "$out"
  flock_log "START refclust $net | $CLUST"
  local t0=$(date +%s)
  python "${REPO_ROOT}/network_evaluation/network_stats/compute_cluster_stats.py" \
    --network "$edge" --community "$com" --outdir "$out" >>"${out}/run.log" 2>&1
  local rc=$?; local t1=$(date +%s)
  flock_log "END   refclust $net | $CLUST rc=${rc} $((t1-t0))s"
}
export -f compute_ref_cluster

echo "[$(date +'%F %T')] dispatching ${#NETS[@]} refnet + refclust jobs (P=${N_PARALLEL})" | tee -a "$LOG"
printf '%s\n' "${NETS[@]}" | xargs -n 1 -P "$N_PARALLEL" -I {} bash -c 'compute_ref_network "$1"' _ {}
printf '%s\n' "${NETS[@]}" | xargs -n 1 -P "$N_PARALLEL" -I {} bash -c 'compute_ref_cluster "$1"' _ {}
echo "[$(date +'%F %T')] === ALL DONE ===" | tee -a "$LOG"
