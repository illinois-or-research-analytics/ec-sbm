"""Generator-agnostic match-degree stage, with optional --remap mode.

Given an input edgelist (current pipeline output) and a reference
edgelist (defining the target per-node degree), add edges to minimize
the residual degree deficit. Five algorithms:

  - greedy        : heap, static candidate set, `set.pop()` partners (silent gridlock)
  - true_greedy   : heap, dynamic re-push; logs gridlock
  - random_greedy : weighted-random u, weighted-random v
  - rewire        : configuration-model pairing + 2-opt rewire
  - hybrid        : rewire → true_greedy fallback on stuck stubs (default)

Two target-degree modes:

  - Default: target_deg[node] = count of that node's edges in --ref-edgelist.
    Requires input and ref to share a node-ID space (ec-sbm case).

  - --remap: input IDs may not align with ref IDs (abcd / abcd+o / lfr /
    npso). Sort both input and ref node sets by descending degree, pair
    rank-by-rank (rearrangement inequality → L1- and L2-optimal pairing),
    and look up target_deg[input_node] = ref_deg[rank-paired-ref-node].
    The algorithm runs entirely in the input's ID space; match-degree
    edges are emitted in that space. No edges or cluster assignments are
    rewritten on disk.

Output: `degree_matching_edge.csv` with columns (source, target), keyed
by the input edgelist's ID space.
"""
import argparse
import json
import logging
import heapq
import random
from collections import defaultdict, deque

import numpy as np
import pandas as pd

from pipeline_common import standard_setup, timed
from graph_utils import (
    cluster_preserving_2opt_rewire,
    normalize_edge,
    run_rewire_attempts,
)


OUTLIER_MODES = ("combined", "singleton")


def parse_args():
    parser = argparse.ArgumentParser(description="Degree Matching")
    parser.add_argument("--input-edgelist", type=str, required=True)
    parser.add_argument("--ref-edgelist", type=str, required=True)
    parser.add_argument("--output-folder", type=str, required=True)
    parser.add_argument("--remap", action="store_true",
                        help="Pair input node IDs to ref node IDs by "
                             "descending-degree rank instead of assuming a "
                             "shared ID space. Target degree per input node is "
                             "the ref degree of its rank-paired ref node. "
                             "Top-up edges stay in the input's ID space.")
    parser.add_argument(
        "--degree-matcher", dest="degree_matcher", type=str,
        choices=list(ALGO_TABLE),
        default="true_greedy",
    )
    parser.add_argument(
        "--input-clustering", type=str, default=None,
        help="Clustering for the input edgelist's ID space. Required when "
             "the algorithm starts with cluster_preserving_.",
    )
    parser.add_argument(
        "--ref-clustering", type=str, default=None,
        help="Clustering for the ref edgelist's ID space. Required when "
             "the algorithm starts with cluster_preserving_; in direct "
             "mode points at the same file as --input-clustering.",
    )
    parser.add_argument(
        "--outlier-mode", choices=list(OUTLIER_MODES), default="combined",
        help="Block assignment for nodes absent from the clustering file. "
             "'combined' lumps every outlier into one block; 'singleton' "
             "gives each outlier its own block. Consulted only by "
             "cluster_preserving_* algorithms.",
    )
    parser.add_argument("--seed", type=int, default=1)
    return parser.parse_args()


def load_reference_topologies(orig_edgelist_fp, input_edgelist_fp=None):
    """Direct-ID mode: node_id2iid + out_degs keyed by ref IDs.

    If an input edgelist path is given, its endpoints are unioned into the
    node set so nodes that are present in the input edgelist but isolated
    in the ref edgelist stay tracked. Such nodes get target degree 0;
    their stage-2 edges still decrement their partners' residuals.
    """
    df_orig_edges = pd.read_csv(orig_edgelist_fp, dtype=str)

    all_orig_nodes = (
        set(df_orig_edges["source"])
        .union(set(df_orig_edges["target"]))
    )
    if input_edgelist_fp is not None:
        df_in = pd.read_csv(input_edgelist_fp, dtype=str)
        all_orig_nodes = all_orig_nodes.union(
            set(df_in["source"]).union(set(df_in["target"]))
        )

    node_id2iid = {u: i for i, u in enumerate(sorted(all_orig_nodes))}
    node_iid2id = {i: u for u, i in node_id2iid.items()}
    out_degs = {iid: 0 for iid in node_iid2id.keys()}

    for src, tgt in zip(df_orig_edges["source"], df_orig_edges["target"]):
        out_degs[node_id2iid[src]] += 1
        out_degs[node_id2iid[tgt]] += 1

    return node_id2iid, node_iid2id, out_degs


