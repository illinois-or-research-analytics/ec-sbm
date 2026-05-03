#!/usr/bin/env bash
# Single-job worker for the CP-TG vs (CP-TG, TG) stack bench.
# Invoked as: worker.sh <config>|<net>|<seed>
# config ∈ {cptg, stack}. Uses leiden-cpm-0.0001 as the reference clustering.
# Drives ec-sbm-v2 with the appropriate --degree-matcher override and uses
# run-id `<config>_s<seed>` so cptg and stack outputs don't collide.

set -uo pipefail

REPO_ROOT="${REPO_ROOT:?must be exported by driver}"
LOG="${LOG:?must be exported by driver}"
SUMMARY="${SUMMARY:?must be exported by driver}"

flock_line() {
  {
    flock 8
    echo "[$(date +'%F %T')] $*" >> "$LOG"
  } 8>>"${LOG}.lock"
}

flock_summary() {
  {
    flock 9
    echo "$1" >> "$SUMMARY"
  } 9>>"${SUMMARY}.lock"
}

IFS='|' read -r CONFIG NET SEED <<<"$1"
case "$CONFIG" in
  cptg)        MATCHER="cluster_preserving_true_greedy" ;;
  stack)       MATCHER="cluster_preserving_true_greedy,true_greedy" ;;
  rewire_stack) MATCHER="cluster_preserving_rewire,cluster_preserving_true_greedy,true_greedy" ;;
  *) echo "unknown config: $CONFIG" >&2; exit 2 ;;
esac

CLUST="leiden-cpm-0.0001"
RUN_ID="${CONFIG}_s${SEED}"
GEN="ec-sbm-v2"
OUT_DIR="${REPO_ROOT}/data/synthetic_networks/networks/${GEN}/${CLUST}/${NET}/${RUN_ID}"
STATS_DIR="${REPO_ROOT}/data/synthetic_networks/stats/${GEN}/${CLUST}/${NET}/${RUN_ID}"
EDGE="${OUT_DIR}/edge.csv"
COMP="${STATS_DIR}/comparison.csv"

if [[ -f "$EDGE" && -f "$COMP" && -s "$COMP" ]]; then
  flock_line "SKIP  $CONFIG | $NET | seed=$SEED (comparison.csv exists)"
  if ! grep -q "^${CONFIG},${NET},${SEED}," "$SUMMARY"; then
    flock_summary "${CONFIG},${NET},${SEED},${RUN_ID},ok,0"
  fi
  exit 0
fi

mkdir -p "$OUT_DIR"
JOB_LOG="${OUT_DIR}/run.log"

flock_line "START $CONFIG | $NET | seed=$SEED (worker pid=$$)"
T0=$(date +%s)
if bash "${REPO_ROOT}/run_generator.sh" \
      --macro \
      --generator "$GEN" \
      --network "$NET" \
      --clustering-id "$CLUST" \
      --run-id "$RUN_ID" \
      --seed "$SEED" \
      --n-threads 1 \
      --degree-matcher "$MATCHER" \
      --run-stats \
      --run-comp \
      >"$JOB_LOG" 2>&1; then
  STATUS=ok
else
  STATUS=fail
fi
T1=$(date +%s); DT=$((T1 - T0))

flock_line "END   $CONFIG | $NET | seed=$SEED | $STATUS | ${DT}s"
flock_summary "${CONFIG},${NET},${SEED},${RUN_ID},${STATUS},${DT}"
