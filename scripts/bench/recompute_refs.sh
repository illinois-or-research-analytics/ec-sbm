#!/usr/bin/env bash
# Recompute every stat artifact the bench depends on so comparison.csv
# carries the latest set of fields exposed by compute_*_stats.py and
# compare_pair.py — without re-running generation, which would corrupt
# the wall_s column in the bench summary.
#
# Stage 1: nuke stale stats:
#          - reference network stats:  data/empirical_networks/stats/<net>/
#          - reference cluster stats:  data/reference_clusterings/stats/<clust>/<net>/
#          - synth network/cluster stats + comparison.csv for every bench run
# Stage 2: parallel ref recompute (per net, per (net,clust)).
# Stage 3: parallel synth recompute (per completed bench run with edge.csv +
#          com.csv on disk) + fresh comparison.csv.
#
# Stage 3 deliberately does NOT append to the bench summary, so wall_s
# stays the original generation wall time.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUBMODULE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPO_ROOT="$(cd "${SUBMODULE_ROOT}/../.." && pwd)"
cd "$REPO_ROOT"

NWBENCH_BIN="/home/vltanh/miniconda3/envs/nwbench/bin"
export PATH="${NWBENCH_BIN}:${PATH}"

OUT_DIR="${SUBMODULE_ROOT}/examples/bench"
mkdir -p "$OUT_DIR"
LOG="${OUT_DIR}/recompute_refs.log"
: > "$LOG"

NET_INFO=(
  "douban|A P"
  "wordnet|A P"
  "wiki_users|A"
  "wiki_link_dyn|A"
  "lastfm_aminer|A"
  "wikiconflict|A"
  "livemocha|A"
)

CLUST_A="leiden-cpm-0.0001"
CLUST_P="leiden-cpm-0.0001+cm(piecewise)"
N_PARALLEL="${N_PARALLEL:-14}"

flock_log() {
  {
    flock 8
    echo "[$(date +'%F %T')] $*" >> "$LOG"
  } 8>>"${LOG}.lock"
}
export -f flock_log
export LOG REPO_ROOT

resolve_clust() {
  case "$1" in
    A) echo "$CLUST_A" ;;
    P) echo "$CLUST_P" ;;
    *) return 1 ;;
  esac
}

# ----- Stage 1: nuke -----
echo "[$(date +'%F %T')] === Stage 1: nuke stale stats ===" | tee -a "$LOG"
for entry in "${NET_INFO[@]}"; do
  IFS='|' read -r net clusts <<<"$entry"
  rm -rf "data/empirical_networks/stats/${net}"
  for c_tag in $clusts; do
    clust="$(resolve_clust "$c_tag")" || continue
    rm -rf "data/reference_clusterings/stats/${clust}/${net}"
  done
done

shopt -s nullglob
for run_dir in data/synthetic_networks/stats/ec-sbm-v*/*/*/bench_s*/; do
  rm -rf "${run_dir}cluster" "${run_dir}network"
  rm -f  "${run_dir}comparison.csv" "${run_dir}error.log"
done
shopt -u nullglob

# ----- Stage 2: parallel ref recompute -----
echo "[$(date +'%F %T')] === Stage 2: parallel ref recompute ===" | tee -a "$LOG"

compute_ref_network() {
  local net="$1"
  local edge="data/empirical_networks/networks/${net}/${net}.csv"
  local out="data/empirical_networks/stats/${net}"
  if [[ ! -f "$edge" ]]; then
    flock_log "MISS edge for ${net}: ${edge}"
    return
  fi
  mkdir -p "$out"
  flock_log "START refnet ${net}"
  local t0 t1 dt
  t0=$(date +%s)
  python "${REPO_ROOT}/network_evaluation/network_stats/compute_network_stats.py" \
    --network "$edge" --outdir "$out" >>"${out}/run.log" 2>&1
  local rc=$?
  t1=$(date +%s); dt=$((t1 - t0))
  flock_log "END   refnet ${net} rc=${rc} ${dt}s"
}
export -f compute_ref_network

compute_ref_cluster() {
  local net="$1" clust="$2"
  local edge="data/empirical_networks/networks/${net}/${net}.csv"
  local com="data/reference_clusterings/clusterings/${clust}/${net}/com.csv"
  local out="data/reference_clusterings/stats/${clust}/${net}"
  if [[ ! -f "$edge" || ! -f "$com" ]]; then
    flock_log "MISS edge or com for ${net}/${clust}"
    return
  fi
  mkdir -p "$out"
  flock_log "START refclust ${net} | ${clust}"
  local t0 t1 dt
  t0=$(date +%s)
  python "${REPO_ROOT}/network_evaluation/network_stats/compute_cluster_stats.py" \
    --network "$edge" --community "$com" --outdir "$out" >>"${out}/run.log" 2>&1
  local rc=$?
  t1=$(date +%s); dt=$((t1 - t0))
  flock_log "END   refclust ${net} | ${clust} rc=${rc} ${dt}s"
}
export -f compute_ref_cluster