def load_remap_topologies(input_edgelist_fp, ref_edgelist_fp):
    """Remap mode: node_id2iid keyed by INPUT IDs; target degrees come from
    pairing input and ref nodes rank-by-rank on descending degree.
    """
    in_df = pd.read_csv(input_edgelist_fp, dtype=str)
    ref_df = pd.read_csv(ref_edgelist_fp, dtype=str)

    in_endpoints = pd.concat([in_df["source"], in_df["target"]], ignore_index=True)
    ref_endpoints = pd.concat([ref_df["source"], ref_df["target"]], ignore_index=True)

    in_deg_series = in_endpoints.value_counts()
    ref_deg_series = ref_endpoints.value_counts()

    in_nodes = sorted(in_deg_series.index, key=lambda n: (-int(in_deg_series[n]), n))
    ref_nodes = sorted(ref_deg_series.index, key=lambda n: (-int(ref_deg_series[n]), n))

    if len(in_nodes) != len(ref_nodes):
        logging.warning(
            f"Remap: |input nodes|={len(in_nodes)} vs |ref nodes|={len(ref_nodes)}; "
            f"pairing first {min(len(in_nodes), len(ref_nodes))} ranks, dropping excess."
        )

    n_pair = min(len(in_nodes), len(ref_nodes))
    node_id2iid = {u: i for i, u in enumerate(in_nodes[:n_pair])}
    node_iid2id = {i: u for u, i in node_id2iid.items()}

    out_degs = {
        node_id2iid[in_nodes[i]]: int(ref_deg_series[ref_nodes[i]])
        for i in range(n_pair)
    }
    return node_id2iid, node_iid2id, out_degs


def subtract_existing_edges(exist_edgelist_fp, node_id2iid, out_degs):
    df_exist_edges = pd.read_csv(exist_edgelist_fp, dtype=str)
    exist_neighbor = {iid: set() for iid in node_id2iid.values()}

    for src, tgt in zip(df_exist_edges["source"], df_exist_edges["target"]):
        src_iid, tgt_iid = node_id2iid[src], node_id2iid[tgt]
        if tgt_iid in exist_neighbor[src_iid]:
            continue

        exist_neighbor[src_iid].add(tgt_iid)
        exist_neighbor[tgt_iid].add(src_iid)

        out_degs[src_iid] = max(0, out_degs[src_iid] - 1)
        out_degs[tgt_iid] = max(0, out_degs[tgt_iid] - 1)

    return exist_neighbor, out_degs


def match_missing_degrees_random_greedy(out_degs, exist_neighbor):
    logging.info("Starting Randomized Greedy matching algorithm...")

    available_degrees = {k: v for k, v in sorted(out_degs.items()) if v > 0}
    available_nodes = list(available_degrees.keys())

    initial_missing_stubs = sum(available_degrees.values())
    logging.info(
        f"Initial missing stubs: {initial_missing_stubs} (Target edges: {initial_missing_stubs // 2})"
    )

    degree_edges = set()
    stuck_nodes = set()

    while available_nodes:
        weights = [available_degrees[n] for n in available_nodes]
        u = random.choices(available_nodes, weights=weights, k=1)[0]

        invalid_targets = exist_neighbor.get(u, set())
        valid_targets = [
            n for n in available_nodes if n != u and n not in invalid_targets
        ]

        if not valid_targets:
            available_nodes.remove(u)
            stuck_nodes.add(u)
            continue

        v_weights = [available_degrees[n] for n in valid_targets]
        v = random.choices(valid_targets, weights=v_weights, k=1)[0]

        degree_edges.add((min(u, v), max(u, v)))
        exist_neighbor[u].add(v)
        exist_neighbor[v].add(u)

        available_degrees[u] -= 1
        available_degrees[v] -= 1

        if available_degrees[u] == 0:
            available_nodes.remove(u)
        if available_degrees[v] == 0:
            available_nodes.remove(v)

    if stuck_nodes:
        stuck_stubs = sum(available_degrees[n] for n in stuck_nodes)
        logging.warning(
            f"Finished with {len(stuck_nodes)} physically gridlocked nodes. {stuck_stubs} missing stubs dropped."
        )

    return degree_edges


def match_missing_degrees_greedy(out_degs, exist_neighbor):
    logging.info("Starting Original Greedy matching algorithm...")
    available_node_set = {node_iid for node_iid, deg in out_degs.items() if deg > 0}
    available_node_degrees = {
        node_iid: deg for node_iid, deg in out_degs.items() if deg > 0
    }

    initial_missing_stubs = sum(available_node_degrees.values())
    logging.info(f"Initial missing stubs: {initial_missing_stubs}")

    max_heap = [(-degree, node) for node, degree in available_node_degrees.items()]
    heapq.heapify(max_heap)

    degree_edges = set()

    while max_heap:
        _, available_c_node = heapq.heappop(max_heap)

        if available_c_node not in available_node_degrees:
            continue

        invalid_targets = exist_neighbor.get(available_c_node, set()).copy()
        invalid_targets.add(available_c_node)
        available_non_neighbors = available_node_set - invalid_targets

        avail_k = min(
            available_node_degrees[available_c_node], len(available_non_neighbors)
        )

        # `set.pop()` returns hash-slot order; pick the smallest id instead so
        # the algorithm is deterministic across PYTHONHASHSEED values and
        # matches the JS port at vltanh.github.io/netgen/matcher.html.
        sorted_non_neighbors = sorted(available_non_neighbors)
        for k in range(avail_k):
            edge_end = sorted_non_neighbors[k]
            degree_edges.add((available_c_node, edge_end))

            exist_neighbor[available_c_node].add(edge_end)
            exist_neighbor[edge_end].add(available_c_node)

            available_node_degrees[edge_end] -= 1
            if available_node_degrees[edge_end] == 0:
                available_node_set.remove(edge_end)
                del available_node_degrees[edge_end]

        del available_node_degrees[available_c_node]
        available_node_set.remove(available_c_node)

    return degree_edges


