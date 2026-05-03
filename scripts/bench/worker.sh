#!/usr/bin/env bash
# Single-job worker for the parallel ec-sbm bench. Invoked as:
#   externals/ec-sbm/scripts/bench/worker.sh <gen>|<clustering>|<net>|<seed>
# Skips if comparison.csv already exists; otherwise runs run_generator.sh
# and atomically appends a row to $SUMMARY (locked via flock). $LOG and
# $SUMMARY are exported by externals/ec-sbm/scripts/bench/run_bench.sh.
#
# Per-job stdout/stderr goes to data/synthetic_networks/networks/.../bench_s<seed>/run.log
# so concurrent jobs don't corrupt the shared driver LOG.

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

IFS='|' read -r GEN CLUST NET SEED <<<"$1"
RUN_ID="bench_s${SEED}"
OUT_DIR="${REPO_ROOT}/data/synthetic_networks/networks/${GEN}/${CLUST}/${NET}/${RUN_ID}"
STATS_DIR="${REPO_ROOT}/data/synthetic_networks/stats/${GEN}/${CLUST}/${NET}/${RUN_ID}"
EDGE="${OUT_DIR}/edge.csv"
COMP="${STATS_DIR}/comparison.csv"

if [[ -f "$EDGE" && -f "$COMP" && -s "$COMP" ]]; then
  flock_line "SKIP  $GEN | $CLUST | $NET | seed=$SEED (comparison.csv exists)"
  if ! grep -q "^${GEN},${CLUST},${NET},${SEED}," "$SUMMARY"; then
    flock_summary "${GEN},${CLUST},${NET},${SEED},${RUN_ID},ok,0"
  fi
  exit 0
fi

mkdir -p "$OUT_DIR"
JOB_LOG="${OUT_DIR}/run.log"

flock_line "START $GEN | $CLUST | $NET | seed=$SEED (worker pid=$$)"
T0=$(date +%s)
if bash "${REPO_ROOT}/run_generator.sh" \
      --macro \
      --generator "$GEN" \
      --network "$NET" \
      --clustering-id "$CLUST" \
      --run-id "$RUN_ID" \
      --seed "$SEED" \
      --n-threads 1 \
      --run-stats \
      --run-comp \
      >"$JOB_LOG" 2>&1; then
  STATUS=ok
else
  STATUS=fail
fi
T1=$(date +%s); DT=$((T1 - T0))

flock_line "END   $GEN | $CLUST | $NET | seed=$SEED | $STATUS | ${DT}s"
flock_summary "${GEN},${CLUST},${NET},${SEED},${RUN_ID},${STATUS},${DT}"
