#!/usr/bin/env bash
# Benchmark ec-sbm v1/v2 on 100K-1M-node empirical networks against
# leiden-cpm-0.0001 and leiden-cpm-0.0001+cm(piecewise) reference clusterings.
#
# Networks processed in 100K-node buckets sorted ascending by node count
# (1st pass 100K-200K, 2nd pass 200K-300K, ...). Within a bucket, all
# (gen, clustering, net, seed) jobs run in parallel via xargs -P. After
# every bucket completes, the aggregator writes a CUMULATIVE markdown
# report covering every network processed so far.
#
# Resume-safe: a job whose comparison.csv already exists is skipped.
#
# Layout (REPO_ROOT = parent network-generation repo;
# SUBMODULE_ROOT = externals/ec-sbm submodule):
#   ${REPO_ROOT}/data/synthetic_networks/networks/<gen>/<clustering>/<net>/bench_s<seed>/edge.csv,com.csv,run.log
#   ${REPO_ROOT}/data/synthetic_networks/stats/<gen>/<clustering>/<net>/bench_s<seed>/{network,cluster}/...,comparison.csv
#   ${SUBMODULE_ROOT}/examples/bench/bench.log                  driver log (one line per START/END/SKIP, flock-serialised)
#   ${SUBMODULE_ROOT}/examples/bench/summary.csv                gen,clustering,net,seed,run_id,status,wall_s
#   ${SUBMODULE_ROOT}/examples/bench/cumulative_upto_<hi>.md    cumulative report (all nets with n < hi)
#   ${SUBMODULE_ROOT}/examples/bench/cumulative_upto_<hi>.csv   tidy long-form CSV behind the report

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

OUT_DIR="${SUBMODULE_ROOT}/examples/bench"
mkdir -p "$OUT_DIR"
LOG="${OUT_DIR}/bench.log"
SUMMARY="${OUT_DIR}/summary.csv"
AGG_PY="${SCRIPT_DIR}/aggregate.py"
WORKER="${SCRIPT_DIR}/worker.sh"

export REPO_ROOT LOG SUMMARY

# Cap concurrency. 14 P-cores + 6 E-threads on i9-12900HK; leave headroom
# so the box stays usable. Override via N_PARALLEL env.
N_PARALLEL="${N_PARALLEL:-14}"

# net|nodes|edges|clusterings
NET_INFO=(
  "douban|154908|327162|A P"
  "wordnet|146005|656999|A P"
  "wiki_users|138587|715883|A"
  "wiki_link_dyn|100304|824968|A"
  "lastfm_aminer|136409|1685524|A"
  "wikiconflict|116836|2027871|A"
  "livemocha|104103|2193083|A"
)

CLUST_A="leiden-cpm-0.0001"
CLUST_P="leiden-cpm-0.0001+cm(piecewise)"
GENS=(ec-sbm-v1 ec-sbm-v2)
SEEDS=(1 2 3 4 5)

BUCKETS=(
  "100000 200000"
)

mkdir -p "$(dirname "$LOG")"
touch "$LOG"
if [[ ! -s "$SUMMARY" ]]; then
  echo "gen,clustering,net,seed,run_id,status,wall_s" > "$SUMMARY"
fi
chmod +x "$WORKER"

aggregate_cumulative() {
  local hi="$1"
  local out="${OUT_DIR}/scalar_dist.md"
  echo "[$(date +'%F %T')] AGG cumulative [100000,$hi) -> $out" >> "$LOG"
  python "$AGG_PY" --bucket-lo 100000 --bucket-hi "$hi" --out "$out" >>"$LOG" 2>&1 || \
    echo "[$(date +'%F %T')] AGG FAILED for cumulative [100000,$hi)" >> "$LOG"
}

echo "[$(date +'%F %T')] driver start; N_PARALLEL=${N_PARALLEL}" >> "$LOG"

for bk in "${BUCKETS[@]}"; do
  read -r BLO BHI <<<"$bk"
  echo "[$(date +'%F %T')] ===== Bucket [$BLO, $BHI) =====" >> "$LOG"
  bucket_jobs=()
  for entry in "${NET_INFO[@]}"; do
    IFS='|' read -r net nodes edges clusts <<<"$entry"
    if (( nodes >= BLO && nodes < BHI )); then
      for c_tag in $clusts; do
        case "$c_tag" in
          A) clust="$CLUST_A" ;;
          P) clust="$CLUST_P" ;;
          *) continue ;;
        esac
        for gen in "${GENS[@]}"; do
          for seed in "${SEEDS[@]}"; do
            bucket_jobs+=("${gen}|${clust}|${net}|${seed}")
          done
        done
      done
    fi
  done
  if [[ ${#bucket_jobs[@]} -eq 0 ]]; then
    echo "[$(date +'%F %T')] (empty bucket, skipping work + skipping report)" >> "$LOG"
    continue
  fi
  echo "[$(date +'%F %T')] dispatching ${#bucket_jobs[@]} jobs to xargs -P ${N_PARALLEL}" >> "$LOG"
  printf '%s\n' "${bucket_jobs[@]}" | xargs -n 1 -P "$N_PARALLEL" -I {} bash "$WORKER" "{}"
  echo "[$(date +'%F %T')] bucket [$BLO, $BHI) done" >> "$LOG"
  aggregate_cumulative "$BHI"
done

echo "[$(date +'%F %T')] ALL DONE" >> "$LOG"