def match_missing_degrees_true_greedy(out_degs, exist_neighbor):
    logging.info("Starting True Dynamic Greedy matching algorithm...")

    current_degrees = {n: d for n, d in out_degs.items() if d > 0}

    initial_missing_stubs = sum(current_degrees.values())
    logging.info(
        f"Initial missing stubs: {initial_missing_stubs} (Target edges: {initial_missing_stubs // 2})"
    )

    heap = [(-deg, n) for n, deg in current_degrees.items()]
    heapq.heapify(heap)

    degree_edges = set()
    stuck_nodes = set()

    while heap:
        neg_deg, u = heapq.heappop(heap)
        deg_u = -neg_deg

        # Lazy deletion: skip stale heap entries.
        if u not in current_degrees or deg_u != current_degrees[u]:
            continue

        invalid_targets = exist_neighbor.get(u, set())
        valid_targets = [
            n for n in current_degrees if n != u and n not in invalid_targets
        ]

        if not valid_targets:
            stuck_nodes.add(u)
            del current_degrees[u]
            continue

        # Tie-break on id ascending so the choice is deterministic across
        # dict-iteration order and matches the JS port.
        v = max(valid_targets, key=lambda x: (current_degrees[x], -x))

        degree_edges.add((min(u, v), max(u, v)))
        exist_neighbor[u].add(v)
        exist_neighbor[v].add(u)

        current_degrees[u] -= 1
        current_degrees[v] -= 1

        if current_degrees[u] > 0:
            heapq.heappush(heap, (-current_degrees[u], u))
        else:
            del current_degrees[u]

        if current_degrees[v] > 0:
            heapq.heappush(heap, (-current_degrees[v], v))
        elif v in current_degrees:
            del current_degrees[v]

    if stuck_nodes:
        stuck_stubs = sum(out_degs[n] for n in stuck_nodes) - sum(
            current_degrees.get(n, 0) for n in stuck_nodes
        )
        logging.warning(f"Finished with {len(stuck_nodes)} gridlocked nodes.")

    return degree_edges


def match_missing_degrees_rewire(out_degs, exist_neighbor, max_retries=10):
    """Configuration-model pairing + 2-opt rewire for conflicts.

    Returns (valid_edges, invalid_edges). Self-loops, duplicates, and
    pre-existing neighbors are queued for rewiring; hybrid caller falls
    back to true-greedy on whatever remains invalid.
    """
    logging.info("Starting Rewire (Configuration Model) matching algorithm...")

    stubs = []
    for node_iid, deg in sorted(out_degs.items()):
        stubs.extend([node_iid] * int(deg))

    if len(stubs) % 2 != 0:
        logging.warning(
            "Odd number of total missing stubs. Dropping one to maintain parity."
        )
        stubs.pop()

    logging.info(
        f"Total missing stubs to pair: {len(stubs)} (Target edges: {len(stubs)//2})"
    )
    random.shuffle(stubs)

    valid_edges = set()
    invalid_edges = deque()

    for i in range(0, len(stubs), 2):
        u, v = stubs[i], stubs[i + 1]
        e = normalize_edge(u, v)

        if u == v or e in valid_edges or v in exist_neighbor.get(u, set()):
            invalid_edges.append(e)
        else:
            valid_edges.add(e)

    logging.info(
        f"Initial pairing complete -> Valid edges: {len(valid_edges)} | Bad edges to rewire: {len(invalid_edges)}"
    )

    valid_pool = sorted(valid_edges)

    def is_valid(e):
        u, v = e
        return u != v and e not in valid_edges and v not in exist_neighbor.get(u, set())

    def process_one_edge(e1, invalid_edges):
        """2-opt swap e1 against a random valid edge. Returns True to break outer pass."""
        if not valid_pool:
            invalid_edges.append(e1)
            return True

        idx = random.randrange(len(valid_pool))
        e2 = valid_pool[idx]

        if random.random() < 0.5:
            new_e1 = normalize_edge(e1[0], e2[0])
            new_e2 = normalize_edge(e1[1], e2[1])
        else:
            new_e1 = normalize_edge(e1[0], e2[1])
            new_e2 = normalize_edge(e1[1], e2[0])

        if is_valid(new_e1) and is_valid(new_e2) and new_e1 != new_e2:
            valid_edges.remove(e2)
            valid_pool[idx] = valid_pool[-1]
            valid_pool.pop()

            valid_edges.add(new_e1)
            valid_edges.add(new_e2)
            valid_pool.append(new_e1)
            valid_pool.append(new_e2)
        else:
            invalid_edges.append(e1)

        return False

    run_rewire_attempts(invalid_edges, process_one_edge, max_retries)
    if invalid_edges:
        logging.warning(
            f"Finished {max_retries} retries. {len(invalid_edges)} bad edges remain unresolved."
        )
    return valid_edges, list(invalid_edges)