NETS_TO_NETSTAT=()
CLUST_JOBS=()
for entry in "${NET_INFO[@]}"; do
  IFS='|' read -r net clusts <<<"$entry"
  NETS_TO_NETSTAT+=("$net")
  for c_tag in $clusts; do
    clust="$(resolve_clust "$c_tag")" || continue
    CLUST_JOBS+=("${net}|${clust}")
  done
done

echo "[$(date +'%F %T')] dispatching ${#NETS_TO_NETSTAT[@]} refnet + ${#CLUST_JOBS[@]} refclust (P=${N_PARALLEL})" | tee -a "$LOG"
printf '%s\n' "${NETS_TO_NETSTAT[@]}" | xargs -n 1 -P "$N_PARALLEL" -I {} bash -c 'compute_ref_network "$1"' _ {}
printf '%s\n' "${CLUST_JOBS[@]}"      | xargs -n 1 -P "$N_PARALLEL" -I {} bash -c 'IFS="|" read n c <<<"$1"; compute_ref_cluster "$n" "$c"' _ {}

# ----- Stage 3: parallel synth recompute + comparison -----
echo "[$(date +'%F %T')] === Stage 3: parallel synth + comparison recompute ===" | tee -a "$LOG"

compute_synth_and_compare() {
  IFS='|' read -r run_path gen clust net seed <<<"$1"
  local edge="${run_path}/edge.csv"
  local com="${run_path}/com.csv"
  if [[ ! -f "$edge" || ! -f "$com" ]]; then
    flock_log "SKIP synth (no edge/com): ${gen}|${clust}|${net}|${seed}"
    return
  fi
  local stats_dir="data/synthetic_networks/stats/${gen}/${clust}/${net}/bench_s${seed}"
  local synth_n="${stats_dir}/network"
  local synth_c="${stats_dir}/cluster"
  local ref_n="data/empirical_networks/stats/${net}"
  local ref_c="data/reference_clusterings/stats/${clust}/${net}"
  mkdir -p "$synth_n" "$synth_c" "$stats_dir"
  flock_log "START synth ${gen}|${clust}|${net}|${seed}"
  local t0 t1 dt rc=0
  t0=$(date +%s)
  {
    python "${REPO_ROOT}/network_evaluation/network_stats/compute_network_stats.py" \
      --network "$edge" --outdir "$synth_n" \
    && python "${REPO_ROOT}/network_evaluation/network_stats/compute_cluster_stats.py" \
      --network "$edge" --community "$com" --outdir "$synth_c" \
    && python "${REPO_ROOT}/network_evaluation/compare/compare_pair.py" \
      --cluster-1-folder "$synth_c" \
      --cluster-2-folder "$ref_c" \
      --network-1-folder "$synth_n" \
      --network-2-folder "$ref_n" \
      --output-file "${stats_dir}/comparison.csv" \
      --is-compare-sequence
  } >>"${stats_dir}/recompute.log" 2>&1
  rc=$?
  t1=$(date +%s); dt=$((t1 - t0))
  flock_log "END   synth ${gen}|${clust}|${net}|${seed} rc=${rc} ${dt}s"
}
export -f compute_synth_and_compare

SYNTH_JOBS=()
shopt -s nullglob
for run_dir in data/synthetic_networks/networks/ec-sbm-v*/*/*/bench_s*/; do
  if [[ -f "${run_dir}edge.csv" && -f "${run_dir}com.csv" ]]; then
    rel="${run_dir#data/synthetic_networks/networks/}"
    rel="${rel%/}"
    IFS='/' read -r gen clust net run <<<"$rel"
    seed="${run#bench_s}"
    SYNTH_JOBS+=("${run_dir%/}|${gen}|${clust}|${net}|${seed}")
  fi
done
shopt -u nullglob

echo "[$(date +'%F %T')] dispatching ${#SYNTH_JOBS[@]} synth recompute jobs (P=${N_PARALLEL})" | tee -a "$LOG"
if (( ${#SYNTH_JOBS[@]} > 0 )); then
  printf '%s\n' "${SYNTH_JOBS[@]}" | xargs -n 1 -P "$N_PARALLEL" -I {} bash -c 'compute_synth_and_compare "$1"' _ {}
fi

echo "[$(date +'%F %T')] === ALL DONE ===" | tee -a "$LOG"