def match_missing_degrees_hybrid_bands(out_degs, exist_neighbor):
    """Hybrid (rewire → true_greedy fallback) returning the two bands separately.

    Returns ``{"hybrid_rewire": set, "hybrid_true_greedy": set}``.
    """
    logging.info("Starting Hybrid (Rewire -> True Greedy) matching algorithm...")

    valid_edges, invalid_edges = match_missing_degrees_rewire(
        out_degs, exist_neighbor, max_retries=10
    )

    if not invalid_edges:
        return {"hybrid_rewire": valid_edges, "hybrid_true_greedy": set()}

    logging.info(
        f"Hybrid transition: Passing {len(invalid_edges)} gridlocked edges "
        f"({len(invalid_edges) * 2} stubs) to True Greedy deterministic fallback."
    )

    remaining_out_degs = {n: 0 for n in sorted(out_degs.keys())}
    for u, v in invalid_edges:
        remaining_out_degs[u] += 1
        remaining_out_degs[v] += 1

    remaining_out_degs = {n: d for n, d in remaining_out_degs.items() if d > 0}

    for u, v in valid_edges:
        exist_neighbor[u].add(v)
        exist_neighbor[v].add(u)

    greedy_edges = match_missing_degrees_true_greedy(remaining_out_degs, exist_neighbor)

    return {"hybrid_rewire": valid_edges, "hybrid_true_greedy": greedy_edges}


def match_missing_degrees_hybrid(out_degs, exist_neighbor):
    """Backward-compat wrapper: returns flat union of the two hybrid bands."""
    bands = match_missing_degrees_hybrid_bands(out_degs, exist_neighbor)
    return bands["hybrid_rewire"] | bands["hybrid_true_greedy"]


# ---------------------------------------------------------------------------
# Cluster-preserving variants (per-bp budget tracking)
# ---------------------------------------------------------------------------


def build_block_assignment(node_id2iid, clustering_fp, outlier_mode):
    """Block array indexed by node iid.

    Mirrors ``gen_outlier.assign_blocks`` so direct-mode bp counts match
    ec-sbm's stage-3a accounting. Cluster ids enter sorted ascending and
    take iids ``0..K-1``. Outliers (nodes absent from the clustering file)
    are bucketed per ``outlier_mode``: combined -> single block ``K``;
    singleton -> consecutive ids ``K, K+1, ...`` ordered by node id.
    """
    df = pd.read_csv(clustering_fp, dtype=str)
    node2cluster = dict(zip(df["node_id"], df["cluster_id"]))

    n = len(node_id2iid)
    b = np.empty(n, dtype=int)

    relevant_clusters = sorted({
        node2cluster[nd] for nd in node_id2iid if nd in node2cluster
    })
    cluster_id2iid = {c: i for i, c in enumerate(relevant_clusters)}
    next_iid = len(cluster_id2iid)

    sorted_nodes = sorted(node_id2iid.keys())
    has_outliers = any(nd not in node2cluster for nd in sorted_nodes)
    combined_block = None
    if has_outliers and outlier_mode == "combined":
        combined_block = next_iid
        next_iid += 1

    for nd in sorted_nodes:
        u_iid = node_id2iid[nd]
        if nd in node2cluster:
            b[u_iid] = cluster_id2iid[node2cluster[nd]]
        elif outlier_mode == "combined":
            b[u_iid] = combined_block
        else:
            b[u_iid] = next_iid
            next_iid += 1

    return b


def _bp_counts(edgelist_fp, b, node_id2iid):
    """Per-(min_block, max_block) edge counts for an edgelist.

    Endpoints not in ``node_id2iid`` are skipped (rare: would only happen
    if the caller built the iid map from a non-superset input).
    """
    df = pd.read_csv(edgelist_fp, dtype=str)
    counts = defaultdict(int)
    for src, tgt in zip(df["source"], df["target"]):
        if src not in node_id2iid or tgt not in node_id2iid:
            continue
        u, v = node_id2iid[src], node_id2iid[tgt]
        bu, bv = int(b[u]), int(b[v])
        counts[(min(bu, bv), max(bu, bv))] += 1
    return counts


def build_bp_budget_remap(input_edgelist_fp, ref_edgelist_fp,
                          input_clustering_fp, outlier_mode, node_id2iid):
    """Remap-mode bp budget in INPUT block space.

    Rank-pair (descending degree, ties by node id) maps each ref node to
    an input node. Each ref edge ``(a, b)`` translates to its rank-paired
    input pair, whose bp under ``input_clustering`` increments
    ``induced_bp``. Budget = ``induced_bp - input_bp`` clamped at 0.

    Ref-side clustering plays no role: the rank-pair already mediates the
    translation, and the budget lives in input block space.
    """
    b = build_block_assignment(node_id2iid, input_clustering_fp, outlier_mode)

    in_df = pd.read_csv(input_edgelist_fp, dtype=str)
    ref_df = pd.read_csv(ref_edgelist_fp, dtype=str)

    in_endpoints = pd.concat([in_df["source"], in_df["target"]], ignore_index=True)
    ref_endpoints = pd.concat([ref_df["source"], ref_df["target"]], ignore_index=True)
    in_deg = in_endpoints.value_counts()
    ref_deg = ref_endpoints.value_counts()

    in_nodes = sorted(in_deg.index, key=lambda n: (-int(in_deg[n]), n))
    ref_nodes = sorted(ref_deg.index, key=lambda n: (-int(ref_deg[n]), n))
    n_pair = min(len(in_nodes), len(ref_nodes))
    ref_node2input_id = {ref_nodes[i]: in_nodes[i] for i in range(n_pair)}

    induced_bp = defaultdict(int)
    for src, tgt in zip(ref_df["source"], ref_df["target"]):
        u_id = ref_node2input_id.get(src)
        v_id = ref_node2input_id.get(tgt)
        if u_id is None or v_id is None:
            continue
        if u_id not in node_id2iid or v_id not in node_id2iid:
            continue
        u, v = node_id2iid[u_id], node_id2iid[v_id]
        bu, bv = int(b[u]), int(b[v])
        induced_bp[(min(bu, bv), max(bu, bv))] += 1

    inp_bp = _bp_counts(input_edgelist_fp, b, node_id2iid)

    bp_budget = {}
    for key, ind_cnt in induced_bp.items():
        diff = ind_cnt - inp_bp.get(key, 0)
        if diff > 0:
            bp_budget[key] = diff
    return b, bp_budget


def build_bp_budget_direct(input_edgelist_fp, ref_edgelist_fp, clustering_fp,
                           outlier_mode, node_id2iid):
    """Direct-mode bp budget: ``ref_count - input_count`` clamped at 0.

    Returns ``(b, bp_budget)``. ``bp_budget`` only contains keys with a
    strictly positive deficit; missing keys are interpreted as zero by
    callers and the matcher refuses to place edges in those bp's.
    """
    b = build_block_assignment(node_id2iid, clustering_fp, outlier_mode)
    ref_bp = _bp_counts(ref_edgelist_fp, b, node_id2iid)
    inp_bp = _bp_counts(input_edgelist_fp, b, node_id2iid)

    bp_budget = {}
    for key, ref_cnt in ref_bp.items():
        diff = ref_cnt - inp_bp.get(key, 0)
        if diff > 0:
            bp_budget[key] = diff
    return b, bp_budget


def _bp_key(b, u, v):
    bu, bv = int(b[u]), int(b[v])
    return (min(bu, bv), max(bu, bv))


def match_missing_degrees_cluster_preserving_greedy(out_degs, exist_neighbor,
                                                    b, bp_budget):
    """Greedy variant gated by ``bp_budget``.

    Same heap-and-set scaffolding as ``match_missing_degrees_greedy`` but
    only partners whose bp still has remaining budget are considered, and
    each accept decrements the budget.
    """
    logging.info("Starting Cluster-Preserving Greedy matching algorithm...")
    available_node_set = {n for n, d in out_degs.items() if d > 0}
    available_node_degrees = {n: d for n, d in out_degs.items() if d > 0}

    initial_missing_stubs = sum(available_node_degrees.values())
    logging.info(f"Initial missing stubs: {initial_missing_stubs}")

    max_heap = [(-d, n) for n, d in available_node_degrees.items()]
    heapq.heapify(max_heap)

    degree_edges = set()

    while max_heap:
        _, c = heapq.heappop(max_heap)
        if c not in available_node_degrees:
            continue

        invalid_targets = exist_neighbor.get(c, set()).copy()
        invalid_targets.add(c)
        candidates = sorted(available_node_set - invalid_targets)
        candidates = [n for n in candidates if bp_budget.get(_bp_key(b, c, n), 0) > 0]

        avail_k = min(available_node_degrees[c], len(candidates))
        for k in range(avail_k):
            partner = candidates[k]
            bp = _bp_key(b, c, partner)
            if bp_budget.get(bp, 0) <= 0:
                continue
            degree_edges.add((min(c, partner), max(c, partner)))
            exist_neighbor[c].add(partner)
            exist_neighbor[partner].add(c)
            bp_budget[bp] -= 1
            available_node_degrees[partner] -= 1
            if available_node_degrees[partner] == 0:
                available_node_set.remove(partner)
                del available_node_degrees[partner]

        del available_node_degrees[c]
        available_node_set.discard(c)

    return degree_edges


def match_missing_degrees_cluster_preserving_true_greedy(out_degs, exist_neighbor,
                                                          b, bp_budget):
    """True-greedy variant gated by ``bp_budget``."""
    logging.info("Starting Cluster-Preserving True Greedy matching algorithm...")
    current_degrees = {n: d for n, d in out_degs.items() if d > 0}

    initial_missing_stubs = sum(current_degrees.values())
    logging.info(
        f"Initial missing stubs: {initial_missing_stubs} (Target edges: {initial_missing_stubs // 2})"
    )

    heap = [(-d, n) for n, d in current_degrees.items()]
    heapq.heapify(heap)

    degree_edges = set()
    stuck_nodes = set()

    while heap:
        neg_deg, u = heapq.heappop(heap)
        deg_u = -neg_deg
        if u not in current_degrees or deg_u != current_degrees[u]:
            continue

        invalid_targets = exist_neighbor.get(u, set())
        valid_targets = [
            n for n in current_degrees
            if n != u
            and n not in invalid_targets
            and bp_budget.get(_bp_key(b, u, n), 0) > 0
        ]

        if not valid_targets:
            stuck_nodes.add(u)
            del current_degrees[u]
            continue

        v = max(valid_targets, key=lambda x: (current_degrees[x], -x))
        bp = _bp_key(b, u, v)

        degree_edges.add((min(u, v), max(u, v)))
        exist_neighbor[u].add(v)
        exist_neighbor[v].add(u)
        bp_budget[bp] -= 1

        current_degrees[u] -= 1
        current_degrees[v] -= 1

        if current_degrees[u] > 0:
            heapq.heappush(heap, (-current_degrees[u], u))
        else:
            del current_degrees[u]

        if current_degrees[v] > 0:
            heapq.heappush(heap, (-current_degrees[v], v))
        elif v in current_degrees:
            del current_degrees[v]

    if stuck_nodes:
        logging.warning(f"Finished with {len(stuck_nodes)} gridlocked nodes.")

    return degree_edges


def match_missing_degrees_cluster_preserving_random_greedy(out_degs, exist_neighbor,
                                                            b, bp_budget):
    """Random-greedy variant gated by ``bp_budget``."""
    logging.info("Starting Cluster-Preserving Randomized Greedy matching algorithm...")

    available_degrees = {k: v for k, v in sorted(out_degs.items()) if v > 0}
    available_nodes = list(available_degrees.keys())

    initial_missing_stubs = sum(available_degrees.values())
    logging.info(
        f"Initial missing stubs: {initial_missing_stubs} (Target edges: {initial_missing_stubs // 2})"
    )

    degree_edges = set()
    stuck_nodes = set()

    while available_nodes:
        weights = [available_degrees[n] for n in available_nodes]
        u = random.choices(available_nodes, weights=weights, k=1)[0]

        invalid_targets = exist_neighbor.get(u, set())
        valid_targets = [
            n for n in available_nodes
            if n != u
            and n not in invalid_targets
            and bp_budget.get(_bp_key(b, u, n), 0) > 0
        ]

        if not valid_targets:
            available_nodes.remove(u)
            stuck_nodes.add(u)
            continue

        v_weights = [available_degrees[n] for n in valid_targets]
        v = random.choices(valid_targets, weights=v_weights, k=1)[0]
        bp = _bp_key(b, u, v)

        degree_edges.add((min(u, v), max(u, v)))
        exist_neighbor[u].add(v)
        exist_neighbor[v].add(u)
        bp_budget[bp] -= 1

        available_degrees[u] -= 1
        available_degrees[v] -= 1

        if available_degrees[u] == 0:
            available_nodes.remove(u)
        if available_degrees[v] == 0:
            available_nodes.remove(v)

    if stuck_nodes:
        stuck_stubs = sum(available_degrees[n] for n in stuck_nodes)
        logging.warning(
            f"Finished with {len(stuck_nodes)} physically gridlocked nodes. {stuck_stubs} missing stubs dropped."
        )

    return degree_edges


def match_missing_degrees_cluster_preserving_rewire(out_degs, exist_neighbor,
                                                    b, bp_budget,
                                                    max_retries=10):
    """Rewire variant via residual SBM + per-bp 2-opt swap.

    Builds a probs matrix from ``bp_budget`` (mass = remaining edges per
    bp), feeds graph-tool's ``generate_sbm`` with per-node out-degs, then
    cleans up self-loops / duplicates / pre-existing edges via the shared
    ``cluster_preserving_2opt_rewire`` helper. Anything still invalid
    after the swap loop is returned to the caller for hybrid fallback.
    """
    logging.info("Starting Cluster-Preserving Rewire matching algorithm...")
    import graph_tool.all as gt
    from scipy.sparse import dok_matrix

    n_blocks = int(b.max()) + 1 if len(b) else 0
    n_nodes = len(b)

    out_degs_array = np.zeros(n_nodes, dtype=int)
    for node_iid, deg in out_degs.items():
        if deg > 0:
            out_degs_array[node_iid] = deg

    probs = dok_matrix((n_blocks, n_blocks), dtype=int)
    for (B_i, B_j), cnt in bp_budget.items():
        if cnt <= 0:
            continue
        if B_i == B_j:
            probs[B_i, B_j] = 2 * cnt
        else:
            probs[B_i, B_j] = cnt
            probs[B_j, B_i] = cnt

    # graph_tool needs each block's degree sum to match its row sum.
    # Drop excess stubs (per-node, smallest id last) per block where
    # out_degs_array > row_sum, and pad row_sum's diagonal upward when it
    # exceeds out_degs (rare; happens if bp_budget overshoots residual).
    probs_csr = probs.tocsr()
    row_sums = np.array(probs_csr.sum(axis=1)).flatten()

    for k in range(n_blocks):
        nodes_in_k = np.where(b == k)[0]
        if len(nodes_in_k) == 0:
            continue
        D_k = int(out_degs_array[nodes_in_k].sum())
        E_k = int(row_sums[k])
        if D_k > E_k:
            excess = D_k - E_k
            for nd in nodes_in_k[::-1]:
                if excess <= 0:
                    break
                drop = min(excess, int(out_degs_array[nd]))
                out_degs_array[nd] -= drop
                excess -= drop
        elif E_k > D_k:
            deficit = E_k - D_k
            for i in range(deficit):
                out_degs_array[nodes_in_k[i % len(nodes_in_k)]] += 1
        diag = int(probs[k, k])
        if diag % 2 != 0:
            probs[k, k] = diag + 1
            out_degs_array[nodes_in_k[0]] += 1

    if int(out_degs_array.sum()) == 0:
        return set(), []

    g = gt.generate_sbm(
        b, probs.tocsr(),
        out_degs=out_degs_array,
        micro_ers=True,
        micro_degs=True,
        directed=False,
    )

    edges = g.get_edges()
    valid_pool = defaultdict(list)
    valid_set = set()
    invalid_edges = deque()
    for u, v in edges:
        u, v = int(u), int(v)
        e = normalize_edge(u, v)
        if u == v or e in valid_set:
            invalid_edges.append((u, v))
            continue
        valid_set.add(e)
        valid_pool[(int(min(b[u], b[v])), int(max(b[u], b[v])))].append(e)

    sbm_only, rewired = cluster_preserving_2opt_rewire(
        invalid_edges, valid_pool, b, max_retries,
    )

    placed = set(sbm_only) | set(rewired)
    leftover = []
    for u, v in placed:
        if v in exist_neighbor.get(u, set()):
            leftover.append((u, v))
        else:
            exist_neighbor[u].add(v)
            exist_neighbor[v].add(u)

    valid_edges = placed - set(leftover)
    for u, v in valid_edges:
        bp = _bp_key(b, u, v)
        bp_budget[bp] = max(0, bp_budget.get(bp, 0) - 1)
    return valid_edges, leftover


def match_missing_degrees_cluster_preserving_hybrid_bands(out_degs, exist_neighbor,
                                                           b, bp_budget):
    """Cluster-preserving hybrid: rewire then true-greedy fallback.

    Returns ``{"hybrid_rewire": set, "hybrid_true_greedy": set}``.
    """
    logging.info("Starting Cluster-Preserving Hybrid (Rewire -> True Greedy) algorithm...")

    valid_edges, leftover_edges = match_missing_degrees_cluster_preserving_rewire(
        out_degs, exist_neighbor, b, bp_budget, max_retries=10,
    )

    if not leftover_edges:
        return {"hybrid_rewire": valid_edges, "hybrid_true_greedy": set()}

    logging.info(
        f"Hybrid transition: {len(leftover_edges)} edges remained invalid; "
        f"falling back to cluster_preserving_true_greedy."
    )

    remaining_out_degs = defaultdict(int)
    for u, v in leftover_edges:
        remaining_out_degs[u] += 1
        remaining_out_degs[v] += 1
    remaining_out_degs = {n: d for n, d in remaining_out_degs.items() if d > 0}

    greedy_edges = match_missing_degrees_cluster_preserving_true_greedy(
        remaining_out_degs, exist_neighbor, b, bp_budget,
    )

    return {"hybrid_rewire": valid_edges, "hybrid_true_greedy": greedy_edges}


def match_missing_degrees_cluster_preserving_hybrid(out_degs, exist_neighbor,
                                                    b, bp_budget):
    """Backward-compat wrapper: flat union of the two hybrid bands."""
    bands = match_missing_degrees_cluster_preserving_hybrid_bands(
        out_degs, exist_neighbor, b, bp_budget,
    )
    return bands["hybrid_rewire"] | bands["hybrid_true_greedy"]


def export_degree_matched_edgelist(degree_edges, node_iid2id, output_dir,
                                   bands=None):
    """Write ``degree_matching_edge.csv`` with rows in band-block order
    (sorted within each band) and emit a sibling ``sources.json``.

    ``bands`` is an ordered list of ``(band_name, edges_iterable)`` pairs;
    if ``None``, fall back to a single anonymous band carrying every edge
    in ``degree_edges`` (the legacy single-set call shape).
    """
    if bands is None:
        bands = [("match_degree", degree_edges)]

    rows = []
    sources = {}
    cursor = 1
    for band_name, edge_iter in bands:
        sorted_edges = sorted(edge_iter)
        if not sorted_edges:
            continue
        for src, tgt in sorted_edges:
            rows.append((node_iid2id[src], node_iid2id[tgt]))
        sources[band_name] = [cursor, cursor + len(sorted_edges) - 1]
        cursor += len(sorted_edges)

    pd.DataFrame(rows, columns=["source", "target"]).to_csv(
        output_dir / "degree_matching_edge.csv", index=False,
    )
    with open(output_dir / "sources.json", "w") as f:
        json.dump(sources, f, indent=4)


# Algorithm registry consumed by main(). Each entry: (kind, fn, labels, is_cp).
#   kind="single"  → fn(...) returns edges set; bands = [(label, edges)].
#   kind="rewire"  → fn(..., max_retries=10) returns (edges, leftover);
#                    bands = [(label, edges)].
#   kind="hybrid"  → fn(...) returns {"hybrid_rewire": ..., "hybrid_true_greedy": ...};
#                    labels is a (rewire_label, tg_label) pair.
# is_cp=True signals the matcher takes (b, bp_budget) after the standard args.
ALGO_TABLE = {
    "greedy": (
        "single", match_missing_degrees_greedy,
        "match_degree_greedy", False,
    ),
    "true_greedy": (
        "single", match_missing_degrees_true_greedy,
        "match_degree_true_greedy", False,
    ),
    "random_greedy": (
        "single", match_missing_degrees_random_greedy,
        "match_degree_random_greedy", False,
    ),
    "rewire": (
        "rewire", match_missing_degrees_rewire,
        "match_degree_rewire", False,
    ),
    "hybrid": (
        "hybrid", match_missing_degrees_hybrid_bands,
        ("match_degree_hybrid_rewire", "match_degree_hybrid_true_greedy"),
        False,
    ),
    "cluster_preserving_greedy": (
        "single", match_missing_degrees_cluster_preserving_greedy,
        "match_degree_cluster_preserving_greedy", True,
    ),
    "cluster_preserving_true_greedy": (
        "single", match_missing_degrees_cluster_preserving_true_greedy,
        "match_degree_cluster_preserving_true_greedy", True,
    ),
    "cluster_preserving_random_greedy": (
        "single", match_missing_degrees_cluster_preserving_random_greedy,
        "match_degree_cluster_preserving_random_greedy", True,
    ),
    "cluster_preserving_rewire": (
        "rewire", match_missing_degrees_cluster_preserving_rewire,
        "match_degree_cluster_preserving_rewire", True,
    ),
    "cluster_preserving_hybrid": (
        "hybrid", match_missing_degrees_cluster_preserving_hybrid_bands,
        ("match_degree_cluster_preserving_hybrid_rewire",
         "match_degree_cluster_preserving_hybrid_true_greedy"),
        True,
    ),
}


def main():
    args = parse_args()
    out_dir = standard_setup(args.output_folder)

    random.seed(args.seed)
    np.random.seed(args.seed)

    algo = args.degree_matcher
    kind, algo_fn, labels, is_cp = ALGO_TABLE[algo]

    # Cluster-preserving rewire/hybrid call into gt.generate_sbm; seed
    # graph-tool's RNG too so the SBM sample is reproducible.
    if algo in ("cluster_preserving_rewire", "cluster_preserving_hybrid"):
        import graph_tool.all as gt
        gt.seed_rng(args.seed)

    if is_cp and args.input_clustering is None:
        raise SystemExit(
            f"--degree-matcher {algo} requires --input-clustering."
        )
    if is_cp and args.ref_clustering is None and not args.remap:
        args.ref_clustering = args.input_clustering

    logging.info(
        f"--- Starting Degree Matching ({algo.upper()}"
        f"{' + remap' if args.remap else ''} mode) ---"
    )

    if args.remap:
        with timed("Loaded rank-paired target degrees"):
            node_id2iid, node_iid2id, out_degs = load_remap_topologies(
                args.input_edgelist, args.ref_edgelist
            )
    else:
        with timed("Loaded reference topologies"):
            node_id2iid, node_iid2id, out_degs = load_reference_topologies(
                args.ref_edgelist, args.input_edgelist
            )

    with timed("Subtracted existing edges"):
        exist_neighbor, updated_out_degs = subtract_existing_edges(
            args.input_edgelist, node_id2iid, out_degs
        )

    if is_cp:
        if args.remap:
            with timed("Built per-bp budget (remap mode)"):
                b, bp_budget = build_bp_budget_remap(
                    args.input_edgelist, args.ref_edgelist,
                    args.input_clustering, args.outlier_mode, node_id2iid,
                )
        else:
            with timed("Built per-bp budget (direct mode)"):
                b, bp_budget = build_bp_budget_direct(
                    args.input_edgelist, args.ref_edgelist,
                    args.input_clustering, args.outlier_mode, node_id2iid,
                )

    with timed("Degree matching"):
        extra = (b, bp_budget) if is_cp else ()
        if kind == "single":
            degree_edges = algo_fn(updated_out_degs, exist_neighbor, *extra)
            bands = [(labels, degree_edges)]
        elif kind == "rewire":
            degree_edges, _ = algo_fn(
                updated_out_degs, exist_neighbor, *extra, max_retries=10,
            )
            bands = [(labels, degree_edges)]
        else:  # kind == "hybrid"
            band_dict = algo_fn(updated_out_degs, exist_neighbor, *extra)
            degree_edges = band_dict["hybrid_rewire"] | band_dict["hybrid_true_greedy"]
            bands = [
                (labels[0], band_dict["hybrid_rewire"]),
                (labels[1], band_dict["hybrid_true_greedy"]),
            ]

        logging.info(f"Added {len(degree_edges)} edges")

    with timed("Exported edgelist"):
        export_degree_matched_edgelist(
            degree_edges, node_iid2id, out_dir, bands=bands,
        )


if __name__ == "__main__":
    main()
